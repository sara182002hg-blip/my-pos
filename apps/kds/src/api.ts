const defaultBaseUrl = "http://127.0.0.1:4000";

export const apiBaseUrl =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ??
  defaultBaseUrl;

const kdsToken = (import.meta.env.VITE_KDS_TOKEN as string | undefined) ?? "";

export const toWsUrl = (baseUrl: string) => {
  const url = new URL(baseUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws/live";
  if (kdsToken) url.searchParams.set("kds_key", kdsToken);
  return url.toString();
};

export const kdsHeaders: Record<string, string> = {
  "Content-Type": "application/json",
  ...(kdsToken ? { "x-kds-key": kdsToken } : {})
};
