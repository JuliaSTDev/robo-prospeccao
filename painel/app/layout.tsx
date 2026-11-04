import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Cabecalho from "@/components/Cabecalho";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Painel de leads",
  description: "Fila de prospecção da JS Soluções",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" className={`${inter.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">
        <Cabecalho />
        {children}
      </body>
    </html>
  );
}
