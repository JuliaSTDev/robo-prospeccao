// A nota vai de 0 a 10: de 8 para cima é laranja (prioridade), de 5 a 7 é azul, abaixo disso é neutra.
export default function NotaBadge({ nota, grande = false }: { nota: number; grande?: boolean }) {
  const faixa =
    nota >= 8
      ? "text-marca-clara bg-marca/15 border-marca/30"
      : nota >= 5
        ? "text-apoio bg-apoio/15 border-apoio/30"
        : "text-texto-suave bg-texto-suave/10 border-texto-suave/25";
  const tamanho = grande ? "h-14 min-w-14 rounded-2xl px-2 text-2xl" : "h-8 min-w-8 rounded-lg px-1.5 text-sm";
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center border font-bold tabular-nums ${faixa} ${tamanho}`}
      title={`Nota ${nota} de 10`}
    >
      {nota}
    </span>
  );
}
