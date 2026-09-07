"""Association models for Access Group administrator permissions."""

from sqlalchemy import BigInteger, Column, ForeignKey, Index, Integer

from app.db.base import Base


class AccessGroupAdminAccess(Base):
    """Restrict an Access Group to explicit Admin IDs when rows exist."""

    __tablename__ = "access_group_admin_access"
    __table_args__ = (
        Index("ix_access_group_admin_access_admin_group", "admin_id", "access_group_id"),
    )

    access_group_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("access_groups.id", ondelete="CASCADE"),
        primary_key=True,
    )
    admin_id = Column(
        Integer,
        ForeignKey("admins.id", ondelete="CASCADE"),
        primary_key=True,
    )
