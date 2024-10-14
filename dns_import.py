import requests
import json
import os
import argparse
import sys
import traceback
import jsonschema

# Porkbun API credentials
API_KEY = os.environ.get("PORKBUN_API_KEY")
SECRET_KEY = os.environ.get("PORKBUN_SECRET_KEY")

# Check for API credentials
if not API_KEY or not SECRET_KEY:
    print("Error: Porkbun API credentials not found. Please set PORKBUN_API_KEY and PORKBUN_SECRET_KEY environment variables.")
    sys.exit(1)

# Base URL for Porkbun API
BASE_URL = "https://porkbun.com/api/json/v3"

def validate_json_schema(data):
    """
    Validate the input JSON data against the schema defined in schema.json.

    Args:
        data (dict): The JSON data to validate.

    Returns:
        bool: True if the data is valid, False otherwise.

    Raises:
        FileNotFoundError: If schema.json is not found.
        json.JSONDecodeError: If schema.json cannot be decoded.
        jsonschema.exceptions.ValidationError: If the data fails validation.
    """
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to schema.json
    schema_path = os.path.join(script_dir, 'schema.json')

    try:
        # Read the schema from the file
        with open(schema_path, 'r') as schema_file:
            schema = json.load(schema_file)

        # Validate the data against the schema
        jsonschema.validate(instance=data, schema=schema)
        return True
    except FileNotFoundError:
        print(f"Error: schema.json not found at {schema_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"Error decoding schema.json: {e}")
        return False
    except jsonschema.exceptions.ValidationError as e:
        print(f"JSON Schema validation error: {e}")
        return False

def get_existing_records(domain, verbose=False):
    """
    Retrieve existing DNS records for a given domain using the Porkbun API.

    Args:
        domain (str): The domain to retrieve records for.
        verbose (bool): If True, print detailed information about the API request and response.

    Returns:
        list: A list of existing DNS records for the domain, or None if an error occurs.

    Raises:
        json.JSONDecodeError: If the API response cannot be decoded.
        KeyError: If the expected keys are not found in the API response.
    """
    # Extract the root domain
    root_domain = '.'.join(domain.split('.')[-2:])
    url = f"{BASE_URL}/dns/retrieve/{root_domain}"
    payload = {
        "secretapikey": SECRET_KEY,
        "apikey": API_KEY
    }
    if verbose:
        print(f"Sending request to: {url}")
        obfuscated_payload = {
            "secretapikey": SECRET_KEY[:10] + "...",
            "apikey": API_KEY[:10] + "..."
        }
        print(f"Payload: {json.dumps(obfuscated_payload, indent=2)}")

    response = requests.post(url, json=payload)

    if verbose:
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {json.dumps(response.json(), indent=2)}")

    try:
        result = response.json()
        if result['status'] == 'SUCCESS' and 'records' in result:
            return result['records']
        else:
            if verbose:
                print(f"API returned an error or no records: {result}")
            return None
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {str(e)}")
        if verbose:
            print(f"Response content: {response.text}")
        return None
    except KeyError as e:
        print(f"KeyError: {str(e)}")
        if verbose:
            print(f"Full Response: {response.text}")
        return None

def create_record(domain, record, verbose=False):
    """
    Create a new DNS record for a given domain using the Porkbun API.

    Args:
        domain (str): The domain to create the record for.
        record (dict): The record data to create.
        verbose (bool): If True, print detailed information about the API request and response.

    Returns:
        dict: The API response containing the result of the create operation.
    """
    # Extract the root domain
    root_domain = '.'.join(domain.split('.')[-2:])
    url = f"{BASE_URL}/dns/create/{root_domain}"

    payload = {
        "secretapikey": SECRET_KEY,
        "apikey": API_KEY,
        "type": record['type'],
        "content": record['content'],
        "ttl": record['ttl']
    }

    # Set name as the subdomain or @ for root
    if domain != root_domain:
        payload['name'] = domain.split('.')[0]
    else:
        payload['name'] = '@'

    # Add priority for MX, SRV, and NAPTR records
    if record['type'] in ['MX', 'SRV', 'NAPTR']:
        payload['prio'] = record['prio']

    if verbose:
        print(f"Sending request to: {url}")
        obfuscated_payload = {**payload, "secretapikey": SECRET_KEY[:10] + "...", "apikey": API_KEY[:10] + "..."}
        print(f"Payload: {json.dumps(obfuscated_payload, indent=2)}")

    response = requests.post(url, json=payload)
    result = response.json()

    if verbose:
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {json.dumps(result, indent=2)}")

    if result['status'] == 'ERROR':
        print(f"Error creating record: {record['name']} ({record['type']})")
        print(f"Error details: {result.get('message', 'No detailed message provided')}")
        if verbose:
            print(f"Full error response: {json.dumps(result, indent=2)}")
            if 'errors' in result:
                for error in result['errors']:
                    print(f"  - {error}")

    return result

def update_record(domain, record_id, record, verbose=False):
    """
    Update an existing DNS record for a given domain using the Porkbun API.

    Args:
        domain (str): The domain of the record to update.
        record_id (str): The ID of the record to update.
        record (dict): The updated record data.
        verbose (bool): If True, print detailed information about the API request and response.

    Returns:
        dict: The API response containing the result of the update operation.
    """
    # Extract the root domain
    root_domain = '.'.join(domain.split('.')[-2:])
    url = f"{BASE_URL}/dns/edit/{root_domain}/{record_id}"

    payload = {
        "secretapikey": SECRET_KEY,
        "apikey": API_KEY,
        "type": record['type'],
        "content": record['content'],
        "ttl": record['ttl']
    }

    # Set name as the subdomain or @ for root
    if domain != root_domain:
        payload['name'] = domain.split('.')[0]
    else:
        payload['name'] = '@'

    if 'prio' in record:
        payload['prio'] = record['prio']

    if verbose:
        print(f"Sending request to: {url}")
        obfuscated_payload = {**payload, "secretapikey": SECRET_KEY[:10] + "...", "apikey": API_KEY[:10] + "..."}
        print(f"Payload: {json.dumps(obfuscated_payload, indent=2)}")

    response = requests.post(url, json=payload)
    result = response.json()

    if verbose:
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {json.dumps(result, indent=2)}")

    return result

def get_existing_record(domain, record_type, name, content=None, prio=None, verbose=False):
    """
    Retrieve an existing DNS record for a given domain, type, and name using the Porkbun API.

    Args:
        domain (str): The domain to search for the record.
        record_type (str): The type of DNS record (e.g., 'A', 'MX', 'CNAME').
        name (str): The name of the record.
        content (str, optional): The content of the record to match.
        prio (str, optional): The priority of the record to match (for MX, SRV, NAPTR records).
        verbose (bool): If True, print detailed information about the API request and response.

    Returns:
        dict: The matching DNS record if found, None otherwise.

    Raises:
        json.JSONDecodeError: If the API response cannot be decoded.
        KeyError: If the expected keys are not found in the API response.
    """
    # Extract the root domain
    root_domain = '.'.join(domain.split('.')[-2:])

    # Determine the subdomain
    subdomain = name if name != '@' else ''

    url = f"{BASE_URL}/dns/retrieveByNameType/{root_domain}/{record_type}/{subdomain}"
    payload = {
        "secretapikey": SECRET_KEY,
        "apikey": API_KEY
    }

    if verbose:
        print(f"Sending request to: {url}")
        obfuscated_payload = {
            "secretapikey": SECRET_KEY[:10] + "...",
            "apikey": API_KEY[:10] + "..."
        }
        print(f"Payload: {json.dumps(obfuscated_payload, indent=2)}")

    response = requests.post(url, json=payload)

    if verbose:
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {json.dumps(response.json(), indent=2)}")

    try:
        result = response.json()
        if result['status'] == 'SUCCESS' and result.get('records'):
            for record in result['records']:
                if content and record['content'] == content:
                    if record_type in ['MX', 'SRV', 'NAPTR'] and prio:
                        if str(record['prio']) == str(prio):
                            return record
                    else:
                        return record
            if verbose:
                print("No matching record found.")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {str(e)}")
        if verbose:
            print(f"Response content: {response.text}")
        return None
    except KeyError as e:
        print(f"KeyError: {str(e)}")
        if verbose:
            print(f"Full Response: {response.text}")
        return None

def process_record(domain, record_type, name, record, force, verbose=False):
    """
    Process a single DNS record, either creating a new one or updating an existing one.

    Args:
        domain (str): The domain for the record.
        record_type (str): The type of DNS record.
        name (str): The name of the record.
        record (dict): The record data.
        force (bool): If True, force update existing records.
        verbose (bool): If True, print detailed information about the process.

    Raises:
        KeyError: If required keys are missing in the record data.
        Exception: For any unexpected errors during processing.
    """
    try:
        content = record['content']
        ttl = record['ttl']
        prio = record.get('prio')

        if record_type in ['MX', 'SRV', 'NAPTR']:
            if prio is None:
                print(f"Warning: 'prio' is missing for {record_type} record: {name}")
                return

        existing_record = get_existing_record(domain, record_type, name, content, prio, verbose)

        record_data = {
            'name': name,
            'type': record_type,
            'content': content,
            'ttl': ttl
        }
        if prio is not None:
            record_data['prio'] = prio

        if existing_record:
            if force:
                result = update_record(domain, existing_record['id'], record_data, verbose)
                print(f"Updated record: {name} ({record_type}) - {result['status']}")
                if result['status'] == 'ERROR':
                    print(f"Error details: {result.get('message', 'No detailed message provided')}")
                    if verbose:
                        print(f"Full error response: {json.dumps(result, indent=2)}")
            else:
                print(f"Skipping existing record: {name} ({record_type}). Use --force to update.")
        else:
            result = create_record(domain, record_data, verbose)
            print(f"Created record: {name} ({record_type}) - {result['status']}")
            if result['status'] == 'ERROR':
                print(f"Error details: {result.get('message', 'No detailed message provided')}")
                if verbose:
                    print(f"Full error response: {json.dumps(result, indent=2)}")
    except KeyError as e:
        print(f"KeyError in process_record: Missing key {e} for record {name} ({record_type})")
        if verbose:
            print(f"Record data: {json.dumps(record, indent=2)}")
    except Exception as e:
        print(f"Unexpected error in process_record for {name} ({record_type}): {str(e)}")
        if verbose:
            print(f"Record data: {json.dumps(record, indent=2)}")
            traceback.print_exc()

def import_dns_records(new_records, force=False, verbose=False):
    """
    Import DNS records for one or more domains.

    Args:
        new_records (list): A list of dictionaries containing DNS records to import.
        force (bool): If True, force update existing records.
        verbose (bool): If True, print detailed information about the import process.
    """
    for domain_data in new_records:
        for domain, records in domain_data.items():
            print(f"\nProcessing domain: {domain}")
            for record_type, record_list in records.items():
                for record in record_list:
                    name = record.get('name', domain)

                    # Ensure name ends with a dot
                    if not name.endswith('.'):
                        name += '.'

                    if verbose:
                        print(f"Processing record: {name} ({record_type}) - {record['content']}")
                    process_record(domain, record_type, name, record, force, verbose)

def export_dns_records_json(domain, verbose=False):
    """
    Export DNS records for a given domain in JSON format.

    Args:
        domain (str): The domain to export records for.
        verbose (bool): If True, print detailed information about the export process.

    Returns:
        list: A list containing a dictionary of DNS records for the domain, or None if an error occurs.
    """
    records = get_existing_records(domain, verbose)
    if records:
        export_data = {}
        for record in records:
            record_type = record['type']
            if record_type not in export_data:
                export_data[record_type] = {}

            name = record['name'] if record['name'] != domain else '@'

            content = record['content']
            ttl = record['ttl']

            if record_type == 'MX':
                content = f"{record['prio']} {content}"

            # Create a dictionary with 'content' and 'ttl', excluding null values
            record_data = {k: v for k, v in {'content': content, 'ttl': ttl}.items() if v is not None}

            # Handle multiple records for the same name and type
            if name in export_data[record_type]:
                if isinstance(export_data[record_type][name], list):
                    export_data[record_type][name].append(record_data)
                else:
                    export_data[record_type][name] = [export_data[record_type][name], record_data]
            else:
                export_data[record_type][name] = record_data

        # Wrap the export_data in the new structure
        new_structure = [{domain: export_data}]
        return new_structure
    else:
        return None

def read_input(file_path=None):
    """
    Read and parse JSON input from a file or stdin.

    Args:
        file_path (str, optional): Path to the input JSON file. If None, read from stdin.

    Returns:
        dict: The parsed JSON data.

    Raises:
        json.JSONDecodeError: If the input cannot be decoded as JSON.
        ValueError: If the input data does not conform to the required schema.
        FileNotFoundError: If the specified file is not found.
        Exception: For any other unexpected errors during input reading.
    """
    try:
        if file_path:
            with open(file_path, 'r') as f:
                data = json.load(f)
        else:
            data = json.loads(sys.stdin.read())

        if not validate_json_schema(data):
            raise ValueError("Input data does not conform to the required schema")

        return data
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {str(e)}")
        print(f"Error occurred at line {e.lineno}, column {e.colno}")
        print(f"The problematic portion of the JSON: {e.doc[max(0, e.pos-20):e.pos+20]}")
        raise
    except Exception as e:
        print(f"Error reading input: {str(e)}")
        raise

def print_usage():
    """
    Print usage information for the DNS import tool.
    """
    print("\nUsage:")
    print("1. List existing DNS records:")
    print(f"   python {sys.argv[0]} --list")
    print("\n2. Export DNS records in JSON format:")
    print(f"   python {sys.argv[0]} --json")
    print("\n3. Import DNS records from stdin:")
    print(f"   cat records.json | python {sys.argv[0]}")
    print("\n4. Import DNS records from a file:")
    print(f"   python {sys.argv[0]} --file records.json")
    print("\n5. Force overwrite existing records when importing:")
    print(f"   python {sys.argv[0]} --file records.json --force")
    print("\nAdd --verbose or -v to any command for detailed output.")

if __name__ == "__main__":
    """
    Main entry point for the DNS import tool.

    Parses command-line arguments and executes the appropriate actions based on the provided flags.
    """
    parser = argparse.ArgumentParser(description="Manage DNS records using Porkbun API", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output for debugging")
    parser.add_argument("--file", "-f", help="Input file for DNS records to import (JSON format). If not provided, stdin will be used.")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing DNS records when importing")
    args = parser.parse_args()

    if args.help:
        parser.print_help()
        print_usage()
        sys.exit(0)

    if args.file or not sys.stdin.isatty():
        # Import DNS records
        try:
            new_records = read_input(args.file)
            import_dns_records(new_records, args.force, args.verbose)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON input - {str(e)}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        except Exception as e:
            print(f"Error during import: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            if args.verbose:
                traceback.print_exc()
            sys.exit(1)
    else:
        print("Error: Invalid command")
        print_usage()
        sys.exit(1)
