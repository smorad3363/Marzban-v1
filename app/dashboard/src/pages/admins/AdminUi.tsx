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
  bg: "rgba(10,17,29,.84)",
  borderColor: "rgba(148,163,184,.15)",
};

export const control = {
  bg: "rgba(2,8,23,.38)",
  borderColor: "rgba(148,163,184,.20)",
  _hover: { borderColor: "rgba(148,163,184,.34)" },
  _focusVisible: {
    borderColor: "blue.400",
    boxShadow: "0 0 0 2px rgba(59,130,246,.14)",
  },
};

const statusMeta = {
  ACTIVE: { label: "فعال", dot: "#4ade80", text: "green.300", bg: "rgba(34,197,94,.10)" },
  SUSPENDED: { label: "فریز", dot: "#f59e0b", text: "orange.300", bg: "rgba(245,158,11,.10)" },
  DISABLED: { label: "غیرفعال", dot: "#94a3b8", text: "gray.300", bg: "rgba(148,163,184,.10)" },
} as const;

export const SummaryStat: FC<{ label: string; value: string; hint: string; tone?: string }> = ({
  label,
  value,
  hint,
  tone = "gray.100",
}) => (
  <Card
    p={{ base: 3, md: 4 }}
    minH="104px"
    bg={panel.bg}
    borderWidth="1px"
    borderColor={panel.borderColor}
    borderRadius="14px"
    boxShadow="none"
  >
    <Text color="gray.400" fontSize="xs" fontWeight="700">{label}</Text>
    <Text mt={2} color={tone} fontSize={{ base: "xl", md: "2xl" }} fontWeight="800" sx={{ fontVariantNumeric: "tabular-nums" }}>
      {value}
    </Text>
    <Text mt={1.5} color="gray.500" fontSize="11px">{hint}</Text>
  </Card>
);

export const AdminAvatar: FC<{ username: string; owner: boolean }> = ({ username, owner }) => (
  <Box
    flexShrink={0}
    w="38px"
    h="38px"
    display="grid"
    placeItems="center"
    borderRadius="11px"
    bg={owner ? "rgba(139,92,246,.14)" : "rgba(37,99,235,.14)"}
    borderWidth="1px"
    borderColor={owner ? "rgba(167,139,250,.28)" : "rgba(96,165,250,.28)"}
    color={owner ? "purple.200" : "blue.200"}
    fontWeight="800"
    textTransform="uppercase"
    transition="transform .16s ease, border-color .16s ease"
    _groupHover={{ transform: "translateY(-1px)", borderColor: owner ? "purple.400" : "blue.400" }}
  >
    {username.slice(0, 1)}
  </Box>
);

export const StatusPill: FC<{ status: keyof typeof statusMeta }> = ({ status }) => {
  const meta = statusMeta[status];
  return (
    <HStack w="fit-content" spacing={1.5} px={2.5} py={1.5} bg={meta.bg} borderRadius="full">
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
    borderRadius="8px"
    variant="outline"
    bg={active ? "rgba(37,99,235,.18)" : "transparent"}
    borderColor={active ? "rgba(96,165,250,.55)" : "rgba(148,163,184,.18)"}
    color={active ? "blue.100" : "gray.300"}
    fontSize="12px"
    fontWeight={active ? "800" : "600"}
    transition="background .14s ease, border-color .14s ease, transform .14s ease"
    _hover={{
      bg: active ? "rgba(37,99,235,.24)" : "whiteAlpha.100",
      borderColor: active ? "blue.400" : "rgba(148,163,184,.34)",
      transform: "translateY(-1px)",
    }}
    _active={{ transform: "translateY(0)" }}
    onClick={onClick}
  >
    {children}
  </Button>
);

export const DetailChip: FC<{ label: string; value: string; tone?: string }> = ({ label, value, tone = "gray.200" }) => (
  <HStack
    spacing={1.5}
    px={2.5}
    h="28px"
    borderWidth="1px"
    borderColor="rgba(148,163,184,.12)"
    bg="rgba(255,255,255,.025)"
    borderRadius="7px"
    whiteSpace="nowrap"
  >
    <Text color="gray.500" fontSize="10px" fontWeight="700">{label}</Text>
    <Text color={tone} fontSize="11px" fontWeight="700">{value}</Text>
  </HStack>
);
