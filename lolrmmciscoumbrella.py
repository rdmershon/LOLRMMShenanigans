import requests
import csv
import io
import ipaddress # For IPv4 validation
import os # For path operations and directory creation
import time # For rate limiting delays
# from datetime import datetime, timedelta # Not strictly needed for /volume endpoint's default 30-day window

# --- Configuration ---
# The specific GitHub raw CSV URL
GITHUB_CSV_URL = 'https://raw.githubusercontent.com/magicsword-io/LOLRMM/main/website/public/api/rmm_domains.csv'

# Basenames for the output files
ORIGINAL_CSV_BASENAME = 'original_rmm_domains.csv'
CLEANED_CSV_BASENAME = 'cleaned_rmm_domains.csv'
MISC_CSV_BASENAME = 'misc_rmm_domains.csv'

# Target directory for output files
TARGET_DIRECTORY = r'C:\nix\lolrmm'

# --- Cisco Umbrella API Configuration ---
# !! REPLACE WITH YOUR ACTUAL CREDENTIALS or implement a secure way to load them !!
UMBRELLA_API_KEY = 'YOUR_UMBRELLA_API_KEY_HERE'  # Client ID
UMBRELLA_API_SECRET = 'YOUR_UMBRELLA_API_SECRET_HERE' # Client Secret

UMBRELLA_AUTH_URL = 'https://api.umbrella.com/auth/v2/token'
# Using Investigate API v2 for domain volume
UMBRELLA_DOMAIN_VOLUME_API_URL_V2 = 'https://investigate.api.umbrella.com/investigate/v2/domains/volume/'


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
    Returns the full path to the cleaned domains CSV if successful.
    """
    cleaned_domains_set = set()
    misc_domains_set = set()

    try:
        os.makedirs(TARGET_DIRECTORY, exist_ok=True)
        # print(f"Ensured target directory exists: {TARGET_DIRECTORY}") # Less verbose
    except OSError as e:
        print(f"Error creating directory {TARGET_DIRECTORY}: {e}. Exiting.")
        return None

    original_output_path = os.path.join(TARGET_DIRECTORY, ORIGINAL_CSV_BASENAME)
    cleaned_output_path = os.path.join(TARGET_DIRECTORY, CLEANED_CSV_BASENAME)
    misc_output_path = os.path.join(TARGET_DIRECTORY, MISC_CSV_BASENAME)

    print(f"Attempting to download CSV from: {csv_url}")
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        original_csv_content = response.content.decode('utf-8')

        try:
            with open(original_output_path, 'w', encoding='utf-8') as outfile:
                outfile.write(original_csv_content)
            print(f"Successfully saved original content to {original_output_path}")
        except IOError as e:
            print(f"Error writing original content to file {original_output_path}: {e}")

        csv_file = io.StringIO(original_csv_content)
        reader = csv.reader(csv_file)
        header = next(reader, None)
        # if header: print(f"Original CSV Header: {', '.join(header)}")

        parsed_domain_count = 0
        for row in reader:
            if not row: continue
            domain_entry = row[0].strip().lower()
            if not domain_entry: continue
            parsed_domain_count += 1
            is_ipv4_entry = is_valid_ipv4(domain_entry)
            contains_asterisk = '*' in domain_entry
            
            if is_ipv4_entry or contains_asterisk:
                misc_domains_set.add(domain_entry)
            if not is_ipv4_entry and not contains_asterisk:
                cleaned_domains_set.add(domain_entry)
        
        print(f"Finished processing domains from GitHub.")
        print(f"  Total entries parsed (excluding header): {parsed_domain_count}")
        print(f"  Unique domains for '{CLEANED_CSV_BASENAME}': {len(cleaned_domains_set)}")
        print(f"  Unique entries for '{MISC_CSV_BASENAME}': {len(misc_domains_set)}")

        # Save cleaned domains
        saved_cleaned_domains = False
        if cleaned_domains_set:
            sorted_cleaned_domains = sorted(list(cleaned_domains_set))
            try:
                with open(cleaned_output_path, 'w', newline='', encoding='utf-8') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(['domain']) 
                    for domain_to_save in sorted_cleaned_domains:
                        writer.writerow([domain_to_save])
                print(f"Successfully saved cleaned domains to {cleaned_output_path}")
                saved_cleaned_domains = True
            except IOError as e:
                print(f"Error writing cleaned domains to file {cleaned_output_path}: {e}")
        else:
            print(f"No domains to save for {cleaned_output_path}.")
            # Still create empty file with header
            try:
                with open(cleaned_output_path, 'w', newline='', encoding='utf-8') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(['domain'])
                print(f"Empty {cleaned_output_path} with header has been created.")
                saved_cleaned_domains = True # File created, even if empty
            except IOError as e:
                print(f"Error creating empty {cleaned_output_path}: {e}")


        # Save misc domains
        if misc_domains_set:
            sorted_misc_domains = sorted(list(misc_domains_set))
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
            print(f"No entries to save for {misc_output_path}.")
            try:
                with open(misc_output_path, 'w', newline='', encoding='utf-8') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(['entry'])
                print(f"Empty {misc_output_path} with header has been created.")
            except IOError as e:
                print(f"Error creating empty {misc_output_path}: {e}")
        
        return cleaned_output_path if saved_cleaned_domains else None
            
    except requests.exceptions.RequestException as e:
        print(f"Error downloading CSV: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during domain processing: {e}")
        return None

def get_umbrella_api_token(api_key, api_secret):
    """Authenticates with Cisco Umbrella API and returns an access token."""
    if api_key == 'YOUR_UMBRELLA_API_KEY_HERE' or api_secret == 'YOUR_UMBRELLA_API_SECRET_HERE':
        print("ERROR: Umbrella API Key/Secret not configured. Please update them in the script.")
        return None
    try:
        response = requests.post(
            UMBRELLA_AUTH_URL,
            auth=(api_key, api_secret),
            data={'grant_type': 'client_credentials'}
        )
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.exceptions.RequestException as e:
        print(f"Error obtaining Umbrella API token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        return None

def check_domain_in_umbrella(domain, access_token):
    """
    Queries Umbrella Investigate API to check if a domain has been observed
    (has query volume) in the last 30 days.
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    query_url = f"{UMBRELLA_DOMAIN_VOLUME_API_URL_V2}{domain}"
    
    try:
        # print(f"  Querying Umbrella for: {domain}") # Verbose
        response = requests.get(query_url, headers=headers)
        
        if response.status_code == 429: # Rate limit
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"  Rate limit hit. Waiting for {retry_after} seconds before retrying {domain}...")
            time.sleep(retry_after)
            return check_domain_in_umbrella(domain, access_token) # Retry
            
        response.raise_for_status()
        data = response.json() # Expects a list of [timestamp, query_count] pairs

        if isinstance(data, list) and len(data) > 0:
            # Any data point with queries > 0 within the last 30 days means observed.
            # The endpoint itself is for the last 30 days.
            # We can sum up queries if needed or just check for presence of data.
            total_queries = sum(item[1] for item in data if isinstance(item, list) and len(item) == 2)
            if total_queries > 0:
                 return True, f"Observed (Total queries in last 30 days: {total_queries})"
            else: # Data points exist but all are zero queries
                return False, "Not observed (Volume data present but all zero queries)"
        elif isinstance(data, list) and len(data) == 0: # Empty list means no volume
             return False, "Not observed (No volume data in the last 30 days)"
        else: # Unexpected response format
            return False, f"Unexpected response format: {str(data)[:100]}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return False, "Not observed (Domain not found in Umbrella Investigate)"
        else:
            return False, f"HTTP error: {e.response.status_code} - {e.response.text[:100]}"
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {e}"
    except ValueError: # Includes JSONDecodeError
        return False, f"Error decoding JSON. Response: {response.text[:100] if 'response' in locals() else 'N/A'}"


