import Link from "next/link";
import { notFound } from "next/navigation";
import BotoesStatus from "@/components/BotoesStatus";
import { buscarLead } from "@/lib/api";

// "2001-01-23" -> "23/01/2001" (sem usar Date, para o fuso horário não mudar o dia)
function formatarData(iso: string | null): string {
  return iso ? iso.split("-").reverse().join("/") : "—";
}

export default async function PaginaLead({ params }: { params: Promise<{ cnpj: string }> }) {
  const { cnpj } = await params;
  const lead = await buscarLead(cnpj);

  if (lead === null) {
    notFound(); // mostra a página 404; depois dele o TypeScript sabe que `lead` não é null
  }

  return (
    <main className="mx-auto max-w-3xl p-6">
      <Link href="/" className="text-sm text-zinc-500 underline">
        ← Voltar para a fila
      </Link>

      <h1 className="mt-4 text-2xl font-semibold">{lead.nome}</h1>
      <p className="mb-6 text-sm text-zinc-500">
        {lead.razao_social} · {lead.cidade}/{lead.uf} · CNPJ {lead.cnpj}
      </p>

      <section className="mb-6">
        <p className="text-lg">
          <span className="font-semibold">Nota {lead.nota}</span> · status <strong>{lead.status}</strong>
        </p>
        <p className="mb-3 text-sm text-zinc-600 dark:text-zinc-400">{lead.motivo_da_nota}</p>
        <BotoesStatus cnpj={lead.cnpj} atual={lead.status} />
      </section>

      <section className="mb-6">
        <h2 className="mb-2 font-semibold">Sinais</h2>
        <div className="flex flex-wrap gap-1">
          {lead.sinais.map((s) => (
            <span key={s} className="rounded bg-zinc-100 px-2 py-0.5 text-xs dark:bg-zinc-800">
              {s}
            </span>
          ))}
        </div>
      </section>

      <section className="mb-6 text-sm">
        <h2 className="mb-2 font-semibold">Contato</h2>
        <p>Telefone: {lead.telefone ?? "—"}</p>
        <p>E-mail: {lead.email ?? "—"}</p>
        <p>
          Site:{" "}
          {lead.site ? (
            <a href={lead.site} target="_blank" rel="noreferrer" className="text-blue-600 underline">
              {lead.site}
            </a>
          ) : (
            "—"
          )}{" "}
          ({lead.site_situacao ?? "não verificado"}: {lead.site_motivo || "sem motivo registrado"})
        </p>
      </section>

      <section className="mb-6">
        <h2 className="mb-2 font-semibold">Verificar à mão</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm">
          {Object.entries(lead.links).map(([nome, endereco]) => (
            <li key={nome}>
              <a href={endereco} target="_blank" rel="noreferrer" className="text-blue-600 underline">
                {nome}
              </a>
            </li>
          ))}
        </ul>
      </section>

      <section className="text-sm text-zinc-500">
        <p>
          Aberta em {formatarData(lead.data_abertura)} · coletado em {new Date(lead.coletado_em).toLocaleString("pt-BR")}
        </p>
      </section>
    </main>
  );
}
