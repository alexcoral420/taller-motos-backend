import type { Metadata } from "next";
import Navbar from "./components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Taller de Motos | Servicio y mantenimiento",
  description:
    "Servicio técnico especializado para tu motocicleta. Cotiza en línea cambio de aceite, frenos, kit de arrastre y más.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>
        <Navbar />
        {children}
      </body>
    </html>
  );
}