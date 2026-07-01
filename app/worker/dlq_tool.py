"""Operational CLI for inspecting and redriving dead-lettered ingest messages.

Usage:
    python -m app.worker.dlq_tool list
    python -m app.worker.dlq_tool redrive [--limit N]
"""
import asyncio
import json
import sys

from app.core import logger
from app.worker import sqs_queue


async def list_dlq_messages() -> None:
    messages = await sqs_queue.receive_dlq_messages()
    if not messages:
        print("DLQ is empty")
        return

    for message in messages:
        body = json.loads(message["Body"])
        attempts = sqs_queue.receive_count(message)
        print(
            f"document_id={body.get('document_id')} "
            f"filename={body.get('filename')} "
            f"s3_key={body.get('s3_key')} "
            f"deliveries_to_dlq={attempts}"
        )


async def redrive_dlq_messages(limit: int = 10) -> None:
    messages = await sqs_queue.receive_dlq_messages(max_messages=limit)
    if not messages:
        print("DLQ is empty, nothing to redrive")
        return

    for message in messages:
        body = json.loads(message["Body"])
        await sqs_queue.redrive_dlq_message(message)
        logger.info(f"Redriven document {body.get('document_id')} back to ingest queue")

    print(f"Redriven {len(messages)} message(s) back to the main queue")


def _usage() -> None:
    print(__doc__)
    sys.exit(1)


async def main() -> None:
    if len(sys.argv) < 2:
        _usage()

    command = sys.argv[1]
    if command == "list":
        await list_dlq_messages()
    elif command == "redrive":
        limit = 10
        if "--limit" in sys.argv:
            limit = int(sys.argv[sys.argv.index("--limit") + 1])
        await redrive_dlq_messages(limit=limit)
    else:
        _usage()


if __name__ == "__main__":
    asyncio.run(main())
