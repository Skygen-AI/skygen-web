# Analytics API

## Overview

The Analytics API provides comprehensive performance metrics, insights, and recommendations for users to optimize their automation workflows and system usage.

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <access_token>
```

**Note:** System-wide analytics require admin privileges.

## Endpoints

### GET /v1/analytics/performance

Get comprehensive performance analytics for the current user.

**Query Parameters:**

- `days` (optional) - Number of days to analyze (default: 30, range: 1-365)

**Response (200):**

```json
{
  "total_tasks": 150,
  "success_rate": 94.5,
  "avg_duration_minutes": 2.3,
  "device_utilization": 75.0,
  "peak_hours": [9, 14, 16],
  "trend": {
    "direction": "up",
    "percentage": 12.5
  },
  "status_breakdown": {
    "completed": 142,
    "failed": 8,
    "cancelled": 0
  },
  "performance_score": 89
}
```

**Metrics Explained:**

- `total_tasks` - Total tasks executed in the period
- `success_rate` - Percentage of successfully completed tasks
- `avg_duration_minutes` - Average task execution time
- `device_utilization` - Percentage of devices actively used
- `peak_hours` - Hours with highest task activity (24-hour format)
- `trend` - Growth/decline compared to previous period
- `performance_score` - Overall performance rating (0-100)

### GET /v1/analytics/devices

Get analytics for each user device.

**Query Parameters:**

- `days` (optional) - Number of days to analyze (default: 30, range: 1-365)

**Response (200):**

```json
[
  {
    "device_id": "device-uuid",
    "device_name": "MacBook Pro",
    "total_tasks": 85,
    "success_rate": 96.5,
    "avg_duration_seconds": 145.2,
    "avg_duration_minutes": 2.42,
    "last_active": "2024-01-14T15:30:00Z",
    "health_score": 92.0,
    "health_status": "excellent"
  }
]
```

**Health Status Values:**

- `excellent` - Health score ≥ 90
- `good` - Health score ≥ 75
- `warning` - Health score ≥ 50
- `critical` - Health score < 50

### GET /v1/analytics/actions

Get performance breakdown by action type.

**Query Parameters:**

- `days` (optional) - Number of days to analyze (default: 30, range: 1-365)

**Response (200):**

```json
{
  "screenshot": {
    "total_count": 65,
    "success_count": 63,
    "success_rate": 96.9,
    "avg_duration_seconds": 2.1,
    "failure_reasons": {
      "timeout": 1,
      "permission_denied": 1
    }
  },
  "click": {
    "total_count": 120,
    "success_count": 118,
    "success_rate": 98.3,
    "avg_duration_seconds": 0.8,
    "failure_reasons": {
      "element_not_found": 2
    }
  },
  "type_text": {
    "total_count": 45,
    "success_count": 44,
    "success_rate": 97.8,
    "avg_duration_seconds": 1.5,
    "failure_reasons": {
      "input_field_not_active": 1
    }
  }
}
```

### GET /v1/analytics/trends

Get performance trends over different time periods.

**Response (200):**

```json
{
  "last_7_days": {
    "total_tasks": 25,
    "success_rate": 96.0,
    "avg_duration_minutes": 2.1,
    "device_utilization": 70.0
  },
  "last_30_days": {
    "total_tasks": 150,
    "success_rate": 94.5,
    "avg_duration_minutes": 2.3,
    "device_utilization": 75.0
  },
  "last_90_days": {
    "total_tasks": 420,
    "success_rate": 93.2,
    "avg_duration_minutes": 2.4,
    "device_utilization": 78.0
  },
  "trends": {
    "tasks_growth_30d": 42.5,
    "success_rate_trend": -1.5,
    "performance_trend": 0.2
  }
}
```

### GET /v1/analytics/insights

Get AI-powered performance insights and recommendations.

**Response (200):**

```json
{
  "insights": [
    {
      "type": "warning",
      "category": "success_rate",
      "message": "Your task success rate is 85.2%, which is below optimal (>90%)",
      "impact": "high"
    },
    {
      "type": "positive",
      "category": "trend",
      "message": "Task volume increased by 15.3% recently",
      "impact": "positive"
    },
    {
      "type": "info",
      "category": "scheduling",
      "message": "Your peak usage hours are: 09:00, 14:00, 16:00",
      "impact": "low"
    }
  ],
  "recommendations": [
    {
      "category": "success_rate",
      "action": "Review failed tasks and optimize your automation scripts",
      "priority": "high"
    },
    {
      "category": "performance",
      "action": "Optimize 'screenshot' actions to improve execution speed",
      "priority": "medium"
    },
    {
      "category": "scheduling",
      "action": "Consider scheduling non-critical tasks outside peak hours",
      "priority": "low"
    }
  ],
  "summary": {
    "total_insights": 3,
    "high_priority_recommendations": 1,
    "overall_health": "good"
  }
}
```

**Insight Types:**

- `positive` - Good performance indicators
- `warning` - Areas needing attention
- `info` - Informational insights

**Recommendation Priorities:**

- `high` - Critical issues affecting performance
- `medium` - Optimization opportunities
- `low` - Minor improvements

### GET /v1/analytics/system (Admin Only)

Get system-wide analytics (admin users only).

**Response (200):**

```json
{
  "total_users": 1250,
  "total_devices": 3200,
  "total_tasks_today": 15600,
  "system_success_rate": 94.8,
  "avg_tasks_per_user": 12.5,
  "platform_breakdown": {
    "macOS": 45.2,
    "Windows": 38.7,
    "Linux": 16.1
  },
  "peak_load_hours": [9, 14, 16, 20],
  "system_health": {
    "status": "healthy",
    "cpu_usage": 45.2,
    "memory_usage": 62.1,
    "disk_usage": 34.8
  }
}
```

## Performance Metrics

### Success Rate Calculation

```
Success Rate = (Completed Tasks / Total Tasks) × 100
```

### Health Score Calculation

Health scores consider multiple factors:

- Task success rate (40% weight)
- Average execution time (25% weight)
- Device connectivity (20% weight)
- Error frequency (15% weight)

### Device Utilization

```
Device Utilization = (Active Devices / Total Devices) × 100
```

## Time Periods and Filtering

- All endpoints support custom time periods via `days` parameter
- Data is aggregated based on task creation timestamps
- Trends compare current period with previous period of same length
- Peak hours are calculated in user's timezone (if available)

## Data Freshness

- Analytics data is updated in near real-time
- Some aggregated metrics may have up to 5-minute delays
- Historical data is retained for 365 days
- Older data may be archived or summarized

## Use Cases

### Performance Optimization

- Identify slow-performing actions
- Optimize task scheduling based on peak hours
- Improve success rates by addressing failure patterns

### Capacity Planning

- Monitor device utilization trends
- Plan device scaling based on usage patterns
- Identify resource bottlenecks

### Troubleshooting

- Investigate performance degradations
- Identify problematic devices or actions
- Track improvement after optimizations

### Reporting

- Generate performance reports for stakeholders
- Monitor SLA compliance
- Track automation ROI

## Error Responses

- `400` - Invalid parameters (e.g., days out of range)
- `401` - Authentication required
- `403` - Admin privileges required (system endpoint)
- `422` - Validation error

## Rate Limiting

Analytics endpoints may have higher rate limits than other APIs to support dashboard and reporting use cases.

## Best Practices

- Use appropriate time periods for your analysis needs
- Monitor trends regularly to catch issues early
- Act on high-priority recommendations promptly
- Consider device health scores when planning maintenance
- Use insights to guide automation strategy decisions
