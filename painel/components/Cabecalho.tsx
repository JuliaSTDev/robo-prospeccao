import Link from "next/link";
import Logo from "@/components/Logo";

export default function Cabecalho() {
  return (
    <header className="sticky top-0 z-40 border-b border-borda bg-fundo/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-3 rounded-lg">
          <Logo tamanho={28} />
          <span className="font-semibold tracking-tight">JS Soluções</span>
          <span className="hidden text-sm text-texto-suave sm:inline">· Painel de leads</span>
        </Link>
      </div>
    </header>
  );
}
