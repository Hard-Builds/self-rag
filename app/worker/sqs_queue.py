import json

from app.core.aws import sqs_client
from app.core.config import settings

_queue_url_cache: str | None = None
_dlq_url_cache: str | None = None


async def _get_queue_url() -> str:
    global _queue_url_cache
    if _queue_url_cache is None:
        async with sqs_client() as sqs:
            response = await sqs.get_queue_url(QueueName=settings.SQS_QUEUE_NAME)
            _queue_url_cache = response["QueueUrl"]
    return _queue_url_cache


async def _get_dlq_url() -> str:
    global _dlq_url_cache
    if _dlq_url_cache is None:
        async with sqs_client() as sqs:
            response = await sqs.get_queue_url(
                QueueName=f"{settings.SQS_QUEUE_NAME}-dlq"
            )
            _dlq_url_cache = response["QueueUrl"]
    return _dlq_url_cache


async def send_ingest_message(document_id, user_id, filename: str, s3_key: str) -> None:
    queue_url = await _get_queue_url()
    payload = {
        "document_id": str(document_id),
        "user_id": str(user_id),
        "filename": filename,
        "s3_key": s3_key,
    }
    async with sqs_client() as sqs:
        await sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(payload))


def receive_count(message: dict) -> int:
    return int(message.get("Attributes", {}).get("ApproximateReceiveCount", 1))


async def receive_messages(max_messages: int = 10):
    queue_url = await _get_queue_url()
    async with sqs_client() as sqs:
        response = await sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=settings.SQS_POLL_WAIT_SECONDS,
            VisibilityTimeout=settings.SQS_VISIBILITY_TIMEOUT,
            AttributeNames=["ApproximateReceiveCount"],
        )
        return response.get("Messages", [])


async def delete_message(receipt_handle: str) -> None:
    queue_url = await _get_queue_url()
    async with sqs_client() as sqs:
        await sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)


async def receive_dlq_messages(max_messages: int = 10):
    dlq_url = await _get_dlq_url()
    async with sqs_client() as sqs:
        response = await sqs.receive_message(
            QueueUrl=dlq_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=0,
            AttributeNames=["ApproximateReceiveCount"],
        )
        return response.get("Messages", [])


async def delete_dlq_message(receipt_handle: str) -> None:
    dlq_url = await _get_dlq_url()
    async with sqs_client() as sqs:
        await sqs.delete_message(QueueUrl=dlq_url, ReceiptHandle=receipt_handle)


async def redrive_dlq_message(message: dict) -> None:
    """Re-queue a DLQ message onto the main ingest queue, then remove it from the DLQ."""
    queue_url = await _get_queue_url()
    async with sqs_client() as sqs:
        await sqs.send_message(QueueUrl=queue_url, MessageBody=message["Body"])
    await delete_dlq_message(message["ReceiptHandle"])
