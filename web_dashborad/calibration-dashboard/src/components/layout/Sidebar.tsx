"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FolderOpen,
  Radio,
  Antenna,
  SlidersHorizontal,
  Users,
  ChevronRight,
  Menu,
  GitCompare,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

const navItems = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "Sessions", href: "/dashboard/sessions", icon: FolderOpen },
  { label: "Calibrations", href: "/dashboard/calibrations", icon: Antenna },
  {
    label: "Corrections",
    href: "/dashboard/corrections",
    icon: SlidersHorizontal,
  },
  { label: "Comparison", href: "/dashboard/comparison", icon: GitCompare },

  { label: "Users", href: "/dashboard/users", icon: Users },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const NavLinks = () => (
    <>
      {navItems.map(({ label, href, icon: Icon }) => {
        const active = pathname === href || pathname.startsWith(href + "/");
        return (
          <Link
            key={href}
            href={href}
            onClick={() => setOpen(false)}
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
              active
                ? "bg-blue-600 text-white shadow"
                : "text-slate-400 hover:bg-slate-800 hover:text-white",
            )}
          >
            <Icon className="w-4 h-4 shrink-0" />
            <span className="flex-1">{label}</span>
            {active && <ChevronRight className="w-3 h-3 opacity-70" />}
          </Link>
        );
      })}
    </>
  );

  return (
    <>
      {/* Mobile top bar */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 h-14 bg-slate-900 flex items-center px-4 gap-3">
        <button onClick={() => setOpen(true)} className="text-white">
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <div className="bg-blue-500 rounded-lg p-1.5">
            <SlidersHorizontal className="w-4 h-4 text-white" />
          </div>
          <p className="font-bold text-white text-sm">Calibration Dashboard</p>
        </div>
      </div>

      {/* Mobile overlay */}
      {open && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setOpen(false)}
          />
          <aside className="relative z-10 flex flex-col w-64 min-h-screen bg-slate-900 text-white px-4 py-6 shadow-xl">
            <div className="flex items-center justify-between mb-6 px-2">
              <div className="flex items-center gap-2">
                <div className="bg-blue-500 rounded-lg p-1.5">
                  <SlidersHorizontal className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="font-bold text-sm">Calibration</p>
                  <p className="text-xs text-slate-400">Admin Dashboard</p>
                </div>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <Separator className="bg-slate-700 mb-4" />
            <nav className="flex flex-col gap-1 flex-1">
              <p className="text-xs text-slate-500 uppercase font-semibold px-2 mb-2">
                Main Menu
              </p>
              <NavLinks />
            </nav>
            <Separator className="bg-slate-700 my-4" />
            <div className="px-2">
              <p className="text-xs text-slate-500">wifi_calibration DB</p>
              <div className="flex items-center gap-2 mt-1">
                <div className="w-2 h-2 rounded-full bg-green-400" />
                <p className="text-xs text-slate-400">Connected</p>
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-64 min-h-screen bg-slate-900 text-white px-4 py-6 shadow-xl">
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="bg-blue-500 rounded-lg p-2">
            <SlidersHorizontal className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="font-bold text-sm leading-tight">Calibration</p>
            <p className="text-xs text-slate-400">Admin Dashboard</p>
          </div>
        </div>
        <Separator className="bg-slate-700 mb-6" />
        <nav className="flex flex-col gap-1 flex-1">
          <p className="text-xs text-slate-500 uppercase font-semibold px-2 mb-2">
            Main Menu
          </p>
          <NavLinks />
        </nav>
        <Separator className="bg-slate-700 my-4" />
        <div className="px-2">
          <p className="text-xs text-slate-500">wifi_calibration DB</p>
          <div className="flex items-center gap-2 mt-1">
            <div className="w-2 h-2 rounded-full bg-green-400" />
            <p className="text-xs text-slate-400">Connected</p>
          </div>
        </div>
      </aside>
    </>
  );
}
