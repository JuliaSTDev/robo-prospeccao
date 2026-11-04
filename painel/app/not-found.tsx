import Link from "next/link";

export default function NaoEncontrado() {
  return (
    <main className="mx-auto w-full max-w-xl px-4 py-20 text-center">
      <p className="text-sm font-semibold text-marca-clara">404</p>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight">Lead não encontrado</h1>
      <p className="mt-2 text-sm text-texto-suave">
        Esse CNPJ não está na base. Ele pode ter sido digitado errado ou nunca ter sido coletado.
      </p>
      <Link
        href="/"
        className="gradiente-marca mt-6 inline-flex min-h-10 items-center rounded-xl px-5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
      >
        Voltar para a fila
      </Link>
    </main>
  );
}
