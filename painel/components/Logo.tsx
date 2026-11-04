// O logo da JS Soluções: quadrado laranja com "JS" e o ponto azul no canto (o mesmo do favicon da landing).
export default function Logo({ tamanho = 32 }: { tamanho?: number }) {
  return (
    <svg width={tamanho} height={tamanho} viewBox="0 0 32 32" role="img" aria-label="JS Soluções">
      <rect width="32" height="32" rx="7" className="fill-marca" />
      <text
        x="16"
        y="22"
        textAnchor="middle"
        fontSize="14"
        fontWeight="800"
        letterSpacing="-0.5"
        className="fill-white"
        style={{ fontFamily: "var(--font-sans)" }}
      >
        JS
      </text>
      {/* azul fixo da marca (#0369a1), igual nos dois temas */}
      <circle cx="27" cy="27" r="5" fill="#0369a1" strokeWidth="1.5" className="stroke-marca" />
    </svg>
  );
}
