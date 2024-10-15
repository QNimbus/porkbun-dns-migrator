import dns.resolver
import json
import argparse
import sys
import tldextract


def get_records(domain, record_types, raw_output=False, keep_a_aaaa=False):
    """
    Retrieve DNS records for a given domain.

    Args:
        domain (str): The domain name to query.
        record_types (list): List of record types to query.
        raw_output (bool): If True, return raw DNS data. If False, format the data.
        keep_a_aaaa (bool): If True, keep A and AAAA records even when CNAME exists.

    Returns:
        dict: A dictionary containing DNS records, organized by record type.

    Raises:
        dns.resolver.NXDOMAIN: If the domain does not exist.
    """
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ["8.8.8.8", "8.8.4.4"]  # Using Google's DNS servers

    records = {}

    for record_type in record_types:
        try:
            answers = resolver.resolve(domain, record_type)

            if raw_output:
                records[record_type] = [str(rdata) for rdata in answers]
            elif record_type in ["MX", "SRV", "NAPTR"]:
                records[record_type] = [
                    (
                        (str(rdata.exchange), rdata.preference, answers.ttl)
                        if record_type == "MX"
                        else (
                            (
                                str(rdata.target),
                                rdata.priority,
                                rdata.weight,
                                rdata.port,
                                answers.ttl,
                            )
                            if record_type == "SRV"
                            else (
                                str(rdata.replacement),
                                rdata.order,
                                rdata.preference,
                                answers.ttl,
                            )
                        )
                    )
                    for rdata in answers
                ]
            else:
                records[record_type] = [(str(rdata), answers.ttl) for rdata in answers]
        except dns.resolver.NXDOMAIN:
            # Domain does not exist, skip it
            continue
        except dns.resolver.NoAnswer:
            # No records of this type, just continue to the next type
            continue
        except Exception as e:
            print(f"Error querying {record_type} records for {domain}: {str(e)}", file=sys.stderr)
            continue

    # Post-processing: Remove A and AAAA records if CNAME exists, unless keep_a_aaaa is True
    if "CNAME" in records and not keep_a_aaaa:
        records.pop("A", None)
        records.pop("AAAA", None)

    return records


def format_records(domain, records, verbosity=0):
    """
    Format DNS records into a structured dictionary.

    Args:
        domain (str): The domain name.
        records (dict): The DNS records to format.
        verbosity (int): The level of verbosity for output.

    Returns:
        dict: A dictionary with formatted DNS records.
    """
    formatted = {domain: {}}

    for record_type, record_list in records.items():
        formatted[domain][record_type] = []

        for record in record_list:
            if record_type in ["MX", "SRV", "NAPTR"]:
                if record_type == "MX":
                    content, prio, ttl = record
                    record_data = {
                        "content": content,
                        "ttl": str(ttl),
                        "prio": str(prio),
                    }
                elif record_type == "SRV":
                    target, priority, weight, port, ttl = record
                    record_data = {
                        "content": f"{weight} {port} {target}",
                        "ttl": str(ttl),
                        "prio": str(priority),
                    }
                else:  # NAPTR
                    replacement, order, preference, ttl = record
                    record_data = {
                        "content": replacement,
                        "ttl": str(ttl),
                        "order": str(order),
                        "preference": str(preference),
                    }
            elif record_type == "TXT":
                content, ttl = record
                record_data = {"content": content.strip('"'), "ttl": str(ttl)}
            else:
                # Handle other record types (A, AAAA, CNAME, NS)
                content, ttl = record
                record_data = {"content": content, "ttl": str(ttl)}

            formatted[domain][record_type].append(record_data)

    return formatted


