"use client";

import React, { FC, useState, useEffect, memo } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown, Search } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface InterrogatingIndicatorProps {
  toolCall?: {
    name: string;
    arguments: any;
  };
  isActive?: boolean;
}

const InterrogatingIndicatorComponent: FC<InterrogatingIndicatorProps> = ({
  toolCall,
  isActive = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [dots, setDots] = useState("");

  // Animate dots when active
  useEffect(() => {
    if (!isActive) {
      setDots("");
      return;
    }
    
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 500);
    
    return () => clearInterval(interval);
  }, [isActive]);

  if (!toolCall || toolCall.name !== 'interrogation') {
    return null;
  }

  const { query, context, instructions } = toolCall.arguments || {};

  return (
    <div className="w-full mb-3">
      <div 
        className={cn(
          "relative overflow-hidden rounded-xl",
          "bg-[#f9f9f8] dark:bg-[#2a2a28]",
          "border border-[#e5e5e3] dark:border-[#3a3a38]"
        )}
      >
        {/* Subtle shine effect - only when active */}
        {isActive && (
          <motion.div
            key="shine-effect"
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 dark:via-white/5 to-transparent -skew-x-12 pointer-events-none"
            initial={false}
            animate={{ x: ["−100%", "200%"] }}
            transition={{ 
              duration: 2.5,
              repeat: Infinity,
              repeatDelay: 4,
              ease: "easeInOut"
            }}
          />
        )}

        {/* Header */}
        <div 
          className={cn(
            "relative flex items-center gap-3 px-4 py-3 cursor-pointer",
            "transition-colors duration-150",
            "hover:bg-[#f3f3f2] dark:hover:bg-[#323230]"
          )}
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {/* Search Icon */}
          <div className="relative flex-shrink-0">
            <div className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center",
              "bg-[#eeeeec] dark:bg-[#3a3a38]"
            )}>
              <Search className="w-4 h-4 text-[#6b6b69] dark:text-[#a1a1a0]" />
            </div>
            
            {/* Active indicator dot */}
            {isActive && (
              <motion.div
                key="active-dot"
                className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-[#c96442]"
                initial={false}
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            )}
          </div>
          
          {/* Title */}
          <div className="flex-1 min-w-0">
            <span className="text-sm font-medium text-[#1a1a19] dark:text-[#ececec]">
              {isActive ? `Researching${dots}` : "Research complete"}
            </span>
          </div>
          
          {/* Expand Icon */}
          <motion.div
            initial={false}
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="w-4 h-4 text-[#8b8b89] dark:text-[#8b8b89]" />
          </motion.div>
        </div>

        {/* Thin progress line when active */}
        {isActive && (
          <div className="h-[1px] bg-[#e5e5e3] dark:bg-[#3a3a38]">
            <motion.div
              key="progress-bar"
              className="h-full bg-[#c96442]"
              initial={false}
              animate={{ width: ["0%", "100%"] }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
          </div>
        )}

        {/* Expandable Content */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="px-4 py-3 space-y-3 border-t border-[#e5e5e3] dark:border-[#3a3a38]">
                {query && (
                  <div className="space-y-1">
                    <span className="text-xs font-medium text-[#8b8b89] dark:text-[#8b8b89] uppercase tracking-wide">
                      Query
                    </span>
                    <p className="text-sm text-[#1a1a19] dark:text-[#ececec]">
                      {query}
                    </p>
                  </div>
                )}
                
                {context && (
                  <div className="space-y-1">
                    <span className="text-xs font-medium text-[#8b8b89] dark:text-[#8b8b89] uppercase tracking-wide">
                      Context
                    </span>
                    <p className="text-sm text-[#6b6b69] dark:text-[#a1a1a0] font-mono text-xs">
                      {typeof context === 'string' ? context : JSON.stringify(context, null, 2)}
                    </p>
                  </div>
                )}
                
                {instructions && (
                  <div className="space-y-1">
                    <span className="text-xs font-medium text-[#8b8b89] dark:text-[#8b8b89] uppercase tracking-wide">
                      Instructions
                    </span>
                    <p className="text-sm text-[#1a1a19] dark:text-[#ececec]">
                      {instructions}
                    </p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

// Memoize the component to prevent unnecessary re-renders during message streaming
export const InterrogatingIndicator = memo(InterrogatingIndicatorComponent, (prevProps, nextProps) => {
  // Only re-render if isActive or toolCall arguments actually changed
  const prevArgs = prevProps.toolCall?.arguments;
  const nextArgs = nextProps.toolCall?.arguments;
  
  return (
    prevProps.isActive === nextProps.isActive &&
    prevProps.toolCall?.name === nextProps.toolCall?.name &&
    prevArgs?.query === nextArgs?.query &&
    prevArgs?.context === nextArgs?.context &&
    prevArgs?.instructions === nextArgs?.instructions
  );
});
