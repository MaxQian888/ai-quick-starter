"use client";

import { cn } from "@/lib/utils";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";

interface ResponsiveBannerProps {
  title: string;
  message: string;
  className?: string;
}

export function ResponsiveBanner({ title, message, className }: ResponsiveBannerProps) {
  return (
    <Alert
      className={cn(
        "border-blue-200 bg-blue-50 text-blue-900",
        "sm:flex sm:flex-row sm:items-center sm:gap-4",
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
