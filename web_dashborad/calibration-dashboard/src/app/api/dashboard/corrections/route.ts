import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const page  = Math.max(1, parseInt(searchParams.get("page") ?? "1"));
    const limit = 15;
    const skip  = (page - 1) * limit;
    const band  = searchParams.get("band") ?? "";

    const conditions: any[] = [
      { correction_dbm: { not: 0 } }, // only rows with an actual correction
    ];
    if (band) conditions.push({ band });
    const where = { AND: conditions };

    const [results, total, bands, stats] = await Promise.all([
      prisma.txResult.findMany({
        where,
        skip,
        take: limit,
        orderBy: [{ session_id: "desc" }, { freq_mhz: "asc" }],
        include: {
          session: {
            select: { id: true, product_name: true, dut_serial: true, created_at: true },
          },
        },
      }),
      prisma.txResult.count({ where }),
      prisma.txResult.findMany({
        where: { correction_dbm: { not: 0 } },
        select: { band: true },
        distinct: ["band"],
        orderBy: { band: "asc" },
      }),
      prisma.txResult.aggregate({
        where,
        _avg: { correction_dbm: true, delta_dbm: true },
        _max: { correction_dbm: true },
        _min: { correction_dbm: true },
        _count: { correction_dbm: true },
      }),
    ]);

    return NextResponse.json({
      results,
      total,
      page,
      totalPages: Math.ceil(total / limit),
      bands: bands.map((b) => b.band).filter(Boolean),
      stats: {
        count:      stats._count.correction_dbm,
        avgCorr:    Number(stats._avg.correction_dbm?.toFixed(3) ?? 0),
        avgDelta:   Number(stats._avg.delta_dbm?.toFixed(3) ?? 0),
        maxCorr:    Number(stats._max.correction_dbm?.toFixed(3) ?? 0),
        minCorr:    Number(stats._min.correction_dbm?.toFixed(3) ?? 0),
      },
    });
  } catch (err) {
    console.error("[corrections]", err);
    return NextResponse.json({ error: "Failed to load corrections", detail: String(err) }, { status: 500 });
  }
}
