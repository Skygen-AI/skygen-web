# End-to-End Testing Guide

This guide explains how to test the complete Coact system using the provided simulators and test scripts.

## Overview

The E2E testing pipeline includes:

1. **Authentication** - signup/login/refresh endpoints
2. **Device Management** - device enrollment and token management  
3. **WebSocket Connection** - real-time communication with devices
4. **Task Pipeline** - task creation, delivery, execution, and result processing
5. **Artifacts** - presigned uploads for screenshots and files
6. **Admin/Debug APIs** - system monitoring and troubleshooting

## Prerequisites

1. **Backend Running** - Start the Coact backend server
```bash
cd backend
docker-compose up -d  # Start PostgreSQL, Redis, etc.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Install Dependencies**
```bash
pip install aiohttp websockets loguru
```

## Testing Methods

### Method 1: Automated E2E Test Suite

Run the complete test suite that validates all components:

```bash
python test_e2e.py --api-url http://localhost:8000 --ws-url ws://localhost:8000
```

This will:
- ✅ Create a test user and authenticate
- ✅ Enroll a test device  
- ✅ Test WebSocket connection
- ✅ Create and execute a test task
- ✅ Test artifact presigned upload
- ✅ Verify complete pipeline works

### Method 2: Manual Testing with Simulators

#### Step 1: Start User Simulator

Create a user and get authenticated:

```bash
# Sign up new user
python user_simulator.py --signup --email test@example.com --password testpass123

# Or login existing user  
python user_simulator.py --email test@example.com --password testpass123
```

The user simulator will show you available devices and let you create tasks interactively.

#### Step 2: Start Device Simulator

In another terminal, simulate a device connecting:

```bash
# Get JWT token from user simulator first, then:
python device_simulator.py --jwt-token "your-jwt-token-here"
```

The device simulator will:
- Enroll itself automatically
- Connect via WebSocket
- Listen for tasks
- Simulate execution of received actions
- Send back results

#### Step 3: Create Tasks

Back in the user simulator, you can:
- List available devices
- Create sample tasks (screenshot, click, type, shell)
- Create custom tasks
- See tasks being delivered and executed in real-time

## Test Scenarios

### Basic Flow Test
1. User signs up → gets JWT
2. User creates device enrollment → gets device token
3. Device connects via WebSocket → registers presence
4. User creates task → task gets queued
5. Task delivered to device → device executes
6. Device sends results → task marked completed

### Advanced Scenarios

#### Multiple Actions Task
```json
{
  "title": "Complex Web Interaction",
  "actions": [
    {"type": "screenshot", "description": "Take initial screenshot"},
    {"type": "click", "coordinates": [500, 300]},
    {"type": "type", "text": "Hello World"},
    {"type": "screenshot", "description": "Take final screenshot"}
  ]
}
```

#### Shell Command Task  
```json
{
  "title": "System Information",
  "actions": [
    {"type": "shell", "command": "uname -a"},
    {"type": "shell", "command": "df -h"}
  ]
}
```

## Debug and Monitoring

### Admin API Endpoints

The system provides several debug endpoints (requires authentication):

```bash
# System health and stats
curl -H "Authorization: Bearer $JWT_TOKEN" http://localhost:8000/v1/debug/system/health
curl -H "Authorization: Bearer $JWT_TOKEN" http://localhost:8000/v1/debug/system/stats

# Device and task information
curl -H "Authorization: Bearer $JWT_TOKEN" http://localhost:8000/v1/debug/devices
curl -H "Authorization: Bearer $JWT_TOKEN" http://localhost:8000/v1/debug/tasks
curl -H "Authorization: Bearer $JWT_TOKEN" http://localhost:8000/v1/debug/tasks/TASK_ID

# Online devices and recent logs  
curl -H "Authorization: Bearer $JWT_TOKEN" http://localhost:8000/v1/debug/presence/online
curl -H "Authorization: Bearer $JWT_TOKEN" http://localhost:8000/v1/debug/logs/recent
```

### Monitoring Task Flow

1. **Check device is online**:
   ```bash
   curl -H "Authorization: Bearer $JWT_TOKEN" http://localhost:8000/v1/devices/
   ```

2. **Monitor task status**:
   ```bash
   curl -H "Authorization: Bearer $JWT_TOKEN" http://localhost:8000/v1/debug/tasks/TASK_ID
   ```

3. **View action logs**:
   ```bash  
   curl -H "Authorization: Bearer $JWT_TOKEN" http://localhost:8000/v1/debug/logs/recent
   ```

## Troubleshooting

### Common Issues

#### Device Not Connecting
- Check WebSocket URL is correct (`ws://` not `wss://` for local)
- Verify device token is valid and not expired
- Check backend logs for connection errors

#### Tasks Not Being Delivered  
- Verify device is online: `/v1/debug/presence/online`
- Check task status: `/v1/debug/tasks/TASK_ID`
- Ensure WebSocket connection is active

#### Task Stuck in "Assigned" State
- Device received task but hasn't sent result yet
- Check device simulator logs
- May need to restart device simulator

### Logs and Debugging

#### Backend Logs
```bash
# Backend container logs
docker-compose logs -f api

# Or if running directly
python -m uvicorn app.main:app --reload --log-level debug
```

#### Device Simulator Logs
```bash
python device_simulator.py --jwt-token "..." --log-level DEBUG
```

#### User Simulator Logs  
```bash
python user_simulator.py --log-level DEBUG
```

## Expected Flow Timeline

1. **T+0s**: User signup/login → JWT received
2. **T+1s**: Device enrollment → device_token received  
3. **T+2s**: WebSocket connection → device registered in Redis
4. **T+3s**: Task creation → task queued in database
5. **T+4s**: Task delivery → WebSocket message sent to device
6. **T+5s**: Task execution → device processes actions
7. **T+6s**: Result delivery → device sends task.result message
8. **T+7s**: Task completion → database updated, action_logs written

## Performance Testing

To test system performance:

```bash
# Run multiple device simulators concurrently
for i in {1..5}; do
  python device_simulator.py --jwt-token "$JWT_TOKEN" &
done

# Create multiple tasks rapidly in user simulator
python user_simulator.py --auto --email test@example.com --password testpass123
```

## Next Steps

After confirming the E2E pipeline works:

1. **Implement Real Device Client** - Replace simulator with actual device integration
2. **Add artifact Upload** - Implement actual S3/MinIO upload in device client  
3. **Enhance Admin Dashboard** - Build web UI for monitoring and debugging
4. **Add Load Testing** - Test system under realistic load
5. **Security Hardening** - Implement production security measures

## API Endpoints Summary

### Core API
- `POST /v1/auth/signup` - Create user account
- `POST /v1/auth/login` - Authenticate user  
- `POST /v1/devices/enroll` - Register new device
- `GET /v1/devices/` - List user's devices
- `POST /v1/tasks/` - Create new task
- `WS /v1/ws/agent` - Device WebSocket connection

### Debug/Admin API  
- `GET /v1/debug/system/health` - System health check
- `GET /v1/debug/system/stats` - System statistics
- `GET /v1/debug/devices` - Detailed device list
- `GET /v1/debug/tasks` - Task list with filtering
- `GET /v1/debug/tasks/{id}` - Task details with action logs
- `GET /v1/debug/presence/online` - Currently online devices
- `GET /v1/debug/logs/recent` - Recent action logs

The system is now ready for comprehensive end-to-end testing! 🚀