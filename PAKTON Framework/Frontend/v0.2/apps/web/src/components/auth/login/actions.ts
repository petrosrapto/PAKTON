"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import { LoginWithEmailInput } from "./Login";

export async function login(input: LoginWithEmailInput) {
  const supabase = createClient();

  const data = {
    email: input.email,
    password: input.password,
  };

  const { error } = await supabase.auth.signInWithPassword(data);

  if (error) {
    console.error(error);
    // Pass the specific error code to the login page
    const errorCode = error.message.includes('Invalid login credentials') || 
                      error.message.includes('invalid_credentials') ||
                      (error as any).code === 'invalid_credentials'
      ? 'invalid_credentials' 
      : 'generic_error';
    redirect(`/auth/login?error=${errorCode}`);
  }

  revalidatePath("/", "layout");
  redirect("/?loginSuccess=true");
}
