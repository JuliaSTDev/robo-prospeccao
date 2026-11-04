// Cada status tem uma cor. Os nomes das classes ficam escritos por inteiro para o Tailwind encontrá-las.
export const ESTILOS_STATUS: Record<string, string> = {
  novo: "text-apoio bg-apoio/15 border-apoio/30",
  aprovado: "text-verde bg-verde/15 border-verde/30",
  descartado: "text-texto-suave bg-texto-suave/10 border-texto-suave/25",
  abordado: "text-marca-clara bg-marca/15 border-marca/30",
  respondido: "text-violeta bg-violeta/15 border-violeta/30",
};

export default function StatusBadge({ status }: { status: string }) {
  const estilo = ESTILOS_STATUS[status] ?? ESTILOS_STATUS.descartado;
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${estilo}`}>
      {status}
    </span>
  );
}
