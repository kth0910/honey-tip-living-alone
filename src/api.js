const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function getJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json();
}

export function fetchSources() {
  return getJson("/api/sources");
}

export function fetchDocuments({ query = "", type = "전체", sourceId = "", limit = 100 }) {
  const params = new URLSearchParams();
  if (query.trim()) params.set("query", query.trim());
  if (type && type !== "전체") params.set("type", type);
  if (sourceId) params.set("source_id", sourceId);
  if (limit) params.set("limit", String(limit));
  return getJson(`/api/documents?${params.toString()}`);
}

export async function triggerSeed() {
  const response = await fetch(`${API_BASE_URL}/api/admin/seed`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Seed failed: ${response.status}`);
  }
  return response.json();
}
