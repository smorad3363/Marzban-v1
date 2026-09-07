from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"expected exactly one match in {path}: {old[:100]!r}; got {text.count(old)}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


def write(path: str, content: str) -> None:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")


# --- SQLAlchemy model + migration -------------------------------------------------
write(
    "app/db/access_group_models.py",
    '''"""Association models for Access Group administrator permissions."""

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
''',
)

write(
    "app/db/migrations/versions/e1a7c4d9b302_access_group_admin_permissions.py",
    '''"""add Access Group administrator permissions

Revision ID: e1a7c4d9b302
Revises: f6b2c9d4e701
"""

from alembic import op
import sqlalchemy as sa


revision = "e1a7c4d9b302"
down_revision = "f6b2c9d4e701"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "access_group_admin_access",
        sa.Column(
            "access_group_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("access_groups.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "admin_id",
            sa.Integer(),
            sa.ForeignKey("admins.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_access_group_admin_access_admin_group",
        "access_group_admin_access",
        ["admin_id", "access_group_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_access_group_admin_access_admin_group",
        table_name="access_group_admin_access",
    )
    op.drop_table("access_group_admin_access")
''',
)


# --- API schemas ------------------------------------------------------------------
replace_once(
    "app/models/admin_hierarchy.py",
    '''class AccessGroupInput(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, max_length=512)
    node_ids: list[int] = Field(default_factory=list)
    inbounds: list[str] = Field(min_length=1)
    hosts: dict[str, list[int]]

    @field_validator("node_ids", "inbounds")''',
    '''class AccessGroupInput(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, max_length=512)
    node_ids: list[int] = Field(default_factory=list)
    inbounds: list[str] = Field(min_length=1)
    hosts: dict[str, list[int]]
    # Empty preserves the legacy/public behavior. One or more IDs restrict the
    # group to those administrators; Owner always retains management access.
    allowed_admin_ids: list[int] = Field(default_factory=list)

    @field_validator("node_ids", "inbounds", "allowed_admin_ids")''',
)
replace_once(
    "app/models/admin_hierarchy.py",
    '''    hosts: dict[str, list[int]]
    archived_at: Optional[datetime]
    active_user_count: int = 0
''',
    '''    hosts: dict[str, list[int]]
    allowed_admin_ids: list[int] = Field(default_factory=list)
    archived_at: Optional[datetime]
    active_user_count: int = 0
''',
)

replace_once(
    "app/models/user.py",
    '''class UserCreate(User):
    username: str
    status: UserStatusCreate = None
''',
    '''class UserCreate(User):
    username: str
    status: UserStatusCreate = None
    access_group_id: Optional[int] = Field(default=None, gt=0)
''',
)

# Restricted Free Form users may select an authorized Access Group. Their raw
# inbound/proxy/device settings remain server-controlled.
replace_once(
    "app/utils/marzhelp_policy.py",
    '''        concurrent_user_limit=concurrent_user_limit,
        data_limit_reset_strategy=UserDataLimitResetStrategy.no_reset,
    )
''',
    '''        concurrent_user_limit=concurrent_user_limit,
        data_limit_reset_strategy=UserDataLimitResetStrategy.no_reset,
        access_group_id=getattr(user, "access_group_id", None),
    )
''',
)


