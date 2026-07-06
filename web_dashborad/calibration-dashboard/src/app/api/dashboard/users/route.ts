import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import bcrypt from "bcryptjs";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const page  = Math.max(1, parseInt(searchParams.get("page") ?? "1"));
    const limit = 10;
    const skip  = (page - 1) * limit;
    const role  = searchParams.get("role") ?? "";
    const where: any = role ? { role } : {};

    const [users, total, roles] = await Promise.all([
      prisma.user.findMany({
        where, skip, take: limit,
        orderBy: { created_at: "desc" },
        include: { _count: { select: { sessions: true } } },
      }),
      prisma.user.count({ where }),
      prisma.user.findMany({
        select: { role: true },
        distinct: ["role"],
        orderBy: { role: "asc" },
      }),
    ]);

    const safeUsers = users.map(({ password_hash, ...u }) => u);
    return NextResponse.json({
      users: safeUsers, total, page,
      totalPages: Math.ceil(total / limit),
      roles: roles.map((r) => r.role).filter(Boolean),
    });
  } catch (err) {
    return NextResponse.json({ error: "Failed to load users", detail: String(err) }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const { matricule, full_name, role, password } = await req.json();
    if (!matricule || !password)
      return NextResponse.json({ error: "Matricule and password are required" }, { status: 400 });

    const existing = await prisma.user.findUnique({ where: { matricule } });
    if (existing)
      return NextResponse.json({ error: "Matricule already exists" }, { status: 409 });

    const password_hash = await bcrypt.hash(password, 10);
    const user = await prisma.user.create({
      data: { matricule, full_name, role, password_hash },
    });
    const { password_hash: _, ...safeUser } = user;
    return NextResponse.json(safeUser, { status: 201 });
  } catch (err) {
    return NextResponse.json({ error: "Failed to create user", detail: String(err) }, { status: 500 });
  }
}

export async function PUT(req: NextRequest) {
  try {
    const { id, matricule, full_name, role, password } = await req.json();
    if (!id) return NextResponse.json({ error: "id is required" }, { status: 400 });

    const data: any = { matricule, full_name, role };
    if (password) data.password_hash = await bcrypt.hash(password, 10);

    const user = await prisma.user.update({ where: { id }, data });
    const { password_hash: _, ...safeUser } = user;
    return NextResponse.json(safeUser);
  } catch (err) {
    return NextResponse.json({ error: "Failed to update user", detail: String(err) }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const { id } = await req.json();
    if (!id) return NextResponse.json({ error: "id is required" }, { status: 400 });
    await prisma.user.delete({ where: { id } });
    return NextResponse.json({ success: true });
  } catch (err) {
    return NextResponse.json({ error: "Failed to delete user", detail: String(err) }, { status: 500 });
  }
}