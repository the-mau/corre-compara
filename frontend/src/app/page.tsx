"use client";

import { useEffect, useState } from "react";

import SearchBar from "@/components/SearchBar";
import type { Product } from "@/lib/types";
import { getProducts } from "@/lib/api";

const popularBrands = ["Nike", "Adidas", "ASICS", "New Balance"];

export default function HomePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const res = await getProducts();
        if (!cancelled) setProducts(res);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Error al cargar productos");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);
  return (
    <div className="space-y-10">
      <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h1 className="text-3xl font-semibold">Encuentra tus tenis favoritos al mejor precio</h1>
        <p className="mt-2 text-white/70">Compara entre tiendas en México y configura alertas para precios.</p>

        <div className="mt-6">
          <SearchBar />
        </div>

        <div className="mt-6 flex flex-wrap gap-2">
          {popularBrands.map((b) => (
            <button
              key={b}
              className="rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm hover:bg-white/10"
              type="button"
            >
              {b}
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-xl font-semibold">Populares</h2>
        {loading && <div className="text-white/70">Cargando productos…</div>}
        {error && !loading && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</div>
        )}
        {!loading && !error && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {products.map((p) => (
              <a
                key={p.id}
                href={`/product/${p.id}`}
                className="rounded-2xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-white/70">{p.brand}</div>
                    <div className="mt-1 font-medium">{p.name}</div>
                  </div>
                  <div className="h-12 w-12 rounded-xl bg-white/10" />
                </div>
                <button
                  type="button"
                  className="mt-4 w-full rounded-xl bg-green-500 px-3 py-2 text-xs font-medium text-black hover:bg-green-400"
                >
                  Ver precios
                </button>
              </a>
            ))}
            {products.length === 0 && (
              <div className="col-span-full text-sm text-white/60">
                Sin productos todavía. Ejecuta el seed de base de datos.
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

