"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchAuth } from "@/app/lib/auth";

type Orden = {
  id: number;
  numero: number;
  tipo: string;
  placa: string | null;
  total: string;
  created_at: string;
};

export default function Ordenes() {
  const [ordenes, setOrdenes] = useState<Orden[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAuth("/api/v1/ordenes")
      .then((res) => {
        if (!res.ok) throw new Error("No se pudieron cargar las órdenes");
        return res.json();
      })
      .then((data: Orden[]) => {
        setOrdenes(data);
        setCargando(false);
      })
      .catch((err) => {
        setError(err.message);
        setCargando(false);
      });
  }, []);

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        Órdenes de trabajo
      </h1>

      <Link
        href="/panel/ordenes/nueva"
        className="inline-block mb-4 bg-gray-900 text-white rounded px-4 py-2 text-sm font-medium hover:bg-gray-800"
      >
        + Nueva orden
      </Link>

      {cargando && <p className="text-gray-500">Cargando...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!cargando && ordenes.length === 0 && (
        <p className="text-gray-500">Aún no hay órdenes registradas.</p>
      )}

      {ordenes.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-left">
              <tr>
                <th className="px-4 py-3">N°</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Placa</th>
                <th className="px-4 py-3 text-right">Total</th>
              </tr>
            </thead>
            <tbody>
              {ordenes.map((orden) => (
                <tr key={orden.id} className="border-t border-gray-100">
                  <td className="px-4 py-3 font-medium">#{orden.numero}</td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        orden.tipo === "interno"
                          ? "text-blue-600"
                          : "text-green-600"
                      }
                    >
                      {orden.tipo}
                    </span>
                  </td>
                  <td className="px-4 py-3">{orden.placa || "—"}</td>
                  <td className="px-4 py-3 text-right font-medium">
                    ${Number(orden.total).toLocaleString("es-CO")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}