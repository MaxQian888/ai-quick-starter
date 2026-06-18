"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface CustomBadgeProps {
  children: React.ReactNode;
  color?: "blue" | "green" | "red" | "yellow" | "gray";
  className?: string;
}

export function CustomBadge({
  children,
  color = "gray",
  className,
}: CustomBadgeProps) {
  const colorMap: Record<string, "default" | "secondary" | "destructive" | "outline" | "ghost"> = {
    blue: "default",
    green: "secondary",
    red: "destructive",
    yellow: "outline",
    gray: "ghost",
  };

  return (
    <Badge variant={colorMap[color]} className={cn(className)}>
      {children}
    </Badge>
  );
}
