import { cn } from "@/lib/utils";
import NextImage from "next/image";
import Link from "next/link";
import { buttonVariants } from "../../ui/button";
import { UserAuthForm } from "./user-auth-form-login";
import { login } from "./actions";
import { createSupabaseClient } from "@/lib/supabase/client";
import { useSearchParams, useRouter } from "next/navigation";
import { useState, useEffect, useMemo } from "react";
import { FileText, Search, AlertCircle } from "lucide-react";
import { TighterText } from "../../ui/header";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "../../ui/button";
import { ReadOnlyComposer } from "../ReadOnlyComposer";

export interface LoginWithEmailInput {
  email: string;
  password: string;
}

// ContractAnalysisFeatures component from welcome.tsx
const ContractAnalysisFeatures = () => {
  return (
    <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
      <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm hover:shadow transition-all duration-300">
        <div className="flex items-center mb-2 justify-center">
          <div className="bg-gray-100 p-1.5 rounded-full mr-2">
            <FileText className="h-4 w-4 text-gray-600" />
          </div>
          <h3 className="font-medium text-gray-700 text-base text-center">Contract<br />Understanding</h3>
        </div>
        <p className="text-gray-600 text-sm leading-relaxed">PAKTON helps you explore your contracts by identifying obligations, rights, exceptions, and key clauses in a structured and explainable way.</p>
      </div>
      
      <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm hover:shadow transition-all duration-300">
        <div className="flex items-center mb-2 justify-center">
          <div className="bg-gray-100 p-1.5 rounded-full mr-2">
            <Search className="h-4 w-4 text-gray-600" />
          </div>
          <h3 className="font-medium text-gray-700 text-base text-center">Question<br />Answering</h3>
        </div>
        <p className="text-gray-600 text-sm leading-relaxed">Αsk questions about your contracts and receive detailed, well-reasoned reports grounded in both the document and trusted external legal sources.</p>
      </div>
      
      <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm hover:shadow transition-all duration-300">
        <div className="flex items-center mb-2 justify-center">
          <div className="bg-gray-100 p-1.5 rounded-full mr-2">
            <AlertCircle className="h-4 w-4 text-gray-600" />
          </div>
          <h3 className="font-medium text-gray-700 text-base text-center">Explainable<br />Legal Reports</h3>
        </div>
        <p className="text-gray-600 text-sm leading-relaxed">Each answer comes with clear reasoning, cited evidence, and an honest acknowledgment of uncertainty ensuring transparency.</p>
      </div>
    </div>
  );
};

// WhyPakton component from welcome.tsx
const WhyPakton = () => {
  return (
    <div className="mt-8 bg-white p-6 rounded-xl border border-gray-200 shadow-sm max-w-3xl mx-auto">
      <h3 className="text-xl font-medium text-center text-gray-800 mb-3">But, why PAKTON?</h3>
      <p className="text-gray-700 text-sm leading-relaxed text-center mb-4">
      Experimental results show that PAKTON outperforms general-purpose models on contract-related tasks not only in accuracy, but also in explainability, reasoning quality, justification, and the ability to handle ambiguity. 
      </p>
      <div className="flex justify-center">
        <a href="https://pakton.site/evaluation" target="_blank" rel="noopener noreferrer">
          <Button
            variant="outline"
            className="text-gray-700 hover:text-gray-800 transition-colors ease-in rounded-xl flex items-center justify-center gap-2 border-gray-300 hover:border-gray-400 hover:bg-gray-100 px-6 py-2"
          >
            <span>View Evaluation Experiments</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-external-link">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
          </Button>
        </a>
      </div>
    </div>
  );
};

export function Login() {
  const [errorType, setErrorType] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const error = searchParams.get("error");
    if (error) {
      setErrorType(error);
      // Remove the error parameter from the URL
      const newSearchParams = new URLSearchParams(searchParams);
      newSearchParams.delete("error");
      router.replace(
        `${window.location.pathname}?${newSearchParams.toString()}`,
        { scroll: false }
      );
    }
  }, [searchParams, router]);

  const onLoginWithEmail = async (
    input: LoginWithEmailInput
  ): Promise<void> => {
    setErrorType(null);
    await login(input);
  };

  const onLoginWithOauth = async (
    provider: "google" | "github"
  ): Promise<void> => {
    try {
      setErrorType(null);
      const client = createSupabaseClient();
      const currentOrigin =
        typeof window !== "undefined" ? window.location.origin : "";
      
      const { error } = await client.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo: `${currentOrigin}/auth/callback`,
        },
      });

      if (error) {
        console.error("OAuth Error:", error);
        setErrorType("oauth_error");
      }
    } catch (error) {
      console.error("OAuth Error:", error);
      setErrorType("oauth_error");
    }
  };

  return (
    <div className="flex h-screen">
      {/* Left side - Features (2/3 width) - Now white background with vertical centering */}
      <div className="w-2/3 bg-white overflow-y-auto px-8 py-10 flex items-center justify-center">
        <div className="max-w-2xl w-full">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-3 mb-2">
              <Avatar className="h-10 w-10 bg-blue-100 ring-2 ring-blue-50">
                <AvatarFallback className="text-lg font-bold text-blue-800">📜</AvatarFallback>
              </Avatar>
              <TighterText className="text-2xl font-medium">
                <span style={{ 
                  fontFamily: "'Times New Roman', serif", 
                  letterSpacing: "0.1em", 
                  textTransform: "uppercase",
                  fontWeight: "bold",
                  textShadow: "1px 1px 1px rgba(0,0,0,0.1)"
                }}>
                  PAKTON
                </span>
              </TighterText>
            </div>
            <p className="text-gray-600 mt-2">A Multi-Agent Framework for Contract Document Analysis</p>
          </div>
          
          <ContractAnalysisFeatures />
          
          {/* Replace StreamingChatQuestions with ReadOnlyComposer */}
          <ReadOnlyComposer />
          
          <WhyPakton />
        </div>
      </div>
      
      {/* Right side - Auth (1/3 width) - Now gray background */}
      <div className="w-1/3 bg-gray-50 flex items-center justify-center">
        <div className="w-full max-w-md px-8">
          <div className="w-full bg-white rounded-lg overflow-hidden border border-gray-200 shadow-sm">
            {/* Auth Tabs */}
            <div className="flex w-full mb-6">
              <div className="w-1/2 bg-blue-50 border-b-2 border-blue-500 rounded-tl-md">
                <Link href="/auth/login" className="flex justify-center py-3 font-medium text-blue-600">
                  Login
                </Link>
              </div>
              <div className="w-1/2 bg-gray-50 border-b border-gray-200 rounded-tr-md">
                <Link href="/auth/signup" className="flex justify-center py-3 font-medium text-gray-500 hover:text-gray-700">
                  Sign up
                </Link>
              </div>
            </div>

            {/* Auth Form */}
            <div className="p-6">
              <div className="flex flex-col space-y-2 text-center mb-6">
                <h1 className="text-2xl font-semibold tracking-tight">Welcome back</h1>
                <p className="text-sm text-muted-foreground">Enter your credentials to sign in</p>
              </div>
              <UserAuthForm
                onLoginWithEmail={onLoginWithEmail}
                onLoginWithOauth={onLoginWithOauth}
              />
              {errorType && (
                <p className="text-red-500 text-sm text-center mt-4">
                  {errorType === 'invalid_credentials' 
                    ? "Invalid email or password. Please check your credentials and try again."
                    : errorType === 'oauth_error'
                    ? "There was an error with social login. Please try again or contact support if the problem persists."
                    : "There was an error signing into your account. Please try again."
                  }
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
