"use client";

import { useState } from "react";
import Link from "next/link";
import type { Lead } from "@/lib/api";

// A API devolve o código da Receita; o painel mostra o nome da cidade.
const CIDADES: Record<string, string> = {
  "7107": "São Paulo",
  "7151": "Suzano",
};

const STATUS = ["novo", "aprovado", "descartado", "abordado"];

const campo = "rounded border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900";

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

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-3">
        <input
          className={campo}
          placeholder="Buscar por nome"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />

        <select className={campo} value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Todos os status</option>
          {STATUS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <select className={campo} value={cidade} onChange={(e) => setCidade(e.target.value)}>
          <option value="">Todas as cidades</option>
          {Object.entries(CIDADES).map(([codigo, nome]) => (
            <option key={codigo} value={codigo}>
              {nome}
            </option>
          ))}
        </select>

        <select className={campo} value={sinal} onChange={(e) => setSinal(e.target.value)}>
          <option value="">Todos os sinais</option>
          {sinaisDisponiveis.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <p className="mb-2 text-sm text-zinc-500">
        {visiveis.length} de {leads.length} leads
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-zinc-300 text-zinc-500 dark:border-zinc-700">
            <tr>
              <th className="py-2 pr-4">Nota</th>
              <th className="py-2 pr-4">Nome</th>
              <th className="py-2 pr-4">Motivo</th>
              <th className="py-2 pr-4">Sinais</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2 pr-4">Telefone</th>
              <th className="py-2">Site</th>
            </tr>
          </thead>
          <tbody>
            {visiveis.map((lead) => (
              <tr key={lead.cnpj} className="border-b border-zinc-200 align-top dark:border-zinc-800">
                <td className="py-2 pr-4 font-semibold">{lead.nota}</td>
                <td className="py-2 pr-4">
                  <Link href={`/leads/${lead.cnpj}`} className="underline">
                    {lead.nome}
                  </Link>
                </td>
                <td className="py-2 pr-4 text-zinc-600 dark:text-zinc-400">{lead.motivo_da_nota}</td>
                <td className="py-2 pr-4">
                  <div className="flex flex-wrap gap-1">
                    {lead.sinais.map((s) => (
                      <span key={s} className="rounded bg-zinc-100 px-2 py-0.5 text-xs dark:bg-zinc-800">
                        {s}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="py-2 pr-4">{lead.status}</td>
                <td className="whitespace-nowrap py-2 pr-4">{lead.telefone ?? "—"}</td>
                <td className="py-2">
                  {lead.site ? (
                    <a href={lead.site} target="_blank" rel="noreferrer" className="text-blue-600 underline">
                      abrir
                    </a>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
