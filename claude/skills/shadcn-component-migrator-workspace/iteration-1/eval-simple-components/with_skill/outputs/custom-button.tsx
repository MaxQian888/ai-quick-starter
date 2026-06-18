"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface CustomButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "danger";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  className?: string;
}

export function CustomButton({
  children,
  onClick,
  variant = "primary",
  size = "md",
  disabled,
  className,
}: CustomButtonProps) {
  const variantMap: Record<string, "default" | "secondary" | "destructive"> = {
    primary: "default",
    secondary: "secondary",
    danger: "destructive",
  };

  const sizeMap: Record<string, "sm" | "default" | "lg"> = {
    sm: "sm",
    md: "default",
    lg: "lg",
  };

  return (
    <Button
      onClick={onClick}
      disabled={disabled}
      variant={variantMap[variant]}
      size={sizeMap[size]}
      className={cn(className)}
    >
      {children}
    </Button>
  );
}
