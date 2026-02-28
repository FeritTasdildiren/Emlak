"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/auth";

export function LandingRedirect() {
  const router = useRouter();

  useEffect(() => {
    if (auth.isAuthenticated()) {
      router.replace("/dashboard");
    }
  }, [router]);

  return null;
}
