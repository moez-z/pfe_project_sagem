import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const page = Math.max(1, parseInt(searchParams.get("page") ?? "1"));
    const limit = 10;
    const skip = (page - 1) * limit;
    const search = searchParams.get("search") ?? "";
    const status = searchParams.get("status") ?? "all";
    const product = searchParams.get("product") ?? "";

    const conditions: any[] = [];
    if (search) {
      conditions.push({
        OR: [
          { dut_serial: { contains: search } },
          { origin_serial: { contains: search } },
          { product_name: { contains: search } },
        ],
      });
    }
    if (status !== "all") conditions.push({ overall_pass: status === "pass" });
    if (product) conditions.push({ product_name: product });

    const where = conditions.length > 0 ? { AND: conditions } : {};

    const [sessions, total, products] = await Promise.all([
      prisma.calibrationSession.findMany({
        where,
        skip,
        take: limit,
        orderBy: { created_at: "desc" },
        include: {
          user: { select: { full_name: true, matricule: true } },
          post: { select: { name: true, number: true } },
          _count: { select: { tx_results: true, rx_results: true } },
        },
      }),
      prisma.calibrationSession.count({ where }),
      prisma.calibrationSession.findMany({
        select: { product_name: true },
        distinct: ["product_name"],
        orderBy: { product_name: "asc" },
      }),
    ]);

    return NextResponse.json({
      sessions,
      total,
      page,
      totalPages: Math.ceil(total / limit),
      products: products.map((p) => p.product_name),
    });
  } catch (err) {
    console.error("[sessions]", err);
    return NextResponse.json(
      { error: "Failed to load sessions", detail: String(err) },
      { status: 500 },
    );
  }
}