def print_usage():
    """
    Print usage information for the DNS export tool.
    """
    print("\nUsage:")
    print("1. Export DNS records for one or more domains to stdout:")
    print(f"   python {sys.argv[0]} --domains example.com example.org")
    print(f"   python {sys.argv[0]} -d example.com example.org")
    print(f"   echo 'example.com example.org' | python {sys.argv[0]}")
    print("\n2. Export DNS records to a file:")
    print(f"   python {sys.argv[0]} --domains example.com example.org -f output.json")
    print(f"   echo 'example.com example.org' | python {sys.argv[0]} -f output.json")
    print("\n3. Increase verbosity:")
    print(f"   python {sys.argv[0]} --domains example.com example.org -v")
    print(f"   python {sys.argv[0]} --domains example.com example.org -vv")
    print("\n4. Export all record types:")
    print(f"   python {sys.argv[0]} --domains example.com example.org --all")
    print("\n5. Exclude specific record types:")
    print(f"   python {sys.argv[0]} --domains example.com example.org --all --exclude NS SOA")
    print("\n6. Keep A and AAAA records when CNAME exists:")
    print(f"   python {sys.argv[0]} --domains example.com example.org --keep-a-aaaa")
    print("\nAdd --verbose or -v to any command for detailed output.")


def main():
    """
    Main function to handle command-line arguments and execute the DNS export process.
    """
    parser = argparse.ArgumentParser(
        description="Export DNS records for one or more domains", add_help=False
    )
    parser.add_argument(
        "-h", "--help", action="store_true", help="Show this help message and exit"
    )
    parser.add_argument(
        "-d", "--domains", nargs="+", help="Domains to export DNS records for"
    )
    parser.add_argument(
        "-f", "--file", help="Output file name (if not specified, output to stdout)"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity (use -v or -vv)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output raw DNS records as retrieved from the nameserver",
    )
    parser.add_argument(
        "-a", "--all", action="store_true", help="Export all record types"
    )
    parser.add_argument("--exclude", nargs="+", help="Record types to exclude from the output")
    parser.add_argument(
        "--keep-a-aaaa",
        action="store_true",
        help="Keep A and AAAA records even when CNAME exists",
    )
    args = parser.parse_args()

    if args.help:
        parser.print_help()
        print_usage()
        sys.exit(0)

    domains = args.domains
    if not domains:
        if sys.stdin.isatty():
            print("Error: Please provide domains using --domains/-d or via stdin")
            print_usage()
            sys.exit(1)
        else:
            domains = sys.stdin.read().split()

    if not domains:
        print("Error: No domains provided")
        print_usage()
        sys.exit(1)

    output_file = args.file
    verbosity = args.verbose
    raw_output = args.raw

    if args.all:
        record_types = [
            "A",
            "AAAA",
            "AFSDB",
            "APL",
            "CAA",
            "CDNSKEY",
            "CDS",
            "CERT",
            "CNAME",
            "DHCID",
            "DLV",
            "DNAME",
            "DNSKEY",
            "DS",
            "EUI48",
            "EUI64",
            "HINFO",
            "HIP",
            "IPSECKEY",
            "KEY",
            "KX",
            "LOC",
            "MX",
            "NAPTR",
            "NS",
            "NSEC",
            "NSEC3",
            "NSEC3PARAM",
            "PTR",
            "RP",
            "SIG",
            "SMIMEA",
            "SOA",
            "SPF",
            "SRV",
            "SSHFP",
            "SVCB",
            "TLSA",
            "TXT",
            "URI",
            "ZONEMD",
        ]
    else:
        record_types = ["A", "AAAA", "CNAME", "MX", "TXT", "SPF"]

    if args.exclude:
        record_types = [rt for rt in record_types if rt not in args.exclude]

    all_records = []

    for domain in domains:
        if verbosity >= 1:
            print(f"Fetching DNS records for {domain}", file=sys.stderr)

        records = get_records(domain, record_types, raw_output, args.keep_a_aaaa)

        if verbosity >= 1:
            print(f"Raw records for {domain}: {records}", file=sys.stderr)

        if raw_output:
            formatted_records = {domain: records}
        else:
            formatted_records = format_records(domain, records, verbosity)

        all_records.append(formatted_records)

    if output_file:
        with open(output_file, "w") as f:
            json.dump(all_records, f, indent=2)
        if verbosity >= 1:
            print(f"DNS records exported to {output_file}", file=sys.stderr)
        else:
            print(
                f"DNS records for {', '.join(domains)} exported to {output_file}",
                file=sys.stderr,
            )
    else:
        json.dump(all_records, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
