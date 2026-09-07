import {
  Badge,
  Box,
  Button,
  Divider,
  HStack,
  IconButton,
  Input,
  SimpleGrid,
  Stack,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tooltip,
  Tr,
  chakra,
} from "@chakra-ui/react";
import {
  ArrowPathIcon,
  PauseIcon,
  PencilSquareIcon,
  PlayIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import { FC, Fragment } from "react";
import { useTranslation } from "react-i18next";
import { ManagedAdmin } from "types/Admin";
import { formatBytes } from "utils/formatByte";
import { AdminAvatar, billingModeLabels, control, DetailChip, StatusPill } from "./AdminUi";

const EditIcon = chakra(PencilSquareIcon, { baseStyle: { w: 4, h: 4 } });
const DeleteIcon = chakra(TrashIcon, { baseStyle: { w: 4, h: 4 } });
const PauseActionIcon = chakra(PauseIcon, { baseStyle: { w: 4, h: 4 } });
const PlayActionIcon = chakra(PlayIcon, { baseStyle: { w: 4, h: 4 } });
const ResetIcon = chakra(ArrowPathIcon, { baseStyle: { w: 4, h: 4 } });

export type CreditOperation = "grant" | "reclaim";

type Props = {
  admins: ManagedAdmin[];
  currentUsername: string;
  hierarchyReady: boolean;
  creditAmounts: Record<string, string>;
  busy: boolean;
  onCreditAmountChange: (username: string, value: string) => void;
  onCredit: (item: ManagedAdmin, operation: CreditOperation) => void;
  onEdit: (item: ManagedAdmin) => void;
  onDelete: (item: ManagedAdmin) => void;
  onStatus: (item: ManagedAdmin) => void;
  onTrialReset: (item: ManagedAdmin) => void;
};

const creationModeLabel = (item: ManagedAdmin) => {
  if (item.user_creation_mode === "PLAN_ONLY") return "فقط پلن";
  if (item.user_creation_mode === "FREE_FORM") return "سفارشی";
  if (item.user_creation_mode === "FORM_ONLY") return "فقط فرم";
  return "پلن + سفارشی";
};

const limitText = (value: number | null | undefined, suffix = "") =>
  value == null ? "نامحدود" : `${value.toLocaleString("fa-IR")}${suffix}`;

const InlineDetails: FC<{ item: ManagedAdmin }> = ({ item }) => (
  <HStack spacing={1.5} flexWrap="wrap" rowGap={1.5}>
    <Text color="var(--panel-text-muted)" fontSize="11px" fontWeight="800" me={1}>اطلاعات:</Text>
    <DetailChip label="والد" value={item.parent_username || "ریشه"} />
    <DetailChip label="ساخت کاربر" value={creationModeLabel(item)} />
    <DetailChip label="مصرف کل" value={String(formatBytes(item.quota.lifetime_consumed_traffic))} />
    <DetailChip label="ساخت کل" value={String(formatBytes(item.quota.lifetime_created_traffic))} />
    <DetailChip label="عملیات مانده" value={limitText(item.quota.operation_allowance_remaining)} />
    <DetailChip label="مدت کاربر" value={limitText(item.policy.max_user_duration_days, " روز")} />
    <DetailChip label="انقضا" value={item.policy.expiry_date || "نامحدود"} />
    <DetailChip label="تلگرام" value={item.telegram_id?.toString() || "ثبت نشده"} />
    <Box w={{ base: "full", xl: "1px" }} h={{ base: "1px", xl: "24px" }} bg="whiteAlpha.100" mx={1} />
    <Text color="var(--panel-text-muted)" fontSize="11px" fontWeight="800" me={1}>دسترسی:</Text>
    <DetailChip label="ایجاد" value={item.policy.prevent_user_creation ? "مسدود" : "مجاز"} tone={item.policy.prevent_user_creation ? "red.300" : "green.300"} />
    <DetailChip label="حذف" value={item.policy.prevent_user_deletion ? "مسدود" : "مجاز"} tone={item.policy.prevent_user_deletion ? "red.300" : "green.300"} />
    <DetailChip label="ریست" value={item.policy.prevent_user_reset ? "مسدود" : "مجاز"} tone={item.policy.prevent_user_reset ? "red.300" : "green.300"} />
    <DetailChip label="نامحدود" value={item.policy.prevent_unlimited_traffic ? "مسدود" : "مجاز"} tone={item.policy.prevent_unlimited_traffic ? "orange.300" : "green.300"} />
  </HStack>
);

export const AdminTable: FC<Props> = ({
  admins,
  currentUsername,
  hierarchyReady,
  creditAmounts,
  busy,
  onCreditAmountChange,
  onCredit,
  onEdit,
  onDelete,
  onStatus,
  onTrialReset,
}) => {
  const { t } = useTranslation();

  const canEdit = (item: ManagedAdmin) =>
    hierarchyReady && (item.role !== "OWNER" || item.username === currentUsername);
  const canAct = (item: ManagedAdmin) =>
    hierarchyReady && item.role !== "OWNER" && item.username !== currentUsername;

  const statusActionLabel = (item: ManagedAdmin) => {
    if (item.account_status === "SUSPENDED") return "رفع فریز";
    if (item.account_status === "DISABLED") return "فعال‌سازی";
    return "فریز";
  };

  const RowActions: FC<{ item: ManagedAdmin }> = ({ item }) => {
    const amount = creditAmounts[item.username] || "";
    const validAmount = Number.isFinite(Number(amount)) && Number(amount) > 0;

    return (
      <HStack justify="end" spacing={2} minW="500px">
        {canAct(item) && (
          <HStack spacing={2} me={2}>
            <Button
              aria-label={`کاهش اعتبار ${item.username}`}
              size="sm"
              h="36px"
              minW="86px"
              px={3}
              gap={2}
              color="red.100"
              bg="rgba(239,68,68,.16)"
              borderWidth="1px"
              borderColor="rgba(248,113,113,.30)"
              borderRadius="12px"
              isDisabled={!validAmount || busy}
              onClick={() => onCredit(item, "reclaim")}
              transition="background .16s ease, border-color .16s ease, transform .16s ease"
              _hover={{ bg: "rgba(239,68,68,.25)", borderColor: "rgba(248,113,113,.48)", transform: "translateY(-1px)" }}
              _active={{ transform: "translateY(0)" }}
            >
              <Text as="span" fontSize="19px" lineHeight="1" fontWeight="400">−</Text>
              <Text as="span" fontSize="12px" fontWeight="800">کاهش</Text>
            </Button>

            <Input
              aria-label={`مبلغ اعتبار ${item.username}`}
              type="number"
              min={1}
              step={1000}
              inputMode="numeric"
              value={amount}
              onChange={(event) => onCreditAmountChange(item.username, event.target.value)}
              placeholder="مبلغ (تومان)"
              size="sm"
              dir="ltr"
              textAlign="center"
              w="126px"
              h="36px"
              px={2}
              borderRadius="12px"
              fontSize="11px"
              fontWeight="700"
              sx={{ fontVariantNumeric: "tabular-nums" }}
              {...control}
            />

            <Button
              aria-label={`افزایش اعتبار ${item.username}`}
              size="sm"
              h="36px"
              minW="86px"
              px={3}
              gap={2}
              color="green.100"
              bg="rgba(34,197,94,.16)"
              borderWidth="1px"
              borderColor="rgba(74,222,128,.30)"
              borderRadius="12px"
              isDisabled={!validAmount || busy}
              onClick={() => onCredit(item, "grant")}
              transition="background .16s ease, border-color .16s ease, transform .16s ease"
              _hover={{ bg: "rgba(34,197,94,.25)", borderColor: "rgba(74,222,128,.48)", transform: "translateY(-1px)" }}
              _active={{ transform: "translateY(0)" }}
            >
              <Text as="span" fontSize="19px" lineHeight="1" fontWeight="400">+</Text>
              <Text as="span" fontSize="12px" fontWeight="800">افزایش</Text>
            </Button>
          </HStack>
        )}

        <Tooltip label="ویرایش" hasArrow>
          <IconButton
            aria-label={`ویرایش ${item.username}`}
            icon={<EditIcon />}
            size="sm"
            minW="36px"
            h="36px"
            color="blue.100"
            bg="rgba(37,99,235,.18)"
            borderWidth="1px"
            borderColor="rgba(96,165,250,.22)"
            borderRadius="12px"
            isDisabled={!canEdit(item)}
            onClick={() => onEdit(item)}
            _hover={{ bg: "rgba(37,99,235,.28)", transform: "translateY(-1px)" }}
            _active={{ transform: "translateY(0)" }}
          />
        </Tooltip>

        {canAct(item) && (
          <>
            <Tooltip label={statusActionLabel(item)} hasArrow>
              <IconButton
                aria-label={`${statusActionLabel(item)} ${item.username}`}
                icon={item.account_status === "ACTIVE" ? <PauseActionIcon /> : <PlayActionIcon />}
                size="sm"
                minW="36px"
                h="36px"
                color={item.account_status === "ACTIVE" ? "orange.200" : "green.200"}
                bg={item.account_status === "ACTIVE" ? "rgba(245,158,11,.12)" : "rgba(34,197,94,.10)"}
                borderWidth="1px"
                borderColor={item.account_status === "ACTIVE" ? "rgba(245,158,11,.20)" : "rgba(74,222,128,.18)"}
                borderRadius="12px"
                isDisabled={busy}
                onClick={() => onStatus(item)}
                _hover={{ bg: item.account_status === "ACTIVE" ? "rgba(245,158,11,.20)" : "rgba(34,197,94,.18)", transform: "translateY(-1px)" }}
                _active={{ transform: "translateY(0)" }}
              />
            </Tooltip>

            {item.trial_quota_limit > 0 && (
              <Tooltip label="بازنشانی سهمیه تست" hasArrow>
                <IconButton
                  aria-label={`بازنشانی سهمیه تست ${item.username}`}
                  icon={<ResetIcon />}
                  size="sm"
                  minW="36px"
                  h="36px"
                  color="cyan.200"
                  bg="rgba(6,182,212,.10)"
                  borderWidth="1px"
                  borderColor="rgba(34,211,238,.18)"
                  borderRadius="12px"
                  isDisabled={busy}
                  onClick={() => onTrialReset(item)}
                  _hover={{ bg: "rgba(6,182,212,.18)", transform: "translateY(-1px)" }}
                  _active={{ transform: "translateY(0)" }}
                />
              </Tooltip>
            )}

            <Tooltip label="حذف ادمین" hasArrow>
              <IconButton
                aria-label={`حذف ${item.username}`}
                icon={<DeleteIcon />}
                size="sm"
                minW="36px"
                h="36px"
                color="red.200"
                bg="rgba(239,68,68,.11)"
                borderWidth="1px"
                borderColor="rgba(248,113,113,.18)"
                borderRadius="12px"
                isDisabled={busy}
                onClick={() => onDelete(item)}
                _hover={{ bg: "rgba(239,68,68,.19)", transform: "translateY(-1px)" }}
                _active={{ transform: "translateY(0)" }}
              />
            </Tooltip>
          </>
        )}
      </HStack>
    );
  };

  return (
    <>
      <TableContainer display={{ base: "none", lg: "block" }} overflowX="auto">
        <Table size="sm" minW="1500px">
          <Thead bg="var(--panel-nested)">
            <Tr>
              <Th w="16%" fontSize="11px">ادمین</Th>
              <Th w="8%" fontSize="11px">وضعیت</Th>
              <Th w="13%" fontSize="11px">نقش و اعتبار</Th>
              <Th w="10%" fontSize="11px">کیف پول</Th>
              <Th w="9%" fontSize="11px">کاربران</Th>
              <Th w="7%" fontSize="11px">والد</Th>
              <Th w="37%" fontSize="11px" textAlign="end">عملیات سریع</Th>
            </Tr>
          </Thead>
          <Tbody>
            {admins.map((item) => {
              const isItemOwner = item.role === "OWNER";
              return (
                <Fragment key={item.username}>
                  <Tr
                    role="group"
                    data-disabled={item.account_status === "DISABLED" ? "true" : undefined}
                    transition="background-color .16s ease, box-shadow .16s ease"
                    _hover={{ bg: "var(--panel-row-hover)", boxShadow: "inset 3px 0 0 var(--panel-accent)" }}
                  >
                    <Td py={3}>
                      <HStack spacing={3}>
                        <AdminAvatar username={item.username} owner={isItemOwner} />
                        <Box minW={0}>
                          <Text dir="ltr" textAlign="start" fontSize="13px" fontWeight="800" noOfLines={1}>{item.username}</Text>
                          <Text mt={1} color="var(--panel-text-muted)" fontSize="11px" noOfLines={1}>
                            {item.user_creation_mode === "PLAN_ONLY" ? "ساخت کاربر فقط از پلن" : "ساخت کاربر سفارشی"}
                          </Text>
                        </Box>
                      </HStack>
                    </Td>
                    <Td><StatusPill status={item.account_status} /></Td>
                    <Td>
                      <HStack spacing={1.5} flexWrap="wrap">
                        <Badge variant="subtle" colorScheme={isItemOwner ? "purple" : "blue"} fontSize="11px" textTransform="none">
                          {t(`admins.role.${item.role}`)}
                        </Badge>
                        <Badge variant="outline" color="var(--panel-text-body)" borderColor="rgba(148,163,184,.25)" fontSize="11px" textTransform="none">
                          {billingModeLabels[item.policy.billing_mode] || item.policy.billing_mode}
                        </Badge>
                      </HStack>
                    </Td>
                    <Td>
                      <Text fontSize="13px" fontWeight="800" sx={{ fontVariantNumeric: "tabular-nums" }}>
                        {isItemOwner ? "بدون سقف" : item.policy.money_balance_toman.toLocaleString("fa-IR")}
                      </Text>
                      {!isItemOwner && <Text mt={1} color="var(--panel-text-muted)" fontSize="10px">تومان</Text>}
                    </Td>
                    <Td>
                      <Text fontSize="13px" fontWeight="800">
                        {item.quota.current_users.toLocaleString("fa-IR")}
                        <Text as="span" color="var(--panel-text-muted)" fontSize="11px" fontWeight="600">
                          {item.quota.max_users == null ? " / ∞" : ` / ${item.quota.max_users.toLocaleString("fa-IR")}`}
                        </Text>
                      </Text>
                      <Text mt={1} color="var(--panel-text-muted)" fontSize="10px">
                        {item.quota.remaining_user_slots == null ? "بدون سقف" : `${item.quota.remaining_user_slots.toLocaleString("fa-IR")} باقی‌مانده`}
                      </Text>
                    </Td>
                    <Td>
                      <Text dir="ltr" color={item.parent_username ? "gray.200" : "gray.500"} fontSize="12px" fontWeight="700" noOfLines={1}>
                        {item.parent_username || "—"}
                      </Text>
                    </Td>
                    <Td textAlign="end" py={2.5}><RowActions item={item} /></Td>
                  </Tr>
                  <Tr bg="rgba(2,8,23,.24)">
                    <Td colSpan={7} py={2} px={4} borderBottomColor="rgba(148,163,184,.14)">
                      <InlineDetails item={item} />
                    </Td>
                  </Tr>
                </Fragment>
              );
            })}
          </Tbody>
        </Table>
      </TableContainer>

      <Stack display={{ base: "flex", lg: "none" }} divider={<Divider borderColor="whiteAlpha.100" />} spacing={0}>
        {admins.map((item) => {
          const isItemOwner = item.role === "OWNER";
          const amount = creditAmounts[item.username] || "";
          const validAmount = Number.isFinite(Number(amount)) && Number(amount) > 0;

          return (
            <Box key={item.username} p={3.5} role="group" transition="background .16s ease" _hover={{ bg: "whiteAlpha.50" }}>
              <HStack justify="space-between" align="start" gap={3}>
                <HStack align="start" spacing={2.5} minW={0}>
                  <AdminAvatar username={item.username} owner={isItemOwner} />
                  <Box minW={0}>
                    <HStack spacing={2} flexWrap="wrap">
                      <Text dir="ltr" fontSize="14px" fontWeight="800">{item.username}</Text>
                      <StatusPill status={item.account_status} />
                    </HStack>
                    <Text mt={1} color="var(--panel-text-muted)" fontSize="11px" dir="ltr">{item.parent_username ? `↳ ${item.parent_username}` : "ادمین ریشه"}</Text>
                  </Box>
                </HStack>
                <HStack spacing={1}>
                  <IconButton aria-label="ویرایش" icon={<EditIcon />} size="sm" colorScheme="blue" variant="ghost" isDisabled={!canEdit(item)} onClick={() => onEdit(item)} />
                  {canAct(item) && (
                    <>
                      <IconButton aria-label={statusActionLabel(item)} icon={item.account_status === "ACTIVE" ? <PauseActionIcon /> : <PlayActionIcon />} size="sm" colorScheme="orange" variant="ghost" onClick={() => onStatus(item)} />
                      <IconButton aria-label="حذف" icon={<DeleteIcon />} size="sm" colorScheme="red" variant="ghost" onClick={() => onDelete(item)} />
                    </>
                  )}
                </HStack>
              </HStack>

              <SimpleGrid columns={2} gap={3} mt={3}>
                <Box>
                  <Text color="var(--panel-text-muted)" fontSize="10px">نقش / اعتبار</Text>
                  <HStack mt={1.5} spacing={1} flexWrap="wrap">
                    <Badge colorScheme={isItemOwner ? "purple" : "blue"} fontSize="9px">{t(`admins.role.${item.role}`)}</Badge>
                    <Badge variant="outline" borderColor="whiteAlpha.200" color="var(--panel-text-body)" fontSize="9px">{billingModeLabels[item.policy.billing_mode] || item.policy.billing_mode}</Badge>
                  </HStack>
                </Box>
                <Box>
                  <Text color="var(--panel-text-muted)" fontSize="10px">کیف پول</Text>
                  <Text mt={1.5} fontWeight="800">{isItemOwner ? "بدون سقف" : `${item.policy.money_balance_toman.toLocaleString("fa-IR")} تومان`}</Text>
                </Box>
              </SimpleGrid>

              {canAct(item) && (
                <Stack mt={3} spacing={2}>
                  <Input
                    type="number"
                    min={1}
                    step={1000}
                    inputMode="numeric"
                    value={amount}
                    onChange={(event) => onCreditAmountChange(item.username, event.target.value)}
                    placeholder="مبلغ اعتبار (تومان)"
                    size="sm"
                    dir="ltr"
                    textAlign="center"
                    borderRadius="12px"
                    {...control}
                  />
                  <HStack spacing={2}>
                    <Button
                      flex="1"
                      size="sm"
                      h="38px"
                      color="red.100"
                      bg="rgba(239,68,68,.16)"
                      borderWidth="1px"
                      borderColor="rgba(248,113,113,.30)"
                      borderRadius="12px"
                      isDisabled={!validAmount || busy}
                      onClick={() => onCredit(item, "reclaim")}
                      _hover={{ bg: "rgba(239,68,68,.25)" }}
                    >
                      <Text as="span" me={2} fontSize="18px">−</Text>
                      کاهش
                    </Button>
                    <Button
                      flex="1"
                      size="sm"
                      h="38px"
                      color="green.100"
                      bg="rgba(34,197,94,.16)"
                      borderWidth="1px"
                      borderColor="rgba(74,222,128,.30)"
                      borderRadius="12px"
                      isDisabled={!validAmount || busy}
                      onClick={() => onCredit(item, "grant")}
                      _hover={{ bg: "rgba(34,197,94,.25)" }}
                    >
                      <Text as="span" me={2} fontSize="18px">+</Text>
                      افزایش
                    </Button>
                  </HStack>
                </Stack>
              )}

              <Box mt={3} pt={3} borderTopWidth="1px" borderColor="whiteAlpha.100">
                <InlineDetails item={item} />
              </Box>
            </Box>
          );
        })}
      </Stack>
    </>
  );
};
