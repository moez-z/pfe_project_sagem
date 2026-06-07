import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const product = searchParams.get("product") ?? "";

    const posts = await prisma.post.findMany({
      where: { is_active: true },
      orderBy: { number: "asc" },
    });

    const products = await prisma.calibrationSession.findMany({
      select: { product_name: true },
      distinct: ["product_name"],
      orderBy: { product_name: "asc" },
    });

    const productNames = products.map((p) => p.product_name).filter(Boolean);

    if (!product) {
      return NextResponse.json({
        posts,
        products: productNames,
        columns: [],
        rows: [],
      });
    }

    const sessions = await prisma.calibrationSession.findMany({
      where: { product_name: product },
      orderBy: { created_at: "desc" },
      include: {
        post: true,
        tx_results: { orderBy: { freq_mhz: "asc" } },
        rx_results: { orderBy: { freq_mhz: "asc" } },
      },
    });

    // Derive types directly from the Prisma result
    type Session = (typeof sessions)[number];
    type TxResult = Session["tx_results"][number];
    type RxResult = Session["rx_results"][number];

    const txKey = (r: TxResult): string =>
      `TX|${r.band}|${r.freq_mhz}|${r.modulation}|${r.bandwidth}|${r.antenna}`;

    const rxKey = (r: RxResult): string =>
      `RX|${r.band}|${r.freq_mhz}|${r.mcs}|${r.bandwidth}|${r.antenna_label}`;

    // Keep only the latest session per post
    const latestByKey = new Map<number, Session>();
    for (const s of sessions) {
      const key = s.post_id ?? -s.id;
      if (!latestByKey.has(key)) {
        latestByKey.set(key, s);
      }
    }

    // Build columns
    const columns = Array.from(latestByKey.entries()).map(([key, s]) => ({
      key,
      label: s.post ? s.post.name : `Session #${s.id}`,
      sessionId: s.id,
    }));

    // Collect all unique test keys
    const allTestKeys = new Set<string>();
    for (const session of latestByKey.values()) {
      session.tx_results.forEach((r) => allTestKeys.add(txKey(r)));
      session.rx_results.forEach((r) => allTestKeys.add(rxKey(r)));
    }

    // Build rows
    const rows = Array.from(allTestKeys).map((key) => {
      const [type] = key.split("|");
      const colValues: Record<number, number | null> = {};
      let mesureURD: number | null = null;

      for (const [colKey, session] of latestByKey.entries()) {
        if (type === "TX") {
          const match = session.tx_results.find((r) => txKey(r) === key);
          if (match) {
            colValues[colKey] = match.correction_dbm;
            if (mesureURD === null) mesureURD = match.origin_dbm;
          } else {
            colValues[colKey] = null;
          }
        } else {
          const match = session.rx_results.find((r) => rxKey(r) === key);
          if (match) {
            colValues[colKey] = match.dut_rssi;
            if (mesureURD === null) mesureURD = match.origin_rssi;
          } else {
            colValues[colKey] = null;
          }
        }
      }

      return { key, type, mesureURD, colValues };
    });

    return NextResponse.json({
      posts,
      products: productNames,
      columns,
      rows,
    });
  } catch (err) {
    console.error("[comparison]", err);
    return NextResponse.json(
      { error: "Failed to load comparison", detail: String(err) },
      { status: 500 },
    );
  }
}
