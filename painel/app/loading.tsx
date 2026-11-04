// Aparece enquanto a fila carrega: blocos cinza que "respiram" no lugar do conteúdo.
export default function Carregando() {
  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6" aria-busy="true">
      <div className="mb-6 space-y-2">
        <div className="h-7 w-40 animate-pulse rounded-lg bg-superficie" />
        <div className="h-4 w-64 animate-pulse rounded-lg bg-superficie" />
      </div>
      <div className="mb-4 flex gap-2">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-9 w-24 animate-pulse rounded-full bg-superficie" />
        ))}
      </div>
      <div className="space-y-px overflow-hidden rounded-2xl border border-borda">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-16 animate-pulse bg-superficie" />
        ))}
      </div>
    </main>
  );
}
