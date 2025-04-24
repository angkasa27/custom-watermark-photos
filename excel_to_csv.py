import pandas as pd

def convert_excel_to_csv(excel_file_path, sheet_name, csv_file_path):
    """
    Convert a specific sheet from an Excel file to a CSV file.

    Parameters:
    excel_file_path (str): Path to the source Excel file.
    sheet_name (str): Name of the sheet to convert.
    csv_file_path (str): Path to save the output CSV file.
    """
    try:
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        df = df.map(lambda x: x.replace('\n', ' ').replace('  ', ' ') if isinstance(x, str) else x)
        df.to_csv(csv_file_path, index=False)
        print(f"Sheet '{sheet_name}' has been successfully converted to '{csv_file_path}'.")
    except Exception as e:
        print(f"Error: {e}")



if __name__ == "__main__":
    # Replace with your actual file paths and sheet name
    excel_file = "source.xlsx"
    sheet_name = "Sheet1"
    csv_output = "folder_metadata.csv"

    convert_excel_to_csv(excel_file, sheet_name, csv_output)