# --- Access Group authorization ----------------------------------------------------
replace_once(
    "app/utils/access_groups.py",
    '''from app.db.models import (
    AccessGroup,''',
    '''from app.db.access_group_models import AccessGroupAdminAccess
from app.db.models import (
    AccessGroup,''',
)
replace_once(
    "app/utils/access_groups.py",
    '''def _scope(db: Session, group_id: int) -> tuple[set[str], dict[str, set[int]], set[int]]:
''',
    '''def _allowed_admin_ids(db: Session, group_id: int) -> list[int]:
    return [
        row[0]
        for row in db.query(AccessGroupAdminAccess.admin_id)
        .filter(AccessGroupAdminAccess.access_group_id == group_id)
        .order_by(AccessGroupAdminAccess.admin_id)
        .all()
    ]


def _require_group_access(db: Session, group: AccessGroup, admin_id: int) -> None:
    actor = db.get(Admin, admin_id)
    if actor is None:
        raise admin_hierarchy.HierarchyError("policy_missing", "Administrator is unavailable")
    if admin_hierarchy.is_owner(db, actor):
        return
    allowed = _allowed_admin_ids(db, group.id)
    # Backward compatibility: groups created before this permission layer have
    # no rows and remain public until Owner explicitly restricts them.
    if allowed and admin_id not in allowed:
        raise admin_hierarchy.HierarchyError(
            "access_group_forbidden", "Administrator is not allowed to use this Access Group"
        )


def _validate_allowed_admin_ids(db: Session, values: AccessGroupInput) -> set[int]:
    allowed = set(values.allowed_admin_ids)
    if not allowed:
        return allowed
    existing = {
        row[0]
        for row in db.query(Admin.id).filter(Admin.id.in_(allowed)).all()
    }
    missing = sorted(allowed - existing)
    if missing:
        raise admin_hierarchy.HierarchyError(
            "access_group_admin_invalid", f"Unknown administrators: {missing}"
        )
    return allowed


def _replace_admin_access(
    db: Session,
    group: AccessGroup,
    values: AccessGroupInput,
) -> None:
    allowed = _validate_allowed_admin_ids(db, values)
    if allowed:
        disallowed_user_admins = {
            row[0]
            for row in db.query(User.admin_id)
            .filter(
                User.access_group_id == group.id,
                User.admin_id.is_not(None),
                User.admin_id != group.owner_admin_id,
                ~User.admin_id.in_(allowed),
            )
            .distinct()
            .all()
        }
        if disallowed_user_admins:
            raise admin_hierarchy.HierarchyError(
                "access_group_permission_in_use",
                "Cannot remove Access Group permission while users owned by these administrators still reference it: "
                + ", ".join(str(value) for value in sorted(disallowed_user_admins)),
            )
    db.query(AccessGroupAdminAccess).filter(
        AccessGroupAdminAccess.access_group_id == group.id
    ).delete(synchronize_session=False)
    db.add_all(
        AccessGroupAdminAccess(access_group_id=group.id, admin_id=admin_id)
        for admin_id in sorted(allowed)
        if admin_id != group.owner_admin_id
    )


def _scope(db: Session, group_id: int) -> tuple[set[str], dict[str, set[int]], set[int]]:
''',
)
replace_once(
    "app/utils/access_groups.py",
    '''    if group is None or group.archived_at is not None:
        raise admin_hierarchy.HierarchyError(
            "access_group_unavailable", "Access Group is unavailable"
        )
    inbounds, hosts, nodes = _scope(db, group_id)
''',
    '''    if group is None or group.archived_at is not None:
        raise admin_hierarchy.HierarchyError(
            "access_group_unavailable", "Access Group is unavailable"
        )
    _require_group_access(db, group, admin_id)
    inbounds, hosts, nodes = _scope(db, group_id)
''',
)
replace_once(
    "app/utils/access_groups.py",
    '''        hosts={tag: sorted(hosts[tag]) for tag in sorted(inbounds)},
        archived_at=group.archived_at,
''',
    '''        hosts={tag: sorted(hosts[tag]) for tag in sorted(inbounds)},
        allowed_admin_ids=_allowed_admin_ids(db, group.id),
        archived_at=group.archived_at,
''',
)
replace_once(
    "app/utils/access_groups.py",
    '''def list_groups(db: Session, actor: Admin) -> list[AccessGroup]:
    # Admins may select groups while creating users, but cannot manage them.
    return (
        db.query(AccessGroup)
        .filter(AccessGroup.archived_at.is_(None))
        .order_by(AccessGroup.name, AccessGroup.id)
        .all()
    )
''',
    '''def list_groups(db: Session, actor: Admin) -> list[AccessGroup]:
    query = db.query(AccessGroup).filter(AccessGroup.archived_at.is_(None))
    if not admin_hierarchy.is_owner(db, actor):
        group_ids = [row[0] for row in query.with_entities(AccessGroup.id).all()]
        restricted = {
            row[0]
            for row in db.query(AccessGroupAdminAccess.access_group_id)
            .filter(AccessGroupAdminAccess.access_group_id.in_(group_ids))
            .distinct()
            .all()
        }
        allowed = {
            row[0]
            for row in db.query(AccessGroupAdminAccess.access_group_id)
            .filter(
                AccessGroupAdminAccess.access_group_id.in_(group_ids),
                AccessGroupAdminAccess.admin_id == actor.id,
            )
            .all()
        }
        visible = (set(group_ids) - restricted) | allowed
        if not visible:
            return []
        query = query.filter(AccessGroup.id.in_(visible))
    return query.order_by(AccessGroup.name, AccessGroup.id).all()
''',
)
replace_once(
    "app/utils/access_groups.py",
    '''    _replace_scope(db, group, values)
    db.commit()
    db.refresh(group)
''',
    '''    _replace_scope(db, group, values)
    _replace_admin_access(db, group, values)
    db.commit()
    db.refresh(group)
''',
)
replace_once(
    "app/utils/access_groups.py",
    '''    group.description = values.description
    _replace_scope(db, group, values)
    db.flush()
''',
    '''    group.description = values.description
    _replace_scope(db, group, values)
    _replace_admin_access(db, group, values)
    db.flush()
''',
)
replace_once(
    "app/utils/access_groups.py",
    '''def apply_to_user(db: Session, user: User, group_id: int) -> None:
    inbounds, _, _ = validated_scope(db, group_id, user.admin_id)
''',
    '''def apply_to_user(db: Session, user: User, group_id: int) -> None:
    if user.admin_id is None:
        raise admin_hierarchy.HierarchyError(
            "access_group_owner_missing", "Access Group users require an administrator owner"
        )
    inbounds, _, _ = validated_scope(db, group_id, user.admin_id)
''',
)
replace_once(
    "app/utils/access_groups.py",
    '''    active_groups = {
        row[0]
        for row in db.query(AccessGroup.id)
        .filter(AccessGroup.id.in_(group_ids), AccessGroup.archived_at.is_(None))
        .all()
    }
''',
    '''    active_group_rows = (
        db.query(AccessGroup.id, AccessGroup.owner_admin_id)
        .filter(AccessGroup.id.in_(group_ids), AccessGroup.archived_at.is_(None))
        .all()
    )
    active_groups = {row[0] for row in active_group_rows}
    group_owners = {row[0]: row[1] for row in active_group_rows}
''',
)
replace_once(
    "app/utils/access_groups.py",
    '''    configured = set(xray.config.inbounds_by_tag)
    for user in users:
''',
    '''    permission_rows = (
        db.query(AccessGroupAdminAccess.access_group_id, AccessGroupAdminAccess.admin_id)
        .filter(AccessGroupAdminAccess.access_group_id.in_(active_groups))
        .all()
    )
    restricted_groups = {row[0] for row in permission_rows}
    allowed_admins_by_group: dict[int, set[int]] = {}
    for group_id, admin_id in permission_rows:
        allowed_admins_by_group.setdefault(group_id, set()).add(admin_id)
    configured = set(xray.config.inbounds_by_tag)
    for user in users:
''',
)
replace_once(
    "app/utils/access_groups.py",
    '''        valid = (
            bool(inbounds)
            and set(hosts) == inbounds
''',
    '''        permission_valid = (
            group_id not in restricted_groups
            or user.admin_id == group_owners.get(group_id)
            or user.admin_id in allowed_admins_by_group.get(group_id, set())
        )
        valid = (
            permission_valid
            and bool(inbounds)
            and set(hosts) == inbounds
''',
)
replace_once(
    "app/utils/access_groups.py",
    '''    group = db.get(AccessGroup, user.access_group_id)
    if group is None or group.archived_at is not None:
        return set()
    nodes = _scope(db, group.id)[2]
    return nodes or None
''',
    '''    try:
        _, _, nodes = validated_scope(db, user.access_group_id, user.admin_id)
    except admin_hierarchy.HierarchyError:
        return set()
    return nodes or None
''',
)


