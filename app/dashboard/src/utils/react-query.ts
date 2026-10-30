import { QueryClient } from "react-query";

export const queryClient = new QueryClient();

// Refresh delegated creation permissions for already-open Admin sessions.
queryClient.setQueryDefaults("account-summary", { staleTime: 0, refetchInterval: 10000, refetchOnWindowFocus: "always" });
