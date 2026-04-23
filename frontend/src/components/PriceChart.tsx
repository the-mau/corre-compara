"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { PriceHistory } from "@/lib/types";

type ChartPoint = {
  label: string;
  timestamp: number;
  price: number;
};

function asNumber(value: unknown): number | null {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const n = Number(String(value));
  return Number.isFinite(n) ? n : null;
}

export default function PriceChart({ history }: { history: PriceHistory[] }) {
  const points: ChartPoint[] = history
    .map((h) => {
      const n = asNumber(h.price);
      if (n === null) return null;
      const d = new Date(h.scraped_at);
      const label = Number.isNaN(d.getTime()) ? "" : d.toLocaleDateString("es-MX");
      return { label, timestamp: d.getTime(), price: n };
    })
    .filter((x): x is ChartPoint => x !== null)
    .sort((a, b) => a.timestamp - b.timestamp);

  const minPrice = points.length ? Math.min(...points.map((p) => p.price)) : null;

  return (
    <div className="w-full">
      {points.length === 0 ? (
        <div className="text-sm text-white/60">Sin historial suficiente.</div>
      ) : (
        <LineChart width={800} height={300} data={points}>
          <CartesianGrid stroke="rgba(255,255,255,0.08)" />
          <XAxis dataKey="label" tick={{ fill: "rgba(255,255,255,0.7)", fontSize: 12 }} />
          <YAxis tick={{ fill: "rgba(255,255,255,0.7)", fontSize: 12 }} domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{ background: "rgba(0,0,0,0.8)", border: "1px solid rgba(255,255,255,0.1)" }}
            formatter={(value: any) => [`${value} MXN`, "Precio"]}
            labelFormatter={(label: any) => String(label)}
          />
          {minPrice !== null && <ReferenceLine y={minPrice} stroke="rgba(34,197,94,0.9)" strokeDasharray="4 4" />}
          <Line type="monotone" dataKey="price" stroke="#22c55e" strokeWidth={2} dot={false} />
        </LineChart>
      )}
    </div>
  );
}

