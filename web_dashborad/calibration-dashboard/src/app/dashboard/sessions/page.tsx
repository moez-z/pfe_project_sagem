"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle, XCircle, Search, ChevronLeft,
  ChevronRight, Filter, Eye,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface Session {
  id: number;
  dut_serial: string;
  origin_serial: string;
  product_name: string;
  overall_pass: boolean;
  avg_delta_dbm: number;
  max_delta_dbm: number;
  tx_total: number;
  tx_pass: number;
  tx_fail: number;
  tx_corrections: number;
  rx_total: number;
  rx_pass: number;
  rx_fail: number;
  tolerance_dbm: number;
  created_at: string;
  notes: string | null;
  user: { full_name: string; matricule: string } | null;
  _count: { tx_results: number; rx_results: number };
}

interface ApiResponse {
  sessions: Session[];
  total: number;
  page: number;
  totalPages: number;
  products: string[];
}

export default function SessionsPage() {
  const router = useRouter();
  const [data, setData]       = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState("");
  const [status, setStatus]   = useState("all");
  const [product, setProduct] = useState("");
  const [page, setPage]       = useState(1);

  const fetchSessions = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({
      page: String(page),
      search,
      status,
      product,
    });
    const res  = await fetch(`/api/dashboard/sessions?${params}`);
    const json = await res.json();
    setData(json);
    setLoading(false);
  }, [page, search, status, product]);

  useEffect(() => { fetchSessions(); }, [fetchSessions]);

  // Reset to page 1 when filters change
  useEffect(() => { setPage(1); }, [search, status, product]);

  return (
    <div className="space-y-5">
      {/* Filters */}
      <Card className="shadow-sm">
        <CardContent className="p-4 flex flex-wrap gap-3 items-center">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by serial, product..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Status filter */}
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

          {/* Product filter */}
          {data?.products && data.products.length > 0 && (
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-400" />
              <select
                value={product}
                onChange={(e) => setProduct(e.target.value)}
                className="text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                <option value="">All Products</option>
                {data.products.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          )}

          {/* Total count */}
          <span className="text-xs text-slate-400 ml-auto">
            {data?.total ?? 0} sessions found
          </span>
        </CardContent>
      </Card>

      {/* Table */}
      <Card className="shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-slate-700">
            Calibration Sessions
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
              Loading sessions...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-slate-400 border-b border-slate-100 bg-slate-50">
                    <th className="px-4 py-3 font-medium">ID</th>
                    <th className="px-4 py-3 font-medium">DUT Serial</th>
                    <th className="px-4 py-3 font-medium">Product</th>
                    <th className="px-4 py-3 font-medium">Operator</th>
                    <th className="px-4 py-3 font-medium">TX</th>
                    <th className="px-4 py-3 font-medium">RX</th>
                    <th className="px-4 py-3 font-medium">Corrections</th>
                    <th className="px-4 py-3 font-medium">Avg Δ dBm</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {data?.sessions?.length === 0 && (
                    <tr>
                      <td colSpan={11} className="text-center py-12 text-slate-400">
                        No sessions found
                      </td>
                    </tr>
                  )}
                  {data?.sessions?.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 text-slate-400 font-mono text-xs">#{s.id}</td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-700">{s.dut_serial}</td>
                      <td className="px-4 py-3 text-slate-700">{s.product_name}</td>
                      <td className="px-4 py-3 text-slate-500 text-xs">
                        {s.user ? (
                          <div>
                            <p className="text-slate-700 font-medium">{s.user.full_name}</p>
                            <p className="text-slate-400">{s.user.matricule}</p>
                          </div>
                        ) : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-xs">
                          <span className="text-green-600 font-medium">{s.tx_pass}✓</span>
                          {" / "}
                          <span className="text-red-500">{s.tx_fail}✗</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-xs">
                          <span className="text-green-600 font-medium">{s.rx_pass}✓</span>
                          {" / "}
                          <span className="text-red-500">{s.rx_fail}✗</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-700 text-center">{s.tx_corrections}</td>
                      <td className="px-4 py-3 text-slate-700">{s.avg_delta_dbm?.toFixed(2)}</td>
                      <td className="px-4 py-3">
                        <Badge
                          className={
                            s.overall_pass
                              ? "bg-green-100 text-green-700 hover:bg-green-100"
                              : "bg-red-100 text-red-700 hover:bg-red-100"
                          }
                        >
                          {s.overall_pass ? (
                            <span className="flex items-center gap-1">
                              <CheckCircle className="w-3 h-3" /> Pass
                            </span>
                          ) : (
                            <span className="flex items-center gap-1">
                              <XCircle className="w-3 h-3" /> Fail
                            </span>
                          )}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-xs">
                        {new Date(s.created_at).toLocaleDateString()}<br />
                        <span className="text-slate-300">
                          {new Date(s.created_at).toLocaleTimeString()}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => router.push(`/dashboard/sessions/${s.id}`)}
                          className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 h-8 px-2"
                        >
                          <Eye className="w-4 h-4 mr-1" /> View
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {data && data.totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
              <p className="text-xs text-slate-400">
                Page {data.page} of {data.totalPages}
              </p>
              <div className="flex items-center gap-2">
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