import pandas as pd

def remove_duplicates_by_pmid(csv_file_path, output_file_path):
    
    df = pd.read_csv(csv_file_path)

    duplicate_rows = df[df.duplicated('Pmid', keep=False)]
    if not duplicate_rows.empty:
        print(f"Found {len(duplicate_rows)} rows with duplicate 'Pmid' values:")
        print(duplicate_rows)
    else:
        print("No duplicate 'Pmid' values found.")

    df_cleaned = df.drop_duplicates(subset='Pmid', keep='first')

    df_cleaned.to_csv(output_file_path, index=False)
    print(f"Cleaned data saved to {output_file_path}")

input_csv = "search_result.csv" 
output_csv = "search_result.csv"
remove_duplicates_by_pmid(input_csv, output_csv)