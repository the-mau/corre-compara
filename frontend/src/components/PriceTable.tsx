"use client";

import type { PriceHistory } from "@/lib/types";

type StorePrice = PriceHistory & {
  store_name?: string | null;
  domain?: string | null;
  affiliate_tag?: string | null;
};

function asNumber(value: unknown): number | null {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const n = Number(String(value));
  return Number.isFinite(n) ? n : null;
}

function formatMXN(value: number): string {
  return new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" }).format(value);
}

function buildAffiliateUrl(url?: string | null, _affiliateTag?: string | null): string | undefined {
  // Skeleton: por ahora devolvemos la URL tal cual.
  return url ?? undefined;
}

export default function PriceTable({ prices }: { prices: StorePrice[] }) {
  const normalized = prices.map((p) => ({ ...p, _priceNum: asNumber(p.price) }));
  const cheapest = normalized.reduce<number | null>((acc, p) => {
    if (p._priceNum === null) return acc;
    if (acc === null) return p._priceNum;
    return Math.min(acc, p._priceNum);
  }, null);

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="text-left text-white/60">
            <th className="px-2 py-2">Tienda</th>
            <th className="px-2 py-2">Precio</th>
            <th className="px-2 py-2">Stock</th>
            <th className="px-2 py-2">Oferta</th>
          </tr>
        </thead>
        <tbody>
          {normalized.map((p) => {
            const priceNum = p._priceNum ?? 0;
            const isCheapest = cheapest !== null && p._priceNum !== null && priceNum === cheapest;
            const href = buildAffiliateUrl(p.url, p.affiliate_tag);

            return (
              <tr key={String(p.id ?? p.store_id ?? Math.random())} className="border-t border-white/10">
                <td className="px-2 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-9 w-9 rounded-xl bg-white/10" />
                    <div className="min-w-0">
                      <div className="truncate font-medium">{p.store_name || "Tienda"}</div>
                      {p.domain && <div className="truncate text-xs text-white/50">{p.domain}</div>}
                    </div>
                  </div>
                </td>
                <td className="px-2 py-3">
                  <div className={isCheapest ? "font-semibold text-green-300" : "font-semibold"}>
                    {p._priceNum === null ? "—" : formatMXN(priceNum)}
                  </div>
                </td>
                <td className="px-2 py-3">
                  {p.in_stock ? (
                    <span className="inline-flex rounded-full border border-green-500/30 bg-green-500/10 px-2 py-1 text-xs text-green-200">
                      Disponible
                    </span>
                  ) : (
                    <span className="inline-flex rounded-full border border-red-500/30 bg-red-500/10 px-2 py-1 text-xs text-red-200">
                      Sin stock
                    </span>
                  )}
                </td>
                <td className="px-2 py-3">
                  {href ? (
                    <a
                      href={href}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-xl bg-white/10 px-3 py-2 text-xs font-medium hover:bg-white/20"
                    >
                      Ver oferta
                    </a>
                  ) : (
                    <span className="text-xs text-white/50">—</span>
                  )}
                </td>
              </tr>
            );
          })}
          {normalized.length === 0 && (
            <tr>
              <td className="px-2 py-6 text-white/60" colSpan={4}>
                No hay precios todavía. Vuelve más tarde.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

