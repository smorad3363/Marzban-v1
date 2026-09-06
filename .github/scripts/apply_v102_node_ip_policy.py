from pathlib import Path
import json


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# Backend API models and validation.
replace_once(
    "app/models/node.py",
    "from datetime import datetime\nfrom enum import Enum\nfrom typing import List, Optional\n\nfrom pydantic import ConfigDict, BaseModel, Field\n",
    "from datetime import datetime\nfrom enum import Enum\nfrom ipaddress import ip_network\nfrom typing import List, Optional\n\nfrom pydantic import ConfigDict, BaseModel, Field, field_validator, model_validator\n",
)
replace_once(
    "app/models/node.py",
    "class NodeStatus(str, Enum):\n    connected = \"connected\"\n    connecting = \"connecting\"\n    error = \"error\"\n    disabled = \"disabled\"\n\n\nclass NodeSettings(BaseModel):",
    '''class NodeStatus(str, Enum):
    connected = "connected"
    connecting = "connecting"
    error = "error"
    disabled = "disabled"


class NodeIPSourceMode(str, Enum):
    direct = "direct"
    trusted_xff = "trusted_xff"
    proxy_protocol = "proxy_protocol"


class NodeCDNProvider(str, Enum):
    cloudflare = "cloudflare"
    custom = "custom"


MAX_TRUSTED_PROXY_CIDRS = 128


def _validate_complete_ip_source_policy(
    mode: NodeIPSourceMode,
    provider: Optional[NodeCDNProvider],
    cidrs: Optional[List[str]],
) -> None:
    networks = cidrs or []
    if mode is NodeIPSourceMode.direct:
        if provider is not None or networks:
            raise ValueError("direct IP source mode cannot define a CDN provider or trusted proxy CIDRs")
        return
    if mode is NodeIPSourceMode.trusted_xff:
        if provider is None:
            raise ValueError("trusted_xff requires a CDN provider")
        if provider is NodeCDNProvider.custom and not networks:
            raise ValueError("custom trusted_xff requires at least one trusted proxy CIDR")
        return
    if mode is NodeIPSourceMode.proxy_protocol:
        if provider is not None:
            raise ValueError("proxy_protocol does not accept a CDN provider")
        if not networks:
            raise ValueError("proxy_protocol requires at least one trusted proxy CIDR")


class NodeSettings(BaseModel):''',
)
replace_once(
    "app/models/node.py",
    "    usage_coefficient: float = Field(gt=0, default=1.0)\n    watchdog_enabled: bool = True\n\n\nclass NodeCreate(Node):",
    '''    usage_coefficient: float = Field(gt=0, default=1.0)
    watchdog_enabled: bool = True
    ip_source_mode: NodeIPSourceMode = NodeIPSourceMode.direct
    cdn_provider: Optional[NodeCDNProvider] = None
    trusted_proxy_cidrs: Optional[List[str]] = None

    @field_validator("trusted_proxy_cidrs")
    @classmethod
    def canonicalize_trusted_proxy_cidrs(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        if len(value) > MAX_TRUSTED_PROXY_CIDRS:
            raise ValueError(f"at most {MAX_TRUSTED_PROXY_CIDRS} trusted proxy CIDRs are allowed")
        normalized = []
        seen = set()
        for raw in value:
            candidate = str(raw).strip()
            if not candidate:
                continue
            try:
                canonical = str(ip_network(candidate, strict=False))
            except ValueError as exc:
                raise ValueError(f"invalid trusted proxy CIDR: {candidate}") from exc
            if canonical not in seen:
                seen.add(canonical)
                normalized.append(canonical)
        return normalized or None


class NodeCreate(Node):''',
)
replace_once(
    "app/models/node.py",
    "class NodeCreate(Node):\n    add_as_new_host: bool = True\n    model_config = ConfigDict(json_schema_extra={",
    '''class NodeCreate(Node):
    add_as_new_host: bool = True

    @model_validator(mode="after")
    def validate_ip_source_policy(self):
        _validate_complete_ip_source_policy(
            self.ip_source_mode, self.cdn_provider, self.trusted_proxy_cidrs
        )
        return self

    model_config = ConfigDict(json_schema_extra={''',
)
replace_once(
    "app/models/node.py",
    "    watchdog_enabled: Optional[bool] = Field(None, nullable=True)\n    model_config = ConfigDict(json_schema_extra={",
    '''    watchdog_enabled: Optional[bool] = Field(None, nullable=True)
    ip_source_mode: Optional[NodeIPSourceMode] = Field(None, nullable=True)
    cdn_provider: Optional[NodeCDNProvider] = Field(None, nullable=True)
    trusted_proxy_cidrs: Optional[List[str]] = Field(None, nullable=True)

    @model_validator(mode="after")
    def validate_complete_ip_source_update(self):
        fields = {"ip_source_mode", "cdn_provider", "trusted_proxy_cidrs"}
        if fields & self.model_fields_set:
            if not fields.issubset(self.model_fields_set):
                raise ValueError("ip source policy updates must include mode, provider, and trusted proxy CIDRs together")
            if self.ip_source_mode is None:
                raise ValueError("ip_source_mode cannot be null when updating the IP source policy")
            _validate_complete_ip_source_policy(
                self.ip_source_mode, self.cdn_provider, self.trusted_proxy_cidrs
            )
        return self

    model_config = ConfigDict(json_schema_extra={''',
)

