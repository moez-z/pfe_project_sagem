"use client";

import { usePathname } from "next/navigation";
import { Bell, LogOut } from "lucide-react";
import { signOut, useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const pageTitles: Record<string, string> = {
  "/dashboard":                "Overview",
  "/dashboard/sessions":       "Calibration Sessions",
  "/dashboard/calibrations":   "Calibrations",
  "/dashboard/corrections":    "Corrections",
  "/dashboard/comparison":     "Posts Comparison",
  "/dashboard/users":          "Users",
};

export default function Navbar() {
  const pathname   = usePathname();
  const { data: session } = useSession();

  const title = Object.entries(pageTitles).find(([key]) =>
    pathname === key || pathname.startsWith(key + "/")
  )?.[1] ?? "Overview";

  const name     = session?.user?.name ?? "Admin";
  const initials = name.split(" ").map((n: string) => n[0]).join("").toUpperCase().slice(0, 2);

  return (
    <header className="w-full h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 shadow-sm">
      <div>
        <h1 className="text-lg font-semibold text-slate-800">{title}</h1>
        <p className="text-xs text-slate-400">wifi_calibration · localhost</p>
      </div>

      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="w-5 h-5 text-slate-500" />
          <Badge className="absolute -top-1 -right-1 w-4 h-4 p-0 flex items-center justify-center text-[10px] bg-red-500">
            3
          </Badge>
        </Button>

        <div className="flex items-center gap-2">
          <Avatar className="w-8 h-8">
            <AvatarFallback className="bg-blue-600 text-white text-xs">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div className="hidden sm:block">
            <p className="text-sm font-medium text-slate-700">{name}</p>
            <p className="text-xs text-slate-400">Administrator</p>
          </div>
        </div>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => signOut({ callbackUrl: "/login" })}
          className="text-slate-400 hover:text-red-500 hover:bg-red-50"
          title="Sign out"
        >
          <LogOut className="w-4 h-4" />
        </Button>
      </div>
    </header>
  );
}