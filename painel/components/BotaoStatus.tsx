"use client";

import { useFormStatus } from "react-dom";

// Client Component só por causa do useFormStatus: ele sabe se o <form> pai está sendo enviado.
export default function BotaoStatus({ rotulo, ativo, estilo }: { rotulo: string; ativo: boolean; estilo: string }) {
  const { pending } = useFormStatus();

  const aparencia = ativo
    ? estilo
    : "border-borda bg-superficie hover:border-marca/60 hover:text-marca-clara";

  return (
    <button
      type="submit"
      disabled={ativo || pending}
      aria-pressed={ativo}
      className={`inline-flex min-h-10 items-center gap-1.5 rounded-xl border px-4 text-sm font-medium transition-colors disabled:cursor-default ${aparencia} ${pending ? "opacity-60" : ""}`}
    >
      {ativo ? <span aria-hidden>✓</span> : null}
      {pending ? "Salvando…" : rotulo}
    </button>
  );
}
