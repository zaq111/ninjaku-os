# Ninjaku OS Router

Ninjaku OS Router is a Debian-based router control plane for small ARM64 appliances.
It is currently developed and tested on an Amlogic GXL/S905X STB running the custom
`6.12.87-ninjaijo-gxl+` kernel.

The project provides a local REST API, a modular web dashboard, a background daemon,
and the `ninjaku` CLI for day-to-day router management.

> Status: 1.0 alpha

## Current target

- Device class: Amlogic GXL / S905X router appliance
- Kernel tested: `Linux 6.12.87-ninjaijo-gxl+ #4 SMP PREEMPT_DYNAMIC Mon Jun 29 03:45:57 +07 2026`
- Runtime OS: Debian-based ARM64 rootfs
- Primary install path: `/opt/ninjaku`
- API listen address: `0.0.0.0:8181`
- Web dashboard: `http://<router-ip>:8181/`
- Local database: `/var/lib/ninjaku/ninjaku.db`

## Features

- Router state management for WAN, LAN, IPv4 forwarding, NAT, and DHCP
- nftables firewall policy apply and reset flows
- Device discovery from DHCP leases and neighbor tables
- Device aliases, notes, profiles, and online/offline tracking
- Static DHCP lease management with dnsmasq config generation
- Profile-based policy management for internet access, DNS filter mode, bandwidth, schedules, priority, and QoS fields
- Central policy apply path that refreshes firewall rules and QoS together
- QoS shaping with CAKE, IFB ingress redirection, diffserv, NAT mode, ACK filtering, overhead/MPU/RTT tuning, and profile-based DSCP marks
- QoS pipe CRUD backend for reusable shaping profiles
- AdGuard Home integration for status, install, URL config, protection toggle, upstream DNS, filter updates, and query log access
- Lightweight dnsmasq DNS filter backend for domain block lists
- Modular REST API with endpoint discovery
- Modular web dashboard menu loaded from `/api/v1/modules`
- SQLite-backed local storage
- Background daemon that restores router state and refreshes device data

## What this repo contains

- `services/ninjakud.py` - background daemon that initializes DB state, restores router mode, and periodically syncs devices
- `api/app.py` - Flask API and web dashboard entry point
- `api/routes_*.py` - REST route modules
- `webui/` - browser dashboard split into CSS, shared JS, and page modules
- `scripts/ninjaku` - operator CLI
- `scripts/ninjaku-status` - JSON status helper
- `modules/` - command modules used by the CLI/API layer
- `lib/` - router, firewall, DHCP, device, policy, QoS, AdGuard, DNS filter, and settings services
- `core/` - compatibility/shared helpers
- `data/` - development database copy

## Dashboard pages

The dashboard is served by the Flask app from `/` and loads assets from `/assets/...`.
The visible menu is supplied by `GET /api/v1/modules`.

Current dashboard pages:

- Overview
- Router
- Devices
- Static Leases
- Policy
- QoS
- AdGuard Home
- Settings

A DNS Filter page exists under `webui/js/pages/disabled/dns_filter.js`, but it is not currently enabled in the dashboard menu.

## Requirements

- Debian-based Linux on ARM64
- Python 3
- `python3-flask`
- `git`
- `curl`
- `iproute2`
- `nftables`
- `dnsmasq`
- `systemd`
- root access, because the services manage networking

Recommended kernel/module support for the current feature set:

- `nf_tables`, `nft_chain_nat`, `nft_masq`, `nf_conntrack`, `nf_nat`
- `sch_cake`, `sch_ingress`, `act_mirred`, `ifb`
- Ethernet/PHY support for the target board
- Optional USB LAN and WiFi modules if used as WAN/LAN adapters

For the Amlogic GXL/S905X Ethernet fix, `CONFIG_MDIO_BUS_MUX_MESON_GXL=y` must be built in, not loaded as a module.

## Quick install

