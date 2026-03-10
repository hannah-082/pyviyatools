#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# getdefaultqkb.py
# February 2026
#
# Get current default QKB settings as defined in Environment Manager.  
# Optional choose which engine to return (CAS or compute) defaults to both
#
# Change History
#
# 02FEB2026 Initial version

# Import Python modules
from __future__ import print_function
import argparse
import pprint
pp = pprint.PrettyPrinter(indent=4)
import sys

from sharedfunctions import callrestapi, printresult, getconfigurationproperty

# Get current state for cas or compute depending on value in --engine
def parse_cas_qkb(contents):
    """
    Parse the CAS QKB settings from the sas.cas.instance.config contents.

    Expects lines like:
        cas.DQSETUPLOC="DefaultQKBName"
        cas.DQLOCALE="DefaultLocale"
    """
    language = None
    locale = None

    if not contents:
        return {"language": language, "locale": locale}

    for line in contents.splitlines():
        line = line.strip()
        if line.startswith("cas.DQSETUPLOC"):
            _, value = line.split("=", 1)
            language = value.strip().strip('"')
        elif line.startswith("cas.DQLOCALE"):
            _, value = line.split("=", 1)
            locale = value.strip().strip('"')

    return {"language": language, "locale": locale}


def parse_compute_qkb(contents):
    """
    Parse the Compute QKB settings from the sas.compute.server contents.

    Expects tokens like:
        -DQSETUPLOC "DefaultQKBName"
        -DQLOCALE "DefaultLocale"
    """
    language = None
    locale = None

    if not contents:
        return {"language": language, "locale": locale}

    tokens = contents.split()

    for i, tok in enumerate(tokens):
        if tok.startswith("-DQSETUPLOC"):
            if i + 1 < len(tokens):
                value = tokens[i + 1].strip().strip('"')
                language = value
        elif tok.startswith("-DQLOCALE"):
            if i + 1 < len(tokens):
                value = tokens[i + 1].strip().strip('"')
                locale = value

    return {"language": language, "locale": locale}

# Write conditions to only retrieve the ones we need
def get_cas_qkb():
    """Get CAS QKB info as a dict with basic error handling."""
    configurationdef_cas = "sas.cas.instance.config"
    cas_info = {"language": None, "locale": None}

    try:
        configurationproperty_cas = getconfigurationproperty(configurationdef_cas)
    except Exception as e:
        # In pyviyatools, failures are often returned as text JSON via printresult.[web:1][web:18]
        cas_info["error"] = "Failed to retrieve CAS configuration: {0}".format(e)
        return cas_info

    if not configurationproperty_cas or "items" not in configurationproperty_cas:
        cas_info["error"] = "No CAS configuration items found for definition {0}".format(
            configurationdef_cas
        )
        return cas_info

    first_item = configurationproperty_cas["items"][0]
    props = first_item.get("properties", {})
    contents = props.get("contents", "")

    parsed = parse_cas_qkb(contents)
    cas_info.update(parsed)
    return cas_info


def get_compute_qkb():
    """Get Compute QKB info as a dict with basic error handling."""
    configurationdef_compute = "sas.compute.server"
    compute_info = {"language": None, "locale": None}

    try:
        configurationproperty_compute = getconfigurationproperty(configurationdef_compute)
    except Exception as e:
        compute_info["error"] = (
            "Failed to retrieve Compute configuration: {0}".format(e)
        )
        return compute_info

    if not configurationproperty_compute or "items" not in configurationproperty_compute:
        compute_info["error"] = (
            "No Compute configuration items found for definition {0}".format(
                configurationdef_compute
            )
        )
        return compute_info

    first_item = configurationproperty_compute["items"][0]
    props = first_item.get("properties", {})
    contents = props.get("contents", "")

    parsed = parse_compute_qkb(contents)
    compute_info.update(parsed)
    return compute_info


def main():
    # Set input parameters
    parser = argparse.ArgumentParser(
        description="Get default QKB setting for SAS CAS and Compute engines"
    )
    parser.add_argument(
        "--engine",
        nargs="*",
        choices=["cas", "compute"],
        required='True',
        help=(
            "Engine(s) to query: cas, compute. "
            "If omitted, both are returned."
        ),
    )

    parser.add_argument(
        "-o","--output", help="Output Style", choices=['csv','json','simple','simplejson'],default='json'
    )

    args = parser.parse_args()
    configurationdef=args.configuration
    output_style=args.output

    # If no engine specified, default to both
    engines = args.engine if args.engine else ["cas", "compute"]

    results = {}

    if "cas" in engines:
        results["cas"] = get_cas_qkb()

    if "compute" in engines:
        results["compute"] = get_compute_qkb()

    # Output JSON in the same style as other pyviyatools scripts.
    printresult(results, output_style)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Common pattern in CLI tools: exit cleanly on Ctrl+C
        sys.exit(1)
