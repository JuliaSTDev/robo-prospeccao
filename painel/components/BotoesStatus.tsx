import { alterarStatus } from "@/app/leads/[cnpj]/actions";
import BotaoStatus from "@/components/BotaoStatus";
import { ESTILOS_STATUS } from "@/components/ui/StatusBadge";
import { ROTULOS, STATUS } from "@/lib/status";

// Sem "use client": é um Server Component. Cada botão é um <form> que chama a Server Action.
export default function BotoesStatus({ cnpj, atual }: { cnpj: string; atual: string }) {
  return (
    <div className="flex flex-wrap gap-2">
      {STATUS.map((s) => (
        // .bind(null, cnpj, s) pré-preenche os argumentos: ao enviar, o Next chama alterarStatus(cnpj, s) no servidor
        <form key={s} action={alterarStatus.bind(null, cnpj, s)}>
          <BotaoStatus rotulo={ROTULOS[s]} ativo={s === atual} estilo={ESTILOS_STATUS[s]} />
        </form>
      ))}
    </div>
  );
}
