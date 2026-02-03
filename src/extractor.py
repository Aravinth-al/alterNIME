import xml.etree.ElementTree as ET
import zipfile
import os
import shutil
import glob
from src import config

def prepare_workflow_file(file_path):
    """
    Prepares the workflow file for parsing.
    - If .yxzp: Unzips to temp folder and finds the main .yxmd/.yxwz.
    - If .yxmd or .yxwz: Returns the path directly.
    """
    temp_extract_dir = os.path.join(config.BASE_DIR, "temp_extract")
    
    # Clear previous temp data
    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)
    os.makedirs(temp_extract_dir)

    # 1. Direct Text Files (Workflow or App)
    if file_path.lower().endswith(('.yxmd', '.yxwz')):
        print(f"📄 Detected Direct File: {os.path.basename(file_path)}")
        return file_path

    # 2. Archives (Zip/YXZP)
    print(f"📦 Unpacking Archive: {os.path.basename(file_path)}...")
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            z.extractall(temp_extract_dir)
    except zipfile.BadZipFile:
        print(f"❌ Error: {file_path} is not a valid zip file.")
        return None
    
    # Search for workflow files inside the zip
    # Priority: .yxmd (standard) -> .yxwz (app)
    candidates = glob.glob(os.path.join(temp_extract_dir, "**", "*.yxmd"), recursive=True)
    if not candidates:
        candidates = glob.glob(os.path.join(temp_extract_dir, "**", "*.yxwz"), recursive=True)
        
    return candidates[0] if candidates else None

def get_node_config(tool_type, node_xml):
    """Extracts logic and coordinates."""
    conf = node_xml.find('.//Properties/Configuration')
    data = {}
    
    # 1. Capture Visual Coordinates (Crucial for Plotting)
    gui = node_xml.find('.//GuiSettings')
    if gui is not None:
        pos = gui.find('Position')
        if pos is not None:
            try:
                data['x'] = float(pos.get('x', '0'))
                data['y'] = float(pos.get('y', '0'))
            except ValueError:
                data['x'] = 0.0
                data['y'] = 0.0
    else:
        data['x'] = 0.0
        data['y'] = 0.0

    # 2. Extract Logic
    if conf is not None:
        # Formulas
        if "Formula" in tool_type:
            data["formulas"] = [{"field": f.get("field"), "expression": f.get("expression")} 
                                for f in conf.findall('.//FormulaField')]
        
        # Joins
        elif "Join" in tool_type:
            data["join_keys"] = []
            for side in ["Left", "Right"]:
                fields = conf.findall(f'.//JoinInfo[@connection="{side}"]/Field')
                data["join_keys"].append({"side": side, "cols": [f.get("field") for f in fields]})
            
            # Extract Select Configuration for Join
            select_fields = []
            for f in conf.findall('.//SelectConfiguration//SelectField'):
                select_fields.append({
                    'field': f.get('field'),
                    'selected': f.get('selected'),
                    'rename': f.get('rename'),
                    'input': f.get('input') # Helper to know if it came from Right input
                })
            data['select_fields'] = select_fields

        # Input Data
        elif "DbFileInput" in tool_type:
            file_node = conf.find("File")
            if file_node is not None and file_node.text:
                raw_text = file_node.text
                if "|||" in raw_text or "aka:" in raw_text or "select" in raw_text.lower():
                    data['input_type'] = 'DB'
                    parts = raw_text.split("|||")
                    if len(parts) > 1:
                        data['sql_query'] = parts[1].strip()
                    else:
                        data['sql_query'] = raw_text
                else:
                    data['input_type'] = 'File'
                    data['file_path'] = raw_text

        # Summarize (GroupBy)
        elif "Summarize" in tool_type:
            summarize_fields = []
            for field in conf.findall('.//SummarizeFields/SummarizeField'):
                summarize_fields.append({
                    'field': field.get('field'),
                    'action': field.get('action'),
                    'rename': field.get('rename')
                })
            data['summarize_fields'] = summarize_fields
        
        # Union
        elif "Union" in tool_type:
            # DEBUG: Check if Union config is captured
            print(f"   [DEBUG] Found Union Tool.")
            data['mode'] = conf.findtext('Mode')
            data['output_mode'] = conf.findtext('ByName_OutputMode')

        # Select (AlteryxSelect)
        elif "AlteryxSelect" in tool_type or "Select" in tool_type:
            select_fields = []
            # Try finding SelectFields directly under Configuration
            fields = conf.findall('SelectFields/SelectField')
            # If not found, try recursive search (less safe but covers variations)
            if not fields:
                fields = conf.findall('.//SelectField')
            
            for field in fields:
                select_fields.append({
                    'field': field.get('field'),
                    'selected': field.get('selected'),
                    'rename': field.get('rename'),
                    'type': field.get('type'),
                    'size': field.get('size')
                })
            data['select_fields'] = select_fields

    return data

def parse_workflow(workflow_path):
    """Main parsing logic."""
    if not workflow_path:
        print("❌ No valid workflow file found.")
        return None
        
    try:
        tree = ET.parse(workflow_path)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ XML Parse Error: {e}")
        return None

    nodes = []
    edges = []

    # Parse Nodes
    for node in root.findall('.//Node'):
        tool_id = node.get('ToolID')
        gui = node.find('GuiSettings')
        plugin = gui.get('Plugin', "Unknown") if gui is not None else "Unknown"
        
        # Clean Tool Name
        tool_type = plugin.split('.')[-1] if "." in plugin else plugin
        if "Macro" in plugin: tool_type = "Macro"

        config_data = get_node_config(tool_type, node)

        nodes.append({
            "id": tool_id,
            "type": tool_type,
            "x": config_data['x'],
            "y": config_data['y'],
            "config": config_data
        })

    # Parse Connections
    for conn in root.findall('.//Connection'):
        origin = conn.find('Origin')
        destination = conn.find('Destination')
        
        if origin is not None and destination is not None:
            edges.append({
                "source": origin.get('ToolID'),
                "target": destination.get('ToolID'),
                "origin_connection": origin.get('Connection'),       
                "destination_connection": destination.get('Connection'), 
                "name": conn.get('name', '')
            })

    # Cleanup (Only if we created a temp dir for a zip)
    temp_dir = os.path.join(config.BASE_DIR, "temp_extract")
    if os.path.exists(temp_dir) and config.INPUT_DIR not in workflow_path:
        shutil.rmtree(temp_dir)

    return {"nodes": nodes, "edges": edges}