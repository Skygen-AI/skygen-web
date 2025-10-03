from app.routers import analytics as analytics_router
from app.routers import scheduled_tasks as scheduled_tasks_router
from app.routers import templates as templates_router
from app.routers import webhooks as webhooks_router
from app.routers import approvals as approvals_router
from app.routers import notifications as notifications_router
from app.routers import me as me_router
from app.routers import admin as admin_router
from app.routers import chat as chat_router
from app.routers import agent as agent_router
from app.routers import screenshots as screenshots_router
from app.routers import files as files_router
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import time

from app.config import settings
from app.db import init_models
from app.routers import auth, devices
from app.routers import ws as ws_router
from app.routers import tasks as tasks_router
from app.routers import artifacts as artifacts_router
from app.routing import start_delivery_subscriber
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from app.audit import init_audit
from app.clients import close_kafka_producer, get_s3_client
import asyncio

# Import blocked IPs from WebSocket module
from app.routers.ws import _blocked_ips, _rate_limit_lock


class IPBlockingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check requests from blocked IPs (skip localhost)
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip blocking for localhost/development
        is_localhost = client_ip in ["127.0.0.1", "localhost", "::1"]
        
        if not is_localhost:
            current_time = time.time()
            
            # Check if IP is blocked
            async with _rate_limit_lock:
                if client_ip in _blocked_ips:
                    block_info = _blocked_ips[client_ip]
                    if current_time < block_info["blocked_until"]:
                        # Only block non-WebSocket requests to avoid interfering with WS upgrades
                        if request.url.path.startswith("/v1/ws/"):
                            logger.info(f"Allowing WebSocket request from blocked IP {client_ip}")
                        else:
                            logger.warning(f"Blocking HTTP request from IP {client_ip} - {block_info['reason']}")
                            return Response(
                                status_code=429, 
                                content=f"IP blocked: {block_info['reason']}",
                                headers={"Retry-After": str(int(block_info["blocked_until"] - current_time))}
                            )
                    else:
                        # Block expired, remove it
                        del _blocked_ips[client_ip]
        
        response = await call_next(request)
        return response


app = FastAPI(title="Coact Backend", version="0.1.0")

# Add IP blocking middleware first (runs before CORS)
app.add_middleware(IPBlockingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def init_minio_bucket() -> None:
    """Initialize MinIO bucket for artifacts if configured"""
    if not settings.artifacts_bucket:
        logger.info(
            "No artifacts bucket configured, skipping MinIO initialization")
        return

    s3_client = get_s3_client()
    if not s3_client:
        logger.warning(
            "S3 client not available, skipping MinIO bucket creation")
        return

    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=settings.artifacts_bucket)
        logger.info(
            f"MinIO bucket '{settings.artifacts_bucket}' already exists")
    except Exception:
        # Bucket doesn't exist, create it
        try:
            s3_client.create_bucket(Bucket=settings.artifacts_bucket)
            logger.info(f"Created MinIO bucket '{settings.artifacts_bucket}'")
        except Exception as e:
            logger.error(
                f"Failed to create MinIO bucket '{settings.artifacts_bucket}': {e}")
            # Don't raise - let the app start even if bucket creation fails


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting up application")
    await init_models()
    await init_audit()
    await init_minio_bucket()
    # start background tasks
    try:
        import asyncio

        # Create task with proper exception handling
        task = asyncio.create_task(start_delivery_subscriber())
        # Store the task reference to prevent it from being garbage collected
        app.state.delivery_task = task
        logger.info("Started delivery subscriber background task")

        # Start device health monitoring
        from app.device_health import health_monitor
        health_task = asyncio.create_task(health_monitor.start_monitoring())
        app.state.health_task = health_task
        logger.info("Started device health monitoring")

        # Start task scheduler
        from app.scheduler import scheduler
        scheduler_task = asyncio.create_task(scheduler.start())
        app.state.scheduler_task = scheduler_task
        logger.info("Started task scheduler")

    except Exception as e:
        logger.warning(f"Failed to start background tasks: {e}")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Shutting down application")
    # Cancel the delivery subscriber task
    if hasattr(app.state, "delivery_task"):
        app.state.delivery_task.cancel()
        try:
            await app.state.delivery_task
        except asyncio.CancelledError:
            pass
    # Close kafka producer if created
    try:
        await close_kafka_producer()
    except Exception:
        pass

    # Stop device health monitoring
    try:
        from app.device_health import health_monitor
        health_monitor.stop_monitoring()
    except Exception:
        pass

    # Stop task scheduler
    try:
        from app.scheduler import scheduler
        scheduler.stop()
        if hasattr(app.state, "scheduler_task"):
            app.state.scheduler_task.cancel()
            try:
                await app.state.scheduler_task
            except asyncio.CancelledError:
                pass
    except Exception:
        pass


app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(devices.router, prefix="/v1/devices", tags=["devices"])
app.include_router(ws_router.router, prefix="/v1", tags=["ws"])
app.include_router(tasks_router.router, prefix="/v1/tasks", tags=["tasks"])
app.include_router(artifacts_router.router,
                   prefix="/v1/artifacts", tags=["artifacts"])
if settings.enable_debug_routes:
    from app.routers import debug as debug_router

    app.include_router(debug_router.router, prefix="/v1/debug", tags=["debug"])

# Admin and user dashboard routes

app.include_router(admin_router.router, prefix="/v1/admin", tags=["admin"])
app.include_router(me_router.router, prefix="/v1/me", tags=["me"])

# Advanced features

app.include_router(notifications_router.router,
                   prefix="/v1", tags=["notifications"])
app.include_router(approvals_router.router,
                   prefix="/v1/approvals", tags=["approvals"])
app.include_router(webhooks_router.router,
                   prefix="/v1/webhooks", tags=["webhooks"])

# Advanced features - Templates, Scheduling, Analytics

app.include_router(templates_router.router,
                   prefix="/v1/templates", tags=["templates"])
app.include_router(scheduled_tasks_router.router,
                   prefix="/v1/scheduled-tasks", tags=["scheduled"])
app.include_router(analytics_router.router,
                   prefix="/v1/analytics", tags=["analytics"])

# Chat and Agent APIs
app.include_router(chat_router.router,
                   prefix="/v1/chat", tags=["chat"])
app.include_router(agent_router.router,
                   prefix="/v1/agent", tags=["agent"])
app.include_router(screenshots_router.router,
                   prefix="/v1/screenshots", tags=["screenshots"])
app.include_router(files_router.router,
                   prefix="/v1/files", tags=["files"])


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "env": settings.environment}


@app.get("/metrics")
async def metrics(request: Request):
    from fastapi import Response, HTTPException

    # Optional protection via static token header
    if settings.metrics_token:
        token = request.headers.get("X-Metrics-Token")
        if token != settings.metrics_token:
            raise HTTPException(status_code=401, detail="Unauthorized")

    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
