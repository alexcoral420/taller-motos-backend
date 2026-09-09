"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { borrarToken, estaAutenticado } from "@/app/lib/auth";

export default function PanelLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [verificando, setVerificando] = useState(true);

  useEffect(() => {
    // Al cargar cualquier página del panel, verifica que haya sesión.
    if (!estaAutenticado()) {
      router.replace("/panel/login"); // sin sesión -> al login
    } else {
      setVerificando(false); // hay sesión -> mostramos el panel
    }
  }, [router]);

  function cerrarSesion() {
    borrarToken();
    router.replace("/panel/login");
  }

  // Mientras verifica, no mostramos nada (evita un parpadeo del contenido).
  if (verificando) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Cargando...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Barra superior del panel */}
      <header className="bg-gray-900 text-white px-6 py-4 flex items-center justify-between">
        <span className="font-bold">🔧 Panel del Taller</span>
        <button
          onClick={cerrarSesion}
          className="text-sm hover:text-red-400"
        >
          Cerrar sesión
        </button>
      </header>

      <main className="p-6">{children}</main>
    </div>
  );
}