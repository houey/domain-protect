#!/usr/bin/env python
import json
import requests

from utils_aws import (  # pylint:disable=import-error
    list_accounts,
    list_hosted_zones,
    list_resource_record_set_pages,
    publish_to_sns,
)


def vulnerable_storage(domain_name):

    try:
        response = requests.get("https://" + domain_name, timeout=0.5)
        if "NoSuchBucket" in response.text:
            return True

    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
        pass

    try:
        response = requests.get(f"http://{domain_name}", timeout=0.2)
        if "NoSuchBucket" in response.text:
            return True

    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
        pass

    return False


def lambda_handler(event, context):  # pylint:disable=unused-argument

    vulnerable_domains = []
    json_data = {"Findings": []}

    accounts = list_accounts()

    for account in accounts:
        account_id = account["Id"]
        account_name = account["Name"]

        hosted_zones = list_hosted_zones(account_id, account_name)

        for hosted_zone in hosted_zones:
            print(f"Searching for A records with missing storage buckets in hosted zone {hosted_zone['Name']}")

            pages_records = list_resource_record_set_pages(account_id, account_name, hosted_zone["Id"])

            for page_records in pages_records:
                record_sets = [
                    r
                    for r in page_records["ResourceRecordSets"]
                    if r["Type"] in ["A"] and not r["Name"].startswith("10.")
                ]

                for record in record_sets:
                    print(f"checking if {record['Name']} is vulnerable to takeover")
                    result = vulnerable_storage(record["Name"])
                    if result:
                        print(f"{record['Name']} in {account_name} is vulnerable")
                        vulnerable_domains.append(record["Name"])
                        json_data["Findings"].append(
                            {"Account": account_name, "AccountID": str(account_id), "Domain": record["Name"]}
                        )

            if len(hosted_zones) == 0:
                print("No hosted zones found in " + account_name + " account")

    print(json.dumps(json_data, sort_keys=True, indent=2))

    if len(vulnerable_domains) > 0:
        publish_to_sns(json_data, "Amazon Route53 A record with missing storage bucket")
