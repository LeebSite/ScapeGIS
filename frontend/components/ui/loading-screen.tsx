"use client";

import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingScreenProps {
  fullScreen?: boolean;
  message?: string;
}

export function LoadingScreen({
  fullScreen = true,
  message = "Memuat...",
}: LoadingScreenProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-3 p-6 text-center">
      {/* Simple Centered Branded Logo & Spinner */}
      <div className="relative flex items-center justify-center w-12 h-12 mb-1">
        <Loader2 className="w-12 h-12 text-primary animate-spin" />
        <img
          src="/img/logo_scapegis.svg"
          alt="ScapeGIS Logo"
          width={22}
          height={22}
          className="absolute inset-auto"
           onError={(e) => {
            (e.target as HTMLElement).style.display = "none";
          }}
        />
      </div>

      {/* Brand & Loading Text */}
      <div className="flex flex-col items-center gap-1">
        <span className="font-semibold tracking-wide text-foreground font-kayak text-lg">
          ScapeGIS
        </span>
        <p className="text-xs text-muted-foreground animate-pulse">
          {message}
        </p>
      </div>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
        {content}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center w-full min-h-[300px]">
      {content}
    </div>
  );
}

export default LoadingScreen;