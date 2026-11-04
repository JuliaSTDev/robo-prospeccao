import Link from "next/link";
import { notFound } from "next/navigation";
import BotoesStatus from "@/components/BotoesStatus";
import NotaBadge from "@/components/ui/NotaBadge";
import SinalChip from "@/components/ui/SinalChip";
import StatusBadge from "@/components/ui/StatusBadge";
import { buscarLead } from "@/lib/api";

// "2001-01-23" -> "23/01/2001" (sem usar Date, para o fuso horário não mudar o dia)
function formatarData(iso: string | null): string {
  return iso ? iso.split("-").reverse().join("/") : "—";
}

function Secao({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-borda bg-superficie p-5 sm:p-6">
      <h2 className="mb-4 text-xs font-semibold uppercase tracking-wide text-texto-suave">{titulo}</h2>
      {children}
    </section>
  );
}

export default async function PaginaLead({ params }: { params: Promise<{ cnpj: string }> }) {
  const { cnpj } = await params;
  const lead = await buscarLead(cnpj);

  if (lead === null) {
    notFound(); // mostra a página 404; depois dele o TypeScript sabe que `lead` não é null
  }

  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6">
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-sm text-texto-suave transition-colors hover:text-marca-clara"
      >
        ← Voltar para a fila
      </Link>

      <header className="mt-5 flex items-start gap-4">
        <NotaBadge nota={lead.nota} grande />
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{lead.nome}</h1>
          <p className="mt-1 text-sm text-texto-suave">
            {lead.razao_social} · {lead.cidade}/{lead.uf} · CNPJ {lead.cnpj}
          </p>
        </div>
      </header>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Secao titulo="Status">
            <div className="mb-4 flex items-center gap-2 text-sm">
              <span className="text-texto-suave">Agora:</span>
              <StatusBadge status={lead.status} />
            </div>
            <BotoesStatus cnpj={lead.cnpj} atual={lead.status} />
          </Secao>

          <Secao titulo="Por que esta nota">
            <p className="text-sm leading-relaxed">{lead.motivo_da_nota}</p>
          </Secao>

          <Secao titulo="Sinais">
            <div className="flex flex-wrap gap-1.5">
              {lead.sinais.map((s) => (
                <SinalChip key={s} sinal={s} />
              ))}
            </div>
          </Secao>
        </div>

        <div className="space-y-6">
          <Secao titulo="Contato">
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-texto-suave">Telefone</dt>
                <dd>{lead.telefone ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-texto-suave">E-mail</dt>
                <dd className="break-all">{lead.email ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-texto-suave">Site</dt>
                <dd>
                  {lead.site ? (
                    <a
                      href={lead.site}
                      target="_blank"
                      rel="noreferrer"
                      className="break-all text-marca-clara underline-offset-4 hover:underline"
                    >
                      {lead.site}
                    </a>
                  ) : (
                    "—"
                  )}
                  <p className="mt-0.5 text-xs text-texto-suave">
                    {lead.site_situacao ?? "não verificado"}: {lead.site_motivo || "sem motivo registrado"}
                  </p>
                </dd>
              </div>
            </dl>
          </Secao>

          <Secao titulo="Verificar à mão">
            <ul className="space-y-2">
              {Object.entries(lead.links).map(([nome, endereco]) => (
                <li key={nome}>
                  <a
                    href={endereco}
                    target="_blank"
                    rel="noreferrer"
                    className="flex min-h-11 items-center justify-between rounded-xl border border-borda px-4 text-sm transition-colors hover:border-marca/60 hover:text-marca-clara"
                  >
                    {nome}
                    <span aria-hidden>↗</span>
                  </a>
                </li>
              ))}
            </ul>
          </Secao>

          <p className="px-1 text-xs text-texto-suave">
            Aberta em {formatarData(lead.data_abertura)} · coletado em{" "}
            {new Date(lead.coletado_em).toLocaleString("pt-BR")}
          </p>
        </div>
      </div>
    </main>
  );
}
