const defaultBaseUrl = "http://127.0.0.1:4000";

export const apiBaseUrl =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ??
  defaultBaseUrl;

export const toWsUrl = (baseUrl: string) => {
  const url = new URL(baseUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws/live";
  return url.toString();
};
