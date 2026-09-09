"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { borrarToken, estaAutenticado } from "@/app/lib/auth";

export default function PanelLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [verificando, setVerificando] = useState(true);

  const esLogin = pathname === "/panel/login";

  useEffect(() => {
    if (esLogin) {
      setVerificando(false); // la página de login no se protege
      return;
    }
    if (!estaAutenticado()) {
      router.replace("/panel/login");
    } else {
      setVerificando(false);
    }
  }, [router, esLogin]);

  function cerrarSesion() {
    borrarToken();
    router.replace("/panel/login");
  }

  if (verificando) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Cargando...
      </div>
    );
  }

  // En la página de login, no mostramos la barra del panel.
  if (esLogin) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-gray-900 text-white px-6 py-4 flex items-center justify-between">
        <span className="font-bold">🔧 Panel del Taller</span>
        <button onClick={cerrarSesion} className="text-sm hover:text-red-400">
          Cerrar sesión
        </button>
      </header>
      <main className="p-6">{children}</main>
    </div>
  );
}