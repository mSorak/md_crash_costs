import type { MetricDef } from "./types";

/** Census NAMELSAD uses "Baltimore city"; display as "Baltimore City" like other counties. */
export function formatGeoName(name: string | null | undefined): string {
  if (!name) return "";
  if (name === "Baltimore city") return "Baltimore City";
  return name;
}

const currencyFmt = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const numberFmt = new Intl.NumberFormat("en-US");
const decimalFmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

export function formatMetric(value: number | null | undefined, metric: MetricDef | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  if (!metric) return numberFmt.format(value);
  switch (metric.format) {
    case "currency":
      return currencyFmt.format(value);
    case "rate":
      if (metric.rate_per === 10_000) return `${decimalFmt.format(value)} per 10,000`;
      if (metric.rate_per === 100_000) return `${decimalFmt.format(value)} per 100k`;
      if (metric.rate_per != null && metric.rate_per !== 1) {
        return `${decimalFmt.format(value)} per ${numberFmt.format(metric.rate_per)}`;
      }
      return decimalFmt.format(value);
    case "percent":
      return `${decimalFmt.format(value)}%`;
    case "number":
    default:
      return numberFmt.format(value);
  }
}

export function formatCurrency(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return currencyFmt.format(v);
}

export function formatNumber(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return numberFmt.format(v);
}

export function formatPerCapita(sum: number | null, pop: number | null, per = 1): string {
  if (sum === null || pop === null || !pop) return "—";
  return decimalFmt.format((sum / pop) * per);
}

/** Total divided by population, shown as currency (per person). */
export function formatPerCapitaCurrency(sum: number | null, pop: number | null): string {
  if (sum === null || pop === null || !pop) return "—";
  return currencyFmt.format(sum / pop);
}
