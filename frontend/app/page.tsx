"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Servicio = {
  codigo: string;
  nombre: string;
  descripcion: string | null;
  precio_referencia: string;
};

export default function Home() {
  const [servicios, setServicios] = useState<Servicio[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/public/catalogo`)
      .then((res) => {
        if (!res.ok) throw new Error("No se pudo cargar el catálogo");
        return res.json();
      })
      .then((data: Servicio[]) => {
        setServicios(data);
        setCargando(false);
      })
      .catch((err) => {
        setError(err.message);
        setCargando(false);
      });
  }, []);

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Sección de bienvenida */}
      <section className="bg-gray-900 text-white px-6 py-12 text-center">
        <h1 className="text-3xl md:text-4xl font-bold mb-3">
          Cuidamos tu moto como se merece
        </h1>
        <p className="text-gray-300 max-w-xl mx-auto">
          Servicio técnico especializado. Explora nuestros servicios y solicita
          tu cotización en línea.
        </p>
      </section>

      {/* Catálogo de servicios */}
      <section className="max-w-5xl mx-auto px-6 py-10">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">
          Nuestros Servicios
        </h2>

        {cargando && <p className="text-gray-500">Cargando servicios...</p>}
        {error && <p className="text-red-500">Error: {error}</p>}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {servicios.map((servicio) => (
            <div
              key={servicio.codigo}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col"
            >
              <h3 className="text-lg font-semibold text-gray-800">
                {servicio.nombre}
              </h3>
              <p className="text-gray-600 mt-2 flex-1">
                {servicio.descripcion}
              </p>
              <p className="text-2xl font-bold text-blue-600 mt-4">
                ${Number(servicio.precio_referencia).toLocaleString("es-CO")}
              </p>
              <p className="text-xs text-gray-400 mb-4">Precio de referencia</p>

              <Link
                href={`/cotizar?servicio=${servicio.codigo}`}
                className="bg-blue-600 text-white text-center rounded-lg px-4 py-2 font-medium hover:bg-blue-700 transition-colors"
              >
                Cotizar este servicio
              </Link>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}