"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchAuth } from "@/app/lib/auth";

type Cliente = {
  nombres: string;
  telefono: string | null;
};

type Orden = {
  id: number;
  numero: number;
  tipo: string;
  estado: string;
  placa: string | null;
  total: string;
  cliente: Cliente | null;
};

const METODOS = [
  { valor: "efectivo", label: "Efectivo" },
  { valor: "nequi", label: "Nequi" },
  { valor: "daviplata", label: "Daviplata" },
  { valor: "breve", label: "Breve" },
];

export default function Ordenes() {
  const [ordenes, setOrdenes] = useState<Orden[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Liquidación manual
  const [liquidando, setLiquidando] = useState<number | null>(null);
  const [metodo, setMetodo] = useState("efectivo");
  const [procesando, setProcesando] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);

  function cargarOrdenes() {
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
  }

  useEffect(() => {
    cargarOrdenes();
  }, []);

  // Oculta el mensaje de éxito después de unos segundos.
  useEffect(() => {
    if (!mensaje) return;
    const t = setTimeout(() => setMensaje(null), 3000);
    return () => clearTimeout(t);
  }, [mensaje]);

  // ---------- Liquidación manual ----------
  async function confirmarLiquidacion(orden: Orden) {
    setProcesando(true);
    try {
      const res = await fetchAuth(`/api/v1/pagos/liquidar/${orden.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ metodo }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "No se pudo liquidar");
      }
      setLiquidando(null);
      setMensaje("Orden liquidada ✓");
      cargarOrdenes();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error al liquidar");
    } finally {
      setProcesando(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Órdenes de trabajo</h1>

      <Link
        href="/panel/ordenes/nueva"
        className="inline-block mb-4 bg-gray-900 text-white rounded px-4 py-2 text-sm font-medium hover:bg-gray-800"
      >
        + Nueva orden
      </Link>

      {mensaje && (
        <p className="mb-4 bg-green-50 text-green-700 rounded px-4 py-2 text-sm font-medium">
          {mensaje}
        </p>
      )}

      {cargando && <p className="text-gray-500">Cargando...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!cargando && ordenes.length === 0 && (
        <p className="text-gray-500">Aún no hay órdenes registradas.</p>
      )}

      {ordenes.length > 0 && (
        <div className="flex flex-col gap-3">
          {ordenes.map((orden) => (
            <div key={orden.id} className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-semibold">#{orden.numero}</span>
                  <span
                    className={`ml-2 text-xs px-2 py-0.5 rounded ${
                      orden.tipo === "interno"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-green-100 text-green-700"
                    }`}
                  >
                    {orden.tipo}
                  </span>
                  {orden.estado === "liquidada" && (
                    <span className="ml-2 text-xs px-2 py-0.5 rounded bg-gray-200 text-gray-600">
                      liquidada
                    </span>
                  )}
                </div>
                <span className="font-bold">
                  ${Number(orden.total).toLocaleString("es-CO")}
                </span>
              </div>

              <div className="text-sm text-gray-500 mt-1">
                {orden.cliente?.nombres && <span>{orden.cliente.nombres} · </span>}
                Placa: {orden.placa || "—"}
              </div>

              {/* Acciones: solo órdenes externas pendientes */}
              {orden.tipo === "externo" && orden.estado === "pendiente" && (
                <div className="mt-3">
                  {/* Panel de liquidación manual */}
                  {liquidando === orden.id ? (
                    <div className="flex flex-wrap items-center gap-2 bg-gray-50 rounded p-3">
                      <select
                        value={metodo}
                        onChange={(e) => setMetodo(e.target.value)}
                        className="border border-gray-300 rounded px-2 py-1 text-sm"
                      >
                        {METODOS.map((m) => (
                          <option key={m.valor} value={m.valor}>{m.label}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => confirmarLiquidacion(orden)}
                        disabled={procesando}
                        className="bg-green-600 text-white rounded px-3 py-1 text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                      >
                        {procesando ? "Procesando..." : "Confirmar liquidación"}
                      </button>
                      <button onClick={() => setLiquidando(null)} className="text-sm text-gray-500">
                        Cancelar
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => { setLiquidando(orden.id); setMetodo("efectivo"); }}
                      className="bg-gray-900 text-white rounded px-3 py-1 text-sm font-medium hover:bg-gray-800"
                    >
                      Liquidar manual
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}