# SQLAlchemy persistence.
replace_once(
    "app/db/models.py",
    '    usage_coefficient = Column(Float, nullable=False, server_default=text("1.0"), default=1)\n    watchdog_enabled = Column(Boolean, nullable=False, server_default=text("1"), default=True)\n',
    '''    usage_coefficient = Column(Float, nullable=False, server_default=text("1.0"), default=1)
    watchdog_enabled = Column(Boolean, nullable=False, server_default=text("1"), default=True)
    ip_source_mode = Column(String(24), nullable=False, server_default=text("'direct'"), default="direct")
    cdn_provider = Column(String(24), nullable=True, default=None)
    trusted_proxy_cidrs = Column(JSON, nullable=True, default=None)
''',
)

# CRUD round-trip.
replace_once(
    "app/db/crud.py",
    '''    dbnode = Node(name=node.name,
                  address=node.address,
                  port=node.port,
                  api_port=node.api_port,
                  usage_coefficient=node.usage_coefficient,
                  watchdog_enabled=node.watchdog_enabled)''',
    '''    dbnode = Node(name=node.name,
                  address=node.address,
                  port=node.port,
                  api_port=node.api_port,
                  usage_coefficient=node.usage_coefficient,
                  watchdog_enabled=node.watchdog_enabled,
                  ip_source_mode=node.ip_source_mode.value,
                  cdn_provider=node.cdn_provider.value if node.cdn_provider is not None else None,
                  trusted_proxy_cidrs=node.trusted_proxy_cidrs or None)''',
)
replace_once(
    "app/db/crud.py",
    '''    if modify.watchdog_enabled is not None:
        dbnode.watchdog_enabled = modify.watchdog_enabled

    db.commit()''',
    '''    if modify.watchdog_enabled is not None:
        dbnode.watchdog_enabled = modify.watchdog_enabled

    ip_source_fields = {"ip_source_mode", "cdn_provider", "trusted_proxy_cidrs"}
    if ip_source_fields & modify.model_fields_set:
        dbnode.ip_source_mode = modify.ip_source_mode.value
        dbnode.cdn_provider = modify.cdn_provider.value if modify.cdn_provider is not None else None
        dbnode.trusted_proxy_cidrs = modify.trusted_proxy_cidrs or None

    db.commit()''',
)

# Frontend data contract.
replace_once(
    "app/dashboard/src/contexts/NodesContext.tsx",
    "  watchdog_enabled: z.boolean().optional(),\n});",
    '''  watchdog_enabled: z.boolean().optional(),
  ip_source_mode: z.enum(["direct", "trusted_xff", "proxy_protocol"]).default("direct"),
  cdn_provider: z.enum(["cloudflare", "custom"]).nullable().optional(),
  trusted_proxy_cidrs: z.array(z.string()).nullable().optional(),
});''',
)
replace_once(
    "app/dashboard/src/contexts/NodesContext.tsx",
    "  usage_coefficient: 1,\n  watchdog_enabled: true,\n});",
    '''  usage_coefficient: 1,
  watchdog_enabled: true,
  ip_source_mode: "direct",
  cdn_provider: null,
  trusted_proxy_cidrs: [],
});''',
)

