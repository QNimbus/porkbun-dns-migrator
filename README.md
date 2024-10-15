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

The DNS export tool does not require any environment variables.

To use the Porkbun API for DNS import, you need to set the following environment variables:

- `PORKBUN_API_KEY`: Your Porkbun API key
- `PORKBUN_SECRET_KEY`: Your Porkbun secret key

You can set these variables in your shell or create a `.env` file in the project root:

```
PORKBUN_API_KEY=your_api_key_here
PORKBUN_SECRET_KEY=your_secret_api_key_here
```

Make sure to keep these keys secure and never commit them to version control. Also make sure to allow API access in your Porkbun dashboard for the domain you are importing to.

## Usage

### Exporting from Hurricane Electric

If you're transferring from Hurricane Electric, you can use their AXFR (zone transfer) feature to get a raw dump of your DNS records. Here's how to use it with this tool:

1. Log in to your Hurricane Electric DNS management interface.
2. Select your domain and open the 'Raw zone' toggle at the bottom.
3. Copy the entire content and save it to a file, for example `raw.txt`.
4. Extract all unique domain names from the raw output:

  ```
  DOMAIN="mydomain.com"
  ESCAPED_DOMAIN=$(printf '%s\n' "$DOMAIN" | sed 's/[.[\*^$(){}?+|]/\\&/g')
  grep -oP "([a-zA-Z0-9._-]*\\.$ESCAPED_DOMAIN|^$ESCAPED_DOMAIN)" raw.txt | sort -u | tr '\n' ' ' > domains.txt
  ```
5. This will create a file `domains.txt` with a space separated list of all unique domain names.
6. Use the extracted domains with `dns_export.py`:

  ```
  cat domains.txt | python dns_export.py -f output.json
  ```

This process allows you to easily export all DNS records from Hurricane Electric and prepare them for import into Porkbun.

### DNS Export

Export DNS records for one or more domains:

```
python dns_export.py --domains example.com example.org
```

Or use stdin to provide domains:

```
echo "example.com example.org" | python dns_export.py
```

Export to a file:

```
python dns_export.py --domains example.com -f output.json
```

Or using stdin:

```
echo "example.com" | python dns_export.py -f output.json
```

Export all record types, excluding specific ones:

```
python dns_export.py --domains example.com --all --exclude NS SOA
```

Using stdin:

```
echo "example.com" | python dns_export.py --all --exclude NS SOA
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

Run the DNS export tool using Docker (default behavior):

```
docker run -it --rm \
  --name dns-export \
  dns-management-tool --domain example.com
```

By default, this will output the DNS records to stdout. If you need to save the output to a file on your host machine, you can use a bind mount:

```
docker run -it --rm \
  --name dns-export \
  -v $(pwd):/app \
  dns-management-tool --domain example.com -f dns_records.json
```

The `-v $(pwd):/app` option creates a bind mount that maps the current directory on your host to the `/app` directory in the container. This allows the container to write the output file directly to your host filesystem.

The `-f dns_records.json` option tells the script to write the output to a file instead of stdout. The file will be created in
the `/app` directory inside the container, which is mapped to your current directory on the host.

### Using Process Substitution

You can use process substitution to pass the contents of a local file to stdin in the container. This is useful when you have a list of domains in a file and want to process them all:

```
docker run -i --rm \
  --name dns-export \
  -v $(pwd):/app \
  dns-management-tool < <(cat domains.txt)
```

In this command:
- We use `-i` instead of `-it` to keep stdin open without allocating a pseudo-TTY.
- `< <(cat domains.txt)` uses process substitution to redirect the contents of `domains.txt` to the container's stdin.

You can also combine this with output redirection to save the results to a file:

```
docker run -i --rm \
  --name dns-export \
  dns-management-tool < <(cat domains.txt) > dns_records.json
```

This will process all domains listed in `domains.txt` and save the output to `dns_records.json` in your current directory.

For a quick list of domains, you can use a here-string instead of a file:

```
docker run -i --rm \
  --name dns-export \
  dns-management-tool <<< "example.com example.org"
```

These methods allow you to flexibly provide input to your Docker container from various sources on your local machine.

To run the DNS import tool, you need to override the default CMD and pass the Porkbun environment variables:

```
docker run -it --rm \
  --name dns-import \
  -e PORKBUN_API_KEY=your_api_key_here \
  -e PORKBUN_SECRET_KEY=your_secret_api_key_here \
  -v $(pwd)/import.json:/app/import.json \
  dns-management-tool python dns_import.py --file import.json
```

This command assumes that your input JSON file is in the current directory. Adjust the volume mount path as needed.

## Development

This project includes a dev container configuration for Visual Studio Code, making it easy to set up a consistent development environment.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)
