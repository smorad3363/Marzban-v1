import {
  Badge,
  Box,
  Card,
  Grid,
  GridItem,
  HStack,
  Skeleton,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react";
import { useQuery } from "react-query";
import { fetch } from "service/http";

export type NodeBandwidthEntry = {
  node_id: number | null;
  node_name: string;
  state: "online" | "warming_up" | "stale" | "offline" | string;
  sampled_at: string | null;
  sample_age_seconds: number | null;
  uplink_bps: number;
  downlink_bps: number;
  total_bps: number;
  peak_5m_uplink_bps: number;
  peak_5m_downlink_bps: number;
};

type BandwidthResponse = {
  nodes: NodeBandwidthEntry[];
  total_uplink_bps: number;
  total_downlink_bps: number;
  total_bps: number;
  online_nodes: number;
  total_nodes: number;
};

const formatRate = (value: number) => {
  const safe = Number.isFinite(value) && value > 0 ? value : 0;
  const units = ["bps", "Kbps", "Mbps", "Gbps", "Tbps"];
  let amount = safe;
  let index = 0;
  while (amount >= 1000 && index < units.length - 1) {
    amount /= 1000;
    index += 1;
  }
  return `${new Intl.NumberFormat("fa-IR", {
    maximumFractionDigits: index === 0 ? 0 : 1,
  }).format(amount)} ${units[index]}`;
};

const stateMeta = (state: string) => {
  if (state === "online") return { label: "زنده", scheme: "green" };
  if (state === "warming_up") return { label: "در حال نمونه‌گیری", scheme: "blue" };
  if (state === "stale") return { label: "داده قدیمی", scheme: "orange" };
  return { label: "آفلاین", scheme: "gray" };
};

const Metric = ({ label, value }: { label: string; value: string }) => (
  <Box minW={0}>
    <Text fontSize="xs" color="gray.500" _dark={{ color: "gray.400" }}>
      {label}
    </Text>
    <Text mt={1} fontSize={{ base: "lg", md: "xl" }} fontWeight="800" dir="ltr" textAlign="start">
      {value}
    </Text>
  </Box>
);

export const NodeBandwidthPanel = () => {
  const query = useQuery<BandwidthResponse>({
    queryKey: ["nodes-live-bandwidth"],
    queryFn: () => fetch("/nodes/bandwidth"),
    refetchInterval: 10_000,
    refetchOnWindowFocus: false,
    staleTime: 5_000,
  });

  if (query.isLoading) {
    return (
      <Card p={{ base: 4, md: 5 }} mb={4} borderWidth="1px" borderColor="var(--panel-border)" bg="var(--panel-surface)">
        <Skeleton height="120px" borderRadius="12px" />
      </Card>
    );
  }

  if (query.isError || !query.data) {
    return (
      <Card p={{ base: 4, md: 5 }} mb={4} borderWidth="1px" borderColor="var(--panel-border)" bg="var(--panel-surface)">
        <Text fontWeight="800">پهنای‌باند زنده</Text>
        <Text mt={2} fontSize="sm" color="orange.500">
          دریافت وضعیت پهنای‌باند ممکن نیست. این خطا روی حسابداری مصرف اثر نمی‌گذارد.
        </Text>
      </Card>
    );
  }

  const data = query.data;
  return (
    <Card p={{ base: 4, md: 5 }} mb={4} borderWidth="1px" borderColor="var(--panel-border)" bg="var(--panel-surface)">
      <HStack justify="space-between" align="start" gap={3} flexWrap="wrap">
        <Box>
          <Text color="primary.600" _dark={{ color: "primary.300" }} fontSize="xs" fontWeight="800">
            شبکه
          </Text>
          <Text as="h2" mt={1} fontSize="lg" fontWeight="800">
            پهنای‌باند زنده نودها
          </Text>
          <Text mt={1} fontSize="sm" color="gray.600" _dark={{ color: "gray.400" }}>
            سرعت از همان شمارنده‌های حسابداری Xray محاسبه می‌شود و poll اضافه‌ای به نودها نمی‌زند.
          </Text>
        </Box>
        <Badge colorScheme={data.online_nodes === data.total_nodes ? "green" : "orange"} px={3} py={1} borderRadius="full">
          {new Intl.NumberFormat("fa-IR").format(data.online_nodes)} از {new Intl.NumberFormat("fa-IR").format(data.total_nodes)} فعال
        </Badge>
      </HStack>

      <Grid mt={4} templateColumns={{ base: "1fr", sm: "repeat(3, 1fr)" }} gap={3}>
        <GridItem p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px" bg="var(--panel-nested)">
          <Metric label="دانلود کل" value={formatRate(data.total_downlink_bps)} />
        </GridItem>
        <GridItem p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px" bg="var(--panel-nested)">
          <Metric label="آپلود کل" value={formatRate(data.total_uplink_bps)} />
        </GridItem>
        <GridItem p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px" bg="var(--panel-nested)">
          <Metric label="مجموع" value={formatRate(data.total_bps)} />
        </GridItem>
      </Grid>

      <Stack mt={4} spacing={2}>
        {data.nodes.map((node) => {
          const state = stateMeta(node.state);
          return (
            <Box key={node.node_id ?? "master"} p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px">
              <Grid templateColumns={{ base: "1fr", md: "minmax(150px, 1.2fr) repeat(3, minmax(110px, .8fr))" }} gap={3} alignItems="center">
                <VStack align="start" spacing={1} minW={0}>
                  <HStack>
                    <Text fontWeight="800" noOfLines={1}>{node.node_name}</Text>
                    <Badge colorScheme={state.scheme}>{state.label}</Badge>
                  </HStack>
                  {node.sample_age_seconds != null && (
                    <Text fontSize="xs" color="gray.500">
                      آخرین نمونه: {new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 0 }).format(node.sample_age_seconds)} ثانیه پیش
                    </Text>
                  )}
                </VStack>
                <Metric label="دانلود" value={formatRate(node.downlink_bps)} />
                <Metric label="آپلود" value={formatRate(node.uplink_bps)} />
                <Metric label="مجموع" value={formatRate(node.total_bps)} />
              </Grid>
            </Box>
          );
        })}
      </Stack>
    </Card>
  );
};
