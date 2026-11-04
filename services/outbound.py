"""Durable outgoing intent and conservative ambiguous-send quarantine."""

import asyncio
import json
import time
import uuid

from services.http import UpstreamError
from services.jobs import current_job


class DeliveryUncertain(UpstreamError):
    """Provider may have accepted this message; automatic repetition is unsafe."""


class SendPolicyError(UpstreamError):
    """No trusted customer-service window for a free-form send."""


class Outbound:
    def __init__(self, inbox):
        self.inbox = inbox

    async def send(self, recipient, payload, operation):
        job = current_job.get()
        if job is None or job.inbox is not self.inbox or recipient != job.sender:
            raise SendPolicyError("A trusted incoming job is required for delivery")
        if not 0 <= time.time() - job.customer_time < 86400:
            raise SendPolicyError("Customer-service window expired; no message sent")
        sequence = job.sequence
        job.sequence += 1
        serialized = json.dumps(payload, sort_keys=True)

        def begin():
            with self.inbox._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                self.inbox.assert_lease(db, job.job_id, job.lease_token)
                row = db.execute(
                    "SELECT * FROM outbound WHERE job_id=? AND sequence=?",
                    (job.job_id, sequence),
                ).fetchone()
                if row:
                    if row["payload"] != serialized or row["recipient"] != recipient:
                        raise DeliveryUncertain(
                            "Outgoing replay differs from recorded intent"
                        )
                    if row["provider_id"]:
                        return row["id"], json.loads(row["response"])
                    if row["state"] != "prepared":
                        raise DeliveryUncertain("Prior delivery needs operator review")
                    identity = row["id"]
                else:
                    identity = uuid.uuid4().hex
                    db.execute(
                        "INSERT INTO outbound(id,job_id,sequence,recipient,payload,state,created,updated) VALUES(?,?,?,?,?,'prepared',?,?)",
                        (
                            identity,
                            job.job_id,
                            sequence,
                            recipient,
                            serialized,
                            time.time(),
                            time.time(),
                        ),
                    )
                db.execute(
                    "UPDATE outbound SET state='sending',updated=? WHERE id=?",
                    (time.time(), identity),
                )
                return identity, None

        identity, previous = await asyncio.to_thread(begin)
        if previous is not None:
            return previous
        try:
            result = await operation()
            provider_id = result.get("messages", [{}])[0].get("id")
            if not isinstance(provider_id, str) or not 1 <= len(provider_id) <= 256:
                raise DeliveryUncertain(
                    "Provider acceptance did not contain a message ID"
                )
        except (Exception, asyncio.CancelledError) as exc:
            code = getattr(exc, "http_status", None)
            rejected = isinstance(code, int) and 400 <= code < 500 and code != 408
            error_code = "http_" + str(code) if code else type(exc).__name__

            def failed():
                with self.inbox._connection() as db:
                    db.execute(
                        "UPDATE outbound SET state=?,error_code=?,updated=? WHERE id=?",
                        (
                            "rejected" if rejected else "uncertain",
                            error_code,
                            time.time(),
                            identity,
                        ),
                    )

            await asyncio.shield(asyncio.to_thread(failed))
            if isinstance(exc, asyncio.CancelledError):
                raise
            if rejected:
                raise UpstreamError(
                    "Provider rejected delivery; retained for review"
                ) from None
            raise DeliveryUncertain(
                "Delivery outcome unknown; automatic repetition disabled"
            ) from None

        def accepted():
            with self.inbox._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "UPDATE outbound SET state='accepted',provider_id=?,response=?,updated=? WHERE id=?",
                    (provider_id, json.dumps(result), time.time(), identity),
                )
                self.inbox.reconcile(db, provider_id)

        await asyncio.to_thread(accepted)
        return result
