import pandas as pd

# Prevent truncating long strings
pd.set_option('display.max_colwidth', None)

# Load CSVs
group_df = pd.read_csv("Group.csv")
stz_df = pd.read_csv("STZ.csv")

# Column names
link_col = "Add plots & tables: please name each plot or table file by  each Behavioural Type and Method (Test, task, maze)"
doi_col = "Doi Paper"
N_control_col = "In control behavioral group: N = "
N_STZ_col =  "In STZ behavioral group: N = "


behrad_rows = group_df[group_df["group"] == "Behrad"]

# Adjust indices for pandas (idx counts from 1 including header row)
adjusted_indices = behrad_rows["idx"] - 2

# Extract data from STZ.csv and include original idx
result = pd.DataFrame({
    "idx": behrad_rows["idx"].values,
    "Link": stz_df.iloc[adjusted_indices][link_col].values,
    "DOI": stz_df.iloc[adjusted_indices][doi_col].values,
    "N control": stz_df.iloc[adjusted_indices][N_control_col].values,
    "N STZ" : stz_df.iloc[adjusted_indices][N_STZ_col].values
})

# Save to CSV
result.to_csv("Behrad_links.csv", index=False)

print("✅ Extracted idx, links, and DOIs saved to Behrad_links.csv")
