import requests
import re
import textwrap
from src import config

def extract_code_only(text):
    """Extracts content between <CODE> tags."""
    match = re.search(r"<CODE>(.*?)</CODE>", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def convert_alteryx_formula(alteryx_formula, local_vars=None):
    """
    Transpiles Alteryx Expression Language to KNIME Column Expressions (JavaScript) using AI.
    
    Args:
        alteryx_formula (str): The raw Alteryx formula.
        local_vars (dict): ignored in AI version, kept for signature compatibility.
    """
    if not alteryx_formula: return "null;"
    
    clean_input = textwrap.dedent(alteryx_formula).strip()
    
    # We use 'r' prefix for the prompt string to fix syntax warnings
    system_prompt = r"""
    You are a code transpiler specialized in converting Alteryx Formulas to KNIME Column Expressions (JavaScript/Rhino).

    CRITICAL INSTRUCTION:
    Output ONLY the valid JavaScript code inside <CODE> tags. NO explanations.

    CONTEXT:
    The target is the KNIME "Column Expressions" node, which uses a specific JavaScript engine (Rhino/Nashorn) with custom KNIME functions.

    NUANCES & EXECUTION ORDER:
    1. Execution: Code runs row-by-row. Variables defined with 'var' persist only for the current row unless global scope is used (avoid globals).
    2. Data Types: Alteryx handles types loosely. KNIME is strict.
       - If concatenating strings: Ensure numeric columns are wrapped in string() if needed.
       - Use toNumber() for math on string columns.
    3. Missing Values: Alteryx uses Null(). KNIME uses null or Missing Value.
       - To check missing: isMissing(column("Col"))
       - To assign missing: null

    SYNTAX RULES:
    1. Column Reference: column("ColumnName")
    2. String Escaping: Double backslashes are REQUIRED for regex literals strings.
       - WRONG: "\d+"
       - RIGHT: "\\d+"
    3. Date Handling:
       - Alteryx 'DateTimeToday()' -> var currentDate = new Date().toISOString().substring(0, 10);
       - Alteryx 'DateTimeNow()' -> var currentDateTime = new Date().toISOString().replace("T", " ").substring(0, 19);
    4. Regex Functions (KNIME Specific):
       - Alteryx 'REGEX_Replace(str, pat, rep)' -> regexReplace(str, pat, rep)
       - Alteryx 'REGEX_Match(str, pat)' -> regexMatcher(str, pat)
    5. Conditional Logic:
       - Alteryx 'IF c THEN t ELSE f ENDIF' -> if (c) { t; } else { f; }
       - Alteryx 'IIF(c, t, f)' -> (c) ? t : f

    EXAMPLES:

    Example 1 (Simple Regex Replace):
    Input: REGEX_Replace([Col], "(\d+)", "ID_$1")
    Output: <CODE>regexReplace(column("Col"), "(\\d+)", "ID_$1")</CODE>

    Example 2 (Regex Match / Boolean):
    Input: REGEX_Match([Col], "^\d+$")
    Output: <CODE>regexMatcher(column("Col"), "^\\d+$")</CODE>

    Example 3 (Complex Date + String Logic):
    Input: "Log_" + DateTimeFormat(DateTimeToday(), "%Y-%m-%d") + "_" + [ID]
    Output: <CODE>
    var currentDate = new Date().toISOString().substring(0, 10);
    "Log_" + currentDate + "_" + column("ID");
    </CODE>

    Example 4 (Null Handling):
    Input: IF IsNull([Value]) THEN 0 ELSE [Value] ENDIF
    Output: <CODE>
    if (isMissing(column("Value"))) {
        0;
    } else {
        column("Value");
    }
    </CODE>
    """

    payload = {
        "model": config.FORMULA_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Input: {clean_input}\nOutput:"}
        ],
        "stream": False,
        "options": {
            "temperature": 0.0, 
            "stop": ["</CODE>"] 
        }
    }

    try:
        response = requests.post(config.OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        
        raw_output = response.json()['message']['content']
        # Append closing tag to ensure regex matches if LLM stopped strictly at tag
        return extract_code_only(raw_output + "</CODE>")
        
    except Exception as e:
        print(f"[Formula Error] {e}")
        # Fallback to returning comment so workflow doesn't crash
        return f"// Error converting: {clean_input}"