# Node form controls.
replace_once(
    "app/dashboard/src/components/NodesModal.tsx",
    "  Switch,\n  Text,\n  Tooltip,",
    "  Switch,\n  Select,\n  Text,\n  Textarea,\n  Tooltip,",
)
replace_once(
    "app/dashboard/src/components/NodesModal.tsx",
    '  const { t } = useTranslation();\n  const [showCertificate, setShowCertificate] = useState(false);',
    '''  const { t } = useTranslation();
  const [showCertificate, setShowCertificate] = useState(false);
  const ipSourceMode = form.watch("ip_source_mode") || "direct";
  const cdnProvider = form.watch("cdn_provider");
  const submitNode = (value: NodeType) => {
    const normalized: NodeType = { ...value };
    if (normalized.ip_source_mode === "direct") {
      normalized.cdn_provider = null;
      normalized.trusted_proxy_cidrs = [];
    } else if (normalized.ip_source_mode === "proxy_protocol") {
      normalized.cdn_provider = null;
    }
    mutate(normalized);
  };''',
)
replace_once(
    "app/dashboard/src/components/NodesModal.tsx",
    '<form onSubmit={form.handleSubmit((v) => mutate(v))}>',
    '<form onSubmit={form.handleSubmit(submitNode)}>',
)
marker = '''        {addAsHost && (
          <FormControl py={1}>'''
policy_ui = '''        <Box w="full" borderWidth="1px" borderRadius="md" p={3}>
          <VStack align="stretch" spacing={3}>
            <FormControl>
              <FormLabel mb={1}>{t("nodes.ipSourceMode")}</FormLabel>
              <Controller
                name="ip_source_mode"
                control={form.control}
                render={({ field }) => (
                  <Select size="sm" value={field.value || "direct"} onChange={field.onChange}>
                    <option value="direct">{t("nodes.ipSourceDirect")}</option>
                    <option value="trusted_xff">{t("nodes.ipSourceTrustedXff")}</option>
                    <option value="proxy_protocol">{t("nodes.ipSourceProxyProtocol")}</option>
                  </Select>
                )}
              />
              <Text mt={1} fontSize="xs" color="gray.500">
                {t("nodes.ipSourceModeHint")}
              </Text>
            </FormControl>

            {ipSourceMode === "trusted_xff" && (
              <FormControl>
                <FormLabel mb={1}>{t("nodes.cdnProvider")}</FormLabel>
                <Controller
                  name="cdn_provider"
                  control={form.control}
                  render={({ field }) => (
                    <Select
                      size="sm"
                      value={field.value || ""}
                      onChange={(event) => field.onChange(event.target.value || null)}
                    >
                      <option value="">{t("nodes.selectCdnProvider")}</option>
                      <option value="cloudflare">Cloudflare</option>
                      <option value="custom">{t("nodes.customProxy")}</option>
                    </Select>
                  )}
                />
              </FormControl>
            )}

            {(ipSourceMode === "proxy_protocol" ||
              (ipSourceMode === "trusted_xff" && cdnProvider === "custom")) && (
              <FormControl>
                <FormLabel mb={1}>{t("nodes.trustedProxyCidrs")}</FormLabel>
                <Controller
                  name="trusted_proxy_cidrs"
                  control={form.control}
                  render={({ field }) => (
                    <Textarea
                      size="sm"
                      rows={3}
                      dir="ltr"
                      textAlign="left"
                      value={(field.value || []).join("\n")}
                      onChange={(event) =>
                        field.onChange(
                          event.target.value
                            .split(/[\n,]+/)
                            .map((value) => value.trim())
                            .filter(Boolean)
                        )
                      }
                      placeholder={"173.245.48.0/20\n2400:cb00::/32"}
                    />
                  )}
                />
                <Text mt={1} fontSize="xs" color="gray.500">
                  {t("nodes.trustedProxyCidrsHint")}
                </Text>
              </FormControl>
            )}

            {ipSourceMode !== "direct" && (
              <Alert status="warning" borderRadius="md" alignItems="flex-start">
                <AlertIcon mt={0.5} />
                <Text fontSize="xs">{t("nodes.ipSourceRuntimePending")}</Text>
              </Alert>
            )}
          </VStack>
        </Box>
'''
replace_once("app/dashboard/src/components/NodesModal.tsx", marker, policy_ui + marker)

