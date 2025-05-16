# Big thanks to Gemini, it did most of this. 2.5 r0cks!
import requests
import csv
import io

# The specific GitHub raw CSV URL
GITHUB_CSV_URL = 'https://raw.githubusercontent.com/magicsword-io/LOLRMM/main/website/public/api/rmm_domains.csv'

def download_and_print_domains(csv_url):
    """
    Downloads a CSV file from the given URL, parses it,
    and prints each domain to the terminal.

    Args:
        csv_url (str): The raw URL to the CSV file.
    """
    domains = []
    print(f"Attempting to download CSV from: {csv_url}")
    try:
        response = requests.get(csv_url)
        # Raise an exception for HTTP errors (e.g., 404, 500)
        response.raise_for_status()
        
        # Decode the content to a string and use io.StringIO to treat it like a file
        csv_content = response.content.decode('utf-8')
        csv_file = io.StringIO(csv_content)
        
        # Create a CSV reader object
        reader = csv.reader(csv_file)
        
        # Read and print the header, then skip it
        header = next(reader, None)
        if header:
            print(f"CSV Header: {', '.join(header)}")
        else:
            print("No header found or CSV is empty.")
            return

        print("\nDomains found in the CSV:")
        # Iterate over each row in the CSV after the header
        for i, row in enumerate(reader):
            if row:  # Ensure the row is not empty
                domain = row[0].strip() # Get the first column and strip whitespace
                if domain: # Ensure the domain string itself is not empty
                    print(f"{i+1}. {domain}")
                    domains.append(domain)
            else:
                print(f"Row {i+1} is empty.")
        
        if not domains:
            print("No domains were found in the CSV after the header.")
            
    except requests.exceptions.RequestException as e:
        print(f"Error downloading CSV: {e}")
    except csv.Error as e:
        print(f"Error parsing CSV content: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Main Execution ---
if __name__ == '__main__':
    download_and_print_domains(GITHUB_CSV_URL)
    print("\nScript finished.")
