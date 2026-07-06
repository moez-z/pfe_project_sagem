"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  CheckCircle,
  XCircle,
  ArrowLeft,
  Radio,
  Antenna,
  SlidersHorizontal,
  User,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface SessionDetail {
  id: number;
  dut_serial: string;
  origin_serial: string;
  product_name: string;
  dut_filename: string;
  origin_filename: string;
  tolerance_dbm: number;
  overall_pass: boolean;
  tx_total: number;
  tx_pass: number;
  tx_fail: number;
  tx_corrections: number;
  rx_total: number;
  rx_pass: number;
  rx_fail: number;
  avg_delta_dbm: number;
  max_delta_dbm: number;
  created_at: string;
  notes: string | null;
  user: { full_name: string; matricule: string; role: string } | null;
  tx_results: {
    id: number;
    band: string;
    freq_mhz: number;
    modulation: string;
    bandwidth: string;
    antenna: string;
    origin_dbm: number;
    dut_dbm: number;
    delta_dbm: number;
    correction_dbm: number;
    limit_lo: number;
    limit_hi: number;
    status: string;
  }[];
  rx_results: {
    id: number;
    band: string;
    freq_mhz: number;
    mcs: string;
    bandwidth: string;
    antenna_label: string;
    origin_rssi: number;
    dut_rssi: number;
    rssi_delta: number;
    origin_per: number;
    dut_per: number;
    status: string;
  }[];
}

