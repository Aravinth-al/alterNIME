import re
import json
import requests
from collections import defaultdict
from transpiler.engine import get_parser, AlteryxToAST
from transpiler.codegen import KNIMECodeGenerator
from src import config

# --- 1. SYSTEMATIC COMPONENTS ---
PARSER = get_parser()

def preprocess(formula: str) -> str:
    """Normalize keywords to uppercase for the strict parser."""
    keywords = ['if', 'then', 'elseif', 'else', 'endif', 'iif', 'or', 'and', 'not', 'true', 'false']
    for kw in keywords:
        formula = re.sub(rf'\b{kw}\b', kw.upper(), formula, flags=re.IGNORECASE)
    return formula

# --- 2. AI FALLBACK COMPONENTS (Llama 3.2) ---
def convert_with_ai_fallback(field, steps):
    """
    Fallback function: Sends difficult logic to Llama 3.2
    """
    system_prompt = r"""
    You are a KNIME JavaScript Compiler. 
    Task: Convert sequential Alteryx formulas into a SINGLE, STATEFUL KNIME script.

    ### COMPILER RULES
    1. **STATE**: Define `var val`. If first step reads [Tax ID], init `val = column("Tax ID")`. Else init `val = column("SOURCE")`.
    2. **STRICT DICTIONARY**:
       - IsNull(x) -> isMissing(x)
       - REGEX_Match(s, p) -> regexMatcher(s, ".*" + p + ".*")
    3. **NO RETURN**: End script with `val;`.
    4. **SAFETY**: Double escape backslashes (`\\d`).
    """

    user_message = f"""
    TARGET COLUMN: {field}
    STEPS: {json.dumps(steps)}
    OUTPUT JSON: {{"script": "..."}}
    """

    payload = {
        "model": config.FORMULA_MODEL_NAME,
        "format": "json",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "options": {"temperature": 0.0}
    }

    try:
        if config.DEBUG_MODE: print(f"⚠️ [Fallback] Calling AI for {field}...")
        response = requests.post(config.OLLAMA_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        # Extract script from JSON
        data = json.loads(response.json()['message']['content'])
        script = data.get("script", "// AI Conversion Failed")
        
        # Apply Safety Net (Post-Processing)
        script = script.replace("isNull(", "isMissing(")
        return script

    except Exception as e:
        return f"// Critical Error: Both Transpiler and AI failed. {str(e)}"

# --- 3. MAIN HYBRID CONVERTER ---
def convert_formulas_bulk(formulas_list):
    """
    Deterministic Transpiler with Safe Initialization.
    """
    if not formulas_list: return {}

    # 1. Group formulas by Target Column
    grouped_logic = defaultdict(list)
    for item in formulas_list:
        grouped_logic[item['field']].append(item['expression'])

    final_results = {}

    for field, expressions in grouped_logic.items():
        try:
            # --- ATTEMPT 1: SYSTEMATIC TRANSPILER ---
            script_lines = []
            
            # --- SAFE INITIALIZATION BLOCK ---
            # Try to read the column (in case we are updating it).
            # If it fails (because it's a new column), catch the error and default to null.
            script_lines.append(f'var val = null;')
            script_lines.append(f'try {{ val = column("{field}"); }} catch(e) {{}}') 
            
            generator = KNIMECodeGenerator(target_column=field)
            
            for expr in expressions:
                clean_expr = preprocess(expr)
                tree = PARSER.parse(clean_expr)
                ast = AlteryxToAST().transform(tree)
                js_expression = generator.generate(ast)
                
                # Update the variable
                script_lines.append(f'val = {js_expression};')
            
            # Final Return
            script_lines.append('val;')
            final_results[field] = "\n".join(script_lines)

        except Exception as e:
            # --- ATTEMPT 2: AI FALLBACK ---
            print(f"🔄 Transpiler failed on '{field}' ({e}). Switching to AI...")
            final_results[field] = convert_with_ai_fallback(field, expressions)

    return final_results

def convert_alteryx_formula(expr):
    res = convert_formulas_bulk([{'field': 'Result', 'expression': expr}])
    return res.get('Result', '// Error')