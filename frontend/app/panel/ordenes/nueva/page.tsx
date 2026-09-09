"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchAuth } from "@/app/lib/auth";

type Servicio = {
  codigo: string;
  nombre: string;
  precio_referencia: string;
};

// Un servicio seleccionado, con el valor que escribe el técnico.
type Seleccion = {
  codigo: string;
  valor: string;
};

export default function NuevaOrden() {
  const router = useRouter();

  const [servicios, setServicios] = useState<Servicio[]>([]);
  const [seleccionados, setSeleccionados] = useState<Seleccion[]>([]);

  const [placa, setPlaca] = useState("");
  const [sintoma, setSintoma] = useState("");

  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Traemos el catálogo (usamos el endpoint público, no necesita token).
  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/public/catalogo`)
      .then((res) => res.json())
      .then((data: Servicio[]) => setServicios(data))
      .catch(() => setError("No se pudo cargar el catálogo"));
  }, []);

  // ¿Está marcado este servicio?
  function estaMarcado(codigo: string) {
    return seleccionados.some((s) => s.codigo === codigo);
  }

  // Marcar/desmarcar un servicio.
  function alternar(codigo: string) {
    setSeleccionados((actuales) =>
      estaMarcado(codigo)
        ? actuales.filter((s) => s.codigo !== codigo)
        : [...actuales, { codigo, valor: "" }]
    );
  }

  // Actualizar el valor cobrado de un servicio marcado.
  function cambiarValor(codigo: string, valor: string) {
    setSeleccionados((actuales) =>
      actuales.map((s) => (s.codigo === codigo ? { ...s, valor } : s))
    );
  }

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (seleccionados.length === 0) {
      setError("Agrega al menos un servicio");
      return;
    }

    setEnviando(true);
    try {
      const respuesta = await fetchAuth("/api/v1/ordenes/interna", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          placa,
          sintoma: sintoma || null,
          servicios: seleccionados.map((s) => ({
            codigo: s.codigo,
            cantidad: 1,
            valor_unitario: Number(s.valor) || 0,
          })),
        }),
      });

      if (!respuesta.ok) throw new Error("No se pudo registrar la orden");

      router.push("/panel/ordenes"); // volvemos a la lista
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        Nueva orden interna
      </h1>

      <form onSubmit={guardar} className="bg-white rounded-lg shadow p-6 flex flex-col gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Placa *
          </label>
          <input
            type="text"
            value={placa}
            onChange={(e) => setPlaca(e.target.value.toUpperCase())}
            required
            className="w-full border border-gray-300 rounded px-3 py-2"
            placeholder="ABC123"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Síntoma / motivo
          </label>
          <input
            type="text"
            value={sintoma}
            onChange={(e) => setSintoma(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2"
            placeholder="Mantenimiento antes de venta"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Servicios y valor cobrado *
          </label>
          <div className="flex flex-col gap-2">
            {servicios.map((servicio) => {
              const marcado = estaMarcado(servicio.codigo);
              const sel = seleccionados.find((s) => s.codigo === servicio.codigo);
              return (
                <div
                  key={servicio.codigo}
                  className="border border-gray-200 rounded px-3 py-2"
                >
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={marcado}
                      onChange={() => alternar(servicio.codigo)}
                    />
                    <span className="flex-1 text-sm">{servicio.nombre}</span>
                    <span className="text-xs text-gray-400">
                      ref: ${Number(servicio.precio_referencia).toLocaleString("es-CO")}
                    </span>
                  </label>

                  {marcado && (
                    <input
                      type="number"
                      value={sel?.valor ?? ""}
                      onChange={(e) => cambiarValor(servicio.codigo, e.target.value)}
                      placeholder="Valor cobrado"
                      className="mt-2 w-full border border-gray-300 rounded px-3 py-1 text-sm"
                      min="0"
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={enviando}
            className="flex-1 bg-gray-900 text-white rounded px-4 py-2 font-medium hover:bg-gray-800 disabled:opacity-50"
          >
            {enviando ? "Guardando..." : "Registrar orden"}
          </button>
          <button
            type="button"
            onClick={() => router.push("/panel/ordenes")}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}