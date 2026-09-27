import pandas as pd

input_file = "data/raw/schemes.csv"
output_file = "data/raw/schemes_utf8.csv"

# Read the original CSV using Windows encoding
df = pd.read_csv(input_file, encoding="cp1252")

# Save as UTF-8
df.to_csv(output_file, index=False, encoding="utf-8")

print("CSV converted successfully!")
print("Saved to:", output_file)
print("Rows:", len(df))
print("Columns:", list(df.columns))