"use client";

import { useEffect, useState } from "react";

// Tipo de un servicio del catálogo (igual que en la página principal).
type Servicio = {
  codigo: string;
  nombre: string;
  descripcion: string | null;
  precio_referencia: string;
};

export default function Cotizar() {
  // Campos de texto del formulario.
  const [nombre, setNombre] = useState("");
  const [telefono, setTelefono] = useState("");
  const [email, setEmail] = useState("");
  const [modeloMoto, setModeloMoto] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [aceptaPublicidad, setAceptaPublicidad] = useState(false);

  // Catálogo traído de la API y los códigos seleccionados.
  const [servicios, setServicios] = useState<Servicio[]>([]);
  const [seleccionados, setSeleccionados] = useState<string[]>([]);

  // Estados de envío.
  const [enviando, setEnviando] = useState(false);
  const [enviado, setEnviado] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Al cargar la página, traemos el catálogo de servicios.
  useEffect(() => {
    fetch("http://localhost:8000/api/public/catalogo")
      .then((res) => res.json())
      .then((data: Servicio[]) => setServicios(data))
      .catch(() => setError("No se pudo cargar el catálogo de servicios"));
  }, []);

  // Marca o desmarca un servicio según su código.
  function alternarServicio(codigo: string) {
    setSeleccionados((actuales) =>
      actuales.includes(codigo)
        ? actuales.filter((c) => c !== codigo) // ya estaba: lo quitamos
        : [...actuales, codigo] // no estaba: lo agregamos
    );
  }

  async function manejarEnvio(e: React.FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setError(null);

    try {
      const respuesta = await fetch(
        "http://localhost:8000/api/public/cotizaciones",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            nombre,
            telefono: telefono || null,
            email: email || null,
            modelo_moto: modeloMoto || null,
            descripcion: descripcion || null,
            // Convertimos los códigos seleccionados al formato que espera la API.
            items: seleccionados.map((codigo) => ({ codigo, cantidad: 1 })),
            acepta_publicidad: aceptaPublicidad,
          }),
        }
      );

      if (!respuesta.ok) throw new Error("No se pudo enviar la cotización");

      setEnviado(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setEnviando(false);
    }
  }

  if (enviado) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="bg-white rounded-lg shadow p-8 text-center max-w-md">
          <h1 className="text-2xl font-bold text-green-600 mb-2">
            ¡Gracias por tu solicitud!
          </h1>
          <p className="text-gray-600">
            Hemos recibido tu cotización. Te contactaremos pronto.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-lg mx-auto bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">
          Solicita una cotización
        </h1>

        <form onSubmit={manejarEnvio} className="flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre *
            </label>
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              required
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Teléfono
            </label>
            <input
              type="tel"
              value={telefono}
              onChange={(e) => setTelefono(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Correo
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
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

          {/* Selección de servicios (checkboxes) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Servicios que te interesan
            </label>
            <div className="flex flex-col gap-2">
              {servicios.map((servicio) => (
                <label
                  key={servicio.codigo}
                  className="flex items-center gap-2 text-sm text-gray-700 border border-gray-200 rounded px-3 py-2 cursor-pointer hover:bg-gray-50"
                >
                  <input
                    type="checkbox"
                    checked={seleccionados.includes(servicio.codigo)}
                    onChange={() => alternarServicio(servicio.codigo)}
                  />
                  <span className="flex-1">{servicio.nombre}</span>
                  <span className="text-gray-500">
                    ${Number(servicio.precio_referencia).toLocaleString("es-CO")}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ¿Algo más que debamos saber?
            </label>
            <textarea
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              rows={3}
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={aceptaPublicidad}
              onChange={(e) => setAceptaPublicidad(e.target.checked)}
            />
            Acepto ser contactado con información y promociones
          </label>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={enviando}
            className="bg-blue-600 text-white rounded px-4 py-2 font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {enviando ? "Enviando..." : "Enviar cotización"}
          </button>
        </form>
      </div>
    </main>
  );
}