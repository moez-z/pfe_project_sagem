import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  try {
    const [
      totalSessions,
      passedSessions,
      failedSessions,
      totalTx,
      totalRx,
      txCorrections,
      avgDelta,
      recentSessions,
      sessionsByDay,
    ] = await Promise.all([
      // Total sessions
      prisma.calibrationSession.count(),

      // Passed sessions
      prisma.calibrationSession.count({ where: { overall_pass: true } }),

      // Failed sessions
      prisma.calibrationSession.count({ where: { overall_pass: false } }),

      // Total TX results
      prisma.txResult.count(),

      // Total RX results
      prisma.rxResult.count(),

      // Total corrections applied
      prisma.calibrationSession.aggregate({
        _sum: { tx_corrections: true },
      }),

      // Average delta dBm across all sessions
      prisma.calibrationSession.aggregate({
        _avg: { avg_delta_dbm: true },
      }),

      // Last 5 sessions
      prisma.calibrationSession.findMany({
        take: 5,
        orderBy: { created_at: "desc" },
        select: {
          id: true,
          dut_serial: true,
          product_name: true,
          overall_pass: true,
          avg_delta_dbm: true,
          tx_corrections: true,
          created_at: true,
        },
      }),

      // Sessions per day (last 7 days) using raw query
      prisma.$queryRaw<{ day: string; count: number }[]>`
        SELECT 
          TO_CHAR(created_at, 'YYYY-MM-DD') as day,
          COUNT(*)::int as count
        FROM calibration_sessions
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY day
        ORDER BY day ASC
      `,
    ]);

    return NextResponse.json({
      totalSessions,
      passedSessions,
      failedSessions,
      totalTx,
      totalRx,
      totalCorrections: txCorrections._sum.tx_corrections ?? 0,
      avgDelta: Number(avgDelta._avg.avg_delta_dbm?.toFixed(2) ?? 0),
      passRate:
        totalSessions > 0
          ? Number(((passedSessions / totalSessions) * 100).toFixed(1))
          : 0,
      recentSessions,
      sessionsByDay,
    });
  } catch (err) {
    console.error("[overview]", err);
    return NextResponse.json({ error: "Failed to load overview" }, { status: 500 });
  }
}