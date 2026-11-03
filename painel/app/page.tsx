import { buscarLeads } from "@/lib/api";
import TabelaLeads from "@/components/TabelaLeads";

export default async function Home() {
  const leads = await buscarLeads(); 

  return (
    <main className="mx-auto max-w-7xl p-6">
      <h1 className="mb-1 text-2xl font-semibold">Fila de leads</h1>
      <p className="mb-6 text-sm text-zinc-500">Os {leads.length} de maior nota, do melhor para o pior.</p>
      <TabelaLeads leads={leads} />
    </main>
  );
}