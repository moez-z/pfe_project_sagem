"use client";

import { useEffect, useState, useCallback } from "react";
import {
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Radio,
  Antenna,
  Filter,
  X,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface Session {
  id: number;
  product_name: string | null;
  dut_serial: string | null;
  overall_pass: boolean | null;
  avg_delta_dbm: number | null;
  tx_corrections: number | null;
  created_at: string;
  user: { id: number; full_name: string | null; matricule: string } | null;
  post: { id: number; name: string; number: number } | null;
  _count: { tx_results: number; rx_results: number };
}

interface TxResult {
  id: number;
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
  limit_lo: number | null;
  limit_hi: number | null;
  status: string | null;
}

interface RxResult {
  id: number;
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
}

interface UserOption {
  id: number;
  full_name: string | null;
  matricule: string;
}
interface PostOption {
  id: number;
  name: string;
  number: number;
}

interface ApiResponse {
  sessions: Session[];
  total: number;
  page: number;
  totalPages: number;
  users: UserOption[];
  posts: PostOption[];
}

const statusColor = (s: string | null) =>
  s?.toLowerCase() === "pass"
    ? "bg-green-100 text-green-700 hover:bg-green-100"
    : "bg-red-100 text-red-700 hover:bg-red-100";

export default function CalibrationsPage() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  // Filters
  const [userId, setUserId] = useState("");
  const [postId, setPostId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Expand
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [expandTab, setExpandTab] = useState<"tx" | "rx">("tx");
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailData, setDetailData] = useState<{
    tx: TxResult[];
    rx: RxResult[];
  } | null>(null);

  const fetchList = useCallback(async () => {
    setLoading(true);
    const p = new URLSearchParams({
      page: String(page),
      ...(userId && { user: userId }),
      ...(postId && { post: postId }),
      ...(dateFrom && { dateFrom }),
      ...(dateTo && { dateTo }),
    });
    const res = await fetch(`/api/dashboard/calibrations?${p}`);
    setData(await res.json());
    setLoading(false);
  }, [page, userId, postId, dateFrom, dateTo]);

  useEffect(() => {
    fetchList();
  }, [fetchList]);
  useEffect(() => {
    setPage(1);
  }, [userId, postId, dateFrom, dateTo]);

  const clearFilters = () => {
    setUserId("");
    setPostId("");
    setDateFrom("");
    setDateTo("");
  };

  const hasFilters = userId || postId || dateFrom || dateTo;

  const handleExpand = async (session: Session) => {
    if (expandedId === session.id) {
      setExpandedId(null);
      setDetailData(null);
      return;
    }
    setExpandedId(session.id);
    setExpandTab("tx");
    setDetailLoading(true);
    const res = await fetch(`/api/dashboard/sessions/${session.id}`);
    const json = await res.json();
    setDetailData({ tx: json.tx_results ?? [], rx: json.rx_results ?? [] });
    setDetailLoading(false);
  };

  return (
    <div className="space-y-5">
      {/* Filters */}
      <Card className="shadow-sm">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-3 items-end">
            <Filter className="w-4 h-4 text-slate-400 mt-6" />

            {/* User filter */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-500 font-medium">
                Operator
              </label>
              <select
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white min-w-[160px]"
              >
                <option value="">All Operators</option>
                {data?.users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name ?? u.matricule}
                  </option>
                ))}
              </select>
            </div>

            {/* Post filter */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-500 font-medium">
                Post (Caisson)
              </label>
              <select
                value={postId}
                onChange={(e) => setPostId(e.target.value)}
                className="text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white min-w-[140px]"
              >
                <option value="">All Posts</option>
                {data?.posts.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Date From */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-500 font-medium">From</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              />
            </div>

            {/* Date To */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-500 font-medium">To</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              />
            </div>

            {/* Clear */}
            {hasFilters && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearFilters}
                className="flex items-center gap-1 text-slate-500 h-9 mt-5"
              >
                <X className="w-3.5 h-3.5" /> Clear
              </Button>
            )}

            <span className="text-xs text-slate-400 ml-auto mt-5">
              {data?.total ?? 0} calibrations found
            </span>
          </div>
        </CardContent>
      </Card>

      {/* List */}
      <Card className="shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-slate-700">
            All Calibrations
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
              Loading calibrations...
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {data?.sessions.length === 0 && (
                <div className="text-center py-12 text-slate-400 text-sm">
                  No calibrations found
                </div>
              )}
              {data?.sessions.map((s) => (
                <div key={s.id}>
                  <button
                    onClick={() => handleExpand(s)}
                    className="w-full flex items-center gap-4 px-4 py-3.5 hover:bg-slate-50 transition-colors text-left"
                  >
                    <div className="shrink-0">
                      {s.overall_pass ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-500" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0 grid grid-cols-2 lg:grid-cols-5 gap-2">
                      <div>
                        <p className="text-xs text-slate-400">Product</p>
                        <p className="text-sm font-medium text-slate-700 truncate">
                          {s.product_name ?? "—"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">DUT Serial</p>
                        <p className="text-sm font-mono text-slate-600 truncate">
                          {s.dut_serial ?? "—"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Operator</p>
                        <p className="text-sm text-slate-600 truncate">
                          {s.user?.full_name ?? "—"}
                        </p>
                        <p className="text-xs text-slate-400 font-mono">
                          {s.user?.matricule}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Post</p>
                        <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100 text-xs mt-0.5">
                          {s.post ? s.post.name : "No post"}
                        </Badge>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Date</p>
                        <p className="text-sm text-slate-600">
                          {new Date(s.created_at).toLocaleDateString()}
                        </p>
                        <p className="text-xs text-slate-400">
                          {new Date(s.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>

                    <div className="hidden lg:flex items-center gap-3 shrink-0 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Radio className="w-3.5 h-3.5" />
                        {s._count.tx_results} TX
                      </span>
                      <span className="flex items-center gap-1">
                        <Antenna className="w-3.5 h-3.5" />
                        {s._count.rx_results} RX
                      </span>
                    </div>

                    <div className="shrink-0 text-slate-400">
                      {expandedId === s.id ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </div>
                  </button>

                  {/* Expanded detail */}
                  {expandedId === s.id && (
                    <div className="bg-slate-50 border-t border-slate-100 px-4 py-4">
                      <div className="flex gap-2 mb-4">
                        <button
                          onClick={() => setExpandTab("tx")}
                          className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-all flex items-center gap-1.5 ${
                            expandTab === "tx"
                              ? "bg-blue-600 text-white"
                              : "text-slate-500 hover:bg-slate-200"
                          }`}
                        >
                          <Radio className="w-3.5 h-3.5" />
                          TX Results {detailData && `(${detailData.tx.length})`}
                        </button>
                        <button
                          onClick={() => setExpandTab("rx")}
                          className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-all flex items-center gap-1.5 ${
                            expandTab === "rx"
                              ? "bg-blue-600 text-white"
                              : "text-slate-500 hover:bg-slate-200"
                          }`}
                        >
                          <Antenna className="w-3.5 h-3.5" />
                          RX Results {detailData && `(${detailData.rx.length})`}
                        </button>
                      </div>

                      {detailLoading ? (
                        <div className="text-center py-8 text-slate-400 text-sm">
                          Loading results...
                        </div>
                      ) : (
                        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                          {expandTab === "tx" ? (
                            <table className="w-full text-xs">
                              <thead>
                                <tr className="text-left text-slate-400 border-b border-slate-100 bg-slate-50">
                                  {[
                                    "Band",
                                    "Freq (MHz)",
                                    "Modulation",
                                    "BW",
                                    "Antenna",
                                    "Origin dBm",
                                    "DUT dBm",
                                    "Δ dBm",
                                    "Correction",
                                    "Target",
                                    "Lo",
                                    "Hi",
                                    "Status",
                                  ].map((h) => (
                                    <th
                                      key={h}
                                      className="px-3 py-2 font-medium whitespace-nowrap"
                                    >
                                      {h}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-50">
                                {detailData?.tx.length === 0 && (
                                  <tr>
                                    <td
                                      colSpan={13}
                                      className="text-center py-6 text-slate-400"
                                    >
                                      No TX results
                                    </td>
                                  </tr>
                                )}
                                {detailData?.tx.map((r) => (
                                  <tr key={r.id} className="hover:bg-slate-50">
                                    <td className="px-3 py-2 font-medium text-slate-700">
                                      {r.band}
                                    </td>
                                    <td className="px-3 py-2 text-slate-600">
                                      {r.freq_mhz}
                                    </td>
                                    <td className="px-3 py-2 text-slate-600">
                                      {r.modulation}
                                    </td>
                                    <td className="px-3 py-2 text-slate-600">
                                      {r.bandwidth}
                                    </td>
                                    <td className="px-3 py-2 text-slate-600">
                                      {r.antenna}
                                    </td>
                                    <td className="px-3 py-2 text-slate-600">
                                      {r.origin_dbm?.toFixed(2)}
                                    </td>
                                    <td className="px-3 py-2 text-slate-600">
                                      {r.dut_dbm?.toFixed(2)}
                                    </td>
                                    <td
                                      className={`px-3 py-2 font-medium ${Math.abs(r.delta_dbm ?? 0) > 1 ? "text-red-500" : "text-green-600"}`}
                                    >
                                      {r.delta_dbm?.toFixed(2)}
                                    </td>
                                    <td className="px-3 py-2 text-yellow-600 font-medium">
                                      {r.correction_dbm?.toFixed(2)}
                                    </td>
                                    <td className="px-3 py-2 text-slate-600">
                                      {r.tx_target_dbm?.toFixed(2)}
                                    </td>
                                    <td className="px-3 py-2 text-slate-400">
                                      {r.limit_lo?.toFixed(1)}
                                    </td>
                                    <td className="px-3 py-2 text-slate-400">
                                      {r.limit_hi?.toFixed(1)}
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
                          ) : (
                            <table className="w-full text-xs">
                              <thead>
                                <tr className="text-left text-slate-400 border-b border-slate-100 bg-slate-50">
                                  {[
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
                                      className="px-3 py-2 font-medium whitespace-nowrap"
                                    >
                                      {h}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-50">
                                {detailData?.rx.length === 0 && (
                                  <tr>
                                    <td
                                      colSpan={11}
                                      className="text-center py-6 text-slate-400"
                                    >
                                      No RX results
                                    </td>
                                  </tr>
                                )}
                                {detailData?.rx.map((r) => (
                                  <tr key={r.id} className="hover:bg-slate-50">
                                    <td className="px-3 py-2 font-medium text-slate-700">
                                      {r.band}
                                    </td>
                                    <td className="px-3 py-2 text-slate-600">
                                      {r.freq_mhz}
                                    </td>
                                    <td className="px-3 py-2 text-slate-600">
                                      {r.mcs}
                                    </td>
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
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
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
