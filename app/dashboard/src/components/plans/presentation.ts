import type { AccessGroup, AccessGroupNetworkOption, UserPlan } from "types/Admin";

/** Display/search helpers only. The API remains the authority for access and pricing. */
export const catalogText = (value: string) => value.normalize("NFKC").replace(/ي/g, "ی").replace(/ك/g, "ک").trim().toLocaleLowerCase("fa-IR");

export function filterPlans(plans: UserPlan[], search: string, category: string) {
  const needle = catalogText(search);
  return plans.filter(plan => (!category || String(plan.category_id) === category) &&
    (!needle || catalogText(`${plan.name} ${plan.description || ""} ${plan.category_name || ""}`).includes(needle)));
}

export function accessGroupPermissionLabel(group: Pick<AccessGroup, "admin_access_restricted" | "allowed_admin_ids">) {
  if (!group.admin_access_restricted) return "همهٔ ادمین‌ها";
  return group.allowed_admin_ids.length ? `${group.allowed_admin_ids.length.toLocaleString("fa-IR")} ادمین مجاز` : "فقط مالک";
}

export function filterNetworkOptions(options: AccessGroupNetworkOption[], search: string, selected: string[], selectedOnly: boolean) {
  const needle = catalogText(search);
  return options.filter(inbound => (!selectedOnly || selected.includes(inbound.tag)) &&
    (!needle || catalogText(`${inbound.tag} ${inbound.protocol} ${inbound.network} ${inbound.hosts.map(host => host.remark).join(" ")}`).includes(needle)));
}

export const catalogPage = <T,>(items: T[], page: number, size = 12) => {
  const pages = Math.max(1, Math.ceil(items.length / size));
  const current = Math.min(Math.max(0, page), pages - 1);
  return { items: items.slice(current * size, (current + 1) * size), current, pages };
};
