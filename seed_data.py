"""Import actual verified support tickets from a JSON file into Hindsight.

Usage: python seed_data.py tickets.json
Required fields: device_target, issue, resolution, verified (must be true).
No sample tickets are uploaded automatically.
"""
import argparse
import json
from pathlib import Path

from services import error_message, save_resolution, sync_resolution


def import_tickets(path):
    tickets = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(tickets, list) or not tickets:
        raise ValueError("Expected a non-empty JSON array of verified tickets.")
    # Validate the entire input before writing anything.
    for index, ticket in enumerate(tickets, 1):
        if not isinstance(ticket, dict) or ticket.get("verified") is not True:
            raise ValueError(f"Ticket {index}: verified must be true.")
        for field in ("device_target", "issue", "resolution"):
            if not isinstance(ticket.get(field), str) or not ticket[field].strip():
                raise ValueError(f"Ticket {index}: {field} is required.")
    successes = 0
    for index, ticket in enumerate(tickets, 1):
        doc_id = save_resolution(ticket["device_target"], ticket["issue"], ticket["resolution"])
        try:
            sync_resolution(doc_id)
            successes += 1
            print(f"Ticket {index}: saved and synced.")
        except Exception as exc:
            print(f"Ticket {index}: saved locally; sync pending. {error_message(exc)}")
    print(f"Synced {successes}/{len(tickets)} verified tickets.")
    return 0 if successes == len(tickets) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="JSON file containing verified support tickets")
    args = parser.parse_args()
    try:
        raise SystemExit(import_tickets(args.path))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
