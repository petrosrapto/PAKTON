import { NextResponse } from "next/server";
// The client you created from the Server-Side Auth instructions
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  // if "next" is in param, use it as the redirect URL
  const next = searchParams.get("next") ?? "/";

  if (code) {
    const supabase = createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      const forwardedHost = request.headers.get("x-forwarded-host"); // original origin before load balancer
      const isLocalEnv = process.env.NODE_ENV === "development" || process.env.LOCAL_DEVELOPMENT === "true";
      
      // Add loginSuccess parameter to the redirect URL
      const successUrl = next === "/" ? "/?loginSuccess=true" : `${next}${next.includes('?') ? '&' : '?'}loginSuccess=true`;
      
      if (isLocalEnv) {
        // For local development (including Docker), always use localhost
        const localOrigin = origin.includes('localhost') ? origin : 'http://localhost:3000';
        return NextResponse.redirect(`${localOrigin}${successUrl}`);
      } else if (forwardedHost) {
        return NextResponse.redirect(`https://${forwardedHost}${successUrl}`);
      } else {
        return NextResponse.redirect(`${origin}${successUrl}`);
      }
    }
  }

  // return the user to an error page with instructions
  return NextResponse.redirect(`${origin}/auth/auth-code-error`);
}
