"""Dedicated, pagination-safe list contract for the Users management surface."""

from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db import Session, crud, get_db
from app.models.admin import Admin
from app.models.user import UserStatus
from app.models.user_management import UsersManagementResponse
from app.utils import admin_plans, responses, user_management


router = APIRouter(
    tags=["User"],
    prefix="/api",
    responses={401: responses._401, 403: responses._403},
)


@router.get("/users/management", response_model=UsersManagementResponse)
def get_management_users(
    offset: int = 0,
    limit: int = 10,
    username: List[str] = Query(None),
    search: Union[str, None] = None,
    owner: Union[List[str], None] = Query(None, alias="admin"),
    status: UserStatus = None,
    sort: str = None,
    plan_id: int | None = Query(default=None, ge=1),
    without_plan: bool = False,
    trial: bool = False,
    attention: bool = False,
    expires_within_days: int | None = Query(default=None, ge=1, le=3650),
    usage_percent_min: int | None = Query(default=None, ge=1, le=100),
    has_device_limit: bool | None = None,
    unlimited_traffic: bool = False,
    inactive_hours: int | None = Query(default=None, ge=1, le=87600),
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.get_current),
):
    """Return one authorized User page plus bounded current-Plan metadata."""

    if limit not in {10, 25, 50}:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "pagination_size_invalid",
                "message": "Page size must be one of 10, 25, or 50",
            },
        )
    if offset < 0 or offset % limit != 0:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "pagination_offset_invalid",
                "message": "Offset must be non-negative and aligned to page size",
            },
        )
    if without_plan and (plan_id is not None or trial):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "plan_filter_conflict",
                "message": "without_plan cannot be combined with plan_id or trial",
            },
        )

    sort_options = None
    if sort is not None:
        sort_options = []
        for option in sort.strip(",").split(","):
            try:
                sort_options.append(crud.UsersSortingOptions[option])
            except KeyError as exc:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "sort_option_invalid",
                        "message": f'"{option}" is not a valid sort option',
                    },
                ) from exc

    query = user_management.scoped_query(
        db,
        admin,
        usernames=username,
        search=search,
        owners=owner,
        status=status,
        plan_id=plan_id,
        without_plan=without_plan,
        trial=trial,
        attention=attention,
        expires_within_days=expires_within_days,
        usage_percent_min=usage_percent_min,
        has_device_limit=has_device_limit,
        unlimited_traffic=unlimited_traffic,
        inactive_hours=inactive_hours,
    )
    users, count = user_management.page_users(
        query,
        offset=offset,
        limit=limit,
        sort_options=sort_options,
    )

    dbadmin = crud.get_admin(db, admin.username)
    page = offset // limit + 1
    return UsersManagementResponse(
        users=admin_plans.scoped_user_responses(
            db,
            users,
            actor=dbadmin or admin,
        ),
        total=count,
        page=page,
        page_size=limit,
        pages=(count + limit - 1) // limit,
        plan_meta=user_management.plan_meta_for_users(db, users),
    )
