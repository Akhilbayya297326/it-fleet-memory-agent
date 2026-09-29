"""Read-only measurements of the machine hosting Streamlit, never remote personas."""
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import platform
import subprocess
import time

import psutil


def powershell_json(script, timeout=10):
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, timeout=timeout, check=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return json.loads(result.stdout.lstrip("\ufeff")) if result.stdout.strip() else []


def hardware_profile():
    profile = {
        "device": platform.node(), "os": platform.platform(),
        "cpu": platform.processor() or f"{psutil.cpu_count()} logical CPUs",
        "ram_gb": round(psutil.virtual_memory().total / 1024**3, 1),
        "user": getpass.getuser(), "logical_cpus": psutil.cpu_count(),
        "physical_cpus": psutil.cpu_count(logical=False),
        "source": "Streamlit host", "model": "Not exposed by operating system",
    }
    if platform.system() == "Windows":
        # Registry inventory is accessible even when CIM/WMI is unavailable.
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                profile["cpu"] = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS") as key:
                profile["model"] = " ".join(winreg.QueryValueEx(key, name)[0] for name in ("SystemManufacturer", "SystemProductName"))
        except OSError:
            pass
        try:
            details = powershell_json(
                "$ErrorActionPreference='Stop'; $c=Get-CimInstance Win32_ComputerSystem; "
                "$p=Get-CimInstance Win32_Processor | Select-Object -First 1; "
                "$o=Get-CimInstance Win32_OperatingSystem; "
                "@{model=$c.Model;manufacturer=$c.Manufacturer;cpu=$p.Name;"
                "os=$o.Caption;version=$o.Version} | ConvertTo-Json -Compress"
            )
            if details.get("model") and details.get("manufacturer"):
                profile["model"] = f"{details['manufacturer']} {details['model']}"
            if details.get("cpu"):
                profile["cpu"] = details["cpu"]
            if details.get("os") and details.get("version"):
                profile["os"] = f"{details['os']} ({details['version']})"
        except (OSError, subprocess.SubprocessError, ValueError, KeyError):
            pass  # OS-reported fallback remains real, albeit less specific.
    return profile


def network_rates(before, after, elapsed):
    if elapsed <= 0:
        return {"sent_bps": 0.0, "received_bps": 0.0}
    return {"sent_bps": max(0, after.bytes_sent - before.bytes_sent) / elapsed,
            "received_bps": max(0, after.bytes_recv - before.bytes_recv) / elapsed}


def snapshot(interval=0.25):
    before = psutil.net_io_counters()
    start = time.monotonic()
    cpu = psutil.cpu_percent(interval=interval)
    after = psutil.net_io_counters()
    memory = psutil.virtual_memory()
    disk_root = Path.home().anchor or os.path.abspath(os.sep)
    disk = psutil.disk_usage(disk_root)
    rates = network_rates(before, after, time.monotonic() - start)
    adapters = [{"name": name, "up": info.isup, "speed_mbps": info.speed}
                for name, info in psutil.net_if_stats().items()]
    battery = psutil.sensors_battery()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": cpu, "memory_percent": memory.percent,
        "memory_used_gb": round(memory.used / 1024**3, 2),
        "memory_total_gb": round(memory.total / 1024**3, 2),
        "disk_percent": disk.percent, "disk_root": disk_root,
        "disk_free_gb": round(disk.free / 1024**3, 2),
        "disk_total_gb": round(disk.total / 1024**3, 2),
        "network": rates, "adapters": adapters,
        "uptime_seconds": int(time.time() - psutil.boot_time()),
        "battery_percent": battery.percent if battery else None,
        "plugged_in": battery.power_plugged if battery else None,
    }


def process_memory(limit=8):
    rows = []
    for process in psutil.process_iter(["name", "memory_info", "pid"]):
        try:
            memory = process.info["memory_info"]
            if memory:
                rows.append({"Process": process.info["name"], "PID": process.info["pid"],
                             "Memory (MiB)": round(memory.rss / 1024**2, 1)})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(rows, key=lambda row: row["Memory (MiB)"], reverse=True)[:limit]


def recent_system_events():
    if platform.system() != "Windows":
        return [], "Automatic event-log collection is currently available on Windows only."
    try:
        result = powershell_json(
            "$ErrorActionPreference='Stop'; "
            "try { @(Get-WinEvent -FilterHashtable @{LogName='System';Level=2,3;"
            "StartTime=(Get-Date).AddDays(-1)} -MaxEvents 20 | "
            "Select-Object @{n='Time';e={$_.TimeCreated.ToString('s')}},"
            "Id,LevelDisplayName,ProviderName,Message) | ConvertTo-Json -Depth 3 -Compress } "
            "catch { if ($_.FullyQualifiedErrorId -like 'NoMatchingEventsFound*') { '[]' } else { throw } }"
        )
        return result if isinstance(result, list) else [result], None
    except (OSError, subprocess.SubprocessError, ValueError):
        return [], "Windows did not allow event-log access, or collection timed out."


def diagnostic_report(kind, profile, readings):
    heading = f"### {kind}\nMeasured on **{profile['device']}** (Streamlit host).\n\n"
    if kind == "Hardware diagnostics":
        return heading + (f"- Model: {profile['model']}\n- OS: {profile['os']}\n"
                          f"- CPU: {profile['cpu']}\n- Logical CPUs: {profile['logical_cpus']}\n"
                          f"- Installed RAM: {profile['ram_gb']} GiB\n"
                          f"- Battery: {readings['battery_percent'] if readings['battery_percent'] is not None else 'Not exposed'}\n"
                          "\nThese are inventory readings, not a hardware stress test.")
    if kind == "Network issues":
        adapters = "\n".join(f"- {a['name']}: {'up' if a['up'] else 'down'}; reported link speed {a['speed_mbps']} Mbps" for a in readings["adapters"])
        return heading + adapters + (f"\n\nReceive: {readings['network']['received_bps']/1024:.1f} KiB/s; "
                                     f"send: {readings['network']['sent_bps']/1024:.1f} KiB/s. "
                                     "Adapter state does not establish Internet or VPN reachability.")
    return heading + (f"- CPU utilization: {readings['cpu_percent']:.1f}%\n"
                      f"- Memory: {readings['memory_percent']:.1f}% "
                      f"({readings['memory_used_gb']} / {readings['memory_total_gb']} GiB)\n"
                      f"- System disk {readings['disk_root']}: {readings['disk_percent']:.1f}% used; "
                      f"{readings['disk_free_gb']} GiB free\n"
                      f"- Uptime: {readings['uptime_seconds']//3600} hours\n\n"
                      "Point-in-time readings; sustained high usage needs further investigation.")
