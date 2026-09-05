export type AccessGroupInboundOption = {
  tag: string;
  protocol: string;
  network: string;
  tls: string;
  port?: number;
};

export const normalizeAccessGroupInboundTags = (tags: readonly string[]): string[] =>
  [...new Set(tags.map((tag) => tag.trim()).filter(Boolean))].sort();

export const toggleAccessGroupInboundTag = (
  selected: readonly string[],
  tag: string,
  checked: boolean
): string[] =>
  normalizeAccessGroupInboundTags(
    checked ? [...selected, tag] : selected.filter((value) => value !== tag)
  );

export const missingAccessGroupInboundTags = (
  selected: readonly string[],
  options: readonly AccessGroupInboundOption[]
): string[] => {
  const configured = new Set(options.map((option) => option.tag));
  return normalizeAccessGroupInboundTags(selected).filter((tag) => !configured.has(tag));
};

export const normalizeAccessGroupHostScope = (
  hosts: Readonly<Record<string, readonly number[]>>
): Record<string, number[]> =>
  Object.fromEntries(
    Object.entries(hosts)
      .map(([tag, ids]) => [
        tag.trim(),
        [...new Set(ids.filter((id) => Number.isInteger(id) && id > 0))].sort((a, b) => a - b),
      ] as const)
      .filter(([tag]) => Boolean(tag))
      .sort(([left], [right]) => left.localeCompare(right))
  );

export const toggleAccessGroupHostId = (
  hosts: Readonly<Record<string, readonly number[]>>,
  inboundTag: string,
  hostId: number,
  checked: boolean
): Record<string, number[]> =>
  normalizeAccessGroupHostScope({
    ...hosts,
    [inboundTag]: checked
      ? [...(hosts[inboundTag] || []), hostId]
      : (hosts[inboundTag] || []).filter((id) => id !== hostId),
  });

export const missingAccessGroupHostIds = (
  hosts: Readonly<Record<string, readonly number[]>>,
  options: readonly { tag: string; hosts: readonly { id: number }[] }[]
): number[] => {
  const available = new Map(options.map((option) => [
    option.tag,
    new Set(option.hosts.map((host) => host.id)),
  ]));
  return [...new Set(
    Object.entries(hosts).flatMap(([tag, ids]) =>
      ids.filter((id) => !available.get(tag)?.has(id))
    )
  )].sort((a, b) => a - b);
};
