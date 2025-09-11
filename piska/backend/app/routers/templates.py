from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models import TaskTemplate, User


router = APIRouter()


@router.post("/", status_code=201)
async def create_template(
    payload: Dict[str, Any],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Create a new task template"""

    # Validate required fields
    if "name" not in payload:
        raise HTTPException(status_code=422, detail="Field 'name' is required")
    if "actions" not in payload:
        raise HTTPException(
            status_code=422, detail="Field 'actions' is required")

    # Validate actions is a list
    if not isinstance(payload["actions"], list):
        raise HTTPException(
            status_code=422, detail="Field 'actions' must be a list")

    template = TaskTemplate(
        user_id=user.id,
        name=payload["name"],
        description=payload.get("description"),
        category=payload.get("category", "general"),
        actions=payload["actions"],
        variables=payload.get("variables", {}),
        is_public=payload.get("is_public", False),
    )

    db.add(template)
    await db.commit()

    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "actions": template.actions,
        "variables": template.variables,
        "is_public": template.is_public,
        "usage_count": template.usage_count,
        "created_at": template.created_at,
    }


@router.get("/", response_model=List[Dict[str, Any]])
async def list_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    category: str | None = Query(default=None),
    include_public: bool = Query(default=True),
    limit: int = Query(default=50, le=200),
) -> List[Dict[str, Any]]:
    """List task templates"""

    # Base query - user's templates
    q = select(TaskTemplate).where(TaskTemplate.user_id == user.id)

    # Include public templates if requested
    if include_public:
        q = select(TaskTemplate).where(
            (TaskTemplate.user_id == user.id) | (
                TaskTemplate.is_public == True)
        )

    # Filter by category
    if category:
        q = q.where(TaskTemplate.category == category)

    q = q.order_by(desc(TaskTemplate.usage_count), desc(
        TaskTemplate.created_at)).limit(limit)

    templates = (await db.execute(q)).scalars().all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "actions": t.actions,
            "variables": t.variables,
            "is_public": t.is_public,
            "usage_count": t.usage_count,
            "created_at": t.created_at,
            "is_owner": t.user_id == user.id,
        }
        for t in templates
    ]


@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_template_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> List[Dict[str, Any]]:
    """Get template categories with counts"""

    # Get categories from user's templates and public templates
    result = await db.execute(
        select(TaskTemplate.category, func.count(
            TaskTemplate.id).label('count'))
        .where((TaskTemplate.user_id == user.id) | (TaskTemplate.is_public == True))
        .group_by(TaskTemplate.category)
        .order_by(func.count(TaskTemplate.id).desc())
    )

    categories = result.all()

    return [
        {"name": cat.category, "count": cat.count}
        for cat in categories
    ]


@router.get("/statistics")
async def get_template_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Get template usage statistics"""

    # Total templates
    total_count = await db.execute(
        select(func.count(TaskTemplate.id))
        .where((TaskTemplate.user_id == user.id) | (TaskTemplate.is_public == True))
    )
    total = total_count.scalar()

    # User's templates
    user_count = await db.execute(
        select(func.count(TaskTemplate.id))
        .where(TaskTemplate.user_id == user.id)
    )
    user_templates = user_count.scalar()

    # Most used templates
    popular_templates = await db.execute(
        select(TaskTemplate.name, TaskTemplate.usage_count)
        .where((TaskTemplate.user_id == user.id) | (TaskTemplate.is_public == True))
        .order_by(desc(TaskTemplate.usage_count))
        .limit(5)
    )

    popular = [{"name": t.name, "usage_count": t.usage_count}
               for t in popular_templates.all()]

    return {
        "total_templates": total,
        "public_templates": total - user_templates,
        "private_templates": user_templates,
        "most_used": popular
    }


@router.get("/{template_id}")
async def get_template(
    template_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Get a specific template"""

    template = (await db.execute(
        select(TaskTemplate).where(
            TaskTemplate.id == template_id,
            (TaskTemplate.user_id == user.id) | (
                TaskTemplate.is_public == True)
        )
    )).scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "actions": template.actions,
        "variables": template.variables,
        "is_public": template.is_public,
        "usage_count": template.usage_count,
        "created_at": template.created_at,
        "is_owner": template.user_id == user.id,
    }


@router.put("/{template_id}")
async def update_template(
    template_id: uuid.UUID,
    payload: Dict[str, Any],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Update a template (only owner can update)"""

    template = (await db.execute(
        select(TaskTemplate).where(
            TaskTemplate.id == template_id,
            TaskTemplate.user_id == user.id
        )
    )).scalar_one_or_none()

    if not template:
        # Check if template exists but user doesn't own it
        existing = (await db.execute(
            select(TaskTemplate).where(TaskTemplate.id == template_id)
        )).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=403, detail="Not authorized to update this template")
        raise HTTPException(status_code=404, detail="Template not found")

    # Update fields
    if "name" in payload:
        template.name = payload["name"]
    if "description" in payload:
        template.description = payload["description"]
    if "category" in payload:
        template.category = payload["category"]
    if "actions" in payload:
        template.actions = payload["actions"]
    if "variables" in payload:
        template.variables = payload["variables"]
    if "is_public" in payload:
        template.is_public = payload["is_public"]

    template.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()

    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "actions": template.actions,
        "variables": template.variables,
        "is_public": template.is_public,
        "usage_count": template.usage_count,
        "updated_at": template.updated_at,
    }


