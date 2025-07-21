"""
Project management endpoints
"""
from typing import Annotated, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
import structlog

from src.core.database.connection import get_db
from src.core.database.models import Project, User
from api.dependencies import (
    get_current_user,
    Pagination,
    check_project_ownership,
    rate_limit_per_minute
)
from api.validators import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectStatus,
)

router = APIRouter(prefix="/projects", tags=["projects"])
logger = structlog.get_logger()


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[Pagination, Depends()],
    status: Optional[ProjectStatus] = None,
    search: Optional[str] = None,
    sort_by: str = Query(default="created_at", pattern="^(created_at|updated_at|name)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$")
) -> ProjectListResponse:
    """
    List user's projects with filtering and pagination
    
    - **status**: Filter by project status
    - **search**: Search in project name and description
    - **sort_by**: Sort by created_at, updated_at, or name
    - **order**: Sort order (asc or desc)
    - **skip**: Number of items to skip (pagination)
    - **limit**: Number of items to return (max 100)
    """
    # Build query
    query = select(Project).where(Project.user_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.where(Project.status == status)
    
    if search:
        search_filter = or_(
            Project.name.ilike(f"%{search}%"),
            Project.description.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    
    # Count total items
    count_query = select(func.count()).select_from(Project).where(Project.user_id == current_user.id)
    if status:
        count_query = count_query.where(Project.status == status)
    if search:
        count_query = count_query.where(search_filter)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply sorting
    sort_column = getattr(Project, sort_by)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    query = query.offset(pagination.skip).limit(pagination.limit)
    
    # Execute query
    result = await db.execute(query)
    projects = result.scalars().all()
    
    logger.info(
        "Projects listed",
        user_id=str(current_user.id),
        total=total,
        returned=len(projects),
        filters={
            "status": status,
            "search": search,
            "sort_by": sort_by,
            "order": order
        }
    )
    
    return ProjectListResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit
    )


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(rate_limit_per_minute)]
) -> ProjectResponse:
    """
    Create a new project
    
    - **name**: Project name
    - **description**: Optional project description
    - **script_content**: The script content to process
    - **style**: Visual style for video generation
    - **voice_type**: Voice type for narration
    """
    # Create project
    project = Project(
        user_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
        script_content=project_data.script_content,
        style=project_data.style,
        voice_type=project_data.voice_type,
        status=ProjectStatus.DRAFT,
        metadata={
            "created_by": current_user.email,
            "version": 1
        }
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    logger.info(
        "Project created",
        user_id=str(current_user.id),
        project_id=str(project.id),
        name=project.name
    )
    
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> ProjectResponse:
    """
    Get project details by ID
    
    Returns detailed information about a specific project
    """
    # Get project with ownership check
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        logger.warning(
            "Project not found",
            user_id=str(current_user.id),
            project_id=project_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    logger.info(
        "Project retrieved",
        user_id=str(current_user.id),
        project_id=str(project.id)
    )
    
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(check_project_ownership)]
) -> ProjectResponse:
    """
    Update project details
    
    Update project properties. Only draft projects can have their
    script content modified.
    """
    # Get project
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if project can be modified
    if project.status != ProjectStatus.DRAFT and project_update.script_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify script content of non-draft projects"
        )
    
    # Update fields
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    # Update metadata
    if project.metadata is None:
        project.metadata = {}
    project.metadata["updated_by"] = current_user.email
    project.metadata["version"] = project.metadata.get("version", 1) + 1
    project.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(project)
    
    logger.info(
        "Project updated",
        user_id=str(current_user.id),
        project_id=str(project.id),
        updated_fields=list(update_data.keys())
    )
    
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(check_project_ownership)]
) -> None:
    """
    Delete a project
    
    Permanently deletes a project and all associated data.
    This action cannot be undone.
    """
    # Get project
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if project can be deleted
    if project.status == ProjectStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete project while processing"
        )
    
    # Delete project
    await db.delete(project)
    await db.commit()
    
    logger.info(
        "Project deleted",
        user_id=str(current_user.id),
        project_id=project_id,
        project_name=project.name
    )


@router.post("/{project_id}/duplicate", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_project(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(check_project_ownership)]
) -> ProjectResponse:
    """
    Duplicate an existing project
    
    Creates a copy of the project with a new ID and resets the status to draft
    """
    # Get original project
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    original = result.scalar_one_or_none()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Create duplicate
    duplicate = Project(
        user_id=current_user.id,
        name=f"{original.name} (Copy)",
        description=original.description,
        script_content=original.script_content,
        style=original.style,
        voice_type=original.voice_type,
        status=ProjectStatus.DRAFT,
        metadata={
            "created_by": current_user.email,
            "version": 1,
            "duplicated_from": str(original.id)
        }
    )
    
    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)
    
    logger.info(
        "Project duplicated",
        user_id=str(current_user.id),
        original_id=project_id,
        duplicate_id=str(duplicate.id)
    )
    
    return ProjectResponse.model_validate(duplicate)