# --- Free Form backend -------------------------------------------------------------
replace_once(
    "app/routers/user.py",
    '''    admin_billing,
    admin_hierarchy,
    admin_plans,
''',
    '''    access_groups,
    admin_billing,
    admin_hierarchy,
    admin_plans,
''',
)
replace_once(
    "app/routers/user.py",
    '''        dbuser = crud.create_user(db, new_user, admin=dbadmin, commit=False)
        if dbadmin is not None:
            money_billing.charge_form_purchase(
''',
    '''        dbuser = crud.create_user(db, new_user, admin=dbadmin, commit=False)
        if new_user.access_group_id is not None:
            access_groups.apply_to_user(db, dbuser, new_user.access_group_id)
        if dbadmin is not None:
            money_billing.charge_form_purchase(
''',
)
replace_once(
    "app/routers/user.py",
    '''        dbuser = crud.set_owner(db, dbuser, new_admin, commit=False)
        user = admin_plans.scoped_user_response(
''',
    '''        dbuser = crud.set_owner(db, dbuser, new_admin, commit=False)
        if dbuser.access_group_id is not None:
            access_groups.apply_to_user(db, dbuser, dbuser.access_group_id)
        user = admin_plans.scoped_user_response(
''',
)


# --- Dashboard types ---------------------------------------------------------------
replace_once(
    "app/dashboard/src/types/Admin.ts",
    '''  hosts: Record<string, number[]>;
  archived_at: string | null;
  active_user_count: number;
};
''',
    '''  hosts: Record<string, number[]>;
  allowed_admin_ids: number[];
  archived_at: string | null;
  active_user_count: number;
};
''',
)
replace_once(
    "app/dashboard/src/types/User.ts",
    '''export type UserCreate = Pick<
  User,
  | "inbounds"
  | "proxies"
  | "expire"
  | "data_limit"
  | "data_limit_reset_strategy"
  | "on_hold_expire_duration"
  | "username"
  | "status"
  | "note"
>;
''',
    '''export type UserCreate = Pick<
  User,
  | "inbounds"
  | "proxies"
  | "expire"
  | "data_limit"
  | "data_limit_reset_strategy"
  | "on_hold_expire_duration"
  | "username"
  | "status"
  | "note"
> & {
  access_group_id?: number | null;
};
''',
)


