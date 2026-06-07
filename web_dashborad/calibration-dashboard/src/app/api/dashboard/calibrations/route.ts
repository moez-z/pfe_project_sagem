import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const page    = Math.max(1, parseInt(searchParams.get("page") ?? "1"));
    const limit   = 10;
    const skip    = (page - 1) * limit;
    const userId  = searchParams.get("user") ?? "";
    const postId  = searchParams.get("post") ?? "";
    const dateFrom = searchParams.get("dateFrom") ?? "";
    const dateTo   = searchParams.get("dateTo") ?? "";

    const conditions: any[] = [];
    if (userId)  conditions.push({ user_id: parseInt(userId) });
    if (postId)  conditions.push({ post_id: parseInt(postId) });
    if (dateFrom) conditions.push({ created_at: { gte: new Date(dateFrom) } });
    if (dateTo)   conditions.push({ created_at: { lte: new Date(dateTo + "T23:59:59") } });
    const where = conditions.length > 0 ? { AND: conditions } : {};

    const [sessions, total, users, posts] = await Promise.all([
      prisma.calibrationSession.findMany({
        where, skip, take: limit,
        orderBy: { created_at: "desc" },
        include: {
          user: { select: { id: true, full_name: true, matricule: true } },
          post: { select: { id: true, name: true, number: true } },
          _count: { select: { tx_results: true, rx_results: true } },
        },
      }),
      prisma.calibrationSession.count({ where }),
      prisma.user.findMany({
        select: { id: true, full_name: true, matricule: true },
        orderBy: { full_name: "asc" },
      }),
      prisma.post.findMany({
        where: { is_active: true },
        orderBy: { number: "asc" },
      }),
    ]);

    return NextResponse.json({
      sessions, total, page,
      totalPages: Math.ceil(total / limit),
      users, posts,
    });
  } catch (err) {
    console.error("[calibrations]", err);
    return NextResponse.json({ error: "Failed to load calibrations", detail: String(err) }, { status: 500 });
  }
}