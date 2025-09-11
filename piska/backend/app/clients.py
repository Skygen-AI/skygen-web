from __future__ import annotations

from typing import Optional
import json
import asyncio
from urllib.parse import urlparse
from loguru import logger

try:
    from clickhouse_connect import get_client as get_ch_client  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    get_ch_client = None  # type: ignore[assignment]
from aiokafka import AIOKafkaProducer  # type: ignore
import boto3
from redis.asyncio import Redis

from app.config import settings


redis_client: Optional[Redis] = None


def get_redis() -> Redis | None:
    global redis_client
    if settings.redis_url is None:
        return None
    if redis_client is None:
        redis_client = Redis.from_url(
            settings.redis_url, decode_responses=True)
    return redis_client


def get_clickhouse():  # type: ignore[no-untyped-def]
    if settings.clickhouse_url is None or get_ch_client is None:
        return None
    parsed = urlparse(settings.clickhouse_url)
    host = parsed.hostname or settings.clickhouse_url
    port = parsed.port or 8123
    return get_ch_client(host=host, port=port)


# Kafka
kafka_producer: Optional[AIOKafkaProducer] = None


async def get_kafka_producer() -> AIOKafkaProducer | None:
    global kafka_producer
    if settings.__dict__.get("kafka_brokers") is None and not hasattr(settings, "kafka_brokers"):
        # compat if not present
        pass
    brokers = getattr(settings, "kafka_brokers", None) or None
    if brokers is None:
        return None
    if kafka_producer is None:
        try:
            kafka_producer = AIOKafkaProducer(
                bootstrap_servers=brokers.split(","),
                retry_backoff_ms=1000,
                max_block_ms=5000,
                request_timeout_ms=10000,
            )
            await asyncio.wait_for(kafka_producer.start(), timeout=5.0)
            logger.info(f"Kafka producer connected to brokers: {brokers}")
        except Exception as e:
            logger.warning(
                f"Failed to connect to Kafka brokers {brokers}: {e}")
            # If we can't connect to Kafka, return None instead of failing
            kafka_producer = None
            return None
    return kafka_producer


async def close_kafka_producer() -> None:
    global kafka_producer
    try:
        if kafka_producer is not None:
            try:
                logger.info("Closing Kafka producer...")
                await asyncio.wait_for(kafka_producer.stop(), timeout=3.0)
                logger.info("Kafka producer closed successfully")
            except Exception as e:
                logger.warning(f"Error closing Kafka producer: {e}")
            finally:
                kafka_producer = None
    except Exception as e:
        logger.warning(f"Error in close_kafka_producer: {e}")
        kafka_producer = None


# MinIO / S3
_s3_client = None


def get_s3_client():  # type: ignore[no-untyped-def]
    global _s3_client
    if _s3_client is not None:
        return _s3_client
    if settings.__dict__.get("minio_endpoint") is None:
        return None

    from botocore.config import Config
    config = Config(
        region_name="us-east-1",
        signature_version='s3v4',
        connect_timeout=5,
        read_timeout=10,
        retries={'max_attempts': 3}
    )

    _s3_client = boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=config,
    )
    return _s3_client


async def publish_event(channel: str, event: dict) -> None:
    """
    Publish an event to Redis pub/sub channel if Redis is configured.
    """
    redis = get_redis()
    if redis is None:
        return
    try:
        await redis.publish(channel, json.dumps(event))
    except Exception as e:
        logger.warning(
            f"Failed to publish event to Redis channel {channel}: {e}")