# --- Access Group manager UI -------------------------------------------------------
replace_once(
    "app/dashboard/src/components/AccessGroupManager.tsx",
    '''import { AccessGroup, AccessGroupNetworkOption } from "types/Admin";
''',
    '''import { AccessGroup, AccessGroupNetworkOption, ManagedAdmin, ManagedAdminList } from "types/Admin";
''',
)
replace_once(
    "app/dashboard/src/components/AccessGroupManager.tsx",
    '''  hosts: Record<string, number[]>;
};
''',
    '''  hosts: Record<string, number[]>;
  allowedAdminIds: number[];
};
''',
)
replace_once(
    "app/dashboard/src/components/AccessGroupManager.tsx",
    '''  hosts: {},
});
''',
    '''  hosts: {},
  allowedAdminIds: [],
});

const fetchAdmins = async (): Promise<ManagedAdmin[]> => {
  const result: ManagedAdmin[] = [];
  let offset = 0;
  let total = 0;
  do {
    const page = await fetch<ManagedAdminList>(`/admin-management?offset=${offset}&limit=100`);
    result.push(...page.admins);
    total = page.total;
    if (!page.admins.length) break;
    offset += page.admins.length;
  } while (offset < total);
  return result;
};
''',
)
replace_once(
    "app/dashboard/src/components/AccessGroupManager.tsx",
    '''  const nodes = useQuery<NodeOption[], Error>("access-group-node-options", () => fetch("/nodes"));
  const options = network.data || [];
''',
    '''  const nodes = useQuery<NodeOption[], Error>("access-group-node-options", () => fetch("/nodes"));
  const admins = useQuery<ManagedAdmin[], Error>("access-group-admin-options", fetchAdmins);
  const options = network.data || [];
''',
)
replace_once(
    "app/dashboard/src/components/AccessGroupManager.tsx",
    '''        hosts: normalizeAccessGroupHostScope(draft.hosts),
      },
''',
    '''        hosts: normalizeAccessGroupHostScope(draft.hosts),
        allowed_admin_ids: draft.allowedAdminIds,
      },
''',
)
replace_once(
    "app/dashboard/src/components/AccessGroupManager.tsx",
    '''    hosts: normalizeAccessGroupHostScope(group.hosts),
  });
''',
    '''    hosts: normalizeAccessGroupHostScope(group.hosts),
    allowedAdminIds: [...group.allowed_admin_ids],
  });
''',
)
replace_once(
    "app/dashboard/src/components/AccessGroupManager.tsx",
    '''  if (groups.isLoading || network.isLoading || nodes.isLoading) {
''',
    '''  if (groups.isLoading || network.isLoading || nodes.isLoading || admins.isLoading) {
''',
)
replace_once(
    "app/dashboard/src/components/AccessGroupManager.tsx",
    '''  if (groups.isError || network.isError || nodes.isError) {
    return <Alert status="error"><AlertIcon />گزینه‌های Access Group دریافت نشدند.<Button ms={3} onClick={() => { groups.refetch(); network.refetch(); nodes.refetch(); }}>تلاش دوباره</Button></Alert>;
''',
    '''  if (groups.isError || network.isError || nodes.isError || admins.isError) {
    return <Alert status="error"><AlertIcon />گزینه‌های Access Group دریافت نشدند.<Button ms={3} onClick={() => { groups.refetch(); network.refetch(); nodes.refetch(); admins.refetch(); }}>تلاش دوباره</Button></Alert>;
''',
)
replace_once(
    "app/dashboard/src/components/AccessGroupManager.tsx",
    '''        </SimpleGrid>
        <FormControl>
          <FormLabel>Nodeها</FormLabel>
''',
    '''        </SimpleGrid>
        <FormControl>
          <FormLabel>ادمین‌های مجاز</FormLabel>
          <SimpleGrid columns={{ base: 1, md: 2 }} gap={1} p={2} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px">
            {(admins.data || []).filter((admin) => admin.role === "ADMIN").map((admin) => (
              <Checkbox
                key={admin.id}
                minH="44px"
                isChecked={draft.allowedAdminIds.includes(admin.id)}
                onChange={(event) => setDraft((current) => ({
                  ...current,
                  allowedAdminIds: event.target.checked
                    ? [...new Set([...current.allowedAdminIds, admin.id])].sort((a, b) => a - b)
                    : current.allowedAdminIds.filter((id) => id !== admin.id),
                }))}
              >
                <HStack><Text>{admin.username}</Text><Badge>{admin.account_status}</Badge></HStack>
              </Checkbox>
            ))}
            {!(admins.data || []).some((admin) => admin.role === "ADMIN") && <Text p={2} color="gray.500">ادمینی برای واگذاری این گروه وجود ندارد.</Text>}
          </SimpleGrid>
          <FormHelperText>
            {draft.allowedAdminIds.length
              ? `فقط ${draft.allowedAdminIds.length} ادمین انتخاب‌شده می‌توانند از این گروه استفاده کنند.`
              : "هیچ ادمینی انتخاب نشده: گروه برای همه ادمین‌ها قابل استفاده می‌ماند (سازگاری با گروه‌های قبلی)."}
          </FormHelperText>
        </FormControl>
        <FormControl>
          <FormLabel>Nodeها</FormLabel>
''',
)
replace_once(
    "app/dashboard/src/components/AccessGroupManager.tsx",
    '''<Badge>{group.inbounds.length} Inbound</Badge><Badge>{group.node_ids.length ? `${group.node_ids.length} Node` : "همه Nodeها"}</Badge>''',
    '''<Badge>{group.inbounds.length} Inbound</Badge><Badge colorScheme="purple">{group.allowed_admin_ids.length ? `${group.allowed_admin_ids.length} ادمین مجاز` : "همه ادمین‌ها"}</Badge><Badge>{group.node_ids.length ? `${group.node_ids.length} Node` : "همه Nodeها"}</Badge>''',
)