@router.delete("/{template_id}")
async def delete_template(
    template_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, str]:
    """Delete a template (only owner can delete)"""

    template = (await db.execute(
        select(TaskTemplate).where(
            TaskTemplate.id == template_id,
            TaskTemplate.user_id == user.id
        )
    )).scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    await db.delete(template)
    await db.commit()

    return {"status": "deleted"}


@router.post("/{template_id}/use")
async def use_template(
    template_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Increment template usage count"""

    template = (await db.execute(
        select(TaskTemplate).where(
            TaskTemplate.id == template_id,
            (TaskTemplate.user_id == user.id) | (
                TaskTemplate.is_public == True)
        )
    )).scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Increment usage count atomically
    await db.execute(
        update(TaskTemplate)
        .where(TaskTemplate.id == template_id)
        .values(usage_count=TaskTemplate.usage_count + 1)
    )
    await db.commit()

    # Refresh template to get updated usage count
    await db.refresh(template)

    return {
        "template_id": str(template_id),
        "template_name": template.name,
        "usage_count": template.usage_count,
        "message": "Template usage count incremented"
    }


@router.post("/{template_id}/substitute")
async def substitute_template_variables(
    template_id: uuid.UUID,
    payload: Dict[str, Any],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Substitute variables in template actions"""

    template = (await db.execute(
        select(TaskTemplate).where(
            TaskTemplate.id == template_id,
            (TaskTemplate.user_id == user.id) | (
                TaskTemplate.is_public == True)
        )
    )).scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Variable substitution
    actions = template.actions.copy()
    variables = payload.get("variables", {})

    def substitute_variables(obj, variables):
        if isinstance(obj, dict):
            return {k: substitute_variables(v, variables) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [substitute_variables(item, variables) for item in obj]
        elif isinstance(obj, str):
            # Simple template substitution {{variable_name}}
            for var_name, var_value in variables.items():
                obj = obj.replace(f"{{{{{var_name}}}}}", str(var_value))
            return obj
        return obj

    substituted_actions = substitute_variables(actions, variables)

    return {
        "template_id": str(template_id),
        "template_name": template.name,
        "actions": substituted_actions,
        "variables_used": variables
    }


@router.get("/{template_id}/export")
async def export_template(
    template_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Export template as JSON"""

    template = (await db.execute(
        select(TaskTemplate).where(
            TaskTemplate.id == template_id,
            (TaskTemplate.user_id == user.id) | (
                TaskTemplate.is_public == True)
        )
    )).scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "actions": template.actions,
        "variables": template.variables,
        "export_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/import", status_code=201)
async def import_template(
    payload: Dict[str, Any],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Import a template from exported data"""

    # Validate required fields for import
    if "name" not in payload:
        raise HTTPException(status_code=422, detail="Field 'name' is required")
    if "actions" not in payload:
        raise HTTPException(
            status_code=422, detail="Field 'actions' is required")

    # Validate actions is a list
    if not isinstance(payload["actions"], list):
        raise HTTPException(
            status_code=422, detail="Field 'actions' must be a list")

    template = TaskTemplate(
        user_id=user.id,
        name=payload["name"],
        description=payload.get("description"),
        category=payload.get("category", "general"),
        actions=payload["actions"],
        variables=payload.get("variables", {}),
        is_public=payload.get("is_public", False),
    )

    db.add(template)
    await db.commit()

    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "actions": template.actions,
        "variables": template.variables,
        "is_public": template.is_public,
        "usage_count": template.usage_count,
        "created_at": template.created_at,
    }
