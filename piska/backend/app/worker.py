from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from loguru import logger

from app.clients import get_kafka_producer, get_redis
from app.routing import publish_task_envelope
from app.security import sign_message_hmac
from app.metrics import tasks_assigned_total, dlq_messages_total


TASK_CREATED_TOPIC = "task.created"
TASK_ASSIGNED_TOPIC = "task.assigned"
DLQ_TOPIC = "task.dlq"


async def worker_assigner() -> None:
    # Minimal assigner using Redis presence and Kafka producer for events
    from aiokafka import AIOKafkaConsumer  # type: ignore

    redis = get_redis()
    producer = await get_kafka_producer()
    if producer is None:
        logger.warning("Kafka producer not available; worker disabled")
        return

    try:
        # type: ignore[attr-defined]
        brokers = producer.client.client._client._bootstrap_servers
        consumer = AIOKafkaConsumer(
            TASK_CREATED_TOPIC,
            bootstrap_servers=brokers,
            group_id="assigner",
            retry_backoff_ms=1000,
            request_timeout_ms=10000,
        )
        logger.info(
            f"Starting Kafka consumer for topic {TASK_CREATED_TOPIC} with brokers: {brokers}"
        )
        await consumer.start()
        logger.info("Kafka consumer started successfully")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumer: {e}")
        return
    try:
        async for msg in consumer:
            try:
                evt = json.loads(msg.value)
                device_id = evt.get("device_id")
                task_id = evt.get("task_id")
                if not device_id or not task_id:
                    continue
                online = False
                if redis is not None:
                    try:
                        # prefer simple set maintained by ws router
                        online = await redis.sismember("presence:online", device_id)
                        if not online:
                            # fallback to presence hash TTL if set not available
                            key = f"presence:device:{device_id}"
                            status = await redis.hget(key, "status")
                            online = status == "online"
                    except Exception:
                        online = False
                if online:
                    envelope = {
                        "type": "task.exec",
                        "task_id": task_id,
                        "issued_at": datetime.now(timezone.utc).isoformat(),
                        "actions": evt.get("actions", []),
                    }
                    envelope["signature"] = sign_message_hmac(envelope)
                    await publish_task_envelope(device_id, envelope)
                    try:
                        tasks_assigned_total.inc()
                    except Exception:
                        pass
                    # publish task.assigned
                    await producer.send_and_wait(
                        TASK_ASSIGNED_TOPIC,
                        json.dumps(
                            {
                                "type": "task.assigned",
                                "task_id": task_id,
                                "device_id": device_id,
                                "at": datetime.now(timezone.utc).isoformat(),
                            }
                        ).encode(),
                    )
                else:
                    # naive DLQ fallback
                    await producer.send_and_wait(DLQ_TOPIC, msg.value)
                    try:
                        dlq_messages_total.inc()
                    except Exception:
                        pass
            except Exception as e:  # noqa: BLE001
                logger.error(f"worker error: {e}")
    finally:
        try:
            logger.info("Stopping Kafka consumer...")
            await consumer.stop()
            logger.info("Kafka consumer stopped successfully")
        except Exception as e:
            logger.warning(f"Error stopping Kafka consumer: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(worker_assigner())
    except KeyboardInterrupt:
        pass
