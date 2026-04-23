"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { createAlert, getLatestPrices, getProduct, getProductHistory, triggerScrape } from "@/lib/api";
import type { PriceHistory, Product } from "@/lib/types";
import PriceChart from "@/components/PriceChart";
import PriceTable from "@/components/PriceTable";

type ModalMode = "create" | "auth";

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return (
    window.localStorage.getItem("sb-access-token") ||
    window.localStorage.getItem("access_token") ||
    window.localStorage.getItem("token")
  );
}

export default function ProductDetailPage() {
  const params = useParams<{ id: string }>();
  const productId = params.id;

  const [product, setProduct] = useState<Product | null>(null);
  const [prices, setPrices] = useState<any[]>([]);
  const [history, setHistory] = useState<PriceHistory[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<ModalMode>("create");

  const [targetPrice, setTargetPrice] = useState<string>("");
  const [size, setSize] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    setIsAuthenticated(!!getStoredToken());
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const [p, pr, h] = await Promise.all([
          getProduct(productId),
          getLatestPrices(productId),
          getProductHistory(productId, 30),
        ]);
        if (cancelled) return;
        setProduct(p);
        setPrices(pr as any[]);
        setHistory(h);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Error al cargar el producto");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [productId]);

  const currentMinPrice = useMemo(() => {
    const vals = prices
      .map((p) => p?.price)
      .map((v) => {
        const n = typeof v === "number" ? v : Number(String(v));
        return Number.isFinite(n) ? n : null;
      })
      .filter((v): v is number => v !== null);
    if (!vals.length) return null;
    return Math.min(...vals);
  }, [prices]);

  function openCreateModal() {
    if (!isAuthenticated) {
      setModalMode("auth");
      setModalOpen(true);
      return;
    }
    setModalMode("create");
    setModalOpen(true);
  }

  async function onSubmit() {
    if (!product) return;
    const parsed = Number(targetPrice);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      alert("Ingresa un precio objetivo válido.");
      return;
    }
    setSubmitting(true);
    try {
      await createAlert(product.id, parsed, size.trim() ? size.trim() : undefined);
      setModalOpen(false);
      alert("Alerta creada.");
    } catch (e) {
      alert(e instanceof Error ? e.message : "No se pudo crear la alerta");
    } finally {
      setSubmitting(false);
    }
  }

  async function onRefreshPrices() {
    try {
      setLoading(true);
      await triggerScrape(productId);
      const latest = await getLatestPrices(productId);
      setPrices(latest as any[]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron actualizar los precios");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {loading && <div className="text-white/70">Cargando...</div>}
      {error && <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">{error}</div>}

      {!loading && !error && product && (
        <>
          <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-sm text-white/70">{product.brand}</div>
                <h1 className="text-3xl font-semibold">{product.name}</h1>
                {currentMinPrice !== null && (
                  <div className="mt-2 text-white/70">
                    Mejor precio detectado:{" "}
                    <span className="font-medium text-green-300">
                      {new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" }).format(currentMinPrice)}
                    </span>
                  </div>
                )}
              </div>

              <div className="h-20 w-20 shrink-0 overflow-hidden rounded-2xl bg-white/10">
                {product.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img className="h-full w-full object-cover" src={product.image_url} alt={product.name} />
                ) : null}
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <h2 className="text-xl font-semibold">Precios actuales</h2>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={onRefreshPrices}
                  className="rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-sm hover:bg-white/10"
                >
                  Actualizar precios
                </button>
                <button
                  type="button"
                  onClick={openCreateModal}
                  className="rounded-xl bg-green-500 px-4 py-2 text-sm font-medium text-black hover:bg-green-400"
                >
                  Crear alerta de precio
                </button>
              </div>
            </div>

            <div className="mt-4">
              <PriceTable prices={prices} />
            </div>
          </section>

          <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
            <h2 className="text-xl font-semibold">Historial (30 días)</h2>
            <div className="mt-4">
              <PriceChart history={history} />
            </div>
          </section>
        </>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-gray-900 p-6">
            {modalMode === "auth" ? (
              <>
                <div className="text-lg font-semibold">Inicia sesión</div>
                <p className="mt-2 text-white/70">
                  Para crear alertas necesitas una cuenta premium (JWT de Supabase).
                </p>
                <div className="mt-4 flex gap-3">
                  <a
                    href="/login"
                    className="rounded-xl border border-white/15 bg-white/5 px-4 py-2 text-center text-sm hover:bg-white/10"
                  >
                    Login
                  </a>
                  <button
                    className="rounded-xl bg-white/10 px-4 py-2 text-sm hover:bg-white/20"
                    onClick={() => setModalOpen(false)}
                    type="button"
                  >
                    Cancelar
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="text-lg font-semibold">Crear alerta</div>
                <p className="mt-2 text-white/70">Te avisaremos cuando el precio baje a tu objetivo.</p>

                <div className="mt-4 space-y-3">
                  <label className="block text-sm text-white/70">
                    Precio objetivo (MXN)
                    <input
                      className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-black"
                      value={targetPrice}
                      onChange={(e) => setTargetPrice(e.target.value)}
                      placeholder="Ej. 999"
                      inputMode="decimal"
                    />
                  </label>
                  <label className="block text-sm text-white/70">
                    Talla (opcional)
                    <input
                      className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-black"
                      value={size}
                      onChange={(e) => setSize(e.target.value)}
                      placeholder="Ej. 27"
                    />
                  </label>
                </div>

                <div className="mt-5 flex gap-3">
                  <button
                    type="button"
                    disabled={submitting}
                    onClick={onSubmit}
                    className="flex-1 rounded-xl bg-green-500 px-4 py-2 text-sm font-medium text-black hover:bg-green-400 disabled:opacity-60"
                  >
                    {submitting ? "Creando..." : "Crear alerta"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setModalOpen(false)}
                    className="rounded-xl bg-white/10 px-4 py-2 text-sm hover:bg-white/20"
                  >
                    Cancelar
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

