import { Box, BoxProps, Card, Flex, HStack, Stack, Text, useColorMode } from "@chakra-ui/react";
import { FC, ReactNode } from "react";

/** Shared presentation primitives. They deliberately know nothing about accounts or APIs. */
export const PageHeader: FC<{ title: ReactNode; description?: ReactNode; eyebrow?: ReactNode; icon?: ReactNode; actions?: ReactNode; children?: ReactNode }> = ({ title, description, eyebrow, icon, actions, children }) => (
  <Box as="header" className="console-page-header">
    <Flex gap={5} justify="space-between" align={{ base: "start", md: "center" }} direction={{ base: "column", md: "row" }}>
      <Box minW={0} flex="1">
        {eyebrow && <HStack color="var(--panel-accent)" spacing={2} mb={2} fontSize="xs" fontWeight="600">{icon}{eyebrow}</HStack>}
        <Text as="h1" fontSize={{ base: "26px", md: "32px" }} fontWeight="700" lineHeight="1.5" letterSpacing="-.025em">{title}</Text>
        {description && <Text mt={1.5} color="var(--panel-text-muted)" fontSize="sm" maxW="72ch" lineHeight="1.9">{description}</Text>}
      </Box>
      {actions && <Flex className="console-page-actions" flexShrink={0} gap={2} align="center" flexWrap="wrap">{actions}</Flex>}
    </Flex>
    {children}
  </Box>
);

export const Surface: FC<BoxProps> = ({ children, ...props }) => (
  <Card className="console-surface" minW={0} borderWidth="1px" borderColor="var(--panel-border)" {...props}>{children}</Card>
);

export const SectionHeader: FC<{ title: ReactNode; description?: ReactNode; action?: ReactNode }> = ({ title, description, action }) => (
  <Flex justify="space-between" align="start" gap={3} mb={5} flexWrap="wrap">
    <Box minW={0} flex="1"><Text as="h2" fontSize="md" fontWeight="700">{title}</Text>{description && <Text mt={1} fontSize="xs" color="var(--panel-text-muted)" lineHeight="1.8">{description}</Text>}</Box>
    {action}
  </Flex>
);

export const Metric: FC<{ label: ReactNode; value: ReactNode; hint?: ReactNode; icon?: ReactNode; tone?: string }> = ({ label, value, hint, icon, tone = "var(--panel-accent)" }) => (
  <Surface p={{ base: 4, md: 5 }} className="console-metric" h="full">
    <HStack justify="space-between" align="start" gap={3}>
      <Text fontSize="xs" fontWeight="500" color="var(--panel-text-muted)" lineHeight="1.8">{label}</Text>
      {icon && <Box color={tone} className="console-metric-icon" flexShrink={0}>{icon}</Box>}
    </HStack>
    <Text dir="auto" mt={3} fontSize={{ base: typeof value === "string" && value.length > 12 ? "16px" : "21px", md: "24px", xl: "29px" }} lineHeight="1.5" fontWeight="700" sx={{ fontVariantNumeric: "tabular-nums" }} overflowWrap="anywhere">{value}</Text>
    {hint && <Text mt={2} fontSize="xs" color="var(--panel-text-muted)" lineHeight="1.8">{hint}</Text>}
  </Surface>
);

export const EmptyState: FC<{ text: ReactNode; description?: ReactNode; icon?: ReactNode; action?: ReactNode }> = ({ text, description, icon, action }) => (
  <Stack align="center" textAlign="center" justify="center" spacing={3} py={{ base: 9, md: 12 }} px={5} className="console-empty">
    <Box aria-hidden="true" className="console-empty-symbol">{icon || <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M4 6h16v14H4V6Zm4-3h8M8 11h8m-8 4h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>}</Box>
    <Text fontSize="sm" fontWeight="600">{text}</Text>
    {description && <Text color="var(--panel-text-muted)" maxW="45ch" fontSize="sm">{description}</Text>}
    {action}
  </Stack>
);

export const TechnicalValue: FC<BoxProps> = props => <Box as="bdi" dir="ltr" fontFamily="mono" className="console-technical" {...props} />;

export function useChartPalette() {
  const { colorMode } = useColorMode();
  return colorMode === "dark"
    ? { accent: "#65d6bd", text: "#a1adaa", grid: "#27312e", surface: "#141b18", success: "#79d6a2", danger: "#ff9e98", warning: "#edc37c", info: "#8ac5ed", mode: "dark" as const }
    : { accent: "#0b7560", text: "#55635d", grid: "#e2e8e4", surface: "#ffffff", success: "#187244", danger: "#b63232", warning: "#8b5c15", info: "#246b97", mode: "light" as const };
}
