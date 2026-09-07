from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}")
    target.write_text(text.replace(old, new), encoding="utf-8")


replace_once(
    "app/models/admin_hierarchy.py",
    '''    # Empty preserves the legacy/public behavior. One or more IDs restrict the
    # group to those administrators; Owner always retains management access.
    allowed_admin_ids: list[int] = Field(default_factory=list)
''',
    '''    # Omitting this field preserves legacy/public persistence. Sending it
    # explicitly, including [], creates a restricted policy; [] is deny-all for
    # delegated Admins while Owner always retains management access.
    allowed_admin_ids: list[int] = Field(default_factory=list)
''',
)
replace_once(
    "app/models/admin_hierarchy.py",
    '''    allowed_admin_ids: list[int] = Field(default_factory=list)
    archived_at: Optional[datetime]
''',
    '''    allowed_admin_ids: list[int] = Field(default_factory=list)
    admin_access_restricted: bool = False
    archived_at: Optional[datetime]
''',
)

replace_once(
    "app/utils/access_groups.py",
    '''        allowed_admin_ids=_allowed_admin_ids(db, group.id),
        archived_at=group.archived_at,
''',
    '''        allowed_admin_ids=_allowed_admin_ids(db, group.id),
        admin_access_restricted=bool(_permission_admin_ids(db, group.id)),
        archived_at=group.archived_at,
''',
)

replace_once(
    "app/dashboard/src/types/Admin.ts",
    '''  allowed_admin_ids: number[];
  archived_at: string | null;
''',
    '''  allowed_admin_ids: number[];
  admin_access_restricted: boolean;
  archived_at: string | null;
''',
)

replace_once(
    "app/dashboard/src/components/UserDialog.tsx",
    '''    const groupPermissionAllowed =
      group.allowed_admin_ids.length === 0 || group.allowed_admin_ids.includes(selectedOwner.id);
''',
    '''    const groupPermissionAllowed =
      !group.admin_access_restricted || group.allowed_admin_ids.includes(selectedOwner.id);
''',
)

replace_once(
    "app/dashboard/src/components/AccessGroupManager.tsx",
    '''              : "هیچ ادمینی انتخاب نشده: گروه برای همه ادمین‌ها قابل استفاده می‌ماند (سازگاری با گروه‌های قبلی)."}
''',
    '''              : "هیچ ادمینی انتخاب نشده: با ذخیره این تنظیم، دسترسی همه ادمین‌های واگذارشده بسته می‌شود؛ Owner همچنان دسترسی مدیریتی دارد."}
''',
)

replace_once(
    "tests/test_access_group_admin_assignment_validation.py",
    '''    assert access_groups._permission_admin_ids(session, group.id) == []
    assert access_groups._allowed_admin_ids(session, group.id) == []
    access_groups._require_group_access(session, group, target.id)
''',
    '''    assert access_groups._permission_admin_ids(session, group.id) == []
    assert access_groups._allowed_admin_ids(session, group.id) == []
    response = access_groups.response(session, group)
    assert response.allowed_admin_ids == []
    assert response.admin_access_restricted is False
    access_groups._require_group_access(session, group, target.id)
''',
)
replace_once(
    "tests/test_access_group_admin_assignment_validation.py",
    '''    assert access_groups._permission_admin_ids(session, group.id) == [owner.id]
    assert access_groups._allowed_admin_ids(session, group.id) == []
    assert access_groups.response(session, group).allowed_admin_ids == []
    access_groups._require_group_access(session, group, owner.id)
''',
    '''    assert access_groups._permission_admin_ids(session, group.id) == [owner.id]
    assert access_groups._allowed_admin_ids(session, group.id) == []
    response = access_groups.response(session, group)
    assert response.allowed_admin_ids == []
    assert response.admin_access_restricted is True
    access_groups._require_group_access(session, group, owner.id)
''',
)
replace_once(
    "tests/test_access_group_admin_assignment_validation.py",
    '''    assert access_groups._permission_admin_ids(session, group.id) == sorted([owner.id, target.id])
    assert access_groups._allowed_admin_ids(session, group.id) == [target.id]
    assert access_groups.response(session, group).allowed_admin_ids == [target.id]
    access_groups._require_group_access(session, group, target.id)
''',
    '''    assert access_groups._permission_admin_ids(session, group.id) == sorted([owner.id, target.id])
    assert access_groups._allowed_admin_ids(session, group.id) == [target.id]
    response = access_groups.response(session, group)
    assert response.allowed_admin_ids == [target.id]
    assert response.admin_access_restricted is True
    access_groups._require_group_access(session, group, target.id)
''',
)

contract = Path("tests/test_access_group_admin_permissions_contract.py")
text = contract.read_text(encoding="utf-8")
addition = '''\n\ndef test_access_group_response_exposes_legacy_vs_restricted_policy_state():
    backend = Path("app/utils/access_groups.py").read_text(encoding="utf-8")
    model = Path("app/models/admin_hierarchy.py").read_text(encoding="utf-8")
    types = Path("app/dashboard/src/types/Admin.ts").read_text(encoding="utf-8")
    dialog = Path("app/dashboard/src/components/UserDialog.tsx").read_text(encoding="utf-8")
    manager = Path("app/dashboard/src/components/AccessGroupManager.tsx").read_text(encoding="utf-8")

    assert "admin_access_restricted=bool(_permission_admin_ids(db, group.id))" in backend
    assert "admin_access_restricted: bool = False" in model
    assert "admin_access_restricted: boolean;" in types
    assert "!group.admin_access_restricted || group.allowed_admin_ids.includes(selectedOwner.id)" in dialog
    assert "گروه برای همه ادمین‌ها قابل استفاده می‌ماند" not in manager
    assert "دسترسی همه ادمین‌های واگذارشده بسته می‌شود" in manager
'''
if "def test_access_group_response_exposes_legacy_vs_restricted_policy_state" in text:
    raise SystemExit("contract test already exists")
contract.write_text(text.rstrip() + addition + "\n", encoding="utf-8")
