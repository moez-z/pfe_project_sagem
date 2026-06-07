import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const page      = Math.max(1, parseInt(searchParams.get("page") ?? "1"));
    const limit     = 15;
    const skip      = (page - 1) * limit;
    const band      = searchParams.get("band") ?? "";
    const status    = searchParams.get("status") ?? "all";
    const sessionId = searchParams.get("session") ?? "";

    const conditions: any[] = [];
    if (band)             conditions.push({ band });
    if (status !== "all") conditions.push({ status: { equals: status } });
    if (sessionId)        conditions.push({ session_id: parseInt(sessionId) });
    const where = conditions.length > 0 ? { AND: conditions } : {};

    const [results, total, bands] = await Promise.all([
      prisma.rxResult.findMany({
        where,
        skip,
        take: limit,
        orderBy: [{ session_id: "desc" }, { freq_mhz: "asc" }],
        include: {
          session: { select: { id: true, product_name: true, dut_serial: true } },
        },
      }),
      prisma.rxResult.count({ where }),
      prisma.rxResult.findMany({
        select: { band: true },
        distinct: ["band"],
        orderBy: { band: "asc" },
      }),
    ]);

    return NextResponse.json({
      results,
      total,
      page,
      totalPages: Math.ceil(total / limit),
      bands: bands.map((b) => b.band).filter(Boolean),
    });
  } catch (err) {
    console.error("[rx-results]", err);
    return NextResponse.json({ error: "Failed to load RX results", detail: String(err) }, { status: 500 });
  }
}