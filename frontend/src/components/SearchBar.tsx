"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import type { Product } from "@/lib/types";
import { searchProducts } from "@/lib/api";

export default function SearchBar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const canSearch = query.trim().length >= 3;

  const placeholder = useMemo(() => "Busca por modelo, por ejemplo: Pegasus, Supernova…", []);

  useEffect(() => {
    if (!canSearch) {
      setResults([]);
      setOpen(false);
      return;
    }

    let cancelled = false;
    const t = setTimeout(async () => {
      try {
        setLoading(true);
        const res = await searchProducts(query.trim());
        if (cancelled) return;
        setResults(res);
        setOpen(true);
      } catch {
        if (cancelled) return;
        setResults([]);
        setOpen(false);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 350);

    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [canSearch, query]);

  return (
    <div className="relative w-full">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm outline-none placeholder:text-white/40"
        onFocus={() => setOpen(canSearch)}
      />

      {open && (loading || results.length > 0) && (
        <div className="absolute z-20 mt-2 w-full overflow-hidden rounded-2xl border border-white/10 bg-gray-900/95">
          {loading && <div className="p-3 text-sm text-white/70">Buscando…</div>}
          {!loading && results.length === 0 && <div className="p-3 text-sm text-white/70">Sin resultados</div>}
          {!loading &&
            results.map((p) => (
              <Link
                key={p.id}
                href={`/product/${p.id}`}
                onClick={() => setOpen(false)}
                className="flex items-center gap-3 px-3 py-2 hover:bg-white/5"
              >
                {p.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img className="h-10 w-10 shrink-0 rounded-xl object-cover bg-white/10" src={p.image_url} alt={p.name} />
                ) : (
                  <div className="h-10 w-10 shrink-0 rounded-xl bg-white/10" />
                )}
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{p.name}</div>
                  <div className="truncate text-xs text-white/60">{p.brand}</div>
                </div>
                <div className="text-xs text-white/40">Ver</div>
              </Link>
            ))}
        </div>
      )}
    </div>
  );
}

