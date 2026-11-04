import "server-only"; // se isto for importado num Client Component, o build falha
import { createClient } from "@supabase/supabase-js";

const urlBruta = process.env.SUPABASE_URL;
const chave = process.env.SUPABASE_SECRET_KEY;

if (!urlBruta || !chave) {
  throw new Error("Faltam SUPABASE_URL e SUPABASE_SECRET_KEY no painel/.env.local");
}

// A página Data API do Supabase mostra a URL com "/rest/v1/" no fim, mas o cliente quer só o endereço
// do projeto (ele acrescenta o resto sozinho). Aqui aceitamos os dois jeitos, como o Banco do Python.
const url = urlBruta.replace(/\/+$/, "").replace(/\/rest\/v1$/, "");

export const supabase = createClient(url, chave, { auth: { persistSession: false } });
