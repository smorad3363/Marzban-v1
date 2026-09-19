from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError

from app.db import Session, crud, get_db
from app.db.models import Admin as DBAdmin
from app.models.admin import Admin
from app.models.product import ProductInput, ProductResponse
from app.utils import admin_hierarchy, products, responses
from app.utils.audit import AuditLogService


router = APIRouter(
    tags=["Products"],
    prefix="/api",
    responses={401: responses._401, 403: responses._403},
)


def _actor(db: Session, admin: Admin) -> DBAdmin:
    actor = crud.get_admin(db, admin.username)
    if actor is None:
        raise HTTPException(status_code=401, detail="Database administrator record is required")
    return actor


def _raise_domain(exc: admin_hierarchy.HierarchyError) -> None:
    if exc.code == "product_not_found":
        status_code = 404
    elif exc.code == "product_management_forbidden":
        status_code = 403
    else:
        status_code = 409
    raise HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "message": str(exc)},
    )


@router.get("/products", response_model=list[ProductResponse])
def list_products(
    include_archived: bool = Query(default=False),
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.get_current),
):
    actor = _actor(db, admin)
    try:
        rows = products.list_products(db, actor, include_archived=include_archived)
    except admin_hierarchy.HierarchyError as exc:
        _raise_domain(exc)
    return [products.response(db, product) for product in rows]


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.get_current),
):
    actor = _actor(db, admin)
    try:
        product = products.get(db, actor, product_id)
    except admin_hierarchy.HierarchyError as exc:
        _raise_domain(exc)
    return products.response(db, product)


@router.post("/products", response_model=ProductResponse)
def create_product(
    values: ProductInput,
    request: Request,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.get_current),
):
    actor = _actor(db, admin)
    try:
        product = products.create(db, actor, values)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product name already exists")
    except admin_hierarchy.HierarchyError as exc:
        _raise_domain(exc)
    AuditLogService.log(
        db,
        actor,
        "product.create",
        "product",
        f"Owner {actor.username} created Product {product.name}",
        target_id=product.id,
        target_name=product.name,
        new_value=values.model_dump(),
        request=request,
    )
    return products.response(db, product)


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    values: ProductInput,
    request: Request,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.get_current),
):
    actor = _actor(db, admin)
    try:
        product = products.get(db, actor, product_id)
        previous = products.response(db, product).model_dump()
        product = products.update(db, actor, product, values)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product name already exists")
    except admin_hierarchy.HierarchyError as exc:
        _raise_domain(exc)
    AuditLogService.log(
        db,
        actor,
        "product.update",
        "product",
        f"Owner {actor.username} updated Product {product.name}",
        target_id=product.id,
        target_name=product.name,
        previous_value=previous,
        new_value=products.response(db, product).model_dump(),
        request=request,
    )
    return products.response(db, product)


@router.delete("/products/{product_id}", response_model=ProductResponse)
def archive_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.get_current),
):
    actor = _actor(db, admin)
    try:
        product = products.get(db, actor, product_id)
        was_archived = product.archived_at is not None
        product = products.archive(db, actor, product)
    except admin_hierarchy.HierarchyError as exc:
        _raise_domain(exc)
    AuditLogService.log(
        db,
        actor,
        "product.archive",
        "product",
        f"Owner {actor.username} archived Product {product.name}",
        target_id=product.id,
        target_name=product.name,
        details={"idempotent_replay": was_archived},
        request=request,
    )
    return products.response(db, product)


@router.post("/products/{product_id}/restore", response_model=ProductResponse)
def restore_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.get_current),
):
    actor = _actor(db, admin)
    try:
        product = products.get(db, actor, product_id)
        was_active = product.archived_at is None
        product = products.restore(db, actor, product)
    except admin_hierarchy.HierarchyError as exc:
        _raise_domain(exc)
    AuditLogService.log(
        db,
        actor,
        "product.restore",
        "product",
        f"Owner {actor.username} restored Product {product.name}",
        target_id=product.id,
        target_name=product.name,
        details={"idempotent_replay": was_active},
        request=request,
    )
    return products.response(db, product)
