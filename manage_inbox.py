"""Local operator tools: metadata, consistent backups and reviewed quarantine resolution.

No command sends messages or replays a handler. Resolve only after checking external
provider/merchant state; ambiguous effects cannot be made exactly-once locally.
"""

import argparse
import json
import sqlite3
import time
from pathlib import Path

from database.inbox import Inbox


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("summary")
    sub.add_parser("live")
    backup = sub.add_parser("backup")
    backup.add_argument("--output", required=True)
    resolve = sub.add_parser("resolve")
    resolve.add_argument("--id", required=True)
    resolve.add_argument(
        "--outcome", choices=["already_processed", "abandoned"], required=True
    )
    resolve.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    path = Path(args.database).resolve()
    if not path.is_file():
        parser.error("Database does not exist")
    if args.command == "backup":
        target = Path(args.output).resolve()
        if target.exists():
            parser.error("Backup destination must not exist")
        source = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        destination = sqlite3.connect(target)
        try:
            source.backup(destination)
            if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Backup integrity check failed")
        finally:
            source.close()
            destination.close()
        print("Consistent backup created")
        return
    inbox = Inbox(str(path))
    with inbox._connection() as db:
        if args.command == "summary":
            counts = dict(
                db.execute("SELECT status,count(*) FROM inbox GROUP BY status")
            )
            rows = [
                dict(r)
                for r in db.execute(
                    "SELECT id,status,attempts,last_error,updated FROM inbox WHERE status IN ('review','failed') ORDER BY created LIMIT 100"
                )
            ]
            print(json.dumps({"counts": counts, "needs_review": rows}, indent=2))
            return
        if args.command == "live":
            inbound = [
                dict(r)
                for r in db.execute(
                    "SELECT id,sender,status,created,updated,last_error FROM inbox ORDER BY created DESC LIMIT 25"
                )
            ]
            outbound = [
                dict(r)
                for r in db.execute(
                    "SELECT id,job_id,recipient,state,provider_id,error_code,updated FROM outbound ORDER BY created DESC LIMIT 25"
                )
            ]
            print(
                json.dumps(
                    {"recent_inbound": inbound, "recent_outbound": outbound}, indent=2
                )
            )
            return
        if not 8 <= len(args.reason) <= 500:
            parser.error(
                "Provide a review reason of 8 to 500 characters; do not include secrets"
            )
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT status FROM inbox WHERE id=?", (args.id,)).fetchone()
        if row is None or row["status"] not in {"review", "failed"}:
            parser.error("Only quarantined or failed jobs can be resolved")
        db.execute(
            "UPDATE outbound SET state='uncertain',error_code='operator_review',updated=? WHERE job_id=? AND state='sending'",
            (time.time(), args.id),
        )
        db.execute(
            "INSERT INTO job_reviews(job_id,outcome,reason,created) VALUES(?,?,?,?)",
            (args.id, args.outcome, args.reason, time.time()),
        )
        db.execute(
            "UPDATE inbox SET status='done',updated=?,lease_token=NULL,lease_until=NULL,last_error='operator_resolved' WHERE id=?",
            (time.time(), args.id),
        )
    print("Review recorded; no message sent and no handler replayed")


if __name__ == "__main__":
    main()
