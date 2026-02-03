import matplotlib
# CRITICAL FIX: Force non-interactive backend for Web/Flask use
matplotlib.use('Agg') 

import json
import networkx as nx
import matplotlib.pyplot as plt
import os

def draw_exact_workflow(graph_data, output_path):
    """Draws the workflow using exact Alteryx coordinates."""
    
    # Safety Check
    if not graph_data.get('nodes'):
        print("⚠️  No nodes to visualize.")
        return

    G = nx.DiGraph()
    pos = {}
    node_colors = []
    labels = {}

    # 1. Build Graph & Position Dictionary
    for n in graph_data['nodes']:
        n_id = n['id']
        n_type = n['type']
        
        G.add_node(n_id)
        
        # Alteryx Coords: (0,0) is Top-Left. 
        # Matplotlib Coords: (0,0) is Bottom-Left.
        # We must FLIP the Y-axis (-n['y']) so the graph isn't upside down.
        pos[n_id] = (n['x'], -n['y']) 
        
        labels[n_id] = f"{n_id}\n{n_type}"
        
        # Color Coding for easier visual debugging
        if "Input" in n_type or "Reader" in n_type: 
            col = '#90EE90'   # Green
        elif "Join" in n_type: 
            col = '#FFD700'   # Yellow/Gold
        elif "Browse" in n_type or "Output" in n_type: 
            col = '#FFB6C1'   # Pink
        elif "Formula" in n_type or "Filter" in n_type: 
            col = '#ADD8E6'   # Blue
        else: 
            col = '#D3D3D3'   # Grey
        node_colors.append(col)

    # 2. Add Edges
    for e in graph_data['edges']:
        G.add_edge(e['source'], e['target'])

    # 3. Plot Configuration
    plt.figure(figsize=(20, 12)) # Large canvas for clarity
    
    # Draw Nodes (Square shape 's' mimics icons better)
    nx.draw_networkx_nodes(G, pos, node_size=2500, node_color=node_colors, 
                           edgecolors='black', node_shape='s', linewidths=1)
    
    # Draw Labels
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight="bold")
    
    # Draw Edges
    nx.draw_networkx_edges(G, pos, arrowstyle='-|>', arrowsize=20, edge_color='gray', width=1.5)

    plt.title("Alteryx Workflow Structure (Exact Layout)", fontsize=16)
    plt.axis('off')
    
    # Ensure directory exists before saving
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close() # Close memory to prevent leaks
    print(f"🖼️  Graph saved to {output_path}")