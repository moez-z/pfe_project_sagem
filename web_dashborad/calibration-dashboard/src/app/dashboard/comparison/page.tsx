"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Download, FileText } from "lucide-react";

interface Column { key: number; label: string; sessionId: number }
interface Row    { key: string; type: "TX" | "RX"; mesureURD: number | null; colValues: Record<number, number | null> }
interface ApiResponse { columns: Column[]; products: string[]; rows: Row[] }

const formatKey = (key: string) => key.split("|").slice(1).filter(Boolean).join(" · ");

const cellColor = (val: number | null, type: string) => {
  if (val === null) return "text-slate-300";
  if (type === "TX") {
    if (Math.abs(val) > 2) return "text-red-600 font-semibold";
    if (Math.abs(val) > 1) return "text-orange-500 font-medium";
    return "text-green-600";
  }
  if (val < -75) return "text-red-600 font-semibold";
  if (val < -70) return "text-orange-500 font-medium";
  return "text-green-600";
};

export default function ComparisonPage() {
  const [data, setData]         = useState<ApiResponse | null>(null);
  const [loading, setLoading]   = useState(false);
  const [product, setProduct]   = useState("");
  const [products, setProducts] = useState<string[]>([]);
  const [typeFilter, setType]   = useState<"ALL" | "TX" | "RX">("ALL");
  const tableRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/dashboard/comparison")
      .then(r => r.json())
      .then(d => setProducts(d.products ?? []));
  }, []);

  const fetchData = useCallback(async () => {
    if (!product) return;
    setLoading(true);
    const res = await fetch(`/api/dashboard/comparison?product=${encodeURIComponent(product)}`);
    setData(await res.json());
    setLoading(false);
  }, [product]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filteredRows = data?.rows.filter(r =>
    typeFilter === "ALL" ? true : r.type === typeFilter
  ) ?? [];

  // ── CSV Export ──────────────────────────────────────────────
  const exportCSV = () => {
    if (!data || filteredRows.length === 0) return;
    const headers = ["Type", "Test", "Mesure URD", ...data.columns.map(c => c.label)];
    const rows = filteredRows.map(r => [
      r.type,
      `"${formatKey(r.key)}"`,
      r.mesureURD?.toFixed(2) ?? "",
      ...data.columns.map(c => r.colValues[c.key]?.toFixed(2) ?? ""),
    ]);
    const csv  = [headers, ...rows].map(r => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `comparison_${product}_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ── PDF Export ──────────────────────────────────────────────
  const exportPDF = () => {
    if (!data || filteredRows.length === 0) return;
    const printWindow = window.open("", "_blank");
    if (!printWindow) return;

    const headers = ["Type", "Test", "Mesure URD", ...data.columns.map(c => c.label)];
    const rowsHtml = filteredRows.map(r => `
      <tr>
        <td style="color:${r.type === "TX" ? "#7c3aed" : "#0891b2"};font-weight:600">${r.type}</td>
        <td style="font-family:monospace;font-size:10px">${formatKey(r.key)}</td>
        <td style="text-align:right;font-weight:600">${r.mesureURD?.toFixed(2) ?? "—"}</td>
        ${data.columns.map(c => {
          const val   = r.colValues[c.key] ?? null;
          const color = val === null ? "#cbd5e1"
            : r.type === "TX"
              ? Math.abs(val) > 2 ? "#dc2626" : Math.abs(val) > 1 ? "#f97316" : "#16a34a"
              : val < -75 ? "#dc2626" : val < -70 ? "#f97316" : "#16a34a";
          return `<td style="text-align:right;color:${color};font-weight:500">${val !== null ? val.toFixed(2) : "—"}</td>`;
        }).join("")}
      </tr>`).join("");

    printWindow.document.write(`
      <!DOCTYPE html><html>
      <head>
        <title>Comparison – ${product}</title>
        <style>
          body  { font-family: Arial, sans-serif; font-size: 11px; margin: 20px; color: #1e293b; }
          h2    { color: #1e40af; margin-bottom: 4px; }
          p     { color: #64748b; margin: 0 0 12px; }
          table { width: 100%; border-collapse: collapse; }
          th    { background: #f1f5f9; color: #94a3b8; font-size: 10px; text-align: left;
                  padding: 6px 8px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
          td    { padding: 5px 8px; border-bottom: 1px solid #f8fafc; }
          .footer { margin-top: 16px; font-size: 10px; color: #94a3b8; }
        </style>
      </head>
      <body>
        <h2>Posts Comparison — ${product}</h2>
        <p>Generated: ${new Date().toLocaleString()} · Filter: ${typeFilter}</p>
        <table>
          <thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead>
          <tbody>${rowsHtml}</tbody>
        </table>
        <div class="footer">wifi_calibration · calibration-dashboard</div>
        <script>window.onload = () => { window.print(); window.close(); }<\/script>
      </body></html>
    `);
    printWindow.document.close();
  };

  return (
    <div className="space-y-5">
      {/* Filters */}
      <Card className="shadow-sm">
        <CardContent className="p-4 flex flex-wrap gap-3 items-center">
          <select value={product} onChange={e => setProduct(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
            <option value="">Select a product...</option>
            {products.map(p => <option key={p} value={p}>{p}</option>)}
          </select>

          <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
            {["ALL", "TX", "RX"].map(t => (
              <button key={t} onClick={() => setType(t as any)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  typeFilter === t ? "bg-white shadow text-slate-800" : "text-slate-500 hover:text-slate-700"
                }`}>
                {t}
              </button>
            ))}
          </div>

          {data && (
            <div className="flex items-center gap-3 text-xs text-slate-500">
              <span><span className="font-semibold text-slate-700">{data.columns.length}</span> sessions</span>
              <span><span className="font-semibold text-slate-700">{filteredRows.length}</span> tests</span>
            </div>
          )}

          {data && filteredRows.length > 0 && (
            <div className="flex gap-2 ml-auto">
              <Button size="sm" variant="outline" onClick={exportCSV}
                className="h-8 text-green-700 border-green-200 hover:bg-green-50 flex items-center gap-1.5">
                <Download className="w-3.5 h-3.5" /> CSV
              </Button>
              <Button size="sm" variant="outline" onClick={exportPDF}
                className="h-8 text-red-700 border-red-200 hover:bg-red-50 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5" /> PDF
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {!product && (
        <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
          Select a product to view the comparison table
        </div>
      )}
      {loading && (
        <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
          Loading comparison...
        </div>
      )}

      {!loading && data && product && (
        <Card className="shadow-sm">
          <CardHeader className="pb-2 flex flex-row items-center justify-between flex-wrap gap-2">
            <CardTitle className="text-sm font-semibold text-slate-700">
              {product} — Posts Comparison
            </CardTitle>
            <div className="flex gap-2 flex-wrap">
              {data.columns.map(c => (
                <Badge key={c.key} className="bg-blue-100 text-blue-700 hover:bg-blue-100 text-xs">
                  {c.label}
                </Badge>
              ))}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto" ref={tableRef}>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-slate-400 border-b border-slate-100 bg-slate-50">
                    <th className="px-3 py-2.5 font-medium w-10">Type</th>
                    <th className="px-3 py-2.5 font-medium min-w-[300px]">Test</th>
                    <th className="px-3 py-2.5 font-medium text-right">Mesure URD</th>
                    {data.columns.map(c => (
                      <th key={c.key} className="px-3 py-2.5 font-medium text-right whitespace-nowrap">
                        {c.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {filteredRows.length === 0 && (
                    <tr>
                      <td colSpan={3 + data.columns.length} className="text-center py-12 text-slate-400">
                        No data available for this product
                      </td>
                    </tr>
                  )}
                  {filteredRows.map((row, i) => (
                    <tr key={i} className={`hover:bg-slate-50 transition-colors ${row.type === "RX" ? "bg-blue-50/30" : ""}`}>
                      <td className="px-3 py-2">
                        <Badge className={row.type === "TX"
                          ? "bg-purple-100 text-purple-700 hover:bg-purple-100"
                          : "bg-cyan-100 text-cyan-700 hover:bg-cyan-100"}>
                          {row.type}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 font-mono text-slate-600 text-[11px]">{formatKey(row.key)}</td>
                      <td className="px-3 py-2 text-right font-medium text-slate-700">
                        {row.mesureURD?.toFixed(2) ?? "—"}
                      </td>
                      {data.columns.map(c => {
                        const val = row.colValues[c.key] ?? null;
                        return (
                          <td key={c.key} className={`px-3 py-2 text-right ${cellColor(val, row.type)}`}>
                            {val !== null ? val.toFixed(2) : "—"}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}