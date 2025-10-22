import LayoutCajero from "../corte/LayoutCajero";
import SummaryNeto from "../corte/SummaryNeto";
import FormCorte from "../corte/FormCorte";

export default function CorteCaja() {
  return (
    <LayoutCajero>
      <div className="mx-auto max-w-5xl">
        <SummaryNeto />

        <div className="rounded-2xl border bg-card text-card-foreground shadow">
          <div className="p-6 pb-2">
            <h2 className="text-2xl font-bold">Información del Corte</h2>
            <p className="text-sm text-muted-foreground">
              Completa los datos del corte de caja actual
            </p>
          </div>
          <div className="p-6 pt-0">
            <FormCorte />
          </div>
        </div>
      </div>
    </LayoutCajero>
  );
}
