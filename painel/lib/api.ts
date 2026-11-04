// painel/lib/api.ts
// Fala com a API do robô. Só é usado no servidor (Server Components), por isso não precisa de CORS.

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";
import { STATUS, type Status } from "./status";

export { STATUS };
export type { Status };

// A ficha completa (o LeadDetalhe do Python): tudo do Lead mais o que a página do lead mostra.
export interface LeadDetalhe extends Lead {
  razao_social: string;
  nome_fantasia: string | null;
  cnae: string;
  uf: string;
  matriz_filial: string;
  site_motivo: string;
  cidade: string;
  coletado_em: string;
  links: Record<string, string>;
}

// O lead como a API devolve (espelha o LeadSaida do Python).
export interface Lead {
  cnpj: string;
  nome: string;
  nota: number;
  motivo_da_nota: string;
  sinais: string[];
  status: string;
  municipio: string;
  porte: string;
  telefone: string | null;
  email: string | null;
  site: string | null;
  site_situacao: string | null;
  data_abertura: string | null; // "2001-01-23": no JSON a data chega como texto
}

export async function buscarLead(cnpj: string): Promise<LeadDetalhe | null> {
  const resposta = await fetch(`${API_URL}/leads/${cnpj}`, { cache: "no-store" });
  if (resposta.status === 404) {
    return null;
  }
  if (!resposta.ok) {
    throw new Error(`API respondeu ${resposta.status}: ${await resposta.text()}`);
  }
  return resposta.json();
}

export async function mudarStatus(cnpj: string, status: Status): Promise<void> {
  const resposta = await fetch(`${API_URL}/leads/${cnpj}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!resposta.ok) {
    throw new Error(`API respondeu ${resposta.status}: ${await resposta.text()}`);
  }
}

export async function buscarLeads(limite = 200): Promise<Lead[]> {
  // no-store: pede o dado atual a cada visita, porque a fila muda quando o robô roda
  const resposta = await fetch(`${API_URL}/leads?limite=${limite}`, { cache: "no-store" });
  if (!resposta.ok) {
    throw new Error(`API respondeu ${resposta.status}: ${await resposta.text()}`);
  }
  return resposta.json();
}