```bash
sudo apt update
sudo apt install -y git python3 python3-flask curl iproute2 nftables dnsmasq
sudo mkdir -p /opt
sudo git clone <repository-url> /opt/ninjaku
cd /opt/ninjaku
sudo chmod +x scripts/ninjaku scripts/ninjaku-status services/ninjakud.py api/app.py
sudo ln -sf /opt/ninjaku/scripts/ninjaku /usr/local/bin/ninjaku
sudo ln -sf /opt/ninjaku/scripts/ninjaku-status /usr/local/bin/ninjaku-status
sudo mkdir -p /var/lib/ninjaku
```

## systemd services

Create `/etc/systemd/system/ninjakud.service`:

```ini
[Unit]
Description=Ninjaku OS Router Core Daemon
After=network.target

[Service]
Type=simple
ExecStart=/opt/ninjaku/services/ninjakud.py
Restart=always
RestartSec=5
User=root
WorkingDirectory=/opt/ninjaku

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/ninjaku-api.service`:

```ini
[Unit]
Description=Ninjaku OS Router REST API
After=network.target ninjakud.service
Requires=ninjakud.service

[Service]
Type=simple
ExecStart=/opt/ninjaku/api/app.py
Restart=always
RestartSec=5
User=root
WorkingDirectory=/opt/ninjaku

[Install]
WantedBy=multi-user.target
```

