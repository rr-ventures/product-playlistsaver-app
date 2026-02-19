"use client";

import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export function LogoutButton() {
  const router = useRouter();

  const logout = async () => {
    await apiFetch<void>("/api/auth/logout", { method: "POST" });
    router.push("/");
    router.refresh();
  };

  return (
    <button
      onClick={logout}
      className="rounded bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
      type="button"
    >
      Logout
    </button>
  );
}
