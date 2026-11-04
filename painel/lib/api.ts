// Fala com o banco (Supabase) a partir do servidor do painel.
// O `import "server-only"` faz o build falhar se este arquivo for parar num Client Component:
// aqui se usa a chave secreta do banco, que nunca pode chegar ao navegador.
import "server-only";
import { connection } from "next/server";
import { supabase } from "./supabase";
import { STATUS, type Status } from "./status";

export { STATUS };
export type { Status };

// O lead como a fila mostra (o mesmo formato que a API do robô devolvia).
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

// A ficha completa: tudo do Lead mais o que a página do lead mostra.
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

// Uma linha da tabela `leads`, como o Supabase devolve.
interface LinhaLead {
  cnpj: string;
  razao_social: string;
  nome_fantasia: string | null;
  cnae: string;
  municipio: string;
  uf: string;
  porte: string;
  matriz_filial: string;
  data_abertura: string | null;
  telefone: string | null;
  email: string | null;
  site: string | null;
  site_situacao: string | null;
  site_motivo: string;
  sinais: string[];
  nota: number;
  motivo_da_nota: string;
  status: string;
  coletado_em: string;
  cidade: string;
  links: Record<string, string>;
}

function paraLead(l: LinhaLead): Lead {
  return {
    cnpj: l.cnpj,
    nome: l.nome_fantasia || l.razao_social,
    nota: l.nota,
    motivo_da_nota: l.motivo_da_nota,
    sinais: l.sinais,
    status: l.status,
    municipio: l.municipio,
    porte: l.porte,
    telefone: l.telefone,
    email: l.email,
    site: l.site,
    site_situacao: l.site_situacao,
    data_abertura: l.data_abertura,
  };
}

function paraDetalhe(l: LinhaLead): LeadDetalhe {
  return {
    ...paraLead(l),
    razao_social: l.razao_social,
    nome_fantasia: l.nome_fantasia,
    cnae: l.cnae,
    uf: l.uf,
    matriz_filial: l.matriz_filial,
    site_motivo: l.site_motivo,
    cidade: l.cidade,
    coletado_em: l.coletado_em,
    links: l.links,
  };
}

export async function buscarLeads(limite = 200): Promise<Lead[]> {
  await connection(); // só no momento do pedido: a fila muda quando o robô roda
  const { data, error } = await supabase
    .from("leads")
    .select("*")
    .order("nota", { ascending: false })
    .order("cnpj")
    .limit(limite);
  if (error) {
    throw new Error(`Supabase: ${error.message}`);
  }
  return (data as LinhaLead[]).map(paraLead);
}

export async function buscarLead(cnpj: string): Promise<LeadDetalhe | null> {
  await connection();
  // maybeSingle: se não existe, devolve data = null (em vez de dar erro). É o 404.
  const { data, error } = await supabase.from("leads").select("*").eq("cnpj", cnpj).maybeSingle();
  if (error) {
    throw new Error(`Supabase: ${error.message}`);
  }
  return data ? paraDetalhe(data as LinhaLead) : null;
}

export async function mudarStatus(cnpj: string, status: Status): Promise<void> {
  // .select("cnpj") faz o update devolver as linhas alteradas: lista vazia = esse CNPJ não existe
  const { data, error } = await supabase.from("leads").update({ status }).eq("cnpj", cnpj).select("cnpj");
  if (error) {
    throw new Error(`Supabase: ${error.message}`);
  }
  if (!data || data.length === 0) {
    throw new Error(`Lead não encontrado: ${cnpj}`);
  }
}