# Persian localization, parsed as JSON to avoid hand-editing a large locale file.
locale_path = Path("app/dashboard/public/statics/locales/fa.json")
locale = json.loads(locale_path.read_text(encoding="utf-8"))
locale.update({
    "nodes.ipSourceMode": "منبع تشخیص IP کاربر",
    "nodes.ipSourceModeHint": "مشخص کنید این نود IP واقعی کاربر را مستقیم می‌بیند یا پشت CDN / پراکسی مورد اعتماد قرار دارد.",
    "nodes.ipSourceDirect": "اتصال مستقیم",
    "nodes.ipSourceTrustedXff": "CDN / هدر X-Forwarded-For مورد اعتماد",
    "nodes.ipSourceProxyProtocol": "Reverse Proxy با PROXY Protocol",
    "nodes.cdnProvider": "ارائه‌دهنده CDN / پراکسی",
    "nodes.selectCdnProvider": "انتخاب ارائه‌دهنده",
    "nodes.customProxy": "پراکسی سفارشی",
    "nodes.trustedProxyCidrs": "شبکه‌های پراکسی مورد اعتماد (CIDR)",
    "nodes.trustedProxyCidrsHint": "فقط IPهای واسطی که واقعاً تحت کنترل شما یا ارائه‌دهنده معتبر هستند وارد کنید؛ هر خط یک CIDR.",
    "nodes.ipSourceRuntimePending": "این سیاست اکنون ذخیره می‌شود، اما تا فعال‌شدن Node Runtime امن V1.0.2 به هدرهای واسط برای اعمال محدودیت دستگاه اعتماد نمی‌شود.",
})
locale_path.write_text(json.dumps(locale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Alembic migration on the current custom head.
migration = Path("app/db/migrations/versions/f6b2c9d4e701_add_node_ip_source_policy.py")
if migration.exists():
    raise SystemExit(f"{migration} already exists")
migration.write_text('''"""add trusted client IP source policy to nodes

Revision ID: f6b2c9d4e701
Revises: c9e1f4a7b203
"""

from alembic import op
import sqlalchemy as sa


revision = "f6b2c9d4e701"
down_revision = "c9e1f4a7b203"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "nodes",
        sa.Column("ip_source_mode", sa.String(24), nullable=False, server_default="direct"),
    )
    op.add_column("nodes", sa.Column("cdn_provider", sa.String(24), nullable=True))
    op.add_column("nodes", sa.Column("trusted_proxy_cidrs", sa.JSON(), nullable=True))
    op.create_check_constraint(
        "ck_nodes_ip_source_mode",
        "nodes",
        "ip_source_mode IN ('direct','trusted_xff','proxy_protocol')",
    )
    op.create_check_constraint(
        "ck_nodes_cdn_provider",
        "nodes",
        "cdn_provider IS NULL OR cdn_provider IN ('cloudflare','custom')",
    )


def downgrade():
    op.drop_constraint("ck_nodes_cdn_provider", "nodes", type_="check")
    op.drop_constraint("ck_nodes_ip_source_mode", "nodes", type_="check")
    op.drop_column("nodes", "trusted_proxy_cidrs")
    op.drop_column("nodes", "cdn_provider")
    op.drop_column("nodes", "ip_source_mode")
''', encoding="utf-8")

# Focused unit/contract tests.
test_path = Path("tests/test_v102_node_ip_policy.py")
if test_path.exists():
    raise SystemExit(f"{test_path} already exists")
test_path.write_text('''from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import crud
from app.db.models import Node as DBNode
from app.models.node import NodeCreate, NodeModify


def _base(**overrides):
    data = {
        "name": "edge-1",
        "address": "127.0.0.1",
        "port": 62050,
        "api_port": 62051,
        "usage_coefficient": 1.0,
        "watchdog_enabled": True,
    }
    data.update(overrides)
    return data


def test_direct_is_default_and_rejects_trust_material():
    direct = NodeCreate(**_base())
    assert direct.ip_source_mode.value == "direct"
    assert direct.cdn_provider is None
    assert direct.trusted_proxy_cidrs is None
    with pytest.raises(ValidationError):
        NodeCreate(**_base(cdn_provider="cloudflare"))


def test_custom_xff_requires_and_canonicalizes_cidrs():
    with pytest.raises(ValidationError):
        NodeCreate(**_base(ip_source_mode="trusted_xff", cdn_provider="custom"))
    node = NodeCreate(**_base(
        ip_source_mode="trusted_xff",
        cdn_provider="custom",
        trusted_proxy_cidrs=["10.1.2.3/8", "10.0.0.0/8", "2001:db8::1/32"],
    ))
    assert node.trusted_proxy_cidrs == ["10.0.0.0/8", "2001:db8::/32"]


def test_cloudflare_xff_can_defer_managed_ranges_to_runtime():
    node = NodeCreate(**_base(ip_source_mode="trusted_xff", cdn_provider="cloudflare"))
    assert node.cdn_provider.value == "cloudflare"
    assert node.trusted_proxy_cidrs is None


def test_proxy_protocol_requires_trusted_peer_and_no_cdn_provider():
    with pytest.raises(ValidationError):
        NodeCreate(**_base(ip_source_mode="proxy_protocol"))
    with pytest.raises(ValidationError):
        NodeCreate(**_base(
            ip_source_mode="proxy_protocol",
            cdn_provider="cloudflare",
            trusted_proxy_cidrs=["10.0.0.0/8"],
        ))


def test_policy_update_is_atomic_at_api_model_boundary():
    with pytest.raises(ValidationError):
        NodeModify(ip_source_mode="trusted_xff")
    update = NodeModify(
        ip_source_mode="trusted_xff",
        cdn_provider="custom",
        trusted_proxy_cidrs=["192.0.2.10/24"],
    )
    assert update.trusted_proxy_cidrs == ["192.0.2.0/24"]


def test_crud_round_trip_persists_node_ip_policy():
    engine = create_engine("sqlite:///:memory:")
    DBNode.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        created = crud.create_node(db, NodeCreate(**_base(
            ip_source_mode="trusted_xff",
            cdn_provider="custom",
            trusted_proxy_cidrs=["192.0.2.8/24"],
        )))
        assert created.ip_source_mode == "trusted_xff"
        assert created.cdn_provider == "custom"
        assert created.trusted_proxy_cidrs == ["192.0.2.0/24"]

        updated = crud.update_node(db, created, NodeModify(
            ip_source_mode="proxy_protocol",
            cdn_provider=None,
            trusted_proxy_cidrs=["198.51.100.7/24"],
        ))
        assert updated.ip_source_mode == "proxy_protocol"
        assert updated.cdn_provider is None
        assert updated.trusted_proxy_cidrs == ["198.51.100.0/24"]
    finally:
        db.close()


def test_migration_is_single_extension_of_access_group_head():
    migration = Path("app/db/migrations/versions/f6b2c9d4e701_add_node_ip_source_policy.py").read_text(encoding="utf-8")
    assert 'revision = "f6b2c9d4e701"' in migration
    assert 'down_revision = "c9e1f4a7b203"' in migration
    assert 'server_default="direct"' in migration


def test_frontend_exposes_safe_node_ip_source_controls():
    context = Path("app/dashboard/src/contexts/NodesContext.tsx").read_text(encoding="utf-8")
    modal = Path("app/dashboard/src/components/NodesModal.tsx").read_text(encoding="utf-8")
    assert 'z.enum(["direct", "trusted_xff", "proxy_protocol"])' in context
    assert 'name="ip_source_mode"' in modal
    assert 'name="trusted_proxy_cidrs"' in modal
    assert 'nodes.ipSourceRuntimePending' in modal
''', encoding="utf-8")
