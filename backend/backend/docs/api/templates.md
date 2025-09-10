# Task Templates API

## Overview

The Task Templates API allows users to create reusable task templates with variable substitution, share public templates, and track usage statistics.

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <access_token>
```

## Endpoints

### POST /v1/templates/

Create a new task template.

**Request Body:**

```json
{
  "name": "Web Form Automation",
  "description": "Template for filling web forms",
  "category": "automation",
  "actions": [
    {
      "action_id": "1",
      "type": "type_text",
      "params": {
        "text": "{{user_name}}",
        "selector": "#name-field"
      }
    },
    {
      "action_id": "2",
      "type": "click",
      "params": {
        "x": "{{submit_x}}",
        "y": "{{submit_y}}"
      }
    }
  ],
  "variables": {
    "user_name": "John Doe",
    "submit_x": "100",
    "submit_y": "200"
  },
  "is_public": false
}
```

**Response (201):**

```json
{
  "id": "template-uuid",
  "name": "Web Form Automation",
  "description": "Template for filling web forms",
  "category": "automation",
  "actions": [...],
  "variables": {
    "user_name": "John Doe",
    "submit_x": "100",
    "submit_y": "200"
  },
  "is_public": false,
  "usage_count": 0,
  "created_at": "2024-01-14T12:00:00Z"
}
```

### GET /v1/templates/

List available templates.

**Query Parameters:**

- `category` (optional) - Filter by category
- `include_public` (optional) - Include public templates (default: true)
- `limit` (optional) - Max results (default: 50, max: 200)

**Response (200):**

```json
[
  {
    "id": "template-uuid",
    "name": "Web Form Automation",
    "description": "Template for filling web forms",
    "category": "automation",
    "actions": [...],
    "variables": {...},
    "is_public": false,
    "usage_count": 5,
    "created_at": "2024-01-10T12:00:00Z",
    "is_owner": true
  }
]
```

**Note:** Templates are sorted by usage count (descending), then by creation date (descending).

### GET /v1/templates/{template_id}

Get a specific template.

**Response (200):**

```json
{
  "id": "template-uuid",
  "name": "Web Form Automation",
  "description": "Template for filling web forms",
  "category": "automation",
  "actions": [...],
  "variables": {...},
  "is_public": false,
  "usage_count": 5,
  "created_at": "2024-01-10T12:00:00Z",
  "is_owner": true
}
```

### PUT /v1/templates/{template_id}

Update a template (owner only).

**Request Body (partial update):**

```json
{
  "name": "Updated Template Name",
  "description": "Updated description",
  "is_public": true
}
```

**Response (200):**

```json
{
  "id": "template-uuid",
  "name": "Updated Template Name",
  "description": "Updated description",
  "category": "automation",
  "actions": [...],
  "variables": {...},
  "is_public": true,
  "usage_count": 5,
  "updated_at": "2024-01-14T15:00:00Z"
}
```

### DELETE /v1/templates/{template_id}

Delete a template (owner only).

**Response (200):**

```json
{
  "status": "deleted"
}
```

### POST /v1/templates/{template_id}/use

Use a template to generate task data with variable substitution.

**Request Body:**

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "variables": {
    "user_name": "Jane Smith",
    "submit_x": "150",
    "submit_y": "250"
  }
}
```

**Response (200):**

```json
{
  "template_id": "template-uuid",
  "template_name": "Web Form Automation",
  "substituted_actions": [
    {
      "action_id": "1",
      "type": "type_text",
      "params": {
        "text": "Jane Smith",
        "selector": "#name-field"
      }
    },
    {
      "action_id": "2",
      "type": "click",
      "params": {
        "x": "150",
        "y": "250"
      }
    }
  ],
  "idempotency_key": "generated-hash",
  "message": "Use this data to create task via POST /v1/tasks with Idempotency-Key header"
}
```

### GET /v1/templates/categories/

Get template categories with usage counts.

**Response (200):**

```json
[
  {
    "category": "automation",
    "count": 15
  },
  {
    "category": "testing",
    "count": 8
  },
  {
    "category": "utilities",
    "count": 5
  }
]
```

## Variable Substitution

Templates support variable substitution using `{{variable_name}}` syntax:

- **String substitution:** `"Hello {{name}}"` → `"Hello John"`
- **Numeric substitution:** `"{{x_coord}}"` → `"100"`
- **Nested objects:** Variables work in nested action parameters
- **Array support:** Variables work within array elements

**Example:**

```json
{
  "actions": [
    {
      "type": "type_text",
      "params": {
        "text": "Welcome {{user_name}}! You have {{message_count}} messages."
      }
    }
  ],
  "variables": {
    "user_name": "Alice",
    "message_count": "5"
  }
}
```

Results in:

```json
{
  "type": "type_text",
  "params": {
    "text": "Welcome Alice! You have 5 messages."
  }
}
```

## Categories

Templates are organized into categories:

- `automation` - Workflow automation
- `testing` - Test scenarios
- `utilities` - Utility functions
- `personal` - Personal tasks
- `general` - General purpose (default)

## Public Templates

- **Public templates** can be viewed and used by all users
- **Private templates** are only accessible to their owners
- Only template owners can edit or delete their templates
- Public templates contribute to the community template library

## Usage Tracking

- `usage_count` increments each time a template is used via `/use` endpoint
- Usage statistics help identify popular templates
- Templates are sorted by usage count in listings

## Integration with Tasks

Templates integrate with the task system:

1. Use `/templates/{id}/use` to generate task data
2. Use the returned `idempotency_key` when creating tasks
3. The substituted actions become the task's action list

## Integration with Scheduled Tasks

Templates can be referenced in scheduled tasks:

1. Create a template with variables
2. Reference template ID in scheduled task creation
3. Variables are resolved at execution time

## Error Responses

- `400` - Invalid template data or variables
- `404` - Template not found or access denied
- `401` - Authentication required
- `403` - Access denied (not owner for edit/delete)

## Best Practices

- Use descriptive names and categories
- Define clear variable names and default values
- Add helpful descriptions for public templates
- Test variable substitution before publishing
- Use appropriate categories for discoverability
- Consider making useful templates public to help the community
