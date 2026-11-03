import { alterarStatus } from "@/app/leads/[cnpj]/actions";
import { STATUS } from "@/lib/api";

const ROTULOS: Record<string, string> = {
  novo: "Voltar para novo",
  aprovado: "Aprovar",
  descartado: "Descartar",
  abordado: "Marcar como abordado",
  respondido: "Marcar como respondido",
};

// Sem "use client": é um Server Component. Cada botão é um <form> que chama a Server Action.
export default function BotoesStatus({ cnpj, atual }: { cnpj: string; atual: string }) {
  return (
    <div className="flex flex-wrap gap-2">
      {STATUS.map((s) => (
        // .bind(null, cnpj, s) pré-preenche os argumentos: ao enviar, o Next chama alterarStatus(cnpj, s) no servidor
        <form key={s} action={alterarStatus.bind(null, cnpj, s)}>
          <button
            type="submit"
            disabled={s === atual}
            className="rounded border border-zinc-300 px-3 py-2 text-sm hover:bg-zinc-100 disabled:opacity-40 dark:border-zinc-700 dark:hover:bg-zinc-800"
          >
            {ROTULOS[s]}
          </button>
        </form>
      ))}
    </div>
  );
}
