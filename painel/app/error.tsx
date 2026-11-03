"use client"; // o Next exige que o error boundary seja Client Component

export default function Erro({ retry }: { error: unknown; retry: () => void }) {
  return (
    <main className="mx-auto max-w-xl p-6">
      <h1 className="mb-2 text-xl font-semibold">Não consegui carregar a fila</h1>
      <p className="mb-4 text-sm text-zinc-500">
        A API do robô pode estar desligada. Ligue com{" "}
        <code className="rounded bg-zinc-100 px-1.5 py-0.5 dark:bg-zinc-800">uvicorn robo.api.app:app --reload</code> e
        tente de novo.
      </p>
      <button
        onClick={() => retry()}
        className="rounded bg-zinc-900 px-4 py-2 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900"
      >
        Tentar de novo
      </button>
    </main>
  );
}
