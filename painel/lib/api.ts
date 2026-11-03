// painel/lib/api.ts
// Fala com a API do robô. Só é usado no servidor (Server Components), por isso não precisa de CORS.

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

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

export async function buscarLeads(limite = 200): Promise<Lead[]> {
  // no-store: pede o dado atual a cada visita, porque a fila muda quando o robô roda
  const resposta = await fetch(`${API_URL}/leads?limite=${limite}`, { cache: "no-store" });
  if (!resposta.ok) {
    throw new Error(`API respondeu ${resposta.status}: ${await resposta.text()}`);
  }
  return resposta.json();
}
