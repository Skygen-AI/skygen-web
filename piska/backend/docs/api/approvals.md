# Approvals API

## Overview

The Approvals API manages tasks that require user confirmation before execution. This is typically used for high-risk or sensitive operations that need explicit user approval.

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <access_token>
```

## Endpoints

### GET /v1/approvals/pending

Get tasks awaiting user approval.

**Response (200):**

```json
[
  {
    "id": "task_123",
    "device_id": "device-uuid",
    "title": "File System Access Task",
    "description": "Task requires file system access permissions",
    "created_at": "2024-01-14T14:00:00Z",
    "actions": [
      {
        "action_id": "1",
        "type": "file_read",
        "params": {
          "path": "/etc/passwd"
        }
      }
    ],
    "risk_analysis": {
      "risk_level": "high",
      "reasons": ["file_system_access", "sensitive_file"],
      "confidence": 0.95
    }
  }
]
```

**Ordering:** Results are ordered by `created_at` descending (newest first).

### POST /v1/approvals/{task_id}/approve

Approve a task for execution.

**Response (200):**

```json
{
  "status": "approved",
  "task_id": "task_123"
}
```

**Workflow:**

1. Task status changes from `awaiting_confirmation` to `queued`
2. Task envelope is generated and signed
3. Task is published to device queue for execution
4. User receives notification about approval

### POST /v1/approvals/{task_id}/reject

Reject a task (cancel execution).

**Response (200):**

```json
{
  "status": "rejected",
  "task_id": "task_123"
}
```

**Workflow:**

1. Task status changes from `awaiting_confirmation` to `cancelled`
2. Task will not be executed
3. User receives notification about rejection

## Task Risk Analysis

Tasks requiring approval include risk analysis information:

### Risk Levels

- `low` - Minimal risk operations (e.g., screenshots, simple clicks)
- `medium` - Moderate risk operations (e.g., form submissions, file uploads)
- `high` - High risk operations (e.g., file system access, system commands)
- `critical` - Critical operations (e.g., system modifications, security changes)

### Risk Reasons

Common risk factors that trigger approval requirements:

**File System Access:**

- `file_system_access` - Reading or writing files
- `sensitive_file` - Accessing system or configuration files
- `executable_file` - Interacting with executable files

**Network Operations:**

- `network_request` - Making HTTP requests
- `external_service` - Connecting to external services
- `data_transmission` - Sending sensitive data

**System Operations:**

- `system_command` - Executing system commands
- `registry_access` - Windows registry modifications
- `process_control` - Starting/stopping processes

**User Interface:**

- `sensitive_input` - Entering passwords or sensitive data
- `system_dialog` - Interacting with system security dialogs
- `privilege_escalation` - Operations requiring elevated privileges

### Confidence Score

- Range: 0.0 - 1.0
- Higher values indicate more confident risk assessment
- Based on action analysis and pattern matching

## Approval Workflow

### 1. Task Creation

```
User creates task → Risk analysis → High risk detected → Status: awaiting_confirmation
```

### 2. User Notification

- Real-time notification via WebSocket
- Email notification (if configured)
- Push notification (mobile apps)

### 3. User Decision

- User reviews task details and risk analysis
- User approves or rejects via API or UI

### 4. Task Execution

- **Approved:** Task queued for execution
- **Rejected:** Task cancelled permanently

## Auto-Expiration

Tasks awaiting approval have automatic expiration:

- **Default timeout:** 1 hour
- **Auto-action:** Cancelled (status: `cancelled`)
- **Notification:** User notified of auto-cancellation
- **Reason:** `auto_cancelled` in notification

This prevents indefinite pending states and maintains system security.

## Security Considerations

### Risk Assessment

- Risk analysis uses multiple heuristics and patterns
- Conservative approach: when in doubt, require approval
- Regular updates to risk detection algorithms

### Approval Requirements

- Only task owner can approve/reject
- Approval cannot be delegated or automated
- Each task requires individual approval (no bulk operations)

### Audit Trail

- All approval/rejection actions are logged
- Includes user ID, timestamp, and decision
- Risk analysis results are preserved for audit

## Integration with Task System

### Task Status Flow

```
created → queued → assigned → in_progress → completed
              ↑
awaiting_confirmation → (approve) ──┘
              ↓
         (reject/expire) → cancelled
```

### Notification Integration

- Approval requests trigger real-time notifications
- Status changes (approve/reject) notify user
- Auto-cancellation sends notification with reason

## Error Responses

- `400` - Task not awaiting approval
- `404` - Task not found or access denied
- `401` - Authentication required
- `409` - Task already processed (approved/rejected)

## Best Practices

### For Users

- Review risk analysis carefully before approving
- Understand what actions will be executed
- Reject tasks you don't recognize or trust
- Monitor approval notifications promptly

### For Developers

- Design tasks to minimize approval requirements
- Use least-privilege principles in actions
- Provide clear task titles and descriptions
- Test risk analysis accuracy

### For Administrators

- Monitor approval patterns for security insights
- Adjust risk thresholds based on organizational needs
- Review auto-cancelled tasks for potential issues
- Implement approval notification redundancy

## Rate Limiting

Approval endpoints may have specific rate limits to prevent abuse while allowing legitimate user workflows.

## Monitoring and Alerting

Consider monitoring:

- High rejection rates (may indicate poor task design)
- Frequent auto-cancellations (may indicate user absence)
- Unusual approval patterns (potential security issues)
- Risk analysis accuracy (false positives/negatives)
