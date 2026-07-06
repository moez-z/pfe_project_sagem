"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle,
  XCircle,
  Radio,
  Antenna,
  SlidersHorizontal,
  Activity,
  TrendingUp,
  FolderOpen,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

interface OverviewData {
  totalSessions: number;
  passedSessions: number;
  failedSessions: number;
  totalTx: number;
  totalRx: number;
  totalCorrections: number;
  avgDelta: number;
  passRate: number;
  recentSessions: {
    id: number;
    dut_serial: string;
    product_name: string;
    overall_pass: boolean;
    avg_delta_dbm: number;
    tx_corrections: number;
    created_at: string;
  }[];
  sessionsByDay: { day: string; count: number }[];
}

const COLORS = ["#22c55e", "#ef4444"];

export default function DashboardPage() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/dashboard/overview")
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        Loading overview...
      </div>
    );
  }

  if (!data) return null;

  const pieData = [
    { name: "Passed", value: data.passedSessions },
    { name: "Failed", value: data.failedSessions },
  ];

  const stats = [
    {
      label: "Total Sessions",
      value: data.totalSessions,
      icon: FolderOpen,
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      label: "Pass Rate",
      value: `${data.passRate}%`,
      icon: TrendingUp,
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      label: "TX Results",
      value: data.totalTx,
      icon: Radio,
      color: "text-purple-600",
      bg: "bg-purple-50",
    },
    {
      label: "RX Results",
      value: data.totalRx,
      icon: Antenna,
      color: "text-orange-600",
      bg: "bg-orange-50",
    },
    {
      label: "Corrections Applied",
      value: data.totalCorrections,
      icon: SlidersHorizontal,
      color: "text-yellow-600",
      bg: "bg-yellow-50",
    },
    {
      label: "Avg Delta dBm",
      value: `${data.avgDelta} dBm`,
      icon: Activity,
      color: "text-rose-600",
      bg: "bg-rose-50",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map(({ label, value, icon: Icon, color, bg }) => (
          <Card key={label} className="shadow-sm">
            <CardContent className="flex items-center gap-4 p-5">
              <div className={`${bg} p-3 rounded-xl`}>
                <Icon className={`w-5 h-5 ${color}`} />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">{label}</p>
                <p className="text-2xl font-bold text-slate-800">{value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Area Chart */}
        <Card className="lg:col-span-2 shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-slate-700">
              Sessions — Last 7 Days
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={data.sessionsByDay}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fill="url(#colorCount)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Pie Chart */}
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-slate-700">
              Pass / Fail Ratio
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i]} />
                  ))}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Recent Sessions Table */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="text-sm font-semibold text-slate-700">
            Recent Sessions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-400 border-b border-slate-100">
                  <th className="pb-2 font-medium">ID</th>
                  <th className="pb-2 font-medium">DUT Serial</th>
                  <th className="pb-2 font-medium">Product</th>
                  <th className="pb-2 font-medium">Avg Δ dBm</th>
                  <th className="pb-2 font-medium">Corrections</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {data.recentSessions.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 text-slate-500">#{s.id}</td>
                    <td className="py-2.5 font-mono text-xs text-slate-700">{s.dut_serial}</td>
                    <td className="py-2.5 text-slate-700">{s.product_name}</td>
                    <td className="py-2.5 text-slate-700">{s.avg_delta_dbm?.toFixed(2)}</td>
                    <td className="py-2.5 text-slate-700">{s.tx_corrections}</td>
                    <td className="py-2.5">
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
                    <td className="py-2.5 text-slate-400 text-xs">
                      {new Date(s.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}