# --- Free Form UI ------------------------------------------------------------------
replace_once(
    "app/dashboard/src/components/UserDialog.tsx",
    '''import { AccountSummary, AdminCapabilities, ManagedAdmin, ManagedAdminList, SubscriptionMode } from "types/Admin";
''',
    '''import { AccessGroup, AccountSummary, AdminCapabilities, ManagedAdmin, ManagedAdminList, SubscriptionMode } from "types/Admin";
''',
)
replace_once(
    "app/dashboard/src/components/UserDialog.tsx",
    '''    concurrent_user_limit: null,
    owner_admin: "",
    inbounds,
''',
    '''    concurrent_user_limit: null,
    owner_admin: "",
    access_group_id: null,
    inbounds,
''',
)
replace_once(
    "app/dashboard/src/components/UserDialog.tsx",
    '''  owner_admin: z.string(),
  inbounds: z.record(z.string(), z.array(z.string())).transform((ins) => {
''',
    '''  owner_admin: z.string(),
  access_group_id: z.preprocess(
    (value) => value === "" || value === null || value === undefined ? null : Number(value),
    z.number().int().positive().nullable()
  ),
  inbounds: z.record(z.string(), z.array(z.string())).transform((ins) => {
''',
)
replace_once(
    "app/dashboard/src/components/UserDialog.tsx",
    '''  const accountQuery = useQuery<AccountSummary, Error>(
    ["account-summary"],
    () => fetch("/account/summary"),
    { enabled: isOpen, staleTime: 30000 }
  );
''',
    '''  const accountQuery = useQuery<AccountSummary, Error>(
    ["account-summary"],
    () => fetch("/account/summary"),
    { enabled: isOpen, staleTime: 30000 }
  );
  const accessGroupsQuery = useQuery<AccessGroup[], Error>(
    ["access-groups", "free-form"],
    () => fetch("/access-groups"),
    { enabled: isOpen && !isEditing, staleTime: 30000 }
  );
''',
)
replace_once(
    "app/dashboard/src/components/UserDialog.tsx",
    '''  const selectedOwner = adminsQuery.data?.find(
    (admin) => admin.username === ownerAdmin
  );
''',
    '''  const selectedOwner = adminsQuery.data?.find(
    (admin) => admin.username === ownerAdmin
  );
  const visibleAccessGroups = (accessGroupsQuery.data || []).filter((group) => {
    if (!userData.is_sudo || !selectedOwner) return true;
    return group.allowed_admin_ids.length === 0 || group.allowed_admin_ids.includes(selectedOwner.id);
  });
''',
)
replace_once(
    "app/dashboard/src/components/UserDialog.tsx",
    '''        note: values.note,
      }
''',
    '''        note: values.note,
        access_group_id: values.access_group_id,
      }
''',
)
replace_once(
    "app/dashboard/src/components/UserDialog.tsx",
    '''                      )}
                      <Divider my={2} borderColor="#33483b" />
''',
    '''                      )}
                      {!isEditing && (
                        <FormControl mb="10px" isInvalid={!!form.formState.errors.access_group_id}>
                          <FormLabel>Access Group</FormLabel>
                          <Controller
                            control={form.control}
                            name="access_group_id"
                            render={({ field }) => (
                              <Select
                                size="sm"
                                minH="44px"
                                value={field.value ?? ""}
                                onChange={(event) => field.onChange(event.target.value === "" ? null : Number(event.target.value))}
                                isDisabled={disabled || accessGroupsQuery.isLoading}
                              >
                                <option value="">بدون Access Group</option>
                                {visibleAccessGroups.map((group) => (
                                  <option key={group.id} value={group.id}>{group.name}</option>
                                ))}
                              </Select>
                            )}
                          />
                          <FormHelperText>
                            فقط گروه‌های مجاز برای ادمین نهایی نمایش داده می‌شوند. با انتخاب گروه، Inbound/Host/Node آن در Backend مرجع نهایی شبکه است.
                          </FormHelperText>
                          <FormErrorMessage>{form.formState.errors.access_group_id?.message}</FormErrorMessage>
                        </FormControl>
                      )}
                      <Divider my={2} borderColor="#33483b" />
''',
)


