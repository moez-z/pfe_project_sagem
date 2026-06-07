import { SessionProvider } from "next-auth/react";
import Sidebar from "@/components/layout/Sidebar";
import Navbar from "@/components/layout/Navbar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SessionProvider>
      <div className="flex min-h-screen bg-slate-100">
        <Sidebar />
        <div className="flex flex-col flex-1 overflow-hidden lg:ml-0">
          {/* Spacer for mobile top bar */}
          <div className="h-14 lg:hidden shrink-0" />
          <Navbar />
          <main className="flex-1 overflow-y-auto p-4 lg:p-6">{children}</main>
        </div>
      </div>
    </SessionProvider>
  );
}
