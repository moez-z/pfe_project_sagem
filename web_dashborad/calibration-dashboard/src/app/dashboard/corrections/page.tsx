"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Filter, ExternalLink, SlidersHorizontal } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface CorrectionResult {
  id: number;
  session_id: number;
  band: string | null;
  freq_mhz: number | null;
  modulation: string | null;
  bandwidth: string | null;
  antenna: string | null;
  origin_dbm: number | null;
  dut_dbm: number | null;
  delta_dbm: number | null;
  correction_dbm: number | null;
  tx_target_dbm: number | null;
  status: string | null;
  session: { id: number; product_name: string | null; dut_serial: string | null; created_at: string };
}

interface Stats {
  count: number;
  avgCorr: number;
  avgDelta: number;
  maxCorr: number;
  minCorr: number;
}

interface ApiResponse {
  results: CorrectionResult[];
  total: number;
  page: number;
  totalPages: number;
  bands: string[];
  stats: Stats;
}

export default function CorrectionsPage() {
  const router = useRouter();
  const [data, setData]       = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [band, setBand]       = useState("");
  const [page, setPage]       = useState(1);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    const p = new URLSearchParams({ page: String(page), band });
    const res = await fetch(`/api/dashboard/corrections?${p}`);
    setData(await res.json());
    setLoading(false);
  }, [page, band]);

  useEffect(() => { fetch_(); }, [fetch_]);
  useEffect(() => { setPage(1); }, [band]);

  const statCards = data ? [
    { label: "Total Corrections", value: data.stats.count },
    { label: "Avg Correction",    value: `${data.stats.avgCorr} dBm` },
    { label: "Avg Delta",         value: `${data.stats.avgDelta} dBm` },
    { label: "Max Correction",    value: `${data.stats.maxCorr} dBm` },
    { label: "Min Correction",    value: `${data.stats.minCorr} dBm` },
  ] : [];

  return (
    <div className="space-y-5">
      {/* Stats */}
      {data && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          {statCards.map(({ label, value }) => (
            <Card key={label} className="shadow-sm">
              <CardContent className="p-4 flex items-center gap-3">
                <div className="bg-yellow-50 p-2 rounded-lg">
                  <SlidersHorizontal className="w-4 h-4 text-yellow-600" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">{label}</p>
                  <p className="text-lg font-bold text-slate-800">{value}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Filter */}
      <Card className="shadow-sm">
        <CardContent className="p-4 flex flex-wrap gap-3 items-center">
          <Filter className="w-4 h-4 text-slate-400" />
          <select value={band} onChange={(e) => setBand(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-400 bg-white">
            <option value="">All Bands</option>
            {data?.bands.map((b) => <option key={b} value={b}>{b}</option>)}
          </select>
          <span className="text-xs text-slate-400 ml-auto">{data?.total ?? 0} corrections found</span>
        </CardContent>
      </Card>

      {/* Table */}
      <Card className="shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-slate-700">Applied Corrections</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-48 text-slate-400 text-sm">Loading corrections...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-slate-400 border-b border-slate-100 bg-slate-50">
                    {["Session","Product","DUT Serial","Date","Band","Freq (MHz)","Modulation",
                      "BW","Antenna","Origin dBm","DUT dBm","Δ dBm","Correction dBm","Target"].map(h => (
                      <th key={h} className="px-3 py-2.5 font-medium whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {data?.results.length === 0 && (
                    <tr><td colSpan={14} className="text-center py-12 text-slate-400">No corrections found</td></tr>
                  )}
                  {data?.results.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-3 py-2">
                        <button onClick={() => router.push(`/dashboard/sessions/${r.session_id}`)}
                          className="flex items-center gap-1 text-blue-600 hover:underline font-medium">
                          #{r.session_id} <ExternalLink className="w-3 h-3" />
                        </button>
                      </td>
                      <td className="px-3 py-2 text-slate-600">{r.session.product_name ?? "—"}</td>
                      <td className="px-3 py-2 font-mono text-slate-600">{r.session.dut_serial ?? "—"}</td>
                      <td className="px-3 py-2 text-slate-400">
                        {new Date(r.session.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-3 py-2 font-medium text-slate-700">{r.band}</td>
                      <td className="px-3 py-2 text-slate-600">{r.freq_mhz}</td>
                      <td className="px-3 py-2 text-slate-600">{r.modulation}</td>
                      <td className="px-3 py-2 text-slate-600">{r.bandwidth}</td>
                      <td className="px-3 py-2 text-slate-600">{r.antenna}</td>
                      <td className="px-3 py-2 text-slate-600">{r.origin_dbm?.toFixed(2)}</td>
                      <td className="px-3 py-2 text-slate-600">{r.dut_dbm?.toFixed(2)}</td>
                      <td className={`px-3 py-2 font-medium ${Math.abs(r.delta_dbm ?? 0) > 1 ? "text-red-500" : "text-green-600"}`}>
                        {r.delta_dbm?.toFixed(2)}
                      </td>
                      <td className="px-3 py-2 font-bold text-yellow-600">{r.correction_dbm?.toFixed(3)}</td>
                      <td className="px-3 py-2 text-slate-600">{r.tx_target_dbm?.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {data && data.totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
              <p className="text-xs text-slate-400">Page {data.page} of {data.totalPages}</p>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" disabled={page === 1} onClick={() => setPage(p => p - 1)} className="h-8">
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button size="sm" variant="outline" disabled={page === data.totalPages} onClick={() => setPage(p => p + 1)} className="h-8">
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}