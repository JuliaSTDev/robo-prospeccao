// Os status possíveis de um lead e o texto de cada um. Sem fetch aqui: pode ser usado em qualquer componente.
export const STATUS = ["novo", "aprovado", "descartado", "abordado", "respondido"] as const;
export type Status = (typeof STATUS)[number];

export const ROTULOS: Record<Status, string> = {
  novo: "Novo",
  aprovado: "Aprovado",
  descartado: "Descartado",
  abordado: "Abordado",
  respondido: "Respondido",
};
