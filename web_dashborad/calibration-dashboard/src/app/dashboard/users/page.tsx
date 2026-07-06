"use client";

import { useEffect, useState, useCallback } from "react";
import {
  ChevronLeft, ChevronRight, Filter,
  Plus, Pencil, Trash2, X, Save, Eye, EyeOff,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Dialog, DialogContent, DialogHeader,
  DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface User {
  id: number;
  matricule: string;
  full_name: string | null;
  role: string | null;
  created_at: string | null;
  last_login: string | null;
  _count: { sessions: number };
}

interface ApiResponse {
  users: User[];
  total: number;
  page: number;
  totalPages: number;
  roles: string[];
}

interface FormData {
  matricule: string;
  full_name: string;
  role: string;
  password: string;
}

const EMPTY_FORM: FormData = { matricule: "", full_name: "", role: "operator", password: "" };

const roleColor = (role: string | null) => {
  switch (role?.toLowerCase()) {
    case "admin":      return "bg-purple-100 text-purple-700";
    case "operator":   return "bg-blue-100 text-blue-700";
    case "technician": return "bg-orange-100 text-orange-700";
    default:           return "bg-slate-100 text-slate-600";
  }
};

const initials = (name: string | null, matricule: string) => {
  if (name) return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  return matricule.slice(0, 2).toUpperCase();
};

export default function UsersPage() {
  const [data, setData]           = useState<ApiResponse | null>(null);
  const [loading, setLoading]     = useState(true);
  const [role, setRole]           = useState("");
  const [page, setPage]           = useState(1);

  // dialog state
  const [dialog, setDialog]       = useState<"none" | "create" | "edit" | "delete">("none");
  const [selected, setSelected]   = useState<User | null>(null);
  const [form, setForm]           = useState<FormData>(EMPTY_FORM);
  const [showPw, setShowPw]       = useState(false);
  const [saving, setSaving]       = useState(false);
  const [error, setError]         = useState("");

  const fetch_ = useCallback(async () => {
    setLoading(true);
    const p = new URLSearchParams({ page: String(page), role });
    const res = await fetch(`/api/dashboard/users?${p}`);
    setData(await res.json());
    setLoading(false);
  }, [page, role]);

  useEffect(() => { fetch_(); }, [fetch_]);
  useEffect(() => { setPage(1); }, [role]);

  const openCreate = () => {
    setForm(EMPTY_FORM); setError(""); setShowPw(false); setDialog("create");
  };
  const openEdit = (u: User) => {
    setSelected(u);
    setForm({ matricule: u.matricule, full_name: u.full_name ?? "", role: u.role ?? "operator", password: "" });
    setError(""); setShowPw(false); setDialog("edit");
  };
  const openDelete = (u: User) => { setSelected(u); setDialog("delete"); };
  const closeDialog = () => { setDialog("none"); setSelected(null); setError(""); };

  const handleSave = async () => {
    setSaving(true); setError("");
    try {
      const isEdit = dialog === "edit";
      const body = isEdit
        ? { id: selected!.id, ...form }
        : form;

      const res = await fetch("/api/dashboard/users", {
        method: isEdit ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      if (!res.ok) { setError(json.error ?? "Something went wrong"); return; }
      closeDialog(); fetch_();
    } finally { setSaving(false); }
  };

  const handleDelete = async () => {
    setSaving(true);
    try {
      await fetch("/api/dashboard/users", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: selected!.id }),
      });
      closeDialog(); fetch_();
    } finally { setSaving(false); }
  };

  return (
    <div className="space-y-5">
      {/* Toolbar */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select value={role} onChange={(e) => setRole(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
            <option value="">All Roles</option>
            {data?.roles.map((r) => <option key={r} value={r ?? ""}>{r}</option>)}
          </select>
        </div>
        <span className="text-xs text-slate-400">{data?.total ?? 0} users</span>
        <Button onClick={openCreate} className="ml-auto bg-blue-600 hover:bg-blue-700 text-white h-9">
          <Plus className="w-4 h-4 mr-1" /> Add User
        </Button>
      </div>

      {/* User Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading && (
          <div className="col-span-3 flex items-center justify-center h-48 text-slate-400 text-sm">
            Loading users...
          </div>
        )}
        {!loading && data?.users.length === 0 && (
          <div className="col-span-3 text-center py-12 text-slate-400">No users found</div>
        )}
        {!loading && data?.users.map((u) => (
          <Card key={u.id} className="shadow-sm hover:shadow-md transition-shadow">
            <CardContent className="p-5">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-3 min-w-0">
                  <Avatar className="w-11 h-11 shrink-0">
                    <AvatarFallback className="bg-blue-600 text-white text-sm font-semibold">
                      {initials(u.full_name, u.matricule)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0">
                    <p className="font-semibold text-slate-800 truncate">{u.full_name ?? "—"}</p>
                    <p className="text-xs text-slate-400 font-mono truncate">{u.matricule}</p>
                    <Badge className={`text-xs mt-1 ${roleColor(u.role)}`}>{u.role ?? "—"}</Badge>
                  </div>
                </div>
                {/* Actions */}
                <div className="flex gap-1 shrink-0">
                  <Button size="icon" variant="ghost" onClick={() => openEdit(u)}
                    className="w-7 h-7 text-slate-400 hover:text-blue-600 hover:bg-blue-50">
                    <Pencil className="w-3.5 h-3.5" />
                  </Button>
                  <Button size="icon" variant="ghost" onClick={() => openDelete(u)}
                    className="w-7 h-7 text-slate-400 hover:text-red-600 hover:bg-red-50">
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="bg-slate-50 rounded-lg p-2">
                  <p className="text-slate-400">Sessions</p>
                  <p className="font-bold text-slate-700 text-base">{u._count.sessions}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-2">
                  <p className="text-slate-400">Last Login</p>
                  <p className="font-medium text-slate-700">
                    {u.last_login ? new Date(u.last_login).toLocaleDateString() : "Never"}
                  </p>
                </div>
              </div>
              <div className="mt-3 text-xs text-slate-400">
                Joined {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pagination */}
      {data && data.totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-400">Page {data.page} of {data.totalPages}</p>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" disabled={page === 1} onClick={() => setPage(p => p - 1)} className="h-8">
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button size="sm" variant="outline" disabled={page === data.totalPages} onClick={() => setPage(p => p + 1)} className="h-8">
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Create / Edit Dialog */}
      <Dialog open={dialog === "create" || dialog === "edit"} onOpenChange={closeDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{dialog === "create" ? "Add New User" : "Edit User"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            {error && (
              <div className="bg-red-50 text-red-600 text-sm px-3 py-2 rounded-lg flex items-center gap-2">
                <X className="w-4 h-4 shrink-0" /> {error}
              </div>
            )}
            <div className="space-y-1.5">
              <Label>matricule</Label>
              <Input value={form.matricule} onChange={e => setForm(f => ({ ...f, matricule: e.target.value }))}
                placeholder="e.g. john.doe" />
            </div>
            <div className="space-y-1.5">
              <Label>Full Name</Label>
              <Input value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
                placeholder="e.g. John Doe" />
            </div>
            <div className="space-y-1.5">
              <Label>Role</Label>
              <select value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))}
                className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                <option value="admin">Admin</option>
                <option value="operator">Operator</option>
                <option value="technician">Technician</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <Label>{dialog === "edit" ? "New Password (leave blank to keep)" : "Password"}</Label>
              <div className="relative">
                <Input type={showPw ? "text" : "password"}
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  placeholder={dialog === "edit" ? "Leave blank to keep current" : "Enter password"} />
                <button type="button" onClick={() => setShowPw(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={closeDialog} disabled={saving}>Cancel</Button>
            <Button onClick={handleSave} disabled={saving} className="bg-blue-600 hover:bg-blue-700 text-white">
              <Save className="w-4 h-4 mr-1" />
              {saving ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={dialog === "delete"} onOpenChange={closeDialog}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Delete User</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-slate-600 py-2">
            Are you sure you want to delete{" "}
            <span className="font-semibold text-slate-800">{selected?.full_name ?? selected?.matricule}</span>?
            This action cannot be undone.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={closeDialog} disabled={saving}>Cancel</Button>
            <Button onClick={handleDelete} disabled={saving}
              className="bg-red-600 hover:bg-red-700 text-white">
              <Trash2 className="w-4 h-4 mr-1" />
              {saving ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}