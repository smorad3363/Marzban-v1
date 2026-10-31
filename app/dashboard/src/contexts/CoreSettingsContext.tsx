import { fetch } from "service/http";
import { create } from "zustand";

type CoreSettingsStore = {
  isLoading: boolean;
  isPostLoading: boolean;
  fetchCoreSettings: () => void;
  updateConfig: (json: string) => Promise<void>;
  restartCore: () => Promise<void>;
  version: string | null;
  started: boolean | null;
  local_enabled: boolean;
  logs_websocket: string | null;
  config: string;
};

export const useCoreSettings = create<CoreSettingsStore>((set) => ({
  isLoading: true,
  isPostLoading: false,
  version: null,
  started: false,
  local_enabled: true,
  logs_websocket: null,
  config: "",
  fetchCoreSettings: () => {
    set({ isLoading: true });
    Promise.all([
      fetch("/core").then(({ version, started, logs_websocket, local_enabled = true }) =>
        set({ version, started, logs_websocket, local_enabled })
      ),
      fetch("/core/config").then((config) => set({ config })),
    ]).finally(() => set({ isLoading: false }));
  },
  updateConfig: (body) => {
    set({ isPostLoading: true });
    return fetch("/core/config", { method: "PUT", body }).finally(() => {
      set({ isPostLoading: false });
    });
  },
  restartCore: () => {
    return fetch("/core/restart", { method: "POST" });
  },
}));
