# About

* Cloudflare DDNS Python script
* Update source IP addresses of A/AAAA records
* Choose between LAN/WAN IP address
* Ensure high availability with multiple APIs for finding the current public IP address
* Supports IPv6

# Requirements

* Python
* Venv
* DNS records must be pre-created (the API token should only edit DNS records)
* Cloudflare API token with Zone-DNS-Edit permissions

# Creating a Cloudflare API Token

To create a Cloudflare API token for your specific DNS zone, follow these steps:

1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Search for ```Edit zone DNS``` in ```API token templates```
3. Select ```Use template```
4. The following permission is required:
   * ```Zone - DNS - Edit```
5. Select the domain you want to use under ```Zone Resources```
   * ```Include - Specific zone - example.com```
6. Click on ```Continue to summary```
7. Click on ```Create Token```

# Installation
1. Install dependencies if not already installed (Debian/Ubuntu):
```bash
sudo apt install python3 python3-venv
```

2. Clone the repository:

```bash
git clone https://github.com/SpiritofthePast/DDNS-Cloudflare-Python.git .
```

3. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Edit the configuration file with your Cloudflare Zone ID and API token

# Configuration Settings

## Required Settings

| Option                    | Description                                                                                         | Example                            |
| ------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------- |
| IP                        | Which IP should be used for the record: internal/external                                           | external                           |
| DNS_RECORDS               | A/AAAA records to be updated. You can separate multiple records with commas. Use * for all records. | ddns1.example.com,ddns2.example.com|
| ZONE_ID                   | Cloudflare Zone ID. Accessible on the overview page of your domain.                                 | Cloudflare Zone ID: https://developers.cloudflare.com/fundamentals/account/find-account-and-zone-ids/ |
| CLOUDFLARE_ZONE_API_TOKEN | Cloudflare Zone API token                                                                           |                                    |
| PROXIED                   | Use Cloudflare proxy, yes or no                                                                     | false                              |
| TTL                       | 120–7200 seconds or 1 for Auto                                                                      | 120                                                                                                   |

## IP mode specific settings

| Option           | Description                                                                                                  | Example                                                              |
| ---------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| EXTERNAL_IP_APIS | Required for ```IP=external```. URLs used to determine your public IP. You can separate multiple URLs with commas. | https://api.ipify.org/,https://icanhazip.com/,https://ifconfig.me/ip |
| INTERFACE        | Required for ```IP=internal```. Sets the local network interface used to fetch the IP address.                     | e.g. eth0, wlan0. Look for a suitable interface with `ip a`          |

# Usage
## Run the script manually
```bash
python cloudflare-ddns.py
```

## Run the script using crontab

Run every 5 minutes:
```
*/5 * * * * cd /opt/cloudflare-ddns && .venv/bin/python cloudflare-ddns.py
```

Run at boot:

```
@reboot cd /opt/cloudflare-ddns && .venv/bin/python cloudflare-ddns.py
```

Run 1 minute after boot:

```
@reboot sleep 60 && cd /opt/cloudflare-ddns && .venv/bin/python cloudflare-ddns.py
```

Run daily at 05:00:

```
0 5 * * * cd /opt/cloudflare-ddns && .venv/bin/python cloudflare-ddns.py
```

# Logging

The script will create a rotating log file located in the script's folder.

# Example Configuration
```env
#########################
### Required settings ###
#########################

## Which IP should be used for the record: internal/external
IP="external"

## A/AAAA records to be updated. You can separate multiple records by comma. Use * for all records.
DNS_RECORDS="ddns1.example.com,ddns2.example.com"

## Cloudflare Zone ID. You can find this on the overview page of your domain
ZONE_ID="changeMe"

## Cloudflare Zone API Token
CLOUDFLARE_ZONE_API_TOKEN="changeMe"

## Use Cloudflare proxy
PROXIED="false"

## 120–7200 seconds or 1 for Auto
TTL=120

##############################
### Mode-specific settings ###
##############################

## Required for IP=external
## URLs used to determine your public IP. You can separate multiple URLs with commas.
EXTERNAL_IP_APIS="https://api.ipify.org/,https://icanhazip.com/,https://ifconfig.me/ip"

## Required for IP=internal
## Sets the local network interface to fetch the IP from
## e.g. eth0, wlan0, ...
INTERFACE="eth0"
```
# License
Distributed under the MIT License. See LICENSE for more information.
