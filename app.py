import os
import uuid
import json
import time
import shutil
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_file, url_for, after_this_request
from src import config, extractor, visualizer, formula_converter, builder, mappings

app = Flask(__name__)

# --- CRITICAL CONFIGURATION ---
# These keys MUST be set for the app to work.
app.config['UPLOAD_FOLDER'] = config.INPUT_DIR
app.config['OUTPUT_FOLDER'] = config.OUTPUT_DIR
app.config['STATIC_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static')
app.config['GRAPH_FOLDER'] = os.path.join(app.config['STATIC_FOLDER'], 'graphs')

# Create directories if they don't exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'], app.config['GRAPH_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# Global Session Store
SESSIONS = {}

@app.route('/')
def index():
    return render_template('index.html')

# --- STAGE 1: UPLOAD ---
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files['file']
    
    session_id = str(uuid.uuid4())
    filename = f"{session_id}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    SESSIONS[session_id] = {
        "filepath": filepath,
        "filename": file.filename,
        "graph": None
    }
    
    return jsonify({"status": "success", "session_id": session_id})

# --- STAGE 2: VISUALIZE ---
@app.route('/visualize/<session_id>')
def visualize(session_id):
    if session_id not in SESSIONS: return jsonify({"error": "Expired"}), 404
    session = SESSIONS[session_id]

    workflow_file = extractor.prepare_workflow_file(session['filepath'])
    graph = extractor.parse_workflow(workflow_file)
    session['graph'] = graph 
    
    img_filename = f"viz_{session_id}.png"
    img_path = os.path.join(app.config['GRAPH_FOLDER'], img_filename)
    visualizer.draw_exact_workflow(graph, img_path)
    
    return jsonify({
        "status": "success",
        "image_url": f"/static/graphs/{img_filename}",
        "node_count": len(graph['nodes'])
    })

# --- STAGE 3: STREAM CONVERSION ---
@app.route('/stream_conversion/<session_id>')
def stream_conversion(session_id):
    def generate():
        session = SESSIONS.get(session_id)
        if not session or not session['graph']:
            yield "data: Error: Session lost\n\n"
            return

        graph = session['graph']
        total = len(graph['nodes'])
        
        yield f"data: {json.dumps({'progress': 0, 'log': '🚀 Initializing Conversion Engine...'})}\n\n"

        for i, node in enumerate(graph['nodes']):
            tool_type = node['type']
            knime_map = mappings.get_spec(tool_type)['name']
            time.sleep(0.01) # Small delay for visual effect

            if "Formula" in tool_type and 'formulas' in node['config']:
                 yield f"data: {json.dumps({'progress': int((i/total)*100), 'log': f'⚡ AI Generating Logic for Node {node['id']}...'})}\n\n"
                 js_dict = formula_converter.convert_formulas_bulk(node['config']['formulas'])
                 node['config']['reviewed_js'] = js_dict
                 msg = f"✅ Node {node['id']}: Translated formulas."
            else:
                 msg = f"INFO: Node {node['id']} ({tool_type}) → {knime_map}"

            yield f"data: {json.dumps({'progress': int(((i+1)/total)*100), 'log': msg})}\n\n"
        
        yield f"data: {json.dumps({'progress': 100, 'log': '✨ Analysis Complete.', 'done': True})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

# --- STAGE 4: REVIEW ---
@app.route('/review/<session_id>')
def review(session_id):
    session = SESSIONS.get(session_id)
    if not session: return "Session Expired", 400
    
    nodes_data = []
    for node in session['graph']['nodes']:
        
        # Prepare Formula Data
        formula_comparison = []
        if "Formula" in node['type'] and 'formulas' in node['config']:
            # Get the Converted Code (if it exists)
            converted_dict = node['config'].get('reviewed_js', {})
            
            # Match Original vs Converted
            for original_f in node['config']['formulas']:
                col = original_f['field']
                original_expr = original_f['expression']
                # Get the converted JS for this specific column
                converted_expr = converted_dict.get(col, "// No conversion found")
                
                formula_comparison.append({
                    "column": col,
                    "original": original_expr,
                    "converted": converted_expr
                })

        nodes_data.append({
            "id": node['id'],
            "type": node['type'],
            "knime_default": mappings.get_spec(node['type'])['name'],
            "is_formula": "Formula" in node['type'],
            "formulas": formula_comparison, # New List
            # Keep js_code for the builder logic compatibility if needed, 
            # though we primarily rely on the list above for the UI now.
            "js_code": node['config'].get('reviewed_js', {}) 
        })

    return render_template('review.html', nodes=nodes_data, session_id=session_id)

# --- STAGE 5: BUILD ---
@app.route('/build/<session_id>', methods=['POST'])
def build(session_id):
    session = SESSIONS.get(session_id)
    if not session: return jsonify({"error": "Expired"}), 400
    
    edits = request.json 
    graph = session['graph']

    # Apply Edits
    for node in graph['nodes']:
        nid = str(node['id'])
        if nid in edits:
            if 'js_code' in edits[nid]:
                node['config']['reviewed_js'] = edits[nid]['js_code']
            if 'knime_type' in edits[nid]:
                node['config']['knime_type_override'] = edits[nid]['knime_type']

    # 1. Build the skeleton (Default name: skeleton.knwf)
    builder.build_skeleton(graph)
    
    # 2. Rename it to a session-specific file to avoid collisions
    default_output = os.path.join(app.config['OUTPUT_FOLDER'], "skeleton.knwf")
    output_filename = f"workflow_{session_id}.knwf"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    
    if os.path.exists(default_output):
        # Remove existing file if it exists (overwrite)
        if os.path.exists(output_path):
            os.remove(output_path)
        shutil.move(default_output, output_path)
    
    session['output_file'] = output_filename

    return jsonify({"status": "success", "redirect": url_for('report', session_id=session_id)})

# --- STAGE 6: REPORT & DOWNLOAD ---
@app.route('/report/<session_id>')
def report(session_id):
    session = SESSIONS.get(session_id)
    if not session: return redirect(url_for('index'))
    
    # Suggest a name: Original filename (minus extension) + .knwf
    original_name = os.path.splitext(session['filename'])[0]
    suggested_name = f"{original_name}.knwf"
    
    # FIX: Pass session_id explicitly to the template
    return render_template('report.html', session=session, session_id=session_id, suggested_name=suggested_name)

@app.route('/download/<session_id>')
def download(session_id):
    session = SESSIONS.get(session_id)
    if not session: return "Session Expired", 400
    
    # Path to the built file
    real_filename = session['output_file']
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], real_filename)
    
    # Get custom name from user query param
    download_name = request.args.get('name', real_filename)
    if not download_name.endswith('.knwf'):
        download_name += '.knwf'

    # CLEANUP LOGIC: Delete files AFTER they are sent
    @after_this_request
    def cleanup(response):
        try:
            # 1. Delete Uploaded Input
            if os.path.exists(session['filepath']):
                os.remove(session['filepath'])
            
            # 2. Delete Generated Output
            if os.path.exists(file_path):
                os.remove(file_path)
                
            # 3. Delete Temp Extraction Folder (if exists)
            temp_dir = os.path.join(config.BASE_DIR, "temp_extract")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

            print(f"🧹 Cleaned up session {session_id}")
        except Exception as e:
            print(f"⚠️ Cleanup Error: {e}")
        return response

    return send_file(file_path, as_attachment=True, download_name=download_name)

if __name__ == '__main__':
    app.run(debug=True, port=5000)