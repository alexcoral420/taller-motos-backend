// Utilidades de sesión: guardar, leer y borrar el token en localStorage.
// Es lo más simple para empezar. Todo el manejo del token vive aquí,
// así el resto del código no toca localStorage directamente.

const TOKEN_KEY = "taller_token";

// Guarda el token tras un login exitoso.
export function guardarToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

// Lee el token actual (o null si no hay sesión).
export function obtenerToken(): string | null {
  if (typeof window === "undefined") return null; // seguridad para Next.js (server)
  return localStorage.getItem(TOKEN_KEY);
}

// Borra el token (logout).
export function borrarToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// ¿Hay una sesión activa?
export function estaAutenticado(): boolean {
  return obtenerToken() !== null;
}

// Hace una petición al backend incluyendo el token automáticamente.
// Si el token expiró (401), borra la sesión para forzar un nuevo login.
export async function fetchAuth(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = obtenerToken();

  const respuesta = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });

  // Token vencido o inválido: limpiamos la sesión.
  if (respuesta.status === 401) {
    borrarToken();
    if (typeof window !== "undefined") {
      window.location.href = "/panel/login";
    }
  }

  return respuesta;
}