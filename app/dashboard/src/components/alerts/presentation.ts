export type Incident = { id: number; admin_id: number; admin_username: string; resource: string; state: string; severity: string; revision: number; seen: boolean; resolved_at: string | null; opened_at: string; details: Record<string, any> };
export type Center = { items: Incident[]; counts: { critical: number; warning: number }; next_before: number | null; inherited_restriction: boolean; checked_at: string | null };

export const labels: Record<string, string> = { financial: "موجودی و بدهی", accounts: "سقف تعداد اکانت", create_operations: "سهمیه ساخت و تغییر زمان", renewals: "سهمیه تمدید", renewal_budget: "سقف تمدید", provisioning_volume: "سقف حجم ساخت", devices: "ظرفیت دستگاه", traffic: "اعتبار حجم", trials: "سهمیه تست", expiry: "انقضای حساب", account: "وضعیت حساب" };
export const states: Record<string, string> = { low: "کمبود موجودی", empty: "اتمام موجودی", frozen: "فریز مالی", disabled: "غیرفعال", suspended: "تعلیق", near_limit: "نزدیک محدودیت", exhausted: "سهمیه تمام شده", expired: "منقضی شده" };
export const fa = (n: number) => Number.isFinite(n) ? n.toLocaleString("fa-IR", { maximumFractionDigits: 2 }) : "—";
export const incidentTitle = (item: Incident) => `${labels[item.resource] || "هشدار حساب"} · ${states[item.state] || "نیاز به بررسی"}`;

export function incidentSummary(item: Incident) {
  const d = item.details;
  if (item.resource === "financial") return `مانده ${fa(d.balance_toman)} تومان؛ ${item.state === "disabled" ? "قطع کاربران به دلیل بدهی" : item.state === "frozen" ? "ساخت و تمدید متوقف است" : "اعتبار حساب را بررسی کنید"}.`;
  if ("limit" in d) return `${fa(d.percent)}٪ از سهمیه استفاده شده؛ ${d.unit === "bytes" ? `${fa(d.remaining / 1024 ** 3)} گیگ` : fa(d.remaining)} باقی مانده است.`;
  if ("remaining_days" in d) return d.remaining_days < 0 ? "اعتبار زمانی حساب به پایان رسیده است." : `${fa(d.remaining_days)} روز تا پایان اعتبار حساب باقی مانده است.`;
  return "وضعیت حساب و علت محدودیت را بررسی کنید.";
}

export function alertTime(value: string | null) {
  if (!value) return "ثبت نشده";
  const date = new Date(/(?:Z|[+-]\d{2}:?\d{2})$/i.test(value) ? value : value + "Z");
  return Number.isNaN(date.getTime()) ? "زمان نامشخص" : date.toLocaleString("fa-IR");
}

export function priorityIncidents(items: Incident[]) {
  return [...items].sort((a, b) => Number(!!a.resolved_at) - Number(!!b.resolved_at)
    || Number(b.severity === "critical") - Number(a.severity === "critical")
    || Number(a.seen) - Number(b.seen) || b.id - a.id);
}

type NotificationStorage = Pick<Storage, "getItem" | "setItem">;
const memory = new Map<string, Map<number, number>>();
const prefix = "marzban.alert-notifications.v1:";

function browserStorage(): NotificationStorage | undefined {
  try { return window.localStorage; } catch (_) { return undefined; }
}

/** Presentation receipts only: the API remains authoritative for active/seen/resolved. */
export function takeNewCriticalAlerts(actor: string, items: Incident[], storage = browserStorage()) {
  const key = prefix + encodeURIComponent(actor);
  const remembered = new Map(memory.get(actor) || []);
  try {
    const saved = JSON.parse(storage?.getItem(key) || "[]");
    if (Array.isArray(saved)) for (const entry of saved) {
      if (Array.isArray(entry) && entry.length === 2 && entry.every(n => Number.isSafeInteger(n) && n > 0)) {
        remembered.set(entry[0], Math.max(remembered.get(entry[0]) || 0, entry[1]));
      }
    }
  } catch (_) { /* Private browsing or a corrupt receipt must not break the panel. */ }
  const fresh = priorityIncidents(items).filter(item => !item.resolved_at && !item.seen
    && item.severity === "critical" && item.revision > (remembered.get(item.id) || 0));
  for (const item of items) {
    if (item.seen || fresh.includes(item)) {
      const revision = Math.max(item.revision, remembered.get(item.id) || 0);
      remembered.delete(item.id);
      remembered.set(item.id, revision);
    }
  }
  // Bound local presentation state; store only incident IDs and revisions, never balances or tokens.
  while (remembered.size > 256) remembered.delete(remembered.keys().next().value!);
  memory.set(actor, remembered);
  try { storage?.setItem(key, JSON.stringify([...remembered])); } catch (_) { /* Memory fallback remains active. */ }
  return fresh;
}