export default function SessionDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"tx" | "rx">("tx");

  useEffect(() => {
    fetch(`/api/dashboard/sessions/${id}`)
      .then((r) => r.json())
      .then((d) => {
        setSession(d);
        setLoading(false);
      });
  }, [id]);

  if (loading)
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        Loading session...
      </div>
    );
  if (!session)
    return (
      <div className="text-center text-slate-400 mt-20">Session not found.</div>
    );

  const infoItems = [
    { label: "DUT Serial", value: session.dut_serial },
    { label: "Origin Serial", value: session.origin_serial },
    { label: "Product", value: session.product_name },
    { label: "Tolerance", value: `${session.tolerance_dbm} dBm` },
    { label: "Avg Δ dBm", value: session.avg_delta_dbm?.toFixed(3) },
    { label: "Max Δ dBm", value: session.max_delta_dbm?.toFixed(3) },
    { label: "DUT File", value: session.dut_filename },
    { label: "Origin File", value: session.origin_filename },
    { label: "Date", value: new Date(session.created_at).toLocaleString() },
    { label: "Notes", value: session.notes ?? "—" },
  ];

  return (
    <div className="space-y-5">
      {/* Back + title */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.back()}
          className="text-slate-500"
        >
          <ArrowLeft className="w-4 h-4 mr-1" /> Back
        </Button>
        <h2 className="text-lg font-semibold text-slate-800">
          Session #{session.id}
        </h2>
        <Badge
          className={
            session.overall_pass
              ? "bg-green-100 text-green-700 hover:bg-green-100"
              : "bg-red-100 text-red-700 hover:bg-red-100"
          }
        >
          {session.overall_pass ? (
            <span className="flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              Pass
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <XCircle className="w-3 h-3" />
              Fail
            </span>
          )}
        </Badge>
      </div>

      {/* Info + Operator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2 shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-slate-700">
              Session Info
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-3">
              {infoItems.map(({ label, value }) => (
                <div key={label}>
                  <dt className="text-xs text-slate-400">{label}</dt>
                  <dd className="text-sm text-slate-700 font-medium truncate">
                    {value}
                  </dd>
                </div>
              ))}
            </dl>
          </CardContent>
        </Card>

        <div className="space-y-4">
          {/* Operator */}
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <User className="w-4 h-4" />
                Operator
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              <p className="text-sm font-medium text-slate-700">
                {session.user?.full_name ?? "—"}
              </p>
              <p className="text-xs text-slate-400">
                {session.user?.matricule}
              </p>
              <Badge variant="outline" className="text-xs">
                {session.user?.role}
              </Badge>
            </CardContent>
          </Card>

          {/* Stats */}
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="text-sm font-semibold text-slate-700">
                Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-3">
              {[
                {
                  icon: Radio,
                  label: "TX Pass",
                  value: session.tx_pass,
                  color: "text-green-600",
                },
                {
                  icon: Radio,
                  label: "TX Fail",
                  value: session.tx_fail,
                  color: "text-red-500",
                },
                {
                  icon: Antenna,
                  label: "RX Pass",
                  value: session.rx_pass,
                  color: "text-green-600",
                },
                {
                  icon: Antenna,
                  label: "RX Fail",
                  value: session.rx_fail,
                  color: "text-red-500",
                },
                {
                  icon: SlidersHorizontal,
                  label: "Corrections",
                  value: session.tx_corrections,
                  color: "text-yellow-600",
                },
              ].map(({ icon: Icon, label, value, color }) => (
                <div key={label} className="flex items-center gap-2">
                  <Icon className={`w-4 h-4 ${color}`} />
                  <div>
                    <p className="text-xs text-slate-400">{label}</p>
                    <p className={`text-sm font-bold ${color}`}>{value}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* TX / RX Results Tabs */}
      <Card className="shadow-sm">
        <CardHeader>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setTab("tx")}
              className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-all ${tab === "tx" ? "bg-blue-600 text-white" : "text-slate-500 hover:bg-slate-100"}`}
            >
              TX Results ({session.tx_results.length})
            </button>
            <button
              onClick={() => setTab("rx")}
              className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-all ${tab === "rx" ? "bg-blue-600 text-white" : "text-slate-500 hover:bg-slate-100"}`}
            >
              RX Results ({session.rx_results.length})
            </button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            {tab === "tx" ? (
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
                      "Lo",
                      "Hi",
                      "Status",
                    ].map((h) => (
                      <th key={h} className="px-3 py-2.5 font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {session.tx_results.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50">
                      <td className="px-3 py-2">{r.band}</td>
                      <td className="px-3 py-2">{r.freq_mhz}</td>
                      <td className="px-3 py-2">{r.modulation}</td>
                      <td className="px-3 py-2">{r.bandwidth}</td>
                      <td className="px-3 py-2">{r.antenna}</td>
                      <td className="px-3 py-2">{r.origin_dbm?.toFixed(2)}</td>
                      <td className="px-3 py-2">{r.dut_dbm?.toFixed(2)}</td>
                      <td
                        className={`px-3 py-2 font-medium ${Math.abs(r.delta_dbm) > 1 ? "text-red-500" : "text-green-600"}`}
                      >
                        {r.delta_dbm?.toFixed(2)}
                      </td>
                      <td className="px-3 py-2 text-yellow-600 font-medium">
                        {r.correction_dbm?.toFixed(2)}
                      </td>
                      <td className="px-3 py-2 text-slate-400">
                        {r.limit_lo?.toFixed(1)}
                      </td>
                      <td className="px-3 py-2 text-slate-400">
                        {r.limit_hi?.toFixed(1)}
                      </td>
                      <td className="px-3 py-2">
                        <Badge
                          className={
                            r.status === "pass" || r.status === "PASS"
                              ? "bg-green-100 text-green-700 hover:bg-green-100"
                              : "bg-red-100 text-red-700 hover:bg-red-100"
                          }
                        >
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
                      <th key={h} className="px-3 py-2.5 font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {session.rx_results.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50">
                      <td className="px-3 py-2">{r.band}</td>
                      <td className="px-3 py-2">{r.freq_mhz}</td>
                      <td className="px-3 py-2">{r.mcs}</td>
                      <td className="px-3 py-2">{r.bandwidth}</td>
                      <td className="px-3 py-2">{r.antenna_label}</td>
                      <td className="px-3 py-2">{r.origin_rssi?.toFixed(2)}</td>
                      <td className="px-3 py-2">{r.dut_rssi?.toFixed(2)}</td>
                      <td
                        className={`px-3 py-2 font-medium ${Math.abs(r.rssi_delta) > 1 ? "text-red-500" : "text-green-600"}`}
                      >
                        {r.rssi_delta?.toFixed(2)}
                      </td>
                      <td className="px-3 py-2">{r.origin_per?.toFixed(2)}</td>
                      <td className="px-3 py-2">{r.dut_per?.toFixed(2)}</td>
                      <td className="px-3 py-2">
                        <Badge
                          className={
                            r.status === "pass" || r.status === "PASS"
                              ? "bg-green-100 text-green-700 hover:bg-green-100"
                              : "bg-red-100 text-red-700 hover:bg-red-100"
                          }
                        >
                          {r.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
