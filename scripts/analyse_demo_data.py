import math

import matplotlib.pyplot as plt
import pandas as pd

# --- Load and filter ---
df = pd.read_parquet(
    r"C:\Users\hugop\Documents\projects\nz-census-map\nz-census-map-backend\data\db-tables\demographic_data_table.parquet"
)

df = df[df["area_code"].astype(str).str.len() == 6]  # SA2 areas
df = df[~df["variable_id"].str.startswith("pop_")]   # drop pop_ variables

variable_ids = sorted(df["variable_id"].unique())
print(f"Found {len(variable_ids)} variables to plot")

# --- Split into 5 groups (as evenly as possible) ---
n_groups = 5
group_size = math.ceil(len(variable_ids) / n_groups)
groups = [variable_ids[i:i + group_size] for i in range(0, len(variable_ids), group_size)]

# --- Plot each group as a grid of histograms ---
for group_idx, group_vars in enumerate(groups, start=1):
    n_vars = len(group_vars)
    n_cols = 4
    n_rows = math.ceil(n_vars / n_cols)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 4, n_rows * 3.5))
    axes = axes.flatten() if n_vars > 1 else [axes]

    for ax, var_id in zip(axes, group_vars):
        values = df.loc[df["variable_id"] == var_id, "variable_value"].dropna()
        ax.hist(values, bins=20, density=True, color="steelblue", edgecolor="white")
        ax.set_title(var_id, fontsize=9)
        ax.set_xlabel("Value", fontsize=8)
        ax.set_ylabel("Density", fontsize=8)
        ax.tick_params(labelsize=7)

    # Hide any unused subplot axes (when the last group has fewer than n_rows*n_cols vars)
    for ax in axes[n_vars:]:
        ax.axis("off")

    fig.suptitle(f"Variable distributions — group {group_idx}", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])

    out_path = f"variable_distributions_group_{group_idx}.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"Saved {out_path} ({n_vars} variables)")