import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 1. LOAD YOUR DATA AND PARAMETERS HERE

# Paths to your CSV files
csv_file_path1 = "C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vyseldky260403/Distribuce/01phrase/word_form/all_SUD_phrase_word_form.csv"
csv_file_path2 = "C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vyseldky260403/Distribuce/02big_chunk/word_form/all_SUD_big_chunk_word_form.csv"
csv_file_path3 = "C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vyseldky260403/Distribuce/03chunk/word_form/all_SUD_chunk_word_form.csv"

# Load and process Data 1
df1 = pd.read_csv(csv_file_path1, sep=';')
df1 = df1.sort_values(by='frequency', ascending=False).reset_index(drop=True)
x1 = np.arange(1, len(df1) + 1)
y1 = df1['frequency'].values
firstConstr1, b1 = 25772, 1.31678738
# Zipf-Mandelbrot parameters
a_mandel1, b_mandel1 = 0.780088029, -0.743215607

# Load and process Data 2
df2 = pd.read_csv(csv_file_path2, sep=';')
df2 = df2.sort_values(by='frequency', ascending=False).reset_index(drop=True)
x2 = np.arange(1, len(df2) + 1)
y2 = df2['frequency'].values
firstConstr2, b2 = 25875, 1.27212784
# Zipf-Mandelbrot parameters
a_mandel2, b_mandel2 = 0.76079283, -0.750188163

# Load and process Data 3
df3 = pd.read_csv(csv_file_path3, sep=';')
df3 = df3.sort_values(by='frequency', ascending=False).reset_index(drop=True)
x3 = np.arange(1, len(df3) + 1)
y3 = df3['frequency'].values
firstConstr3, b3 = 30989, 0.815322509
# Zipf-Mandelbrot parameters
a_mandel3, b_mandel3 = 0.904330422, 0.445396373


# 2. SETUP FIGURE
fig, axes = plt.subplots(1, 3, figsize=(11.69, 3.84))

# --- PLOT 1 ---
ax1 = axes[0]

# Scatter plot for actual data (Black)
ax1.scatter(x1, y1, color='black', s=16, label='Data points')

# Standard Fitted curve (Red)
x_curve1 = np.geomspace(1, len(x1) + 1, len(x1))
y_curve1 = firstConstr1 * (x_curve1 ** -b1)
ax1.plot(x_curve1, y_curve1, linestyle='--', color='red', linewidth=1.5, label='Power law')

# Zipf-Mandelbrot Fitted curve (Blue)
y_mandel1 = firstConstr1 * ((x_curve1 + b_mandel1) / (1 + b_mandel1)) ** -a_mandel1
ax1.plot(x_curve1, y_mandel1, linestyle='--', color='green', linewidth=1.5, label='Zipf-Mandelbrot')

# Setting limits and labels
ax1.set_xlim(1, len(x1) + (len(x1) * 0.05))
ax1.set_ylim(1, max(y1) + (max(y1) * 1.5))
ax1.set_xscale('log')
ax1.set_yscale('log')
ax1.set_xlabel("Rank (log)", fontsize=12)
ax1.set_ylabel("Frequency (log)", fontsize=12)
ax1.set_title("Phrase word forms", fontsize=12, fontweight='bold', pad=10)

# Styling details
ax1.tick_params(axis='both', which='major', labelsize=10)
ax1.grid(True, linestyle=':', alpha=0.7)
ax1.legend(fontsize=9)


# --- PLOT 2 ---
ax2 = axes[1]

# Scatter plot for actual data (Black)
ax2.scatter(x2, y2, color='black', s=16, label='Data points')

# Standard Fitted curve (Red)
x_curve2 = np.geomspace(1, len(x2) + 1, len(x2))
y_curve2 = firstConstr2 * (x_curve2 ** -b2)
ax2.plot(x_curve2, y_curve2, linestyle='--', color='red', linewidth=1.5, label='Power law')

# Zipf-Mandelbrot Fitted curve (Blue)
y_mandel2 = firstConstr2 * ((x_curve2 + b_mandel2) / (1 + b_mandel2)) ** -a_mandel2
ax2.plot(x_curve2, y_mandel2, linestyle='--', color='green', linewidth=1.5, label='Zipf-Mandelbrot')

# Setting limits and labels
ax2.set_xlim(1, len(x2) + (len(x2) * 0.05))
ax2.set_ylim(1, max(y2) + (max(y2) * 1.5))
ax2.set_xscale('log')
ax2.set_yscale('log')
ax2.set_xlabel("Rank (log)", fontsize=12)
ax2.set_ylabel("Frequency (log)", fontsize=12)
ax2.set_title("Subphrase word forms", fontsize=12, fontweight='bold', pad=10)

# Styling details
ax2.tick_params(axis='both', which='major', labelsize=10)
ax2.grid(True, linestyle=':', alpha=0.7)
ax2.legend(fontsize=9)


# --- PLOT 3 ---
ax3 = axes[2]

# Scatter plot for actual data (Black)
ax3.scatter(x3, y3, color='black', s=16, label='Data points')

# Standard Fitted curve (Red)
x_curve3 = np.geomspace(1, len(x3) + 1, len(x3))
y_curve3 = firstConstr3 * (x_curve3 ** -b3)
ax3.plot(x_curve3, y_curve3, linestyle='--', color='red', linewidth=1.5, label='Power law')

# Zipf-Mandelbrot Fitted curve (Blue)
y_mandel3 = firstConstr3 * ((x_curve3 + b_mandel3) / (1 + b_mandel3)) ** -a_mandel3
ax3.plot(x_curve3, y_mandel3, linestyle='--', color='green', linewidth=1.5, label='Zipf-Mandelbrot')

# Setting limits and labels
ax3.set_xlim(1, len(x3) + (len(x3) * 0.05))
ax3.set_ylim(1, max(y3) + (max(y3) * 1.5))
ax3.set_xscale('log')
ax3.set_yscale('log')
ax3.set_xlabel("Rank (log)", fontsize=12)
ax3.set_ylabel("Frequency (log)", fontsize=12)
ax3.set_title("Chunk word forms", fontsize=12, fontweight='bold', pad=10)

# Styling details
ax3.tick_params(axis='both', which='major', labelsize=10)
ax3.grid(True, linestyle=':', alpha=0.7)
ax3.legend(fontsize=9)


# 4. ADJUST SPACING AND SAVE
plt.tight_layout(w_pad=3.0)

# Save the figure
folder_path = "C:/Users/nogol/Documents/Doktorat/Analyzy/SUD/vysledky260820/"
os.makedirs(folder_path, exist_ok=True)
save_path = os.path.join(folder_path, "rank_frequency_3plots_colored.png")

plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.5)
#plt.show()