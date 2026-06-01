import ipaddress
import cloudflare
import requests
import os
import sys
import logging
import psutil
from logging.handlers import RotatingFileHandler
from typing import Any
from dotenv import load_dotenv

def load_and_validate_config(dotenv_path: str) -> dict[str, Any]:
    load_dotenv(os.path.join(os.path.dirname(__file__), dotenv_path))

    config: dict[str, Any] = {
        "ZONE_ID": os.getenv("ZONE_ID"),
        "CLOUDFLARE_ZONE_API_TOKEN": os.getenv("CLOUDFLARE_ZONE_API_TOKEN"),
        "DNS_RECORDS": os.getenv("DNS_RECORDS"),
        "IP": os.getenv("IP", "").strip().lower(),
        "LOG_FILE_NAME": os.getenv("LOG_FILE_NAME", "cloudflare-ddns.log")
    }

    if not all([config["ZONE_ID"], config["CLOUDFLARE_ZONE_API_TOKEN"], config["DNS_RECORDS"], config["IP"]]):
        raise ValueError("ZONE_ID, CLOUDFLARE_ZONE_API_TOKEN, DNS_RECORDS, and IP must be set!")

    config["IS_EXTERNAL"] = (config["IP"] == "external")
    config["DNS_RECORDS"] = config["DNS_RECORDS"].split(",")

    if config["IS_EXTERNAL"]:
        config["EXTERNAL_IP_APIS"] = os.getenv("EXTERNAL_IP_APIS")
        if not config["EXTERNAL_IP_APIS"]:
            raise ValueError("EXTERNAL_IP_APIS must be set when IP=external!")
        config["EXTERNAL_IP_APIS"] = config["EXTERNAL_IP_APIS"].split(",")
    else:
        config["INTERFACE"] = os.getenv("INTERFACE")
        if not config["INTERFACE"]:
            raise ValueError("INTERFACE must be set when IP=internal!")

    config["PROXIED"] = os.getenv("PROXIED", "false").lower() == "true"

    raw_ttl = os.getenv("TTL", "120").strip()
    if not raw_ttl.isdigit():
        raise ValueError(f"TTL must be a valid number! Found: '{raw_ttl}'")

    ttl_value = int(raw_ttl)
    if ttl_value != 1 and not (120 <= ttl_value <= 7200):
        raise ValueError(f"TTL must be 1 (Auto) or between 120 and 7200! Found: {ttl_value}")

    config["TTL"] = ttl_value

    return config

def get_external_ip(external_ip_apis: list[str]) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    for api in external_ip_apis:
        try:
            response = requests.get(api.strip(), timeout=5)
            response.raise_for_status()
            return ipaddress.ip_address(response.text.strip())
        except Exception as error:
            logging.warning(f"Request to API {api} failed: {error}")
    raise Exception("All external IP API providers failed!")

def get_internal_ip(interface: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    if interface not in psutil.net_if_addrs():
        raise ValueError(f"Netzwerk-Interface {interface} existiert nicht!")

    addresses = psutil.net_if_addrs().get(interface, [])

    for address in addresses:
        if address.family == 10:
            ip = ipaddress.ip_address(address.address.split('%')[0])
            if not ip.is_link_local:
                return ip
    # Fallback IPv4-Address
    for address in addresses:
        if address.family == 2:
            return ipaddress.ip_address(address.address)

    raise ValueError(f"Interface {interface} doesn't have a usuable IPv4- or global IPv6-Address!")

def get_ip(mode: bool, external_ip_apis: list[str], interface: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    return get_external_ip(external_ip_apis) if mode else get_internal_ip(interface)

### Main
logger = logging.getLogger("CloudflareDDNS")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

try:
    config = load_and_validate_config("cloudflare-ddns.conf")

    ZONE_ID = config["ZONE_ID"]
    CLOUDFLARE_ZONE_API_TOKEN = config["CLOUDFLARE_ZONE_API_TOKEN"]
    DNS_RECORDS = config["DNS_RECORDS"]
    IS_EXTERNAL = config["IS_EXTERNAL"]
    EXTERNAL_IP_APIS = config.get("EXTERNAL_IP_APIS", [])
    INTERFACE = config.get("INTERFACE", "")
    PROXIED = config["PROXIED"]
    TTL = config["TTL"]
    LOG_FILE_NAME = config["LOG_FILE_NAME"]

    # Must be added later because of LOG_FILE_NAME constant
    log_file = os.path.join(os.path.dirname(__file__), LOG_FILE_NAME)
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    client = cloudflare.Cloudflare(api_token=CLOUDFLARE_ZONE_API_TOKEN)

    dns_records = client.dns.records.list(zone_id=ZONE_ID)
    if not dns_records:
        raise Exception("No DNS records found!")

    if DNS_RECORDS == ["*"]:
        filtered_records = dns_records
    else:
        filtered_records = [record for record in dns_records if record.name in DNS_RECORDS]

    if not filtered_records:
        raise Exception("No matching records found in the zone!")

    current_ip = get_ip(IS_EXTERNAL, EXTERNAL_IP_APIS, INTERFACE)
    record_type = "A" if current_ip.version == 4 else "AAAA"

    updated = False
    for record in filtered_records:
        if record.content != str(current_ip):
            client.dns.records.update(
                record.id,
                zone_id=ZONE_ID,
                name=record.name,
                type=record_type,
                content=str(current_ip),
                proxied=PROXIED,
                ttl=TTL
            )
            ttl_display = "Auto" if TTL == 1 else f"{TTL}s"
            updated = True
            logger.info(f"DNS record {record.name} successfully updated to {current_ip} ({record_type}, TTL: {ttl_display}).")

    if not updated:
        logger.info(f"All records already have {current_ip} applied as their IP.")

except Exception as error:
    logger.error(f"Execution failed: {str(error)}")
    sys.exit(1)
