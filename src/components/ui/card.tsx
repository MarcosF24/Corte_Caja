import * as React from "react";
import { cn } from "../../lib/utils";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-xl border bg-card text-card-foreground shadow", className)} {...props} />;
}
export const CardHeader = (p: React.HTMLAttributes<HTMLDivElement>) => <div className="p-6 pb-3" {...p} />;
export const CardTitle = (p: React.HTMLAttributes<HTMLHeadingElement>) => <h3 className="text-2xl font-bold" {...p} />;
export const CardDescription = (p: React.HTMLAttributes<HTMLParagraphElement>) => <p className="text-sm text-muted-foreground" {...p} />;
export const CardContent = (p: React.HTMLAttributes<HTMLDivElement>) => <div className="p-6 pt-0" {...p} />;
