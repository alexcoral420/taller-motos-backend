"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { guardarToken } from "@/app/lib/auth";

export default function Login() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function manejarLogin(e: React.FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setError(null);

    try {
      // El backend espera formato OAuth2 (form-urlencoded), no JSON.
      // El campo se llama 'username' aunque ahí va el email.
      const body = new URLSearchParams();
      body.append("username", email);
      body.append("password", password);

      const respuesta = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/login`,
        {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: body.toString(),
        }
      );

      if (!respuesta.ok) {
        throw new Error("Email o contraseña incorrectos");
      }

      const data = await respuesta.json();
      guardarToken(data.access_token); // guardamos el token
      router.push("/panel"); // redirigimos al panel
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-100 flex items-center justify-center p-6">
      <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          Panel del Taller
        </h1>

        <form onSubmit={manejarLogin} className="flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Correo
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={enviando}
            className="bg-gray-900 text-white rounded px-4 py-2 font-medium hover:bg-gray-800 disabled:opacity-50"
          >
            {enviando ? "Entrando..." : "Iniciar sesión"}
          </button>
        </form>
      </div>
    </main>
  );
}