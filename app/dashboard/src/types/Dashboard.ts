export type BillingMode = "LEGACY_COMPAT" | "SEAT_CREDIT" | "USED_TRAFFIC" | "ALLOCATED_TRAFFIC" | "USER_CREDIT";
export type DashboardRange = "24h" | "7d" | "30d";
export type DashboardUserStatus = "active" | "disabled" | "limited" | "expired" | "on_hold" | string;

export type DashboardTrafficPoint = {
  timestamp: string;
  total_traffic: number;
};

export type DashboardAttentionUser = {
  username: string;
  status: DashboardUserStatus;
  priority: "critical" | "high" | "warning";
  reason_code: "expired" | "limited" | "traffic_exhausted" | "traffic_near_limit" | "expires_soon" | "device_limit";
  used_traffic: number;
  data_limit: number | null;
  usage_percent: number | null;
  expire: number | null;
};

export type DashboardUserSummary = {
  username: string;
  status: DashboardUserStatus;
  used_traffic: number;
  data_limit: number | null;
  created_at: string;
};

export type DashboardOverview = {
  generated_at: string;
  timezone_offset_minutes: number;
  current_week_start: string;
  previous_week_start: string;
  role: "OWNER" | "ADMIN";
  online_window_seconds: number;
  traffic_range: DashboardRange;
  total_users: number;
  active_users: number;
  online_users: number;
  disabled_users: number;
  expired_users: number;
  limited_users: number;
  on_hold_users: number;
  current_used_traffic: number | null;
  allocated_quota: number;
  today_traffic: number;
  traffic_history_available: boolean;
  traffic_history: DashboardTrafficPoint[];
  attention_count: number;
  attention_users: DashboardAttentionUser[];
  top_consumers: DashboardUserSummary[];
  recent_users: DashboardUserSummary[];
  node_summary: null | {
    total: number;
    healthy: number;
    reconnecting: number;
    error: number;
    disabled: number;
  };
  admin_summary: null | {
    total: number;
    active: number;
    suspended: number;
    disabled: number;
  };
  new_users: { current: number; previous: number; change_percent: number | null };
  billing_modes: Array<{
    billing_mode: BillingMode;
    admin_count: number;
    user_count: number;
    active_users: number;
    current_used_traffic: number | null;
    allocated_quota: number;
  }>;
};
