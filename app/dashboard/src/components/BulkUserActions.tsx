import {
  Alert,
  AlertDescription,
  Badge,
  Box,
  Button,
  Checkbox,
  Divider,
  Flex,
  FormControl,
  FormLabel,
  HStack,
  IconButton,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Select,
  Stack,
  Text,
  useDisclosure,
  useToast,
} from "@chakra-ui/react";
import {
  BoltIcon,
  CalendarDaysIcon,
  ChevronDownIcon,
  CircleStackIcon,
  NoSymbolIcon,
  TrashIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { useDashboard } from "contexts/DashboardContext";
import useGetUser from "hooks/useGetUser";
import { FC, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { fetch } from "service/http";
import { HierarchyAdminNode } from "types/Admin";
import { localizedApiError } from "utils/apiError";
import {
  BulkJobResponse,
  BulkPreviewResponse,
  BulkTargetScope,
  BulkUserOperation,
  User,
} from "types/User";
import { CheckedBulkDialog } from "./CheckedBulkDialog";

type BulkUserActionsProps = {
  users: User[];
  visibleCount: number;
  allVisibleSelected: boolean;
  onToggleAll: (selected: boolean) => void;
  onClear: () => void;
};

type ActionDefinition = {
  operation: BulkUserOperation;
  labelKey: string;
  kind: "status" | "data" | "days" | "data_days" | "delete";
  destructive?: boolean;
};

const actionDefinitions: ActionDefinition[] = [
  {
    operation: "activate",
    labelKey: "usersTable.bulkActivate",
    kind: "status",
  },
  {
    operation: "deactivate",
    labelKey: "usersTable.bulkDeactivate",
    kind: "status",
  },
  { operation: "add_data", labelKey: "usersTable.bulkAddVolume", kind: "data" },
  {
    operation: "subtract_data",
    labelKey: "usersTable.bulkSubtractVolume",
    kind: "data",
  },
  { operation: "add_days", labelKey: "usersTable.bulkAddDays", kind: "days" },
  {
    operation: "subtract_days",
    labelKey: "usersTable.bulkSubtractDays",
    kind: "days",
  },
  {
    operation: "add_data_and_days",
    labelKey: "usersTable.bulkAddVolumeAndDays",
    kind: "data_days",
  },
  {
    operation: "delete",
    labelKey: "usersTable.bulkDeleteSelected",
    kind: "delete",
    destructive: true,
  },
];

const dataUnits = {
  MB: 1024 ** 2,
  GB: 1024 ** 3,
  TB: 1024 ** 4,
} as const;

const getErrorMessage = localizedApiError;

type BulkActionDialogProps = {
  action: ActionDefinition | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  isOwner: boolean;
};

type AdminOption = { id: number; username: string; depth: number };

const flattenAdmins = (
  nodes: HierarchyAdminNode[],
  depth = 0
): AdminOption[] =>
  nodes.flatMap((node) => [
    { id: node.id, username: node.username, depth },
    ...flattenAdmins(node.children || [], depth + 1),
  ]);

const BulkActionDialog: FC<BulkActionDialogProps> = ({
  action,
  isOpen,
  onClose,
  onSuccess,
  isOwner,
}) => {
  const { t, i18n } = useTranslation();
  const toast = useToast();
  const [amount, setAmount] = useState("1");
  const [daysAmount, setDaysAmount] = useState("30");
  const [unit, setUnit] = useState<keyof typeof dataUnits>("GB");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [scope, setScope] = useState<BulkTargetScope | "">("");
  const [selectedAdminIds, setSelectedAdminIds] = useState<number[]>([]);
  const [adminOptions, setAdminOptions] = useState<AdminOption[]>([]);
  const [preview, setPreview] = useState<BulkPreviewResponse | null>(null);
  const [result, setResult] = useState<BulkJobResponse | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setAmount(action?.kind === "days" ? "30" : "1");
    setDaysAmount("30");
    setUnit("GB");
    setScope("");
    setSelectedAdminIds([]);
    setPreview(null);
    setResult(null);
    fetch<HierarchyAdminNode[]>("/admin-management/tree")
      .then((tree) => setAdminOptions(flattenAdmins(tree)))
      .catch(() => setAdminOptions([]));
  }, [action, isOpen]);

  useEffect(() => {
    if (!isOpen || !scope) {
      setPreview(null);
      return;
    }
    if (scope !== "ALL_USERS" && selectedAdminIds.length === 0) {
      setPreview(null);
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setIsPreviewing(true);
      try {
        const value = await fetch<BulkPreviewResponse>("/users/bulk/preview", {
          method: "POST",
          body: {
            target_scope: scope,
            selected_admin_ids:
              scope === "ALL_USERS" ? [] : selectedAdminIds,
          },
          signal: controller.signal,
        });
        setPreview(value);
      } catch (error) {
        if (!controller.signal.aborted) {
          setPreview(null);
          toast({
            title: "پیش‌نمایش هدف‌ها ناموفق بود",
            description: getErrorMessage(error),
            status: "error",
          });
        }
      } finally {
        if (!controller.signal.aborted) setIsPreviewing(false);
      }
    }, 300);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [isOpen, scope, selectedAdminIds, toast]);

  if (!action) return null;

  const numericAmount = Number(amount);
  const numericDays = Number(daysAmount);
  const needsAmount =
    action.kind === "data" ||
    action.kind === "days" ||
    action.kind === "data_days";
  const validAmount =
    !needsAmount ||
    (Number.isFinite(numericAmount) &&
      numericAmount > 0 &&
      (action.kind !== "data_days" ||
        (Number.isFinite(numericDays) && numericDays > 0)));

  const executeUntilSettled = async (
    operationId: string,
    retryFailed: boolean
  ) => {
    let current = await fetch<BulkJobResponse>(
      `/users/bulk/jobs/${operationId}/execute`,
      {
        method: "POST",
        body: { chunk_size: 100, retry_failed: retryFailed },
      }
    );
    while (current.has_more) {
      current = await fetch<BulkJobResponse>(
        `/users/bulk/jobs/${operationId}/execute`,
        {
          method: "POST",
          body: { chunk_size: 100, retry_failed: retryFailed },
        }
      );
    }
    return current;
  };

  const submit = async () => {
    if (!validAmount || !scope || !preview || preview.resolved_target_count < 1 || isSubmitting) return;
    setIsSubmitting(true);
    try {
      const requestAmount =
        action.kind === "data" || action.kind === "data_days"
          ? Math.round(numericAmount * dataUnits[unit])
          : undefined;
      const operationId = `bulk-user-${crypto.randomUUID()}`;
      await fetch<BulkJobResponse>("/users/bulk/jobs", {
        method: "POST",
        body: {
          operation_id: operationId,
          operation: action.operation,
          target_scope: scope,
          selected_admin_ids:
            scope === "ALL_USERS" ? [] : selectedAdminIds,
          data_amount: requestAmount,
          days_amount:
            action.kind === "days"
              ? Math.round(numericAmount)
              : action.kind === "data_days"
              ? Math.round(numericDays)
              : undefined,
        },
      });
      const completed = await executeUntilSettled(operationId, false);
      setResult(completed);
      toast({
        title: t("usersTable.bulkSuccess", { count: completed.success }),
        description: `ناموفق: ${completed.failed} · نادیده‌گرفته‌شده: ${completed.skipped}`,
        status: completed.failed ? "warning" : "success",
        duration: 4000,
        isClosable: true,
      });
      onSuccess();
    } catch (error) {
      toast({
        title: t("usersTable.bulkFailed"),
        description: getErrorMessage(error),
        status: "error",
        duration: 6000,
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const retryFailures = async () => {
    if (!result || isSubmitting) return;
    setIsSubmitting(true);
    try {
      const completed = await executeUntilSettled(result.operation_id, true);
      setResult(completed);
      onSuccess();
    } catch (error) {
      toast({ title: "Retry ناموفق بود", description: getErrorMessage(error), status: "error" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={isSubmitting ? () => undefined : onClose}
      isCentered
    >
      <ModalOverlay bg="blackAlpha.700" backdropFilter="blur(5px)" />
      <ModalContent dir={i18n.dir()} mx={3} maxW="640px">
        <ModalHeader pe={12}>{t(action.labelKey)}</ModalHeader>
        <ModalCloseButton isDisabled={isSubmitting} />
        <ModalBody>
          <Stack spacing={4}>
            <FormControl isRequired>
              <FormLabel>دامنه هدف</FormLabel>
              <Select
                placeholder="دامنه را صریحاً انتخاب کنید"
                value={scope}
                onChange={(event) => {
                  setScope(event.target.value as BulkTargetScope | "");
                  setSelectedAdminIds([]);
                  setResult(null);
                }}
                minH="44px"
              >
                {isOwner && <option value="ALL_USERS">همه کاربران سیستم</option>}
                <option value="SELECTED_ADMINS_DIRECT">فقط کاربران مستقیم ادمین‌های انتخابی</option>
                <option value="SELECTED_ADMINS_SUBTREE">کاربران ادمین‌های انتخابی و زیرمجموعه‌های آن‌ها</option>
              </Select>
            </FormControl>

            {scope && scope !== "ALL_USERS" && (
              <FormControl isRequired>
                <FormLabel>ادمین‌های هدف</FormLabel>
                <Stack
                  maxH="180px"
                  overflowY="auto"
                  spacing={1}
                  p={3}
                  borderWidth="1px"
                  borderColor="var(--panel-border)"
                  borderRadius="10px"
                >
                  {adminOptions.map((option) => (
                    <Checkbox
                      key={option.id}
                      minH="44px"
                      isChecked={selectedAdminIds.includes(option.id)}
                      onChange={(event) =>
                        setSelectedAdminIds((current) =>
                          event.target.checked
                            ? [...current, option.id].sort((a, b) => a - b)
                            : current.filter((id) => id !== option.id)
                        )
                      }
                    >
                      <Text ps={`${option.depth * 12}px`} dir="ltr">{option.username}</Text>
                    </Checkbox>
                  ))}
                </Stack>
              </FormControl>
            )}

            <Alert
              status={action.destructive ? "error" : "info"}
              variant="subtle"
              borderRadius="10px"
              borderWidth="1px"
              borderColor={action.destructive ? "red.700" : "whiteAlpha.200"}
            >
              <AlertDescription fontSize="sm" lineHeight="1.8">
                {action.destructive
                  ? t("usersTable.bulkDeleteWarning", {
                      count: preview?.resolved_target_count || 0,
                    })
                  : t("usersTable.bulkAffected", {
                      count: preview?.resolved_target_count || 0,
                    })}
              </AlertDescription>
            </Alert>

            <Text fontSize="sm" color="var(--panel-text-body)" aria-live="polite">
              {isPreviewing
                ? "در حال محاسبه هدف‌ها…"
                : preview
                ? `تعداد کاربران هدف: ${preview.resolved_target_count}`
                : "برای اجرا ابتدا دامنه معتبر انتخاب کنید."}
            </Text>

            {(action.kind === "data" || action.kind === "data_days") && (
              <FormControl isRequired>
                <FormLabel>{t("usersTable.bulkVolumeAmount")}</FormLabel>
                <HStack dir="ltr">
                  <Input
                    type="number"
                    min="0.01"
                    step="0.25"
                    value={amount}
                    onChange={(event) => setAmount(event.target.value)}
                    textAlign="start"
                  />
                  <Select
                    value={unit}
                    onChange={(event) =>
                      setUnit(event.target.value as keyof typeof dataUnits)
                    }
                    w="110px"
                  >
                    <option value="MB">MB</option>
                    <option value="GB">GB</option>
                    <option value="TB">TB</option>
                  </Select>
                </HStack>
              </FormControl>
            )}

            {(action.kind === "days" || action.kind === "data_days") && (
              <FormControl isRequired>
                <FormLabel>{t("usersTable.bulkDaysAmount")}</FormLabel>
                <Input
                  type="number"
                  min="1"
                  step="1"
                  value={action.kind === "data_days" ? daysAmount : amount}
                  onChange={(event) =>
                    action.kind === "data_days"
                      ? setDaysAmount(event.target.value)
                      : setAmount(event.target.value)
                  }
                  dir="ltr"
                />
              </FormControl>
            )}

            {result && (
              <Box p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px">
                <Text fontWeight="700">گزارش عملیات: {result.status}</Text>
                <Text fontSize="sm" mt={1}>
                  کل {result.total} · موفق {result.success} · ناموفق {result.failed} · نادیده‌گرفته‌شده {result.skipped}
                </Text>
                <Stack mt={2} spacing={1} maxH="150px" overflowY="auto">
                  {result.targets
                    .filter((target) => target.status !== "SUCCESS")
                    .slice(0, 20)
                    .map((target) => (
                      <Text key={target.target_id} fontSize="xs" dir="ltr">
                        {target.target_username}: {target.error_code ? localizedApiError({ data: { detail: { code: target.error_code } } }) : target.status}
                      </Text>
                    ))}
                </Stack>
              </Box>
            )}
          </Stack>
        </ModalBody>
        <ModalFooter gap={2} flexWrap="wrap">
          <Button variant="ghost" onClick={onClose} isDisabled={isSubmitting}>
            {t("cancel")}
          </Button>
          {result && result.failed > 0 && (
            <Button variant="outline" onClick={retryFailures} isLoading={isSubmitting}>
              تلاش دوباره برای خطاهای قابل‌تکرار
            </Button>
          )}
          <Button
            colorScheme={action.destructive ? "red" : "primary"}
            onClick={submit}
            isLoading={isSubmitting}
            isDisabled={
              !validAmount ||
              !scope ||
              isPreviewing ||
              !preview ||
              preview.resolved_target_count < 1
            }
          >
            {t("usersTable.bulkConfirm")}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

type ExpiredCleanupDialogProps = {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  trialOnly?: boolean;
};

const ExpiredCleanupDialog: FC<ExpiredCleanupDialogProps> = ({
  isOpen,
  onClose,
  onSuccess,
  trialOnly = false,
}) => {
  const { t, i18n } = useTranslation();
  const toast = useToast();
  const [days, setDays] = useState("30");
  const [matches, setMatches] = useState<string[]>([]);
  const [matchCount, setMatchCount] = useState(0);
  const [isChecking, setIsChecking] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const cutoff = useMemo(() => {
    const value = Number(days);
    if (!Number.isFinite(value) || value < 1) return null;
    return new Date(
      Date.now() - Math.round(value) * 86400 * 1000
    ).toISOString();
  }, [days]);

  useEffect(() => {
    if (!isOpen || !cutoff) {
      setMatches([]);
      setMatchCount(0);
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setIsChecking(true);
      try {
        if (trialOnly) {
          const result = await fetch<{ count: number; usernames: string[] }>("/trials/cleanup/preview", {
            query: { expired_before: cutoff },
            signal: controller.signal,
          });
          setMatches(result.usernames);
          setMatchCount(result.count);
        } else {
          const result = await fetch<string[]>("/users/expired", {
            query: { expired_before: cutoff },
            signal: controller.signal,
          });
          setMatches(result);
          setMatchCount(result.length);
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setMatches([]);
          setMatchCount(0);
          toast({
            title: t("usersTable.bulkFailed"),
            description: getErrorMessage(error),
            status: "error",
          });
        }
      } finally {
        if (!controller.signal.aborted) setIsChecking(false);
      }
    }, 350);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [cutoff, isOpen, t, toast, trialOnly]);

  const removeExpired = async () => {
    if (!cutoff || matches.length === 0 || isDeleting) return;
    setIsDeleting(true);
    try {
      const removed = trialOnly
        ? (await fetch<{ count: number; usernames: string[] }>("/trials/cleanup", {
            method: "POST",
            body: { expired_before: cutoff, idempotency_key: `trial-cleanup-${crypto.randomUUID()}` },
          })).usernames
        : await fetch<string[]>("/users/expired", {
            method: "DELETE",
            query: { expired_before: cutoff },
          });
      toast({
        title: t("usersTable.cleanupSuccess", { count: removed.length }),
        status: "success",
        duration: 5000,
        isClosable: true,
      });
      onSuccess();
      onClose();
    } catch (error) {
      toast({
        title: t("usersTable.bulkFailed"),
        description: getErrorMessage(error),
        status: "error",
        duration: 6000,
        isClosable: true,
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={isDeleting ? () => undefined : onClose}
      isCentered
    >
      <ModalOverlay bg="blackAlpha.700" backdropFilter="blur(5px)" />
      <ModalContent dir={i18n.dir()} mx={3} maxW="500px">
        <ModalHeader pe={12}>{trialOnly ? "پاک‌سازی اکانت‌های تست منقضی" : t("usersTable.cleanupExpired")}</ModalHeader>
        <ModalCloseButton isDisabled={isDeleting} />
        <ModalBody>
          <Stack spacing={4}>
            <FormControl isRequired>
              <FormLabel>{t("usersTable.cleanupDays")}</FormLabel>
              <Input
                type="number"
                min="1"
                step="1"
                value={days}
                onChange={(event) => setDays(event.target.value)}
                dir="ltr"
              />
            </FormControl>
            <Alert
              status={matches.length > 0 ? "error" : "info"}
              borderRadius="10px"
              borderWidth="1px"
              borderColor={matches.length > 0 ? "red.700" : "whiteAlpha.200"}
            >
              <AlertDescription fontSize="sm" lineHeight="1.8">
                {isChecking
                  ? t("usersTable.cleanupChecking")
                  : t("usersTable.cleanupMatches", { count: matchCount })}
              </AlertDescription>
            </Alert>
            <Text color="var(--panel-text-muted)" fontSize="xs" lineHeight="1.8">
              {t("usersTable.cleanupPermanent")}
            </Text>
          </Stack>
        </ModalBody>
        <ModalFooter gap={2} flexWrap="wrap">
          <Button variant="ghost" onClick={onClose} isDisabled={isDeleting}>
            {t("cancel")}
          </Button>
          <Button
            colorScheme="red"
            leftIcon={<TrashIcon width="18px" aria-hidden="true" />}
            onClick={removeExpired}
            isLoading={isDeleting}
            isDisabled={isChecking || matches.length === 0 || !cutoff}
          >
            {t("usersTable.cleanupConfirm", { count: matches.length })}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export const BulkUserActions: FC<BulkUserActionsProps> = ({
  users,
  visibleCount,
  allVisibleSelected,
  onToggleAll,
  onClear,
}) => {
  const { t, i18n } = useTranslation();
  const actionDialog = useDisclosure();
  const cleanupDialog = useDisclosure();
  const trialCleanupDialog = useDisclosure();
  const [action, setAction] = useState<ActionDefinition | null>(null);
  const { refetchUsers } = useDashboard();
  const { userData } = useGetUser();
  const hasSelection = users.length > 0;
  const fixedCenter = i18n.dir() === "rtl" ? "calc(50% - 136px)" : "calc(50% + 136px)";
  const openAction = (definition: ActionDefinition) => {
    setAction(definition);
    actionDialog.onOpen();
  };

  const success = () => {
    onClear();
    refetchUsers();
  };

  return (
    <>
      <Box w="full">
        <Flex
          dir={i18n.dir()}
          data-sticky-bulk-actions={hasSelection ? "true" : undefined}
          role={hasSelection ? "region" : undefined}
          aria-label={hasSelection ? "عملیات گروهی کاربران انتخاب‌شده" : undefined}
          position={hasSelection ? "fixed" : "relative"}
          bottom={hasSelection ? "max(12px, env(safe-area-inset-bottom))" : undefined}
          left={hasSelection ? { base: "50%", lg: fixedCenter } : undefined}
          transform={hasSelection ? "translateX(-50%)" : undefined}
          zIndex={hasSelection ? 1200 : "auto"}
          w={hasSelection ? { base: "calc(100vw - 24px)", lg: "min(920px, calc(100vw - 320px))" } : "full"}
          maxW={hasSelection ? "920px" : "none"}
          mt={hasSelection ? 0 : 4}
          px={{ base: 2.5, md: 3 }}
          py={{ base: 2.5, md: 2.5 }}
          minW={0}
          align="center"
          justify="space-between"
          gap={{ base: 2, md: 3 }}
          wrap="wrap"
          borderRadius={hasSelection ? "16px" : "12px"}
          bg={hasSelection ? "var(--panel-surface)" : "var(--panel-nested)"}
          borderWidth="1px"
          borderColor={hasSelection ? "var(--panel-accent-border)" : "var(--panel-border)"}
          boxShadow={hasSelection ? "var(--shadow-elevated)" : "none"}
          backdropFilter={hasSelection ? "blur(18px)" : undefined}
        >
          <HStack
            spacing={{ base: 2, md: 3 }}
            minW={0}
            w={{ base: "full", md: "auto" }}
            justify={{ base: "space-between", md: "flex-start" }}
            flexWrap="nowrap"
          >
            <Checkbox
              isChecked={allVisibleSelected}
              isIndeterminate={hasSelection && !allVisibleSelected}
              onChange={(event) => onToggleAll(event.target.checked)}
              colorScheme="primary"
              flexShrink={0}
            >
              <Text fontSize={{ base: "xs", md: "sm" }} fontWeight="700" whiteSpace="nowrap">
                {allVisibleSelected
                  ? t("usersTable.deselectAll")
                  : t("usersTable.selectAll", { count: visibleCount })}
              </Text>
            </Checkbox>
            <Badge
              px={2.5}
              py={1}
              flexShrink={0}
              borderRadius="full"
              bg={hasSelection ? "var(--panel-accent-soft)" : "var(--panel-surface)"}
              color={hasSelection ? "var(--panel-accent)" : "var(--panel-text-muted)"}
              textTransform="none"
            >
              {t("usersTable.selectedCount", { count: users.length })}
            </Badge>
          </HStack>

          <HStack
            spacing={2}
            w={{ base: "full", md: "auto" }}
            maxW="full"
            overflowX={{ base: "auto", md: "visible" }}
            flexWrap={{ base: "nowrap", md: "wrap" }}
            justify={{ base: "flex-start", md: "flex-end" }}
            pb={{ base: 1, md: 0 }}
            sx={{ scrollbarWidth: "thin" }}
          >
            <Menu placement="bottom-end">
              <MenuButton
                as={Button}
                size="sm"
                flexShrink={0}
                variant="outline"
                color="var(--panel-text-body)"
                borderColor="var(--panel-border)"
                rightIcon={<ChevronDownIcon width="15px" aria-hidden="true" />}
              >
                پاک‌سازی
              </MenuButton>
              <MenuList minW="220px" bg="var(--panel-surface)" borderColor="var(--panel-border)" boxShadow="var(--shadow-elevated)">
                <MenuItem bg="transparent" _hover={{ bg: "var(--panel-row-hover)" }} icon={<TrashIcon width="16px" />} onClick={trialCleanupDialog.onOpen}>
                  پاک‌سازی اکانت تست
                </MenuItem>
                {userData.is_sudo && (
                  <MenuItem bg="transparent" color="var(--panel-danger)" _hover={{ bg: "var(--panel-danger-soft)" }} icon={<TrashIcon width="16px" />} onClick={cleanupDialog.onOpen}>
                    {t("usersTable.cleanupExpired")}
                  </MenuItem>
                )}
              </MenuList>
            </Menu>

            {hasSelection && (
              <>
                <Menu placement="bottom-end">
                  <MenuButton
                    as={Button}
                    size="sm"
                    flexShrink={0}
                    variant="outline"
                    color="var(--panel-success)"
                    borderColor="var(--panel-success-border)"
                    bg="var(--panel-success-soft)"
                    rightIcon={<ChevronDownIcon width="15px" aria-hidden="true" />}
                  >
                    وضعیت
                  </MenuButton>
                  <MenuList minW="210px" bg="var(--panel-surface)" borderColor="var(--panel-border)" boxShadow="var(--shadow-elevated)">
                    <MenuItem bg="transparent" _hover={{ bg: "var(--panel-success-soft)" }} icon={<BoltIcon width="16px" />} onClick={() => openAction(actionDefinitions[0])}>
                      {t(actionDefinitions[0].labelKey)}
                    </MenuItem>
                    <MenuItem bg="transparent" _hover={{ bg: "var(--panel-warning-soft)" }} icon={<NoSymbolIcon width="16px" />} onClick={() => openAction(actionDefinitions[1])}>
                      {t(actionDefinitions[1].labelKey)}
                    </MenuItem>
                  </MenuList>
                </Menu>

                <Menu placement="bottom-end">
                  <MenuButton
                    as={Button}
                    size="sm"
                    flexShrink={0}
                    variant="outline"
                    color="var(--panel-accent)"
                    borderColor="var(--panel-accent-border)"
                    bg="var(--panel-accent-soft)"
                    rightIcon={<ChevronDownIcon width="15px" aria-hidden="true" />}
                  >
                    اعتبار
                  </MenuButton>
                  <MenuList minW="230px" bg="var(--panel-surface)" borderColor="var(--panel-border)" boxShadow="var(--shadow-elevated)">
                    <MenuItem bg="transparent" _hover={{ bg: "var(--panel-row-hover)" }} icon={<CircleStackIcon width="16px" />} onClick={() => openAction(actionDefinitions[2])}>{t(actionDefinitions[2].labelKey)}</MenuItem>
                    <MenuItem bg="transparent" _hover={{ bg: "var(--panel-row-hover)" }} icon={<CircleStackIcon width="16px" />} onClick={() => openAction(actionDefinitions[3])}>{t(actionDefinitions[3].labelKey)}</MenuItem>
                    <Divider />
                    <MenuItem bg="transparent" _hover={{ bg: "var(--panel-row-hover)" }} icon={<CalendarDaysIcon width="16px" />} onClick={() => openAction(actionDefinitions[4])}>{t(actionDefinitions[4].labelKey)}</MenuItem>
                    <MenuItem bg="transparent" _hover={{ bg: "var(--panel-row-hover)" }} icon={<CalendarDaysIcon width="16px" />} onClick={() => openAction(actionDefinitions[5])}>{t(actionDefinitions[5].labelKey)}</MenuItem>
                    <MenuItem bg="transparent" _hover={{ bg: "var(--panel-row-hover)" }} icon={<CalendarDaysIcon width="16px" />} onClick={() => openAction(actionDefinitions[6])}>{t(actionDefinitions[6].labelKey)}</MenuItem>
                  </MenuList>
                </Menu>

                <Button
                  size="sm"
                  flexShrink={0}
                  variant="outline"
                  color="var(--panel-danger)"
                  borderColor="var(--panel-danger-border)"
                  bg="var(--panel-danger-soft)"
                  leftIcon={<TrashIcon width="17px" aria-hidden="true" />}
                  onClick={() => openAction(actionDefinitions[7])}
                >
                  {t(actionDefinitions[7].labelKey)}
                </Button>

                <IconButton
                  size="sm"
                  flexShrink={0}
                  variant="ghost"
                  aria-label={t("usersTable.deselectAll")}
                  icon={<XMarkIcon width="18px" aria-hidden="true" />}
                  onClick={onClear}
                />
              </>
            )}
          </HStack>
        </Flex>
      </Box>

      <CheckedBulkDialog
        users={users}
        action={action}
        isOpen={actionDialog.isOpen}
        onClose={actionDialog.onClose}
        onSuccess={success}
      />
      {userData.is_sudo && (
        <ExpiredCleanupDialog
          isOpen={cleanupDialog.isOpen}
          onClose={cleanupDialog.onClose}
          onSuccess={success}
        />
      )}
      <ExpiredCleanupDialog
        trialOnly
        isOpen={trialCleanupDialog.isOpen}
        onClose={trialCleanupDialog.onClose}
        onSuccess={success}
      />
    </>
  );
};
