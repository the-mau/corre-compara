import type { Alert, PriceHistory, Product } from "./types";

const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  // Compatibilidad con tokens típicos (Supabase / custom).
  return (
    window.localStorage.getItem("sb-access-token") ||
    window.localStorage.getItem("access_token") ||
    window.localStorage.getItem("token") ||
    null
  );
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers ? (init.headers as Record<string, string>) : {}),
  };

  const token = getAuthToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${baseUrl}${path}`, { ...init, headers });
  if (!res.ok) {
    const msg = await res.text().catch(() => "");
    throw new Error(`API error ${res.status}: ${msg || res.statusText}`);
  }
  return (await res.json()) as T;
}

export async function searchProducts(query: string, brand?: string): Promise<Product[]> {
  const u = new URL(`${baseUrl}/products/search`);
  u.searchParams.set("q", query);
  if (brand) u.searchParams.set("brand", brand);
  const res = await fetch(u.toString());
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as Product[];
}

export async function getProducts(): Promise<Product[]> {
  return apiFetch<Product[]>("/products");
}

export async function getProduct(id: string): Promise<Product> {
  return apiFetch<Product>(`/products/${id}`);
}

export async function getProductPrices(id: string): Promise<PriceHistory[]> {
  return apiFetch<PriceHistory[]>(`/products/${id}/prices`);
}

export async function getLatestPrices(id: string): Promise<PriceHistory[]> {
  return apiFetch<PriceHistory[]>(`/prices/latest/${id}`);
}

export async function triggerScrape(productId: string): Promise<{ results: number }> {
  return apiFetch<{ results: number }>(`/prices/scrape/${productId}`, { method: "POST" });
}

export async function getProductHistory(id: string, days: number): Promise<PriceHistory[]> {
  return apiFetch<PriceHistory[]>(`/products/${id}/history?days=${days}`);
}

export async function createAlert(
  productId: string,
  targetPrice: number,
  size?: string,
): Promise<Alert> {
  const body = {
    product_id: productId,
    target_price: targetPrice,
    size: size || undefined,
  };
  return apiFetch<Alert>(`/alerts`, { method: "POST", body: JSON.stringify(body) });
}

export async function getMyAlerts(): Promise<Alert[]> {
  return apiFetch<Alert[]>(`/alerts`, { method: "GET" });
}

