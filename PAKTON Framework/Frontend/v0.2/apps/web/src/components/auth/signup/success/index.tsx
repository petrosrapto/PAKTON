"use client";

import { useEffect, useState } from "react";
import { redirect, RedirectType } from "next/navigation";
import { useUserContext } from "@/contexts/UserContext";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Mail, Loader2, Check } from "lucide-react";

export function SignupSuccess() {
  const { getUser, user } = useUserContext();
  const [isChecking, setIsChecking] = useState(true);
  const [open, setOpen] = useState(true);

  useEffect(() => {
    if (user) {
      return;
    }
    const startTime = Date.now();
    const checkDuration = 3 * 60 * 1000; // 3 minutes in milliseconds
    const interval = 4000; // 4 seconds

    const checkUser = async () => {
      await getUser();
      if (Date.now() - startTime >= checkDuration) {
        setIsChecking(false);
      }
    };

    const intervalId = setInterval(checkUser, interval);

    // Initial check
    checkUser();

    // Cleanup function
    return () => clearInterval(intervalId);
  }, [getUser]);

  useEffect(() => {
    if (user) {
      redirect("/", RedirectType.push);
    }
  }, [user]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md border-none shadow-2xl">
          <DialogHeader className="text-center space-y-3">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center shadow-lg animate-in zoom-in duration-300">
              <Check className="w-10 h-10 text-white stroke-[3]" />
            </div>
            <DialogTitle className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent text-center">
              Successfully Signed Up!
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 space-y-2">
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  <Mail className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium text-gray-900">
                    Check your email
                  </p>
                  <DialogDescription className="text-sm text-gray-600">
                    Please check your email for a confirmation link. That link will
                    redirect you to PAKTON.
                  </DialogDescription>
                </div>
              </div>
            </div>

            <div className="bg-amber-50 border border-amber-100 rounded-xl p-4">
              <p className="text-xs text-amber-800 text-center">
                💡 If you don&apos;t see the email, please check your spam folder.
              </p>
            </div>

            {isChecking && (
              <div className="flex items-center justify-center gap-2 pt-2">
                <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                <p className="text-sm text-blue-600 font-medium">
                  Waiting for email confirmation...
                </p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