Enable and start both services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ninjakud.service ninjaku-api.service
```

Check service state:

```bash
systemctl status ninjakud
systemctl status ninjaku-api
journalctl -u ninjakud -u ninjaku-api -f
```

## CLI usage

```bash
ninjaku status
ninjaku status --json
ninjaku audit
ninjaku modules
ninjaku network
ninjaku router [status|lan-up|forward-on|nat-up|nat-down|enable|disable]
ninjaku firewall [status|init|reset|apply-policy]
ninjaku dhcp [status|start|stop]
ninjaku config [list|set]
ninjaku devices [sync|cleanup-wan|mark-offline|set-alias|set-notes|set-profile]
ninjaku leases [set|delete|apply]
ninjaku dns-filter [add|delete|import|apply]
ninjaku profiles [add|delete]
ninjaku policy [set|resolve|apply]
ninjaku api
ninjaku help
```

Useful examples:

```bash
ninjaku router enable
ninjaku firewall apply-policy
ninjaku devices sync
ninjaku devices cleanup-wan
ninjaku devices mark-offline 5
ninjaku devices set-alias <mac> <name>
ninjaku devices set-notes <mac> <notes>
ninjaku devices set-profile <mac> <profile>
ninjaku leases set <mac> <ip> [hostname]
ninjaku leases apply
ninjaku profiles add <name> [description]
ninjaku profiles delete <name>
ninjaku policy set <profile> <field> <value>
ninjaku policy resolve <mac-or-profile>
ninjaku policy apply
```

## API

The Flask API listens on port `8181` and currently binds to `0.0.0.0`.

Discovery endpoints:

- `GET /api/v1`
- `GET /api/v1/endpoints`
- `GET /api/v1/modules`

System and network:

- `GET /api/v1/status`
- `GET /api/v1/network`
- `GET /api/v1/router`
- `POST /api/v1/router/enable`
- `POST /api/v1/router/disable`
- `GET /api/v1/settings`
- `POST /api/v1/settings`

Firewall, DHCP, leases, and devices:

- `GET /api/v1/firewall`
- `POST /api/v1/firewall/apply-policy`
- `GET /api/v1/dhcp`
- `POST /api/v1/dhcp/start`
- `POST /api/v1/dhcp/stop`
- `GET /api/v1/leases`
- `POST /api/v1/leases`
- `DELETE /api/v1/leases/<mac>`
- `POST /api/v1/leases/apply`
- `GET /api/v1/devices`
- `POST /api/v1/devices/sync`
- `POST /api/v1/devices/<mac>/profile`
- `POST /api/v1/devices/<mac>/alias`
- `POST /api/v1/devices/<mac>/notes`

Profiles, policy, and QoS:

- `GET /api/v1/profiles`
- `POST /api/v1/profiles`
- `DELETE /api/v1/profiles/<name>`
- `POST /api/v1/profiles/<name>`
- `GET /api/v1/policy`
- `POST /api/v1/policy`
- `POST /api/v1/policy/<profile>`
- `GET /api/v1/policy/resolve`
- `POST /api/v1/policy/apply`
- `GET /api/v1/qos`
- `POST /api/v1/qos`
- `POST /api/v1/qos/apply`
- `POST /api/v1/qos/disable`
- `GET /api/v1/qos/pipes`
- `POST /api/v1/qos/pipes`
- `DELETE /api/v1/qos/pipes/<pipe_id>`

DNS filtering and AdGuard Home:

- `GET /api/v1/dns-filter`
- `POST /api/v1/dns-filter/domains`
- `DELETE /api/v1/dns-filter/domains/<domain>`
- `POST /api/v1/dns-filter/apply`
- `GET /api/v1/adguard`
- `POST /api/v1/adguard/url`
- `POST /api/v1/adguard/install`
- `POST /api/v1/adguard/protection`
- `POST /api/v1/adguard/update-filters`
- `GET /api/v1/adguard/querylog`
- `GET /api/v1/adguard/dns-config`
- `POST /api/v1/adguard/upstream`

## Policy and QoS notes

Policy is the current source of truth for profile behavior. The policy table includes:

- `internet`
- `bandwidth`
- `dns_filter`
- `schedule`
- `priority`
- `qos_enabled`
- `qos_download`
- `qos_upload`
- `qos_priority`

`POST /api/v1/policy/apply` and `ninjaku policy apply` run the centralized apply path:

- firewall rules are refreshed through the firewall module
- QoS is applied through the QoS module
- QoS can create DSCP rules from device profile policy

QoS defaults are stored in settings keys under `qos.*`, including WAN interface, IFB interface, upload/download rates, diffserv mode, NAT mode, ACK filter, wash, split GSO, overhead, MPU, and RTT.

## Database

Production data is stored in:

```text
/var/lib/ninjaku/ninjaku.db
```

The schema is created and migrated by service helpers at runtime. Core tables include settings, audit logs, devices, profiles, policies, static leases, DNS filter domains, and QoS pipes.

## Development notes

The repository is expected to run from `/opt/ninjaku`. Several files insert or assume that path so services, scripts, and imports are aligned on the target router.

Useful checks on a live router:

```bash
cd /opt/ninjaku
git status --short
git log --oneline --decorate -10
systemctl is-active ninjakud ninjaku-api
curl -s http://127.0.0.1:8181/api/v1
curl -s http://127.0.0.1:8181/api/v1/modules
```

## Troubleshooting

- Check daemon state: `systemctl status ninjakud`
- Check API state: `systemctl status ninjaku-api`
- Follow logs: `journalctl -u ninjakud -u ninjaku-api -f`
- Verify database path: `/var/lib/ninjaku/ninjaku.db`
- Verify nftables support: `modprobe nf_tables nft_chain_nat nft_masq nf_conntrack nf_nat`
- Verify QoS support: `modprobe sch_cake act_mirred sch_ingress ifb`
- Verify API locally: `curl -s http://127.0.0.1:8181/api/v1`
- Verify dashboard from LAN: `http://<router-ip>:8181/`

If `nft` returns `Protocol not supported`, the running kernel usually lacks the required nftables modules in `/lib/modules/$(uname -r)`.

## Recent updates captured in this README

- README updated to match the current modular API and dashboard layout
- Static Leases documented
- QoS and QoS Pipes documented
- AdGuard Home integration documented
- DNS filter backend documented
- Central firewall plus QoS policy apply path documented
- Current tested Ninjaijo kernel target documented

## Changelog

See `CHANGELOG.md` for release notes.
