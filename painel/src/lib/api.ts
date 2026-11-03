const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

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
  data_abertura: string | null;
}

export async function buscarLeads(limite = 200): Promise<Lead[]> {
  const resposta = await fetch(`${API_URL}/leads?limite=${limite}`, { cache: "no-store" });
  if (!resposta.ok) {
    throw new Error(`API respondeu ${resposta.status}: ${await resposta.text()}`);
  }
  return resposta.json();
}