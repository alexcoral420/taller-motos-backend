"use client";

import { useState } from "react";

export default function Cotizar() {
  // Un estado por cada campo del formulario.
  const [nombre, setNombre] = useState("");
  const [telefono, setTelefono] = useState("");
  const [email, setEmail] = useState("");
  const [modeloMoto, setModeloMoto] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [aceptaPublicidad, setAceptaPublicidad] = useState(false);

  // Estados para controlar el envío y el resultado.
  const [enviando, setEnviando] = useState(false);
  const [enviado, setEnviado] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Se ejecuta al enviar el formulario.
  async function manejarEnvio(e: React.FormEvent) {
    e.preventDefault(); // evita que la página se recargue
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
            items: [], // los servicios los agregamos en la Etapa 2
            acepta_publicidad: aceptaPublicidad,
          }),
        }
      );

      if (!respuesta.ok) throw new Error("No se pudo enviar la cotización");

      setEnviado(true); // muestra el mensaje de éxito
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setEnviando(false);
    }
  }

  // Si ya se envió, mostramos solo el mensaje de gracias.
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

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ¿Qué necesitas?
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