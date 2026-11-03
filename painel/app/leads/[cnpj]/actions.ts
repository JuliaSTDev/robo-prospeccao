"use server";

import { revalidatePath } from "next/cache";
import { mudarStatus, STATUS, type Status } from "@/lib/api";

export async function alterarStatus(cnpj: string, status: string) {
  // o servidor não confia no que vem do navegador
  if (!(STATUS as readonly string[]).includes(status)) {
    throw new Error(`Status inválido: ${status}`);
  }
  await mudarStatus(cnpj, status as Status);
  revalidatePath(`/leads/${cnpj}`);
  revalidatePath("/");
}
