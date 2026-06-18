"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface CustomSeparatorProps {
  orientation?: "horizontal" | "vertical";
  className?: string;
}

export function CustomSeparator({
  orientation = "horizontal",
  className,
}: CustomSeparatorProps) {
  return (
    <div
      data-slot="custom-separator"
      data-orientation={orientation}
      role="separator"
      aria-orientation={orientation}
      className={cn(
        "shrink-0 bg-border",
        orientation === "horizontal" && "h-px w-full",
        orientation === "vertical" && "h-full w-px",
        className
      )}
    />
  );
}
