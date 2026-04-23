"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export default function Navbar() {
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    const t =
      window.localStorage.getItem("sb-access-token") ||
      window.localStorage.getItem("access_token") ||
      window.localStorage.getItem("token");
    setAuthed(!!t);
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-gray-950/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          Corre Compara
        </Link>

        <nav className="flex items-center gap-3">
          {!authed ? (
            <>
              <Link
                href="/login"
                className="rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm hover:bg-white/10"
              >
                Login
              </Link>
              <Link
                href="/register"
                className="rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm hover:bg-white/10"
              >
                Register
              </Link>
            </>
          ) : (
            <Link
              href="/dashboard"
              className="flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm hover:bg-white/10"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-white/10 text-xs font-semibold">
                U
              </div>
              Dashboard
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}

