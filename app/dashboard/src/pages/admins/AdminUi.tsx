import { Box, Button, Card, HStack, Text, chakra } from "@chakra-ui/react";
import { UserGroupIcon } from "@heroicons/react/24/outline";
import { FC, ReactNode } from "react";

export const AdminsIcon = chakra(UserGroupIcon, { baseStyle: { w: 5, h: 5 } });

export const billingModeLabels: Record<string, string> = {
  LEGACY_COMPAT: "قدیمی",
  SEAT_CREDIT: "ظرفیت دستگاه",
  USED_TRAFFIC: "مصرف واقعی",
  ALLOCATED_TRAFFIC: "حجم ساخته‌شده",
  USER_CREDIT: "سقف اکانت",
};

export const panel = {
  bg: "var(--panel-surface)",
  borderColor: "var(--panel-border)",
};

export const control = {
  bg: "var(--panel-surface)",
  borderColor: "var(--panel-border)",
  _hover: { borderColor: "var(--panel-border-strong)" },
  _focusVisible: { borderColor: "var(--panel-accent)", boxShadow: "0 0 0 2px var(--panel-accent-soft)" },
};

const statusMeta = {
  ACTIVE: { label: "فعال", dot: "var(--panel-success)", text: "var(--panel-success)", bg: "var(--panel-success-soft)", border: "var(--panel-success-border)" },
  SUSPENDED: { label: "فریز", dot: "var(--panel-warning)", text: "var(--panel-warning)", bg: "var(--panel-warning-soft)", border: "var(--panel-warning-border)" },
  DISABLED: { label: "غیرفعال", dot: "var(--panel-text-muted)", text: "var(--panel-text-muted)", bg: "var(--panel-muted-soft)", border: "var(--panel-border-strong)" },
} as const;

export const SummaryStat: FC<{ label: string; value: string; hint: string; tone?: string }> = ({
  label,
  value,
  hint,
  tone = "var(--panel-text)",
}) => (
  <Card
    p={{ base: 3, md: 4 }}
    minH="104px"
    bg={panel.bg}
    borderWidth="1px"
    borderColor={panel.borderColor}
    borderRadius="16px"
    boxShadow="none"
  >
    <Text color="var(--panel-text-muted)" fontSize="xs" fontWeight="700">{label}</Text>
    <Text mt={2} color={tone} fontSize={{ base: "xl", md: "2xl" }} fontWeight="800" sx={{ fontVariantNumeric: "tabular-nums" }}>
      {value}
    </Text>
    <Text mt={1.5} color="var(--panel-text-muted)" fontSize="11px">{hint}</Text>
  </Card>
);

export const AdminAvatar: FC<{ username: string; owner: boolean }> = ({ username, owner }) => (
  <Box
    flexShrink={0}
    w="38px"
    h="38px"
    display="grid"
    placeItems="center"
    borderRadius="12px"
    bg={owner ? "var(--panel-accent-soft)" : "var(--panel-muted-soft)"}
    borderWidth="1px"
    borderColor={owner ? "var(--panel-accent-border)" : "var(--panel-border)"}
    color={owner ? "var(--panel-accent)" : "var(--panel-text-body)"}
    fontWeight="800"
    textTransform="uppercase"
    transition="transform .16s ease, border-color .16s ease"
    _groupHover={{ transform: "translateY(-1px)", borderColor: "var(--panel-accent)" }}
  >
    {username.slice(0, 1)}
  </Box>
);

export const StatusPill: FC<{ status: keyof typeof statusMeta }> = ({ status }) => {
  const meta = statusMeta[status];
  return (
    <HStack w="fit-content" spacing={1.5} px={2.5} py={1.25} bg={meta.bg} borderWidth="1px" borderColor={meta.border} borderRadius="full">
      <Box boxSize="6px" borderRadius="full" bg={meta.dot} />
      <Text color={meta.text} fontSize="12px" fontWeight="800">{meta.label}</Text>
    </HStack>
  );
};

export const FilterButton: FC<{ active: boolean; onClick: () => void; children: ReactNode }> = ({ active, onClick, children }) => (
  <Button
    size="sm"
    h="34px"
    px={3}
    borderRadius="12px"
    variant="outline"
    bg={active ? "var(--panel-accent-soft)" : "transparent"}
    borderColor={active ? "var(--panel-accent-border)" : "var(--panel-border)"}
    color={active ? "var(--panel-accent)" : "var(--panel-text-body)"}
    fontSize="12px"
    fontWeight={active ? "800" : "600"}
    transition="background .14s ease, border-color .14s ease, transform .14s ease"
    _hover={{
      bg: active ? "var(--panel-accent-soft-strong)" : "var(--panel-row-hover)",
      borderColor: active ? "var(--panel-accent)" : "var(--panel-border-strong)",
      transform: "translateY(-1px)",
    }}
    _active={{ transform: "translateY(0)" }}
    onClick={onClick}
  >
    {children}
  </Button>
);

export const DetailChip: FC<{ label: string; value: string; tone?: string }> = ({ label, value, tone = "var(--panel-text-body)" }) => (
  <HStack
    spacing={1.5}
    px={2.5}
    h="28px"
    borderWidth="1px"
    borderColor="var(--panel-border)"
    bg="var(--panel-muted-soft)"
    borderRadius="12px"
    whiteSpace="nowrap"
  >
    <Text color="var(--panel-text-muted)" fontSize="10px" fontWeight="700">{label}</Text>
    <Text color={tone} fontSize="11px" fontWeight="700">{value}</Text>
  </HStack>
);
