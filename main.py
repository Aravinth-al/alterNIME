from src import config, extractor, builder, visualizer
import os

def run():
    print(">>> altKNIME-2.0: SKELETON BUILDER")
    
    # 1. SETUP
    if not os.path.exists(config.INPUT_DIR):
        os.makedirs(config.INPUT_DIR)
        print("Created input/ directory. Add .yxzp, .yxmd, or .yxwz files.")
        return
    
    # Search for all supported Alteryx file types
    valid_extensions = ('.yxzp', '.yxmd', '.yxwz')
    files = [f for f in os.listdir(config.INPUT_DIR) if f.lower().endswith(valid_extensions)]
    
    if not files:
        print(f"No valid Alteryx files {valid_extensions} found in input/.")
        return
    
    input_path = os.path.join(config.INPUT_DIR, files[0])
    
    # 2. EXTRACT
    print(f"1. Processing {files[0]}...")
    
    # Handles .yxzp (zip), .yxmd (xml), and .yxwz (xml app)
    workflow_file = extractor.prepare_workflow_file(input_path)
    
    if not workflow_file:
        print("❌ Failed to identify a valid workflow XML file.")
        return

    graph = extractor.parse_workflow(workflow_file)
    
    if not graph: 
        print("❌ Failed to parse workflow graph.")
        return

    # 3. VISUALIZE (Proof of Structure)
    print("2. Visualizing Structure...")
    if not os.path.exists(config.OUTPUT_DIR): os.makedirs(config.OUTPUT_DIR)
    
    visualizer.draw_exact_workflow(graph, os.path.join(config.OUTPUT_DIR, "structure.png"))
    
    # 4. BUILD SKELETON (Proof of KNIME Compat)
    print("3. Generating KNIME Skeleton...")
    builder.build_skeleton(graph)
    
    print("✅ DONE. Check output/skeleton.knwf")

if __name__ == "__main__":
    run()