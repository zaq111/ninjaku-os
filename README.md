# Ninjaku OS Router

Ninjaku OS Router is a Debian-based router control plane for small ARM64 appliances.
It is designed for devices like the Amlogic GXL S905X and provides a local API, a web dashboard,
and a CLI for day-to-day router management.

> Status: alpha

## Features
- router, firewall, DHCP, network, device, profile, policy, and system management
- background daemon that restores router state and syncs device data
- REST API for automation
- lightweight web dashboard
- CLI for local administration
- SQLite-backed local storage

## What this repo contains
- `services/ninjakud.py` — background daemon
- `api/` — Flask API and route modules
- `webui/` — browser dashboard
- `scripts/ninjaku` — operator CLI
- `scripts/ninjaku-status` — JSON status helper
- `lib/`, `core/`, `modules/` — shared services and feature modules

## Requirements
- Debian-based Linux
- Python 3
- `python3-flask`
- `git`
- root access is recommended, because the services manage system networking

## Database
Data is stored in:
- `/var/lib/ninjaku/ninjaku.db`

## Quick install

```bash
sudo apt update
sudo apt install -y git python3 python3-flask
sudo mkdir -p /opt
sudo git clone <repository-url> /opt/ninjaku
cd /opt/ninjaku
sudo chmod +x scripts/ninjaku scripts/ninjaku-status services/ninjakud.py api/app.py
sudo ln -sf /opt/ninjaku/scripts/ninjaku /usr/local/bin/ninjaku
sudo ln -sf /opt/ninjaku/scripts/ninjaku-status /usr/local/bin/ninjaku-status
sudo mkdir -p /var/lib/ninjaku
```

### systemd services
Create these files on the target machine.

`/etc/systemd/system/ninjakud.service`

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

`/etc/systemd/system/ninjaku-api.service`

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

Then enable and start the services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ninjakud.service ninjaku-api.service
```

## Usage

### CLI
```bash
ninjaku status
ninjaku api
ninjaku devices
ninjaku devices sync
ninjaku devices cleanup-wan
ninjaku devices mark-offline 5
ninjaku profiles
ninjaku policy
```

Useful subcommands:
- `ninjaku devices set-alias <mac> <name>`
- `ninjaku devices set-notes <mac> <notes>`
- `ninjaku devices set-profile <mac> <profile>`
- `ninjaku policy set <profile> <field> <value>`
- `ninjaku policy resolve <mac-or-profile>`
- `ninjaku policy apply`
- `ninjaku profiles add <name> [description]`
- `ninjaku profiles delete <name>`

### API
The Flask app listens on `127.0.0.1:8181`.
If you want LAN access, put it behind a reverse proxy or port-forward it.

Useful endpoints:
- `GET /api/v1`
- `GET /api/v1/endpoints`

The API is split into route modules for:
- system
- network
- router
- firewall
- DHCP
- devices
- profiles
- policy
- settings

### Web dashboard
The dashboard is served from `/` and static assets are served from `/static/...`.

## Troubleshooting
- Check the daemon: `systemctl status ninjakud`
- Check the API: `systemctl status ninjaku-api`
- Check logs: `journalctl -u ninjakud -u ninjaku-api -f`
- Verify the database directory exists: `/var/lib/ninjaku`

## Changelog
See `CHANGELOG.md` for release notes.
