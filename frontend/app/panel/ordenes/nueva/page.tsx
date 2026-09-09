"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchAuth } from "@/app/lib/auth";

type Servicio = {
  codigo: string;
  nombre: string;
  precio_referencia: string;
};

type Seleccion = {
  codigo: string;
  valor: string;
};

type TipoOrden = "interno" | "externo";

export default function NuevaOrden() {
  const router = useRouter();

  const [tipo, setTipo] = useState<TipoOrden>("interno");

  const [servicios, setServicios] = useState<Servicio[]>([]);
  const [seleccionados, setSeleccionados] = useState<Seleccion[]>([]);

  // Campos comunes
  const [placa, setPlaca] = useState("");
  const [sintoma, setSintoma] = useState("");

  // Campos solo de orden externa
  const [clienteNombre, setClienteNombre] = useState("");
  const [clienteTelefono, setClienteTelefono] = useState("");
  const [modeloMoto, setModeloMoto] = useState("");

  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/public/catalogo`)
      .then((res) => res.json())
      .then((data: Servicio[]) => setServicios(data))
      .catch(() => setError("No se pudo cargar el catálogo"));
  }, []);

  function estaMarcado(codigo: string) {
    return seleccionados.some((s) => s.codigo === codigo);
  }

  function alternar(codigo: string) {
    setSeleccionados((actuales) =>
      estaMarcado(codigo)
        ? actuales.filter((s) => s.codigo !== codigo)
        : [...actuales, { codigo, valor: "" }]
    );
  }

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

    const servicios_payload = seleccionados.map((s) => ({
      codigo: s.codigo,
      cantidad: 1,
      valor_unitario: Number(s.valor) || 0,
    }));

    setEnviando(true);
    try {
      let respuesta: Response;

      if (tipo === "interno") {
        respuesta = await fetchAuth("/api/v1/ordenes/interna", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            placa,
            sintoma: sintoma || null,
            servicios: servicios_payload,
          }),
        });
      } else {
        respuesta = await fetchAuth("/api/v1/ordenes/externa", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            placa: placa || null,
            modelo_moto: modeloMoto || null,
            cliente: {
              nombres: clienteNombre,
              telefono: clienteTelefono || null,
            },
            sintoma: sintoma || null,
            servicios: servicios_payload,
          }),
        });
      }

      if (!respuesta.ok) throw new Error("No se pudo registrar la orden");

      router.push("/panel/ordenes");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Nueva orden</h1>

      {/* Selector de tipo */}
      <div className="flex gap-2 mb-6">
        <button
          type="button"
          onClick={() => setTipo("interno")}
          className={`flex-1 rounded px-4 py-3 font-medium ${
            tipo === "interno"
              ? "bg-blue-600 text-white"
              : "bg-white text-gray-600 border border-gray-300"
          }`}
        >
          Interna
          <span className="block text-xs font-normal opacity-80">
            Moto del inventario
          </span>
        </button>
        <button
          type="button"
          onClick={() => setTipo("externo")}
          className={`flex-1 rounded px-4 py-3 font-medium ${
            tipo === "externo"
              ? "bg-green-600 text-white"
              : "bg-white text-gray-600 border border-gray-300"
          }`}
        >
          Externa
          <span className="block text-xs font-normal opacity-80">
            Moto de cliente
          </span>
        </button>
      </div>

      <form onSubmit={guardar} className="bg-white rounded-lg shadow p-6 flex flex-col gap-4">
        {/* Placa: obligatoria en interna, opcional en externa */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Placa {tipo === "interno" && "*"}
          </label>
          <input
            type="text"
            value={placa}
            onChange={(e) => setPlaca(e.target.value.toUpperCase())}
            required={tipo === "interno"}
            className="w-full border border-gray-300 rounded px-3 py-2"
            placeholder="ABC123"
          />
        </div>

        {/* Campos solo para externa */}
        {tipo === "externo" && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre del cliente *
              </label>
              <input
                type="text"
                value={clienteNombre}
                onChange={(e) => setClienteNombre(e.target.value)}
                required
                className="w-full border border-gray-300 rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Teléfono del cliente
              </label>
              <input
                type="tel"
                value={clienteTelefono}
                onChange={(e) => setClienteTelefono(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Modelo de moto
              </label>
              <input
                type="text"
                value={modeloMoto}
                onChange={(e) => setModeloMoto(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
              />
            </div>
          </>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Síntoma / motivo
          </label>
          <input
            type="text"
            value={sintoma}
            onChange={(e) => setSintoma(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2"
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