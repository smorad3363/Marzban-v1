import { StatisticsQueryKey } from "components/Statistics";
import { fetch } from "service/http";
import { User, UserCreate, UserPlanMeta } from "types/User";
import { getAuthToken } from "utils/authStorage";
import { queryClient } from "utils/react-query";
import { getUsersPerPageLimitSize } from "utils/userPreferenceStorage";
import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";

export type FilterType = {
  search?: string;
  limit?: number;
  offset?: number;
  sort: string;
  admin?: string;
  status?: "active" | "disabled" | "limited" | "expired" | "on_hold";
  plan_id?: number;
  without_plan?: boolean;
  trial?: boolean;
  attention?: boolean;
  expires_within_days?: number;
  usage_percent_min?: number;
  has_device_limit?: boolean;
  unlimited_traffic?: boolean;
  inactive_hours?: number;
};
export type ProtocolType = "vmess" | "vless" | "trojan" | "shadowsocks";

export type FilterUsageType = {
  start?: string;
  end?: string;
};

export type InboundType = {
  tag: string;
  protocol: ProtocolType;
  network: string;
  tls: string;
  port?: number;
};
export type Inbounds = Map<ProtocolType, InboundType[]>;

type DashboardStateType = {
  isCreatingNewUser: boolean;
  editingUser: User | null | undefined;
  deletingUser: User | null;
  version: string | null;
  users: {
    users: User[];
    total: number;
    page: number;
    page_size: number;
    pages: number;
    plan_meta: Record<string, UserPlanMeta | null>;
  };
  inbounds: Inbounds;
  loading: boolean;
  filters: FilterType;
  subscribeUrl: string | null;
  QRcodeLinks: string[] | null;
  isEditingHosts: boolean;
  isEditingNodes: boolean;
  isShowingNodesUsage: boolean;
  isResetingAllUsage: boolean;
  resetUsageUser: User | null;
  revokeSubscriptionUser: User | null;
  isEditingCore: boolean;
  onCreateUser: (isOpen: boolean) => void;
  onEditingUser: (user: User | null) => void;
  onDeletingUser: (user: User | null) => void;
  onResetAllUsage: (isResetingAllUsage: boolean) => void;
  refetchUsers: () => void;
  resetAllUsage: () => Promise<void>;
  onFilterChange: (filters: Partial<FilterType>) => void;
  deleteUser: (user: User) => Promise<void>;
  createUser: (user: UserCreate) => Promise<User>;
  editUser: (user: UserCreate) => Promise<void>;
  fetchUserUsage: (user: User, query: FilterUsageType) => Promise<void>;
  setQRCode: (links: string[] | null) => void;
  setSubLink: (subscribeURL: string | null) => void;
  onEditingHosts: (isEditingHosts: boolean) => void;
  onEditingNodes: (isEditingHosts: boolean) => void;
  onShowingNodesUsage: (isShowingNodesUsage: boolean) => void;
  resetDataUsage: (user: User) => Promise<void>;
  revokeSubscription: (user: User) => Promise<void>;
};

type UsersPage = DashboardStateType["users"];
let latestUsersRequest = 0;

const invalidateUserAggregates = () => {
  queryClient.invalidateQueries(StatisticsQueryKey);
  queryClient.invalidateQueries(["users-summary"]);
};

const fetchUsers = (query: FilterType): Promise<UsersPage> => {
  const authToken = getAuthToken();
  const requestId = ++latestUsersRequest;
  const requestQuery = Object.fromEntries(
    Object.entries(query).filter(([, value]) => value !== undefined && value !== null && value !== "" && value !== false)
  );
  useDashboard.setState({ loading: true });
  return fetch("/users/management", { query: requestQuery })
    .then((users) => {
      if (getAuthToken() === authToken && requestId === latestUsersRequest) {
        useDashboard.setState({ users });
      }
      return users;
    })
    .finally(() => {
      if (getAuthToken() === authToken && requestId === latestUsersRequest) {
        useDashboard.setState({ loading: false });
      }
    });
};

export const fetchInbounds = () => {
  const authToken = getAuthToken();
  return fetch("/inbounds")
    .then((inbounds: Inbounds) => {
      if (getAuthToken() === authToken) {
        useDashboard.setState({
          inbounds: new Map(Object.entries(inbounds)) as Inbounds,
        });
      }
    })
    .finally(() => {
      if (getAuthToken() === authToken) {
        useDashboard.setState({ loading: false });
      }
    });
};

