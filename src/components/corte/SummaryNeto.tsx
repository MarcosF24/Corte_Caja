import { Calculator } from "lucide-react";

export default function SummaryNeto() {
  return (
    <div className="rounded-2xl bg-gradient-to-r from-blue-500 to-indigo-500 text-white p-6 shadow mb-6 flex items-center justify-between">
      <div>
        <p className="text-white/80 text-sm">Total Neto Calculado</p>
        <p className="text-4xl font-extrabold leading-tight">$0.00</p>
      </div>
      <div className="w-11 h-11 rounded-xl bg-white/20 grid place-items-center">
        <Calculator className="w-6 h-6" />
      </div>
    </div>
  );
}
