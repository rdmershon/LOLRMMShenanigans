import requests
import csv
import io
import ipaddress # For IPv4 validation
import os # For path operations and directory creation

# The specific GitHub raw CSV URL
GITHUB_CSV_URL = 'https://raw.githubusercontent.com/magicsword-io/LOLRMM/main/website/public/api/rmm_domains.csv'

# --- Output File Configuration ---
# Basenames for the output files
ORIGINAL_CSV_BASENAME = 'original_rmm_domains.csv'
CLEANED_CSV_BASENAME = 'cleaned_rmm_domains.csv'
MISC_CSV_BASENAME = 'misc_rmm_domains.csv'

# Target directory for output files
# Using a raw string (r'') for Windows paths is good practice
TARGET_DIRECTORY = r'C:\nix\lolrmm'


def is_valid_ipv4(address_string):
    """Checks if a string is a valid IPv4 address."""
    try:
        ipaddress.IPv4Address(address_string)
        return True
    except ipaddress.AddressValueError:
        return False

def download_process_and_save_domains(csv_url):
    """
    Downloads a CSV, saves the original, then processes domains to sort them into
    a 'cleaned' list (no '*' or IPv4s) and a 'misc' list ('*' or IPv4s),
    saving all output files to the TARGET_DIRECTORY.
    """
    cleaned_domains_set = set()
    misc_domains_set = set()

    # --- Prepare output paths ---
    # Create target directory if it doesn't exist
    try:
        os.makedirs(TARGET_DIRECTORY, exist_ok=True)
        print(f"Ensured target directory exists: {TARGET_DIRECTORY}")
    except OSError as e:
        print(f"Error creating directory {TARGET_DIRECTORY}: {e}")
        print("Please check permissions or create the directory manually.")
        return # Exit if directory creation fails

    original_output_path = os.path.join(TARGET_DIRECTORY, ORIGINAL_CSV_BASENAME)
    cleaned_output_path = os.path.join(TARGET_DIRECTORY, CLEANED_CSV_BASENAME)
    misc_output_path = os.path.join(TARGET_DIRECTORY, MISC_CSV_BASENAME)

    print(f"\nAttempting to download CSV from: {csv_url}")
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        
        original_csv_content = response.content.decode('utf-8')
        
        print(f"\nSaving original downloaded content to {original_output_path}...")
        try:
            with open(original_output_path, 'w', encoding='utf-8') as outfile:
                outfile.write(original_csv_content)
            print(f"Successfully saved original content to {original_output_path}")
        except IOError as e:
            print(f"Error writing original content to file {original_output_path}: {e}")

        csv_file = io.StringIO(original_csv_content)
        reader = csv.reader(csv_file)
        
        header = next(reader, None)
        if header:
            print(f"\nOriginal CSV Header: {', '.join(header)}")
        else:
            print("\nNo header found or CSV is empty.")
        
        print("\nProcessing domains from the CSV...")
        parsed_domain_count = 0
        
        for i, row in enumerate(reader):
            if not row:
                continue 

            domain_entry = row[0].strip().lower()
            if not domain_entry:
                continue 

            parsed_domain_count += 1
            is_ipv4_entry = is_valid_ipv4(domain_entry)
            contains_asterisk = '*' in domain_entry
            
            if is_ipv4_entry:
                misc_domains_set.add(domain_entry)
            
            if contains_asterisk: 
                misc_domains_set.add(domain_entry)
            
            if not is_ipv4_entry and not contains_asterisk:
                cleaned_domains_set.add(domain_entry)
        
        print(f"\nFinished processing domains.")
        print(f"Total entries parsed from CSV (excluding header): {parsed_domain_count}")
        print(f"Unique domains for '{CLEANED_CSV_BASENAME}' (no '*' or IPv4): {len(cleaned_domains_set)}")
        print(f"Unique entries for '{MISC_CSV_BASENAME}' (contains '*' or is IPv4): {len(misc_domains_set)}")

        # Save cleaned domains
        if cleaned_domains_set:
            sorted_cleaned_domains = sorted(list(cleaned_domains_set))
            print(f"\nSaving {len(sorted_cleaned_domains)} domains to {cleaned_output_path}...")
            try:
                with open(cleaned_output_path, 'w', newline='', encoding='utf-8') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(['domain']) 
                    for domain_to_save in sorted_cleaned_domains:
                        writer.writerow([domain_to_save])
                print(f"Successfully saved cleaned domains to {cleaned_output_path}")
            except IOError as e:
                print(f"Error writing cleaned domains to file {cleaned_output_path}: {e}")
        else:
            print(f"\nNo domains to save for {cleaned_output_path}.")
            try:
                with open(cleaned_output_path, 'w', newline='', encoding='utf-8') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(['domain'])
                print(f"Empty {cleaned_output_path} with header has been created.")
            except IOError as e:
                print(f"Error creating empty {cleaned_output_path}: {e}")

        # Save misc domains
        if misc_domains_set:
            sorted_misc_domains = sorted(list(misc_domains_set))
            print(f"\nSaving {len(sorted_misc_domains)} entries to {misc_output_path}...")
            try:
                with open(misc_output_path, 'w', newline='', encoding='utf-8') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(['entry']) 
                    for entry_to_save in sorted_misc_domains:
                        writer.writerow([entry_to_save])
                print(f"Successfully saved misc entries to {misc_output_path}")
            except IOError as e:
                print(f"Error writing misc entries to file {misc_output_path}: {e}")
        else:
            print(f"\nNo entries to save for {misc_output_path}.")
            try:
                with open(misc_output_path, 'w', newline='', encoding='utf-8') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(['entry'])
                print(f"Empty {misc_output_path} with header has been created.")
            except IOError as e:
                print(f"Error creating empty {misc_output_path}: {e}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error downloading CSV: {e}")
    except csv.Error as e:
        print(f"Error parsing CSV content: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Main Execution ---
if __name__ == '__main__':
    download_process_and_save_domains(GITHUB_CSV_URL)
    print("\nScript finished.")
