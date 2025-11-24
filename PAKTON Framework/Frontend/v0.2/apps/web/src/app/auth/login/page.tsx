"use client";

import { Login } from "@/components/auth/login/Login";
import { Toaster } from "@/components/ui/toaster";
import { Suspense } from "react";

export default function Page() {
  return (
    <main className="h-screen">
      <Suspense fallback={<div>Loading...</div>}>
        <Login />
      </Suspense>
      <Toaster />
    </main>
  );
}
