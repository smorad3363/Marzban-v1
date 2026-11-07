import { Button, Flex, HStack, Text } from "@chakra-ui/react";

export const CatalogPager = ({ count, page, onPageChange, noun, size = 12 }: {
  count: number; page: number; onPageChange: (page: number) => void; noun: string; size?: number;
}) => {
  const pages = Math.max(1, Math.ceil(count / size));
  return <Flex gap={3} flexWrap="wrap" align="center" justify="space-between" pt={4}>
    <Text fontSize="xs" color="var(--panel-text-muted)" role="status">
      {count ? `نمایش ${(page * size + 1).toLocaleString("fa-IR")} تا ${Math.min(count, (page + 1) * size).toLocaleString("fa-IR")} از ${count.toLocaleString("fa-IR")} ${noun}` : `۰ ${noun}`}
    </Text>
    {pages > 1 && <HStack spacing={2} aria-label={`صفحه‌بندی ${noun}`}>
      <Button size="sm" minH="44px" variant="outline" isDisabled={page === 0} onClick={() => onPageChange(page - 1)}>قبلی</Button>
      <Text fontSize="sm" sx={{ fontVariantNumeric: "tabular-nums" }}>{(page + 1).toLocaleString("fa-IR")} / {pages.toLocaleString("fa-IR")}</Text>
      <Button size="sm" minH="44px" variant="outline" isDisabled={page + 1 >= pages} onClick={() => onPageChange(page + 1)}>بعدی</Button>
    </HStack>}
  </Flex>;
};
