"use client";

import { Canvas } from "@/components/canvas";
import { AssistantProvider } from "@/contexts/AssistantContext";
import { GraphProvider } from "@/contexts/GraphContext";
import { ThreadProvider } from "@/contexts/ThreadProvider";
import { UserProvider } from "@/contexts/UserContext";
import { useToast } from "@/hooks/use-toast";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useEffect } from "react";

function HomeContent() {
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const loginSuccess = searchParams.get("loginSuccess");
    if (loginSuccess === "true") {
      toast({
        title: "✅ Login Successful",
        description: "Welcome back! You have been logged in successfully.",
      });
      
      // Remove the loginSuccess parameter from the URL
      const newSearchParams = new URLSearchParams(searchParams);
      newSearchParams.delete("loginSuccess");
      router.replace(
        `${window.location.pathname}${newSearchParams.toString() ? `?${newSearchParams.toString()}` : ''}`,
        { scroll: false }
      );
    }
  }, [searchParams, router, toast]);

  return (
    <UserProvider>
      <ThreadProvider>
        <AssistantProvider>
          <GraphProvider>
            <Canvas />
          </GraphProvider>
        </AssistantProvider>
      </ThreadProvider>
    </UserProvider>
  );
}

export default function Home() {
  return (
    <Suspense>
      <HomeContent />
    </Suspense>
  );
}
