from src import config, extractor, builder, visualizer
import os

def run():
    print(">>> ALTERNIME-2.0: SKELETON BUILDER")
    
    # 1. SETUP
    if not os.path.exists(config.INPUT_DIR):
        os.makedirs(config.INPUT_DIR)
        print("Created input/ directory. Add .yxzp files.")
        return
    
    files = [f for f in os.listdir(config.INPUT_DIR) if f.endswith('.yxzp') or f.endswith('.yxmd')]
    if not files:
        print("No .yxzp or .yxmd files found in input/.")
        return
    
    input_path = os.path.join(config.INPUT_DIR, files[0])
    
    # 2. EXTRACT
    print(f"1. Parsing {files[0]}...")
    yxmd = extractor.extract_yxzp(input_path)
    graph = extractor.parse_workflow(yxmd)
    
    if not graph: return

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