"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Filter, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface RxResult {
  id: number;
  session_id: number;
  band: string | null;
  freq_mhz: number | null;
  mcs: string | null;
  bandwidth: string | null;
  antenna_label: string | null;
  origin_rssi: number | null;
  dut_rssi: number | null;
  rssi_delta: number | null;
  origin_per: number | null;
  dut_per: number | null;
  status: string | null;
  session: {
    id: number;
    product_name: string | null;
    dut_serial: string | null;
  };
}

interface ApiResponse {
  results: RxResult[];
  total: number;
  page: number;
  totalPages: number;
  bands: string[];
}

const statusColor = (s: string | null) =>
  s?.toLowerCase() === "pass"
    ? "bg-green-100 text-green-700 hover:bg-green-100"
    : "bg-red-100 text-red-700 hover:bg-red-100";

export default function RxResultsPage() {
  const router = useRouter();
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [band, setBand] = useState("");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    const p = new URLSearchParams({ page: String(page), band, status });
    const res = await fetch(`/api/dashboard/rx-results?${p}`);
    setData(await res.json());
    setLoading(false);
  }, [page, band, status]);

  useEffect(() => {
    fetch_();
  }, [fetch_]);
  useEffect(() => {
    setPage(1);
  }, [band, status]);

  return (
    <div className="space-y-5">
      {/* Filters */}
      <Card className="shadow-sm">
        <CardContent className="p-4 flex flex-wrap gap-3 items-center">
          <Filter className="w-4 h-4 text-slate-400" />

          <select
            value={band}
            onChange={(e) => setBand(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          >
            <option value="">All Bands</option>
            {data?.bands.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>

          <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
            {["all", "pass", "fail"].map((s) => (
              <button
                key={s}
                onClick={() => setStatus(s)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all capitalize ${
                  status === s
                    ? "bg-white shadow text-slate-800"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          <span className="text-xs text-slate-400 ml-auto">
            {data?.total ?? 0} results
          </span>
        </CardContent>
      </Card>

      {/* Table */}
      <Card className="shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-slate-700">
            RX Results
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
              Loading RX results...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-slate-400 border-b border-slate-100 bg-slate-50">
                    {[
                      "Session",
                      "Product",
                      "DUT Serial",
                      "Band",
                      "Freq (MHz)",
                      "MCS",
                      "BW",
                      "Antenna",
                      "Origin RSSI",
                      "DUT RSSI",
                      "Δ RSSI",
                      "Origin PER",
                      "DUT PER",
                      "Status",
                    ].map((h) => (
                      <th
                        key={h}
                        className="px-3 py-2.5 font-medium whitespace-nowrap"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {data?.results.length === 0 && (
                    <tr>
                      <td
                        colSpan={14}
                        className="text-center py-12 text-slate-400"
                      >
                        No RX results found
                      </td>
                    </tr>
                  )}
                  {data?.results.map((r) => (
                    <tr
                      key={r.id}
                      className="hover:bg-slate-50 transition-colors"
                    >
                      <td className="px-3 py-2">
                        <button
                          onClick={() =>
                            router.push(`/dashboard/sessions/${r.session_id}`)
                          }
                          className="flex items-center gap-1 text-blue-600 hover:underline font-medium"
                        >
                          #{r.session_id} <ExternalLink className="w-3 h-3" />
                        </button>
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {r.session.product_name ?? "—"}
                      </td>
                      <td className="px-3 py-2 font-mono text-slate-600">
                        {r.session.dut_serial ?? "—"}
                      </td>
                      <td className="px-3 py-2 font-medium text-slate-700">
                        {r.band}
                      </td>
                      <td className="px-3 py-2 text-slate-600">{r.freq_mhz}</td>
                      <td className="px-3 py-2 text-slate-600">{r.mcs}</td>
                      <td className="px-3 py-2 text-slate-600">
                        {r.bandwidth}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {r.antenna_label}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {r.origin_rssi?.toFixed(2)}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {r.dut_rssi?.toFixed(2)}
                      </td>
                      <td
                        className={`px-3 py-2 font-medium ${Math.abs(r.rssi_delta ?? 0) > 1 ? "text-red-500" : "text-green-600"}`}
                      >
                        {r.rssi_delta?.toFixed(2)}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {r.origin_per?.toFixed(2)}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {r.dut_per?.toFixed(2)}
                      </td>
                      <td className="px-3 py-2">
                        <Badge className={statusColor(r.status)}>
                          {r.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {data && data.totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
              <p className="text-xs text-slate-400">
                Page {data.page} of {data.totalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="h-8"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page === data.totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="h-8"
                >
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
