import pandas as pd
import matplotlib.pyplot as plt

# Load the data
data_path = './output1.csv'
data = pd.read_csv(data_path)

# Extract start and end node IDs from the Link ID column
# Assuming Link ID format "startNode_endNode"
data['Start Node ID'] = data['Link ID'].apply(lambda x: float(x.split('_')[0]))
data['End Node ID'] = data['Link ID'].apply(lambda x: float(x.split('_')[1]))

# Map node IDs to their positions for quick lookup
node_positions = dict(zip(data['Node ID'], zip(data['X POS'], data['Y POS'])))

# Initialize the plot
plt.figure(figsize=(10, 10))

# Plot nodes
for node_id, (x, y) in node_positions.items():
    plt.scatter(x, y, color='blue')  # Nodes as blue points

# Draw links between nodes
for _, row in data.iterrows():
    start_node_id, end_node_id = row['Start Node ID'], row['End Node ID']
    if start_node_id in node_positions and end_node_id in node_positions:
        start_pos = node_positions[start_node_id]
        end_pos = node_positions[end_node_id]
        plt.plot([start_pos[0], end_pos[0]], [start_pos[1], end_pos[1]], 'k-')  # Links as black lines

plt.xlabel('X Position')
plt.ylabel('Y Position')
plt.title('AGV Map Visualization')
plt.show()