def read_domains_from_csv(file_path):
    """Reads domains from a CSV file (first column, skipping header)."""
    domains = []
    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        return domains
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None) # Skip header
            for row in reader:
                if row and row[0].strip():
                    domains.append(row[0].strip())
        print(f"Read {len(domains)} domains from {file_path}")
    except Exception as e:
        print(f"Error reading domains from {file_path}: {e}")
    return domains

# --- Main Execution ---
def main():
    print("Starting script...")
    
    # Step 1: Download and process domains from GitHub
    cleaned_domains_csv_path = download_process_and_save_domains(GITHUB_CSV_URL)

    if not cleaned_domains_csv_path:
        print("Failed to generate the cleaned domains CSV. Exiting Umbrella query part.")
        return

    # Step 2: Read domains from the generated "cleaned_rmm_domains.csv"
    domains_to_query = read_domains_from_csv(cleaned_domains_csv_path)
    if not domains_to_query:
        print("No domains to query from Umbrella. Exiting.")
        return

    print(f"\n--- Starting Cisco Umbrella Queries for {len(domains_to_query)} domains ---")
    
    # Step 3: Get Umbrella API Token
    access_token = get_umbrella_api_token(UMBRELLA_API_KEY, UMBRELLA_API_SECRET)
    if not access_token:
        print("Failed to obtain Umbrella API token. Cannot proceed with Umbrella queries.")
        return
    print("Successfully obtained Umbrella API token.")

    # Step 4: Query each domain in Umbrella
    umbrella_results = {}
    for i, domain in enumerate(domains_to_query):
        print(f"Processing domain {i+1}/{len(domains_to_query)}: {domain}")
        observed, message = check_domain_in_umbrella(domain, access_token)
        umbrella_results[domain] = {"observed_last_30_days": observed, "details": message}
        print(f"  Result: {message}")
        
        # API Rate Limiting: Cisco Investigate API allows ~10 reqs/sec.
        # A small delay helps avoid hitting this hard. Retry logic is also in check_domain_in_umbrella.
        time.sleep(0.15) # ~150ms delay

    # Step 5: Report Umbrella results (currently printing to console)
    print("\n--- Final Umbrella Query Results ---")
    observed_count = 0
    for domain, result in umbrella_results.items():
        # print(f"Domain: {domain} - Observed: {result['observed_last_30_days']} ({result['details']})") # More compact
        if result['observed_last_30_days']:
            observed_count += 1
    
    print(f"\nSummary: {observed_count} out of {len(domains_to_query)} domains from '{CLEANED_CSV_BASENAME}' were observed by Umbrella in the last 30 days.")
    print("\nScript finished.")

if __name__ == '__main__':
    main()
