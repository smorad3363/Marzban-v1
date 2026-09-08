import { FetchOptions, $fetch as ohMyFetch } from "ofetch";
import { getAuthToken } from "utils/authStorage";
import { localizedApiError } from "utils/apiError";

export const $fetch = ohMyFetch.create({
  baseURL: import.meta.env.VITE_BASE_API || "/api/",
});

export const fetcher = <T = any>(
  url: string,
  ops: FetchOptions<"json"> = {}
) => {
  const token = getAuthToken();
  if (token) {
    ops["headers"] = {
      ...(ops?.headers || {}),
      Authorization: `Bearer ${getAuthToken()}`,
    };
  }
  return $fetch<T>(url, ops).catch((error: any) => {
    // ofetch already exposes response body as `data`/`response._data`.
    // Normalize `message` as well so legacy callers never surface raw
    // transport/server text to the user.
    error.message = localizedApiError(error);
    throw error;
  });
};

export const fetch = fetcher;
