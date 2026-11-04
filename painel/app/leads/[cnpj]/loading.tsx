export default function CarregandoLead() {
  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6" aria-busy="true">
      <div className="h-4 w-36 animate-pulse rounded-lg bg-superficie" />
      <div className="mt-5 flex items-center gap-4">
        <div className="h-14 w-14 animate-pulse rounded-2xl bg-superficie" />
        <div className="space-y-2">
          <div className="h-7 w-64 animate-pulse rounded-lg bg-superficie" />
          <div className="h-4 w-80 max-w-full animate-pulse rounded-lg bg-superficie" />
        </div>
      </div>
      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="h-40 animate-pulse rounded-2xl bg-superficie" />
          <div className="h-28 animate-pulse rounded-2xl bg-superficie" />
        </div>
        <div className="h-72 animate-pulse rounded-2xl bg-superficie" />
      </div>
    </main>
  );
}
