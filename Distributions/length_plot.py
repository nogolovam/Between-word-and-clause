import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 1. LOAD YOUR DATA HERE
# Update these paths to point to your new CSV files
csv_file_path1 = "C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260820/01phrase_length_Poisson.csv"
csv_file_path2 = "C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260820/02subphrase_length_Poisson.csv"
csv_file_path3 = "C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260820/03chunk_length_Poisson.csv"

# Load the data (assuming ';' separator based on your previous script)
df1 = pd.read_csv(csv_file_path1, sep=',')
df2 = pd.read_csv(csv_file_path2, sep=',')
df3 = pd.read_csv(csv_file_path3, sep=',')

# Group the data and titles for easy looping
dfs = [df1, df2, df3]
titles = ["Phrases in subphrase count", "Subphrases in chunk count", "Chunks in word count"]

# 2. SETUP FIGURE
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
width = 0.35  # The width of the bars

# 3. PLOT EACH GRAPH
for i, ax in enumerate(axes):
    df = dfs[i]

    # Optional: ensure data is sorted by length before plotting
    df = df.sort_values(by='length').reset_index(drop=True)

    # Set the x locations for the groups
    x = np.arange(len(df['length']))

    # Plot grouped bars
    # Light gray for actual frequency (fx), black for model predicted (NPx)
    ax.bar(x - width / 2, df['fx'], width, label='Observed frequency (fx)', color='silver', edgecolor='black')
    ax.bar(x + width / 2, df['NPx'], width, label='Theoretical frequency (N Px)', color='black', edgecolor='black')

    # Setting labels and title
    ax.set_title(titles[i], fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel("length", fontsize=11, labelpad=15)
    ax.set_ylabel("frequency", fontsize=11, labelpad=10)

    # Configure X-axis ticks to show the actual lengths underneath the grouped bars
    ax.set_xticks(x)
    ax.set_xticklabels(df['length'])
    # Note: If you want to completely hide the x-tick numbers like in your image,
    # simply uncomment the line below:
    # ax.set_xticklabels([])

    # Format Y-axis to use scientific notation (e.g., 2e+05) to match your image
    ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))

    # Styling: Remove top and right borders to match the "R" style plot in the picture
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# Add a single legend for the entire figure at the bottom
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', ncol=2, bbox_to_anchor=(0.5, -0.05), frameon=False)

# 4. ADJUST SPACING AND SAVE
plt.tight_layout(w_pad=3.0)

# Save the figure
folder_path = "C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260820/"
os.makedirs(folder_path, exist_ok=True)
save_path = os.path.join(folder_path, "length_distribution_Poisson.png")

plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.3)
print(f"Figure saved successfully to: {save_path}")
# plt.show()