# --- Frontend contract test --------------------------------------------------------
replace_once(
    "app/dashboard/scripts/test-access-groups.cjs",
    '''const userModal = read("src/components/CreateUserFromPlan.tsx");
''',
    '''const userModal = read("src/components/CreateUserFromPlan.tsx");
const freeFormModal = read("src/components/UserDialog.tsx");
''',
)
replace_once(
    "app/dashboard/scripts/test-access-groups.cjs",
    '''assert.ok(manager.includes("hosts: normalizeAccessGroupHostScope"));
''',
    '''assert.ok(manager.includes("hosts: normalizeAccessGroupHostScope"));
assert.ok(manager.includes("allowed_admin_ids: draft.allowedAdminIds"));
assert.ok(manager.includes("ادمین‌های مجاز"));
''',
)
replace_once(
    "app/dashboard/scripts/test-access-groups.cjs",
    '''assert.equal(userModal.includes("Use Plan network"), false);

console.log("Access Group UI contract: assertions passed");
''',
    '''assert.equal(userModal.includes("Use Plan network"), false);
assert.ok(freeFormModal.includes('fetch("/access-groups")'));
assert.ok(freeFormModal.includes('name="access_group_id"'));
assert.ok(freeFormModal.includes("group.allowed_admin_ids.length === 0"));

console.log("Access Group UI contract: assertions passed");
''',
)


# --- Backend contract test ---------------------------------------------------------
write(
    "tests/test_access_group_admin_permissions_contract.py",
    '''from pathlib import Path


def test_access_group_permission_contract_is_enforced_server_side():
    source = Path("app/utils/access_groups.py").read_text(encoding="utf-8")
    assert "AccessGroupAdminAccess" in source
    assert '"access_group_forbidden"' in source
    assert "_require_group_access(db, group, admin_id)" in source
    assert "_replace_admin_access(db, group, values)" in source


def test_free_form_and_owner_transfer_revalidate_access_group():
    source = Path("app/routers/user.py").read_text(encoding="utf-8")
    assert "access_groups.apply_to_user(db, dbuser, new_user.access_group_id)" in source
    assert "access_groups.apply_to_user(db, dbuser, dbuser.access_group_id)" in source


def test_migration_extends_current_node_policy_head():
    source = Path(
        "app/db/migrations/versions/e1a7c4d9b302_access_group_admin_permissions.py"
    ).read_text(encoding="utf-8")
    assert 'revision = "e1a7c4d9b302"' in source
    assert 'down_revision = "f6b2c9d4e701"' in source
''',
)

print("Access Group admin permission patch applied")
