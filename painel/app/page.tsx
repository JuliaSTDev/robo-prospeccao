import { buscarLeads } from "@/lib/api";
import TabelaLeads from "@/components/TabelaLeads";

export default async function Home() {
  const leads = await buscarLeads();

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Fila de leads</h1>
        <p className="mt-1 text-sm text-texto-suave">Os {leads.length} de maior nota, do melhor para o pior.</p>
      </div>
      <TabelaLeads leads={leads} />
    </main>
  );
}
