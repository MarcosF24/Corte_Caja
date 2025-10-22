import { useForm, type SubmitHandler } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "../ui/button";

const schema = z.object({
  fecha: z.string().min(1, "Requerida"),
  turno: z.enum(["matutino", "vespertino", "nocturno"]),
  fondoInicial: z.coerce.number().min(0, "Mínimo 0").transform((val) => Number(val)),
  ventasEfectivo: z.coerce.number().min(0, "Mínimo 0").transform((val) => Number(val)),
  ventasTarjeta: z.coerce.number().min(0, "Mínimo 0").transform((val) => Number(val)),
  gastos: z.coerce.number().min(0, "Mínimo 0").transform((val) => Number(val)),
  observaciones: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export default function FormCorte() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      fecha: new Date().toISOString().slice(0, 10),
      turno: "matutino",
      fondoInicial: 0,
      ventasEfectivo: 0,
      ventasTarjeta: 0,
      gastos: 0,
      observaciones: "",
    },
  });

  const onSubmit: SubmitHandler<FormValues> = (data) => {
    console.table(data);
    alert("Corte capturado (solo UI).");
    reset();
  };

  const Field = ({
    label,
    children,
    error,
  }: {
    label: string;
    children: React.ReactNode;
    error?: string;
  }) => (
    <label className="block">
      <span className="text-sm font-medium">{label}</span>
      <div className="mt-1">{children}</div>
      {error ? <p className="text-destructive text-xs mt-1">{error}</p> : null}
    </label>
  );

  const inputCls =
    "w-full h-10 rounded-md border border-input bg-background px-3 text-sm " +
    "placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Field label="Fecha" error={errors.fecha?.message}>
          <input type="date" className={inputCls} {...register("fecha")} />
        </Field>

        <Field label="Turno" error={errors.turno?.message}>
          <select className={inputCls} {...register("turno")}>
            <option value="matutino">Matutino</option>
            <option value="vespertino">Vespertino</option>
            <option value="nocturno">Nocturno</option>
          </select>
        </Field>

        <Field label="Fondo inicial" error={errors.fondoInicial?.message}>
          <input type="number" className={inputCls} {...register("fondoInicial")} />
        </Field>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Field label="Ventas (efectivo)" error={errors.ventasEfectivo?.message}>
          <input type="number" className={inputCls} {...register("ventasEfectivo")} />
        </Field>

        <Field label="Ventas (tarjeta)" error={errors.ventasTarjeta?.message}>
          <input type="number" className={inputCls} {...register("ventasTarjeta")} />
        </Field>

        <Field label="Gastos" error={errors.gastos?.message}>
          <input type="number" className={inputCls} {...register("gastos")} />
        </Field>
      </div>

      <Field label="Observaciones" error={errors.observaciones?.message}>
        <textarea rows={3} className={`${inputCls} py-2`} {...register("observaciones")} />
      </Field>

      <div className="flex items-center justify-end gap-3 pt-2">
        <button
          type="button"
          className="h-10 px-4 rounded-md border border-input bg-background"
          onClick={() => reset()}
        >
          Limpiar
        </button>
        <Button type="submit" className="h-10 px-5" disabled={isSubmitting}>
          {isSubmitting ? "Guardando..." : "Guardar corte"}
        </Button>
      </div>
    </form>
  );
}
