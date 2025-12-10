import pandas as pd

# Dictionary mapping sheet names to CSV file paths
csv_files = {
    "Spark of Rebellion": "spark_of_rebellion.csv",
    "Shadows of the Galaxy": "shadows_of_the_galaxy.csv",
    "Twilight of the Republic": "twilight_of_the_republic.csv",
    "Jump to Lightspeed": "jump_to_lightspeed.csv",
    "Legends of the Force": "legends_of_the_force.csv",
    "Secrets of Power": "secrets_of_power.csv",
}

# Create Excel writer object
output_file = "star_wars_unlimited_inventory.xlsx"

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    for sheet_name, csv_file in csv_files.items():
        # Read each CSV and write to a separate sheet
        df = pd.read_csv(csv_file)
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"Created {output_file} with {len(csv_files)} sheets")
