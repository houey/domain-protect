import dns.resolver


def vulnerable_ns(domain_name, update_scan=False):

    try:
        dns.resolver.resolve(domain_name)

    except dns.resolver.NXDOMAIN:
        return False

    except dns.resolver.NoNameservers:

        try:
            ns_records = dns.resolver.resolve(domain_name, "NS")
            if len(ns_records) == 0:
                return True

        except dns.resolver.NoNameservers:
            return True

    except dns.resolver.NoAnswer:
        return False

    except (dns.resolver.Timeout):
        if update_scan:
            return True

        return False

    except Exception as e:

        if update_scan:
            print(f"Unhandled exception testing DNS for NS records during update scan: {e}")

        else:
            print(f"Unhandled exception testing DNS for NS records during standard scan: {e}")

    return False


def vulnerable_cname(domain_name, update_scan=False):

    try:
        dns.resolver.resolve(domain_name, "A")
        return False

    except dns.resolver.NXDOMAIN:
        try:
            dns.resolver.resolve(domain_name, "CNAME")
            return True

        except dns.resolver.NoNameservers:
            return False

    except (dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return False

    except (dns.resolver.Timeout):
        if update_scan:
            return True

        return False


def vulnerable_alias(domain_name, update_scan=False):

    try:
        dns.resolver.resolve(domain_name, "A")
        return False

    except dns.resolver.NoAnswer:
        return True

    except (dns.resolver.NoNameservers, dns.resolver.NXDOMAIN):
        return False

    except (dns.resolver.Timeout):
        if update_scan:
            return True

        return False


def dns_deleted(domain_name):

    try:
        # RdataType 0 (NONE) to prevent false positives with CNAME vulnerabilities
        dns.resolver.resolve(domain_name, 0)

    except dns.resolver.NXDOMAIN:
        return True

    except (dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.resolver.Timeout):
        return False

    return False
