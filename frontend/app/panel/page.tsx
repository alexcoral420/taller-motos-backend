"use client";

import Link from "next/link";

export default function Panel() {
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Inicio</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Link
          href="/panel/ordenes"
          className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
        >
          <h2 className="font-semibold text-gray-800">Órdenes de trabajo</h2>
          <p className="text-sm text-gray-500 mt-1">
            Ver y registrar servicios
          </p>
        </Link>

        <Link
          href="/panel/cotizaciones"
          className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
        >
          <h2 className="font-semibold text-gray-800">Cotizaciones</h2>
          <p className="text-sm text-gray-500 mt-1">
            Leads desde la web
          </p>
        </Link>
      </div>
    </div>
  );
}