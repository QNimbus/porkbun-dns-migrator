# DNS Management Tool

## Overview

This DNS Management Tool is a powerful and flexible solution for exporting and importing DNS records across multiple domains. It's designed for DNS administrators, developers, and anyone who needs to manage DNS records efficiently and programmatically.

## Why I Created This Tool

I developed this tool to simplify the process of transferring DNS configurations when moving domains between registrars. Specifically, I needed an easy way to import my existing DNS configuration to Porkbun after transferring my domain from Hurricane Electric. This tool automates the export of DNS records from any nameserver and facilitates their import into Porkbun, saving time and reducing the risk of manual errors during the migration process.

## Features

- **DNS Export**: Retrieve DNS records for one or more domains
  - Support for multiple record types (A, AAAA, CNAME, MX, TXT, SPF, etc.)
  - Option to export all record types or a specific subset
  - Ability to exclude certain record types from export
  - Output to stdout or file in JSON format
  - Raw output option for debugging

- **DNS Import**: Create or update DNS records using the Porkbun API
  - Support for creating new records and updating existing ones
  - Force update option to overwrite existing records
  - Handles various record types

- **Flexible CLI**: Easy-to-use command-line interface for both export and import operations
- **Verbose Output**: Detailed logging for troubleshooting
- **Docker Support**: Run the tool in any environment using Docker
- **Schema Validation**: Ensures data integrity of DNS records

## Why Use This Tool?

1. **Automation**: Easily integrate DNS management into your CI/CD pipelines or automation scripts.
2. **Bulk Operations**: Manage DNS records for multiple domains simultaneously.
3. **Version Control**: Export DNS records to JSON, allowing you to track changes in version control systems.
4. **Consistency**: Ensure DNS configurations are consistent across different environments.
5. **Backup and Restore**: Quickly backup your DNS configurations and restore them when needed.
6. **Domain Transfer**: Simplify the process of moving DNS records when transferring domains between registrars.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/dns-management-tool.git
   cd dns-management-tool
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

Alternatively, use Docker:
```
docker build -t dns-management-tool .
```

## Environment Variables

To use the Porkbun API for DNS import, you need to set the following environment variables:

- `PORKBUN_API_KEY`: Your Porkbun API key
- `PORKBUN_SECRET_API_KEY`: Your Porkbun secret API key

You can set these variables in your shell or create a `.env` file in the project root:

```
PORKBUN_API_KEY=your_api_key_here
PORKBUN_SECRET_API_KEY=your_secret_api_key_here
```

Make sure to keep these keys secure and never commit them to version control. Also make sure to allow API access in your Porkbun dashboard for the domain you are importing to.

## Usage

### DNS Export

Export DNS records for one or more domains:

```
python dns_export.py --domains example.com example.org
```

Export to a file:

```
python dns_export.py --domains example.com -f output.json
```

Export all record types, excluding specific ones:

```
python dns_export.py --domains example.com --all --exclude NS SOA
```

### DNS Import

Import DNS records from a JSON file:

```
python dns_import.py --file input.json
```

Force update existing records:

```
python dns_import.py --file input.json --force
```

## Docker Usage

Run the DNS export tool using Docker:

```
docker run -it --rm \
  -e PORKBUN_API_KEY=your_api_key_here \
  -e PORKBUN_SECRET_API_KEY=your_secret_api_key_here \
  dns-management-tool python dns_export.py --domains example.com
```

## Development

This project includes a dev container configuration for Visual Studio Code, making it easy to set up a consistent development environment.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)
