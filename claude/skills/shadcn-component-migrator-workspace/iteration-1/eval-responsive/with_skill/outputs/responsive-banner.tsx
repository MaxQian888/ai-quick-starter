"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { cn } from "@/lib/utils";

interface ResponsiveBannerProps {
  title: string;
  message: string;
  className?: string;
}

export function ResponsiveBanner({ title, message, className }: ResponsiveBannerProps) {
  return (
    <Alert
      className={cn(
        "flex flex-col gap-2 rounded-lg border border-blue-200 bg-blue-50 p-3",
        "sm:flex-row sm:items-center sm:gap-4 sm:p-4",
        "md:p-5",
        "lg:rounded-xl lg:p-6",
        className
      )}
    >
      <AlertTitle
        className={cn(
          "text-sm font-semibold text-blue-900",
          "sm:text-base",
          "md:text-lg"
        )}
      >
        {title}
      </AlertTitle>
      <AlertDescription
        className={cn(
          "text-xs text-blue-700",
          "sm:text-sm",
          "sm:flex-1"
        )}
      >
        {message}
      </AlertDescription>
    </Alert>
  );
}
