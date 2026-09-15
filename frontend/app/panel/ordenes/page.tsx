"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

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

  // Cobro Nequi (digital)
  const [cobrandoNequi, setCobrandoNequi] = useState<number | null>(null);
  const [numeroNequi, setNumeroNequi] = useState("");
  const [estadoNequi, setEstadoNequi] = useState<string>("");
  const [pagoNequiId, setPagoNequiId] = useState<number | null>(null);
  const intervalo = useRef<ReturnType<typeof setInterval> | null>(null);

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
    // Limpia el intervalo si el componente se desmonta.
    return () => {
      if (intervalo.current) clearInterval(intervalo.current);
    };
  }, []);

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
      const data = await res.json();
      const urlRecibo = `${process.env.NEXT_PUBLIC_API_URL}/api/public/recibo/${data.recibo_token}`;
      const telefono = orden.cliente?.telefono?.replace(/\D/g, "") || "";
      const mensaje = `¡Hola ${orden.cliente?.nombres || ""}! Gracias por tu visita a Taller Surtimotos. Aquí está tu recibo: ${urlRecibo}`;
      if (telefono) {
        window.open(`https://wa.me/57${telefono}?text=${encodeURIComponent(mensaje)}`, "_blank");
      } else {
        alert("Orden liquidada. Recibo: " + urlRecibo);
      }
      setLiquidando(null);
      cargarOrdenes();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error al liquidar");
    } finally {
      setProcesando(false);
    }
  }

  // ---------- Cobro Nequi digital ----------
  function abrirCobroNequi(orden: Orden) {
    setCobrandoNequi(orden.id);
    // Prellenamos con el teléfono de la orden, pero el técnico puede editarlo.
    setNumeroNequi(orden.cliente?.telefono?.replace(/\D/g, "").slice(-10) || "");
    setEstadoNequi("");
    setPagoNequiId(null);
  }

  async function iniciarCobroNequi(orden: Orden) {
    setProcesando(true);
    setEstadoNequi("Enviando notificación a Nequi...");
    try {
      // Enviamos el número editado como query (el backend puede usarlo).
      const res = await fetchAuth(`/api/v1/pagos/nequi/cobrar/${orden.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telefono: numeroNequi }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "No se pudo iniciar el cobro");
      }
      const data = await res.json();
      setPagoNequiId(data.pago_id);
      setEstadoNequi("Esperando que el cliente apruebe en su Nequi...");

      // Consultamos el estado cada 4 segundos.
      intervalo.current = setInterval(() => consultarEstadoNequi(data.pago_id), 4000);
    } catch (err) {
      setEstadoNequi("");
      alert(err instanceof Error ? err.message : "Error al iniciar el cobro");
    } finally {
      setProcesando(false);
    }
  }

  async function consultarEstadoNequi(pagoId: number) {
    try {
      const res = await fetchAuth(`/api/v1/pagos/nequi/estado/${pagoId}`);
      if (!res.ok) return;
      const data = await res.json();

      if (data.estado === "confirmado") {
        if (intervalo.current) clearInterval(intervalo.current);
        setEstadoNequi("¡Pago aprobado! ✓");
        setTimeout(() => {
          setCobrandoNequi(null);
          cargarOrdenes();
        }, 1500);
      } else if (data.estado === "fallido") {
        if (intervalo.current) clearInterval(intervalo.current);
        setEstadoNequi("El pago fue rechazado ✗");
      }
      // Si sigue pendiente, el intervalo vuelve a consultar.
    } catch {
      // Ignoramos errores puntuales de red; el intervalo reintenta.
    }
  }

  function cancelarCobroNequi() {
    if (intervalo.current) clearInterval(intervalo.current);
    setCobrandoNequi(null);
    setEstadoNequi("");
    setPagoNequiId(null);
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
                        {procesando ? "Procesando..." : "Confirmar y enviar recibo"}
                      </button>
                      <button onClick={() => setLiquidando(null)} className="text-sm text-gray-500">
                        Cancelar
                      </button>
                    </div>
                  ) : cobrandoNequi === orden.id ? (
                    /* Panel de cobro Nequi digital */
                    <div className="bg-purple-50 rounded p-3">
                      {!pagoNequiId ? (
                        <>
                          <label className="block text-sm text-gray-700 mb-1">
                            Número Nequi del cliente
                          </label>
                          <input
                            type="tel"
                            value={numeroNequi}
                            onChange={(e) => setNumeroNequi(e.target.value.replace(/\D/g, ""))}
                            className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2"
                            placeholder="3001234567"
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => iniciarCobroNequi(orden)}
                              disabled={procesando || numeroNequi.length < 10}
                              className="bg-purple-600 text-white rounded px-3 py-1 text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
                            >
                              Enviar cobro
                            </button>
                            <button onClick={cancelarCobroNequi} className="text-sm text-gray-500">
                              Cancelar
                            </button>
                          </div>
                        </>
                      ) : (
                        <div className="text-sm">
                          <p className="font-medium text-purple-700">{estadoNequi}</p>
                          {estadoNequi.includes("Esperando") && (
                            <p className="text-gray-500 mt-1">
                              Pídele al cliente que abra su app Nequi y apruebe.
                            </p>
                          )}
                          {estadoNequi.includes("rechazado") && (
                            <button onClick={cancelarCobroNequi} className="text-gray-500 mt-2">
                              Cerrar
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    /* Botones iniciales */
                    <div className="flex gap-2">
                      <button
                        onClick={() => { setLiquidando(orden.id); setMetodo("efectivo"); }}
                        className="bg-gray-900 text-white rounded px-3 py-1 text-sm font-medium hover:bg-gray-800"
                      >
                        Liquidar manual
                      </button>
                      <button
                        onClick={() => abrirCobroNequi(orden)}
                        className="bg-purple-600 text-white rounded px-3 py-1 text-sm font-medium hover:bg-purple-700"
                      >
                        Cobrar con Nequi
                      </button>
                    </div>
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