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
        -DQLOCALE (DefaultLocale)
        -DQSETUPLOC 'DefaultQKBName'
        
    """
    language = None
    locale = None

    if not contents:
        return {"language": language, "locale": locale}

    tokens = contents.split()

    for i, tok in enumerate(tokens):
        if tok.startswith("-DQSETUPLOC"):
            if i + 1 < len(tokens):
                value = tokens[i + 1].strip().strip("'")
                language = value
        elif tok.startswith("-DQLOCALE"):
            if i + 1 < len(tokens):
                value = tokens[i + 1].strip().strip('()')
                locale = value

    return {"language": language, "locale": locale}

# Write conditions to only retrieve the ones we need
def get_cas_qkb():
    """Get CAS QKB info."""
    configurationdef_cas = "sas.cas.instance.config"
    cas_info = {"language": None, "locale": None}

    configurationproperty_cas = getconfigurationproperty(configurationdef_cas)
    if not configurationproperty_cas or "items" not in configurationproperty_cas:
            return cas_info
    
    # Find item where config name == "config"
    cas_contents = ""
    for item in configurationproperty_cas["items"]:
        props = item.get("properties", {})
        config_name = props.get("name", "")
        if config_name == "config":
            cas_contents = props.get("contents", "")
            break    

    parsed = parse_cas_qkb(cas_contents)
    cas_info.update(parsed)
    return cas_info


def get_compute_qkb():
    """Get Compute QKB info."""
    configurationdef_compute = "sas.compute.server"
    compute_info = {"language": None, "locale": None}

    configurationproperty_compute = getconfigurationproperty(configurationdef_compute)
    if not configurationproperty_compute or "items" not in configurationproperty_compute:
        return compute_info

    # Find item where config name == "config_options"
    compute_contents = ""
    for item in configurationproperty_compute["items"]:
        props = item.get("properties", {})
        config_name = props.get("name", "")
        if config_name == "configuration_options":
            compute_contents = props.get("contents", "")
            break

    parsed = parse_compute_qkb(compute_contents)
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
