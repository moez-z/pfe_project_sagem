import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: rawId } = await params;
    const id = parseInt(rawId);
    if (isNaN(id)) return NextResponse.json({ error: "Invalid ID" }, { status: 400 });

    const session = await prisma.calibrationSession.findUnique({
      where: { id },
      include: {
        user: { select: { full_name: true, matricule: true, role: true } },
        post: { select: { name: true, number: true } },
        tx_results: { orderBy: [{ band: "asc" }, { freq_mhz: "asc" }] },
        rx_results: { orderBy: [{ band: "asc" }, { freq_mhz: "asc" }] },
      },
    });

    if (!session) return NextResponse.json({ error: "Not found" }, { status: 404 });

    return NextResponse.json(session);
  } catch (err) {
    console.error("[session detail]", err);
    return NextResponse.json({ error: "Failed to load session", detail: String(err) }, { status: 500 });
  }
}