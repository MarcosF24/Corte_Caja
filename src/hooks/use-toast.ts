import { toast as sonner } from "sonner";
type Opts = { title?: string; description?: string; variant?: "default"|"destructive" };
export function toast({ title, description }: Opts){
  sonner(title ?? "", { description });
}
