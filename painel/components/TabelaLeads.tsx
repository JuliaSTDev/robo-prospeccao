"use client";

import { useState } from "react";
import Link from "next/link";
import type { Lead } from "@/lib/api";
import { ROTULOS, STATUS } from "@/lib/status";
import NotaBadge from "@/components/ui/NotaBadge";
import SinalChip from "@/components/ui/SinalChip";
import StatusBadge from "@/components/ui/StatusBadge";

// A API devolve o código da Receita; o painel mostra o nome da cidade.
const CIDADES: Record<string, string> = {
  "7107": "São Paulo",
  "7151": "Suzano",
};

const campo =
  "h-10 rounded-xl border border-borda bg-superficie px-3 text-sm text-texto placeholder:text-texto-suave transition-colors hover:border-texto-suave/50";

function LinkSite({ site }: { site: string | null }) {
  if (!site) return <span className="text-texto-suave">—</span>;
  return (
    <a
      href={site}
      target="_blank"
      rel="noreferrer"
      className="relative z-10 text-marca-clara underline-offset-4 hover:underline"
    >
      abrir site ↗
    </a>
  );
}

export default function TabelaLeads({ leads }: { leads: Lead[] }) {
  const [busca, setBusca] = useState("");
  const [status, setStatus] = useState(""); // "" quer dizer "todos"
  const [cidade, setCidade] = useState("");
  const [sinal, setSinal] = useState("");

  // todos os sinais de todos os leads, sem repetir (Set) e em ordem alfabética
  const sinaisDisponiveis = Array.from(new Set(leads.flatMap((lead) => lead.sinais))).sort();

  // a lista filtrada é calculada a cada render (não vai no estado), assim nunca fica fora de sincronia
  const termo = busca.toLowerCase();
  const visiveis = leads.filter(
    (lead) =>
      (busca === "" || lead.nome.toLowerCase().includes(termo)) &&
      (status === "" || lead.status === status) &&
      (cidade === "" || lead.municipio === cidade) &&
      (sinal === "" || lead.sinais.includes(sinal)),
  );

  function limparFiltros() {
    setBusca("");
    setStatus("");
    setCidade("");
    setSinal("");
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2" role="group" aria-label="Filtrar por status">
        {["", ...STATUS].map((s) => {
          const ativo = status === s;
          const quantos = s === "" ? leads.length : leads.filter((lead) => lead.status === s).length;
          return (
            <button
              key={s}
              type="button"
              aria-pressed={ativo}
              onClick={() => setStatus(s)}
              className={`inline-flex min-h-9 items-center gap-2 rounded-full border px-3.5 text-sm transition-colors ${
                ativo
                  ? "border-marca/50 bg-marca/15 text-marca-clara"
                  : "border-borda bg-superficie text-texto-suave hover:border-texto-suave/50 hover:text-texto"
              }`}
            >
              {s === "" ? "Todos" : ROTULOS[s as keyof typeof ROTULOS]}
              <span className="text-xs tabular-nums opacity-70">{quantos}</span>
            </button>
          );
        })}
      </div>

      <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        <input
          className={campo}
          placeholder="Buscar por nome"
          aria-label="Buscar por nome"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />

        <select
          className={campo}
          aria-label="Filtrar por cidade"
          value={cidade}
          onChange={(e) => setCidade(e.target.value)}
        >
          <option value="">Todas as cidades</option>
          {Object.entries(CIDADES).map(([codigo, nome]) => (
            <option key={codigo} value={codigo}>
              {nome}
            </option>
          ))}
        </select>

        <select
          className={campo}
          aria-label="Filtrar por sinal"
          value={sinal}
          onChange={(e) => setSinal(e.target.value)}
        >
          <option value="">Todos os sinais</option>
          {sinaisDisponiveis.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <p className="mb-3 text-sm text-texto-suave" aria-live="polite">
        {visiveis.length} de {leads.length} leads
      </p>

      {visiveis.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-borda px-6 py-14 text-center">
          <p className="font-medium">Nenhum lead com esses filtros</p>
          <p className="mt-1 text-sm text-texto-suave">Tente outro termo ou limpe os filtros.</p>
          <button
            type="button"
            onClick={limparFiltros}
            className="mt-4 inline-flex min-h-10 items-center rounded-xl border border-borda bg-superficie px-4 text-sm transition-colors hover:border-marca/60 hover:text-marca-clara"
          >
            Limpar filtros
          </button>
        </div>
      ) : (
        <>
          {/* Computador: tabela */}
          <div className="hidden overflow-hidden rounded-2xl border border-borda bg-superficie md:block">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-borda text-xs uppercase tracking-wide text-texto-suave">
                <tr>
                  <th className="px-4 py-3 font-medium">Nota</th>
                  <th className="px-4 py-3 font-medium">Lead</th>
                  <th className="px-4 py-3 font-medium">Sinais</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Contato</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borda">
                {visiveis.map((lead) => (
                  <tr key={lead.cnpj} className="align-top transition-colors hover:bg-texto/5">
                    <td className="px-4 py-3">
                      <NotaBadge nota={lead.nota} />
                    </td>
                    <td className="max-w-md px-4 py-3">
                      <Link
                        href={`/leads/${lead.cnpj}`}
                        className="font-medium transition-colors hover:text-marca-clara"
                      >
                        {lead.nome}
                      </Link>
                      <p className="mt-0.5 text-xs text-texto-suave">{lead.motivo_da_nota}</p>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {lead.sinais.map((s) => (
                          <SinalChip key={s} sinal={s} />
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={lead.status} />
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <p>{lead.telefone ?? "—"}</p>
                      <p className="mt-0.5 text-xs">
                        <LinkSite site={lead.site} />
                      </p>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Celular: um cartão por lead */}
          <ul className="space-y-3 md:hidden">
            {visiveis.map((lead) => (
              <li
                key={lead.cnpj}
                className="relative rounded-2xl border border-borda bg-superficie p-4 transition-colors hover:border-texto-suave/40"
              >
                <div className="flex items-start gap-3">
                  <NotaBadge nota={lead.nota} />
                  <div className="min-w-0 flex-1">
                    <Link
                      href={`/leads/${lead.cnpj}`}
                      className="font-semibold after:absolute after:inset-0 after:rounded-2xl"
                    >
                      {lead.nome}
                    </Link>
                    <p className="mt-0.5 text-xs text-texto-suave">{lead.motivo_da_nota}</p>
                  </div>
                  <StatusBadge status={lead.status} />
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {lead.sinais.map((s) => (
                    <SinalChip key={s} sinal={s} />
                  ))}
                </div>
                <div className="mt-3 flex items-center justify-between text-sm">
                  <span>{lead.telefone ?? "—"}</span>
                  <LinkSite site={lead.site} />
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
