"use client";

import { useState } from "react";

// 👇 REEMPLAZA por tu número: código de país + número, sin + ni espacios.
const WHATSAPP_NUMERO = "573042827782";
const WHATSAPP_MENSAJE = "Hola, me gustaría hacer una consulta sobre mi moto.";

export default function Contacto() {
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [telefono, setTelefono] = useState("");
  const [asunto, setAsunto] = useState("");
  const [mensaje, setMensaje] = useState("");

  const [enviando, setEnviando] = useState(false);
  const [enviado, setEnviado] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Arma el enlace de WhatsApp con el mensaje predefinido.
  const urlWhatsapp = `https://wa.me/${WHATSAPP_NUMERO}?text=${encodeURIComponent(
    WHATSAPP_MENSAJE
  )}`;

  async function manejarEnvio(e: React.FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setError(null);

    try {
      const respuesta = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/public/contacto`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            nombre,
            email: email || null,
            telefono: telefono || null,
            asunto: asunto || null,
            mensaje,
          }),
        }
      );

      if (!respuesta.ok) throw new Error("No se pudo enviar el mensaje");
      setEnviado(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 p-6 md:p-8">
      <div className="max-w-lg mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Contáctanos</h1>
        <p className="text-gray-600 mb-6">
          Escríbenos por WhatsApp para una respuesta inmediata, o déjanos un
          mensaje y te responderemos pronto.
        </p>

        {/* Botón de WhatsApp */}
        
        <a          
          href={urlWhatsapp}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 bg-green-500 text-white rounded-lg px-4 py-3 font-medium hover:bg-green-600 transition-colors mb-8"
        >
          💬 Escribir por WhatsApp
        </a>

        {/* Separador */}
        <div className="flex items-center gap-3 mb-8">
          <div className="flex-1 h-px bg-gray-300" />
          <span className="text-sm text-gray-400">o déjanos un mensaje</span>
          <div className="flex-1 h-px bg-gray-300" />
        </div>

        {/* Formulario que guarda en el backend */}
        {enviado ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <h2 className="text-xl font-bold text-green-600 mb-2">
              ¡Mensaje enviado!
            </h2>
            <p className="text-gray-600">Te responderemos pronto.</p>
          </div>
        ) : (
          <form
            onSubmit={manejarEnvio}
            className="bg-white rounded-lg shadow p-6 flex flex-col gap-4"
          >
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
                Asunto
              </label>
              <input
                type="text"
                value={asunto}
                onChange={(e) => setAsunto(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mensaje *
              </label>
              <textarea
                value={mensaje}
                onChange={(e) => setMensaje(e.target.value)}
                required
                rows={4}
                className="w-full border border-gray-300 rounded px-3 py-2"
              />
            </div>

            {error && <p className="text-red-500 text-sm">{error}</p>}

            <button
              type="submit"
              disabled={enviando}
              className="bg-blue-600 text-white rounded px-4 py-2 font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {enviando ? "Enviando..." : "Enviar mensaje"}
            </button>
          </form>
        )}
      </div>
    </main>
  );
}