import Link from "next/link";

const TELEFONO = "3042827782";
const WHATSAPP_MSG = "Hola, quiero información sobre sus servicios.";

export default function Footer() {
  const urlWhatsapp = `https://wa.me/57${TELEFONO}?text=${encodeURIComponent(WHATSAPP_MSG)}`;

  return (
    <footer className="bg-gray-900 text-gray-300 mt-12">
      <div className="max-w-5xl mx-auto px-6 py-10 grid grid-cols-1 sm:grid-cols-3 gap-8">
        {/* Nombre y descripción */}
        <div>
          <h3 className="text-white text-lg font-bold mb-2">🏍️ Taller Surtimotos</h3>
          <p className="text-sm">
            Servicio técnico especializado para tu motocicleta.
          </p>
        </div>

        {/* Contacto */}
        <div>
          <h4 className="text-white font-semibold mb-2">Contacto</h4>
          <ul className="text-sm space-y-1">
            <li>📍 Av 1 de Mayo #29c-35</li>
            <li>
              📱{" "}
              <a
                href={urlWhatsapp}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-white"
              >
                {TELEFONO} (WhatsApp)
              </a>
            </li>
            <li>
              📷{" "}
              <a
                href="https://instagram.com/tallersurtimotos"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-white"
              >
                @tallersurtimotos
              </a>
            </li>
          </ul>
        </div>

        {/* Horario y enlaces */}
        <div>
          <h4 className="text-white font-semibold mb-2">Horario</h4>
          <p className="text-sm">Lunes a sábado</p>
          <p className="text-sm mb-3">9:30 am – 6:00 pm</p>
          <div className="flex flex-col gap-1 text-sm">
            <Link href="/cotizar" className="hover:text-white">Cotizar servicio</Link>
            <Link href="/contacto" className="hover:text-white">Escríbenos</Link>
          </div>
        </div>
      </div>

      <div className="border-t border-gray-800 py-4 text-center text-xs text-gray-500">
        © {new Date().getFullYear()} Taller Surtimotos. Todos los derechos reservados.
      </div>
    </footer>
  );
}