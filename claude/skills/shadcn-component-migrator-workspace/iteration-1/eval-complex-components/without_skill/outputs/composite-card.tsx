"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface TaskCardProps {
  title: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  className?: string;
}

export function TaskCard({ title, status, progress, className }: TaskCardProps) {
  const statusColors = {
    pending: "bg-yellow-500/15 text-yellow-700",
    running: "bg-blue-500/15 text-blue-700",
    completed: "bg-green-500/15 text-green-700",
    failed: "bg-red-500/15 text-red-700",
  };

  return (
    <Card className={cn(className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{title}</CardTitle>
          <Badge variant="secondary" className={cn(statusColors[status])}>
            {status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <Progress value={progress} className="h-2" />
        <p className="mt-2 text-xs text-muted-foreground">{progress}% complete</p>
      </CardContent>
    </Card>
  );
}
