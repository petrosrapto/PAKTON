"use client";

import { useUserContext } from "@/contexts/UserContext";
import { createSupabaseClient } from "@/lib/supabase/client";
import { Loader2, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { useToast } from "@/hooks/use-toast";
import { useState } from "react";

export function UserAvatarMenu() {
  const { user } = useUserContext();
  const router = useRouter();
  const { toast } = useToast();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    try {
      setIsLoggingOut(true);
      const supabase = createSupabaseClient();
      await supabase.auth.signOut();
      toast({
        title: "✅ Logged out successfully",
        description: "You have been logged out of your account",
        duration: 2000,
      });
      // Delay navigation to allow toast to be visible
      setTimeout(() => {
        router.push("/auth/login");
      }, 1500);
    } catch (error) {
      toast({
        title: "Error logging out",
        description: "An error occurred while logging out",
        variant: "destructive",
        duration: 3000,
      });
      console.error("Error logging out:", error);
      setIsLoggingOut(false);
    }
  };

  if (!user) return null;

  // Get user initials for the avatar fallback
  const getInitials = () => {
    const email = user.email || "";
    if (!email) return "U";
    return email.charAt(0).toUpperCase();
  };

  return (
    <div className="absolute top-4 right-4 z-50">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Avatar className="cursor-pointer hover:opacity-80 transition-opacity border border-black/25 ml-3">
            <AvatarImage src={user.user_metadata?.avatar_url} />
            <AvatarFallback>{getInitials()}</AvatarFallback>
          </Avatar>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium">My Account</p>
              <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                {user.email}
              </p>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem 
            onClick={handleLogout} 
            className="text-red-600 cursor-pointer"
            disabled={isLoggingOut}
          >
            {isLoggingOut ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Logging out...
              </>
            ) : (
              <>
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </>
            )}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}