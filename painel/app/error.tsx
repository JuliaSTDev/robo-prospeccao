"use client"; // o Next exige que o error boundary seja Client Component

export default function Erro({ retry }: { error: unknown; retry: () => void }) {
  return (
    <main className="mx-auto w-full max-w-xl px-4 py-20">
      <div className="rounded-2xl border border-borda bg-superficie p-6 sm:p-8">
        <h1 className="text-xl font-semibold tracking-tight">Não consegui carregar a fila</h1>
        <p className="mt-2 text-sm leading-relaxed text-texto-suave">
          A API do robô pode estar desligada. Ligue com{" "}
          <code className="rounded-md border border-borda bg-texto/5 px-1.5 py-0.5 text-xs text-texto">
            uvicorn robo.api.app:app --reload
          </code>{" "}
          e tente de novo.
        </p>
        <button
          onClick={() => retry()}
          className="gradiente-marca mt-6 inline-flex min-h-10 items-center rounded-xl px-5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
        >
          Tentar de novo
        </button>
      </div>
    </main>
  );
}
