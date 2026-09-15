import type { Metadata } from "next";
import Navbar from "./components/Navbar";
import "./globals.css";
import Footer from "./components/Footer";

export const metadata: Metadata = {
  title: "Taller surtimotos | Servicio y mantenimiento",
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
        <Footer />
      </body>
    </html>
  );
}