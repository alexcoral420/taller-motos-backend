"use client";

import { useEffect, useState } from "react";

// El "tipo" de un servicio: describe la forma de los datos que llegan de la API.
// Esto es TypeScript: le decimos exactamente qué campos esperar.
type Servicio = {
  codigo: string;
  nombre: string;
  descripcion: string | null;
  precio_referencia: string;
};

export default function Home() {
  // Estado: aquí guardamos la lista de servicios que traigamos de la API.
  const [servicios, setServicios] = useState<Servicio[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // useEffect corre una vez cuando la página carga: pide los datos a la API.
  useEffect(() => {
    fetch("http://localhost:8000/api/public/catalogo")
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
    <main className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        Nuestros Servicios
      </h1>

      {cargando && <p className="text-gray-500">Cargando servicios...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {servicios.map((servicio) => (
          <div
            key={servicio.codigo}
            className="bg-white rounded-lg shadow p-5 border border-gray-200"
          >
            <h2 className="text-xl font-semibold text-gray-800">
              {servicio.nombre}
            </h2>
            <p className="text-gray-600 mt-1">{servicio.descripcion}</p>
            <p className="text-lg font-bold text-blue-600 mt-3">
              ${Number(servicio.precio_referencia).toLocaleString("es-CO")}
            </p>
          </div>
        ))}
      </div>
    </main>
  );
}