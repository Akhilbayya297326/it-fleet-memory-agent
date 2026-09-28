import os
import time
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

# Initialize the Hindsight client
client = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key=os.getenv("HINDSIGHT_API_KEY")
)
BANK_ID = "fleet-memory-bank"

EMPLOYEE_PROFILES = {
    "John": {"role": "Sales", "device": "Lenovo ThinkPad", "os": "Windows 11 23H2"},
    "Sarah": {"role": "Engineering", "device": "MacBook Pro M2", "os": "macOS 14.2"},
    "Mike": {"role": "Marketing", "device": "Dell XPS 15", "os": "Windows 11 22H2"},
    "Lisa": {"role": "HR", "device": "Microsoft Surface Pro", "os": "Windows 11 23H2"},
    "Kevin": {"role": "Design", "device": "MacBook Air M3", "os": "macOS 14.4"}
}

PAST_TICKETS = [
    {
        "ticket_id": "TKT-402",
        "device_target": "Lenovo ThinkPad",
        "issue": "Audio keeps cutting out or crashing when Microsoft Teams is open.",
        "resolution": "The Dolby Audio driver causes a collision with Teams. Fix: Open Task Manager, go to Services, and disable the 'Dolby DAX' service."
    },
    {
        "ticket_id": "TKT-381",
        "device_target": "MacBook",
        "issue": "Wi-Fi frequently drops when connected to the office network.",
        "resolution": "macOS DNS caching issue on the new corporate router. Fix: Open Terminal and run 'sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder'."
    },
    {
        "ticket_id": "TKT-415",
        "device_target": "Dell XPS 15",
        "issue": "Cisco AnyConnect VPN disconnects when switching from home Wi-Fi to a mobile hotspot.",
        "resolution": "Recent security patch KB503412 caused an IPv6 DNS conflict on Dell network cards. Fix: Disable IPv6 on the virtual network adapter via PowerShell."
    },
    {
        "ticket_id": "TKT-420",
        "device_target": "Microsoft Surface Pro",
        "issue": "External monitor flickers constantly after waking the device from sleep mode.",
        "resolution": "Hardware-firmware collision with the Surface Dock 2. Fix: Roll back the Intel Iris Xe Graphics driver to version 27.20.100.9664 in Device Manager."
    },
    {
        "ticket_id": "TKT-432",
        "device_target": "MacBook",
        "issue": "Cannot access the ADP payroll portal; browser says 'Connection Refused'.",
        "resolution": "The new enterprise firewall update blocks the payroll portal on macOS endpoints. Fix: Whitelist IP 192.168.1.50 in the local firewall settings."
    },
    {
        "ticket_id": "TKT-440",
        "device_target": "Lenovo ThinkPad",
        "issue": "Severe battery drain even when the laptop is closed and in sleep mode.",
        "resolution": "Windows 'Modern Standby' is failing to suspend background apps. Fix: Enter BIOS, navigate to Config > Power, and change Sleep State from 'Windows 10' to 'Linux'."
    }
]

def upload_mock_data():
    print("Uploading expanded fleet memory to Hindsight...")
    for ticket in PAST_TICKETS:
        memory_text = (
            f"Ticket ID: {ticket['ticket_id']} | "
            f"Device Target: {ticket['device_target']} | "
            f"Issue: {ticket['issue']} | "
            f"Resolution: {ticket['resolution']}"
        )
        
        # Robust Retry Logic
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                client.retain(bank_id=BANK_ID, content=memory_text)
                print(f"Successfully memorized: {ticket['ticket_id']}")
                time.sleep(2)  # Critical 2-second pause to respect rate limits
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {ticket['ticket_id']}: {e}")
                if attempt < max_attempts - 1:
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"Skipping {ticket['ticket_id']} after {max_attempts} failures.")
            
    print("\nAll expanded mock data seeded successfully!")
    
    # Attempt to gracefully close the async connection to prevent warnings
    try:
        if hasattr(client, 'close'):
            client.close()
    except Exception:
        pass

if __name__ == "__main__":
    upload_mock_data()