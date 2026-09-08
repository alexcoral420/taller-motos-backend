"use client";

import Link from "next/link";
import { useState } from "react";

export default function Navbar() {
  const [abierto, setAbierto] = useState(false);

  const enlaces = [
    { href: "/", texto: "Servicios" },
    { href: "/cotizar", texto: "Cotizar" },
    { href: "/contacto", texto: "Contacto" },
  ];

  return (
    <nav className="bg-gray-900 text-white px-6 py-4">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <Link href="/" className="text-xl font-bold" onClick={() => setAbierto(false)}>
          🏍️ Mi Taller
        </Link>

        {/* Enlaces en escritorio: ocultos en móvil, visibles desde 'md' */}
        <div className="hidden md:flex gap-6">
          {enlaces.map((e) => (
            <Link key={e.href} href={e.href} className="hover:text-blue-400">
              {e.texto}
            </Link>
          ))}
        </div>

        {/* Botón hamburguesa: visible solo en móvil (oculto desde 'md') */}
        <button
          className="md:hidden text-2xl"
          onClick={() => setAbierto(!abierto)}
          aria-label="Menú"
        >
          {abierto ? "✕" : "☰"}
        </button>
      </div>

      {/* Menú desplegable en móvil */}
      {abierto && (
        <div className="md:hidden mt-3 flex flex-col gap-3 max-w-5xl mx-auto">
          {enlaces.map((e) => (
            <Link
              key={e.href}
              href={e.href}
              className="hover:text-blue-400 py-1"
              onClick={() => setAbierto(false)}
            >
              {e.texto}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}