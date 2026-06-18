"use client";

import { Separator } from "@/components/ui/separator";
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
    <Separator
      orientation={orientation}
      className={cn(className)}
    />
  );
}
