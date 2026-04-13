import os
import shutil

from lib.system import run

def distro():
    info = {}

    try:
        with open("/etc/os-release") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    info[k] = v.strip('"')
    except Exception:
        pass

    return {
        "id": info.get("ID", ""),
        "version": info.get("VERSION_ID", ""),
        "pretty": info.get("PRETTY_NAME", ""),
    }


def has_binary(binary):
    return shutil.which(binary) is not None


def dpkg_installed(pkg):
    r = run(["dpkg", "-s", pkg])
    return r["ok"]


def apt_install(pkg):
    return run([
        "apt-get",
        "-y",
        "install",
        pkg
    ])


def apt_remove(pkg):
    return run([
        "apt-get",
        "-y",
        "remove",
        pkg
    ])


def status():
    return {
        "distro": distro(),
        "packages": {
            "tailscale": {
                "installed": dpkg_installed("tailscale"),
                "binary": has_binary("tailscale"),
            },
            "wireguard-tools": {
                "installed": dpkg_installed("wireguard-tools"),
                "binary": has_binary("wg"),
            },
        }
    }