export const useDashboard = create(
  subscribeWithSelector<DashboardStateType>((set, get) => ({
    version: null,
    editingUser: null,
    deletingUser: null,
    isCreatingNewUser: false,
    QRcodeLinks: null,
    subscribeUrl: null,
    users: {
      users: [],
      total: 0,
      page: 1,
      page_size: getUsersPerPageLimitSize(),
      pages: 0,
      plan_meta: {},
    },
    loading: true,
    isResetingAllUsage: false,
    isEditingHosts: false,
    isEditingNodes: false,
    isShowingNodesUsage: false,
    resetUsageUser: null,
    revokeSubscriptionUser: null,
    filters: {
      username: "",
      limit: getUsersPerPageLimitSize(),
      sort: "-created_at",
    },
    inbounds: new Map(),
    isEditingCore: false,
    refetchUsers: () => {
      fetchUsers(get().filters);
    },
    resetAllUsage: () => {
      return fetch(`/users/reset`, { method: "POST" }).then(() => {
        get().onResetAllUsage(false);
        get().refetchUsers();
        invalidateUserAggregates();
      });
    },
    onResetAllUsage: (isResetingAllUsage) => set({ isResetingAllUsage }),
    onCreateUser: (isCreatingNewUser) => set({ isCreatingNewUser }),
    onEditingUser: (editingUser) => {
      set({ editingUser });
    },
    onDeletingUser: (deletingUser) => {
      set({ deletingUser });
    },
    onFilterChange: (filters) => {
      set({
        filters: {
          ...get().filters,
          ...filters,
        },
      });
      get().refetchUsers();
    },
    setQRCode: (QRcodeLinks) => {
      set({ QRcodeLinks });
    },
    deleteUser: (user: User) => {
      set({ editingUser: null });
      return fetch(`/user/${user.username}`, { method: "DELETE" }).then(() => {
        set({ deletingUser: null });
        get().refetchUsers();
        invalidateUserAggregates();
      });
    },
    createUser: (body: UserCreate) => {
      return fetch<User>(`/user`, { method: "POST", body }).then((createdUser) => {
        set({ editingUser: null });
        get().refetchUsers();
        invalidateUserAggregates();
        return createdUser;
      });
    },
    editUser: (body: UserCreate) => {
      return fetch(`/user/${body.username}`, { method: "PUT", body }).then(
        () => {
          get().onEditingUser(null);
          get().refetchUsers();
          invalidateUserAggregates();
        }
      );
    },
    fetchUserUsage: (body: User, query: FilterUsageType) => {
      const requestQuery = Object.fromEntries(
        Object.entries(query).filter(([, value]) => value !== undefined && value !== null && value !== "")
      );
      return fetch(`/user/${body.username}/usage`, { method: "GET", query: requestQuery });
    },
    onEditingHosts: (isEditingHosts: boolean) => {
      set({ isEditingHosts });
    },
    onEditingNodes: (isEditingNodes: boolean) => {
      set({ isEditingNodes });
    },
    onShowingNodesUsage: (isShowingNodesUsage: boolean) => {
      set({ isShowingNodesUsage });
    },
    setSubLink: (subscribeUrl) => {
      set({ subscribeUrl });
    },
    resetDataUsage: (user) => {
      return fetch(`/user/${user.username}/reset`, { method: "POST" }).then(
        () => {
          set({ resetUsageUser: null });
          get().refetchUsers();
          invalidateUserAggregates();
        }
      );
    },
    revokeSubscription: (user) => {
      return fetch(`/user/${user.username}/revoke_sub`, {
        method: "POST",
      }).then((user) => {
        set({ revokeSubscriptionUser: null, editingUser: user });
        get().refetchUsers();
      });
    },
  }))
);

export const resetDashboardState = () => {
  useDashboard.setState({
    version: null,
    editingUser: null,
    deletingUser: null,
    isCreatingNewUser: false,
    QRcodeLinks: null,
    subscribeUrl: null,
    users: {
      users: [],
      total: 0,
      page: 1,
      page_size: getUsersPerPageLimitSize(),
      pages: 0,
      plan_meta: {},
    },
    loading: true,
    isResetingAllUsage: false,
    isEditingHosts: false,
    isEditingNodes: false,
    isShowingNodesUsage: false,
    resetUsageUser: null,
    revokeSubscriptionUser: null,
    filters: {
      limit: getUsersPerPageLimitSize(),
      sort: "-created_at",
    },
    inbounds: new Map(),
    isEditingCore: false,
  });
};
