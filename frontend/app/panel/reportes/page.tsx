"use client";

import Link from "next/link";
import { Fragment, useEffect, useState } from "react";

import { fetchAuth } from "@/app/lib/auth";

type Usuario = {
  id: number;
  nombre: string;
  rol: string;
};

type ItemOrden = {
  descripcion: string;
  cantidad: string;
  valor_unitario: string;
  subtotal: string;
};

type FilaReporte = {
  numero: number;
  tipo: string;
  fecha: string;
  tecnico: string | null;
  placa: string | null;
  cliente: string | null;
  total: string;
  estado: string;
  sintoma: string | null;
  items: ItemOrden[];
};

type ResumenTipo = {
  cantidad: number;
  total: string;
};

type Reporte = {
  ordenes: FilaReporte[];
  resumen: {
    cantidad_ordenes: number;
    total: string;
    interno: ResumenTipo;
    externo: ResumenTipo;
    cobrado_efectivo: string;
    cobrado_nequi: string;
    cobrado_otros: string;
    pendiente_cobro: string;
  };
};

type Filtros = {
  fecha_desde: string;
  fecha_hasta: string;
  tecnico_id: string;
  tipo: string;
  estado: string;
};

const formatoPesos = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

const formatoFecha = new Intl.DateTimeFormat("es-CO", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "America/Bogota",
});

function pesos(valor: string | number) {
  return formatoPesos.format(Number(valor));
}

// Fecha local en formato YYYY-MM-DD (lo que espera <input type="date">).
function aIsoLocal(fecha: Date) {
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const dia = String(fecha.getDate()).padStart(2, "0");
  return `${fecha.getFullYear()}-${mes}-${dia}`;
}

// Semana actual: del lunes de esta semana a hoy.
function semanaActual() {
  const hoy = new Date();
  const lunes = new Date(hoy);
  // getDay(): 0 = domingo. El domingo pertenece a la semana que empezó 6 días antes.
  lunes.setDate(hoy.getDate() - ((hoy.getDay() + 6) % 7));
  return { desde: aIsoLocal(lunes), hasta: aIsoLocal(hoy) };
}

function filtrosIniciales(): Filtros {
  const { desde, hasta } = semanaActual();
  return { fecha_desde: desde, fecha_hasta: hasta, tecnico_id: "", tipo: "", estado: "" };
}

const claseInput = "w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white";

function EtiquetaTipo({ tipo }: { tipo: string }) {
  return (
    <span
      className={`text-xs px-2 py-0.5 rounded ${
        tipo === "interno" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"
      }`}
    >
      {tipo}
    </span>
  );
}

function EtiquetaEstado({ estado }: { estado: string }) {
  return (
    <span
      className={`text-xs px-2 py-0.5 rounded ${
        estado === "liquidada" ? "bg-gray-200 text-gray-600" : "bg-yellow-100 text-yellow-700"
      }`}
    >
      {estado}
    </span>
  );
}

// Síntoma completo + servicios con sus valores (común a tabla y tarjetas).
function DetalleOrden({ orden }: { orden: FilaReporte }) {
  return (
    <div className="text-sm">
      <p className="text-gray-500">Síntoma</p>
      <p className="text-gray-800 whitespace-pre-line mb-3">{orden.sintoma || "—"}</p>

      <p className="text-gray-500 mb-1">Servicios</p>
      {orden.items.length === 0 ? (
        <p className="text-gray-400">Sin servicios registrados.</p>
      ) : (
        <ul className="divide-y divide-gray-200">
          {orden.items.map((item, i) => (
            <li key={i} className="flex justify-between gap-3 py-1.5">
              <span className="text-gray-800">
                {item.descripcion}
                {Number(item.cantidad) !== 1 && (
                  <span className="text-gray-500">
                    {" "}
                    · {Number(item.cantidad)} × {pesos(item.valor_unitario)}
                  </span>
                )}
              </span>
              <span className="font-medium whitespace-nowrap">{pesos(item.subtotal)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Reportes() {
  // null = verificando el rol
  const [esAdmin, setEsAdmin] = useState<boolean | null>(null);
  const [tecnicos, setTecnicos] = useState<Usuario[]>([]);
  const [filtros, setFiltros] = useState<Filtros>(filtrosIniciales);
  const [reporte, setReporte] = useState<Reporte | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Números de las órdenes con el detalle abierto.
  const [expandidas, setExpandidas] = useState<Set<number>>(new Set());

  function alternar(numero: number) {
    setExpandidas((prev) => {
      const nuevo = new Set(prev);
      if (nuevo.has(numero)) nuevo.delete(numero);
      else nuevo.add(numero);
      return nuevo;
    });
  }

  async function cargarReporte(f: Filtros) {
    setCargando(true);
    setError(null);
    setExpandidas(new Set());
    const params = new URLSearchParams();
    // Solo enviamos los filtros con valor; los vacíos = "todos".
    for (const [clave, valor] of Object.entries(f)) {
      if (valor) params.set(clave, valor);
    }
    try {
      const res = await fetchAuth(`/api/v1/ordenes/reporte?${params}`);
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(
          typeof err?.detail === "string" ? err.detail : "No se pudo cargar el reporte"
        );
      }
      setReporte(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar el reporte");
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    // Primero el rol: el reporte y la lista de usuarios son solo para admin.
    fetchAuth("/api/v1/auth/me")
      .then((res) => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then((yo: Usuario) => {
        const admin = yo.rol === "administrador";
        setEsAdmin(admin);
        if (!admin) return;

        fetchAuth("/api/v1/usuarios")
          .then((res) => (res.ok ? res.json() : []))
          .then((data: Usuario[]) =>
            setTecnicos([...data].sort((a, b) => a.nombre.localeCompare(b.nombre)))
          );
        cargarReporte(filtrosIniciales());
      })
      .catch(() => setEsAdmin(false));
  }, []);

  function cambiar(campo: keyof Filtros, valor: string) {
    setFiltros((prev) => ({ ...prev, [campo]: valor }));
  }

  function aplicarFiltros(e: React.FormEvent) {
    e.preventDefault();
    cargarReporte(filtros);
  }

  if (esAdmin === null) {
    return <p className="text-gray-500 max-w-6xl mx-auto">Cargando...</p>;
  }

  if (!esAdmin) {
    return (
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">Reportes</h1>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-700">
            No tienes permiso para ver esta sección. Solo el administrador puede ver los reportes.
          </p>
          <Link href="/panel" className="inline-block mt-4 text-sm text-gray-500 hover:text-gray-800">
            ← Volver al inicio
          </Link>
        </div>
      </div>
    );
  }

  const resumen = reporte?.resumen;

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Reportes de órdenes</h1>

      {/* Filtros */}
      <form
        onSubmit={aplicarFiltros}
        className="bg-white rounded-lg shadow p-4 mb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 items-end"
      >
        <label className="text-sm text-gray-700">
          Desde
          <input
            type="date"
            value={filtros.fecha_desde}
            max={filtros.fecha_hasta || undefined}
            onChange={(e) => cambiar("fecha_desde", e.target.value)}
            className={`${claseInput} mt-1`}
          />
        </label>
        <label className="text-sm text-gray-700">
          Hasta
          <input
            type="date"
            value={filtros.fecha_hasta}
            min={filtros.fecha_desde || undefined}
            onChange={(e) => cambiar("fecha_hasta", e.target.value)}
            className={`${claseInput} mt-1`}
          />
        </label>
        <label className="text-sm text-gray-700">
          Técnico
          <select
            value={filtros.tecnico_id}
            onChange={(e) => cambiar("tecnico_id", e.target.value)}
            className={`${claseInput} mt-1`}
          >
            <option value="">Todos</option>
            {tecnicos.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nombre}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm text-gray-700">
          Tipo
          <select
            value={filtros.tipo}
            onChange={(e) => cambiar("tipo", e.target.value)}
            className={`${claseInput} mt-1`}
          >
            <option value="">Todos</option>
            <option value="interno">Interno</option>
            <option value="externo">Externo</option>
          </select>
        </label>
        <label className="text-sm text-gray-700">
          Estado
          <select
            value={filtros.estado}
            onChange={(e) => cambiar("estado", e.target.value)}
            className={`${claseInput} mt-1`}
          >
            <option value="">Todos</option>
            <option value="pendiente">Pendiente</option>
            <option value="liquidada">Liquidada</option>
          </select>
        </label>
        <button
          type="submit"
          disabled={cargando}
          className="bg-gray-900 text-white rounded px-4 py-2 text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
        >
          {cargando ? "Cargando..." : "Aplicar filtros"}
        </button>
      </form>

      {error && <p className="text-red-500 mb-4">{error}</p>}

      {/* Resumen */}
      {resumen && (
        <div className="bg-white rounded-lg shadow p-4 mb-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-500">Total</p>
            <p className="text-2xl font-bold text-gray-800">{pesos(resumen.total)}</p>
            <p className="text-sm text-gray-500">
              {resumen.cantidad_ordenes} {resumen.cantidad_ordenes === 1 ? "orden" : "órdenes"}
            </p>
          </div>
          <div className="sm:border-l sm:pl-4 border-gray-200">
            <p className="text-sm">
              <span className="text-xs px-2 py-0.5 rounded bg-green-100 text-green-700">externo</span>
            </p>
            <p className="text-lg font-semibold text-gray-800 mt-1">{pesos(resumen.externo.total)}</p>
            <p className="text-sm text-gray-500">
              {resumen.externo.cantidad} {resumen.externo.cantidad === 1 ? "orden" : "órdenes"} · ingreso
            </p>
          </div>
          <div className="sm:border-l sm:pl-4 border-gray-200">
            <p className="text-sm">
              <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700">interno</span>
            </p>
            <p className="text-lg font-semibold text-gray-800 mt-1">{pesos(resumen.interno.total)}</p>
            <p className="text-sm text-gray-500">
              {resumen.interno.cantidad} {resumen.interno.cantidad === 1 ? "orden" : "órdenes"} · costo
            </p>
          </div>

          {/* Desglose de cobros por método */}
          <dl className="sm:col-span-3 border-t border-gray-200 pt-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">Cobrado en efectivo</dt>
              <dd className="font-semibold text-gray-800">{pesos(resumen.cobrado_efectivo)}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Cobrado en Nequi</dt>
              <dd className="font-semibold text-gray-800">{pesos(resumen.cobrado_nequi)}</dd>
            </div>
            {Number(resumen.cobrado_otros) > 0 && (
              <div>
                <dt className="text-gray-500">Otros</dt>
                <dd className="font-semibold text-gray-800">{pesos(resumen.cobrado_otros)}</dd>
              </div>
            )}
            <div>
              <dt className="text-gray-500">Pendiente de cobro</dt>
              <dd className="font-semibold text-amber-700">{pesos(resumen.pendiente_cobro)}</dd>
            </div>
          </dl>
        </div>
      )}

      {/* Tabla */}
      {reporte && reporte.ordenes.length === 0 && (
        <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
          No hay órdenes para los filtros seleccionados.
        </div>
      )}

      {/* Móvil: tarjetas apiladas */}
      {reporte && reporte.ordenes.length > 0 && (
        <div className="md:hidden flex flex-col gap-3">
          {reporte.ordenes.map((o) => {
            const abierta = expandidas.has(o.numero);
            return (
              <div key={o.numero} className="bg-white rounded-lg shadow">
                <button
                  type="button"
                  onClick={() => alternar(o.numero)}
                  aria-expanded={abierta}
                  className="w-full text-left p-4"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 min-w-0">
                      <EtiquetaTipo tipo={o.tipo} />
                      <span className="font-semibold text-gray-800 truncate">
                        {o.cliente || o.placa || "—"}
                      </span>
                    </div>
                    <span className="font-bold whitespace-nowrap">{pesos(o.total)}</span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1 truncate">
                    {o.tecnico || "Sin técnico"} · Placa: {o.placa || "—"}
                  </p>
                  {o.sintoma && !abierta && (
                    <p className="text-sm text-gray-600 mt-1 truncate">{o.sintoma}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-2">
                    {abierta ? "▲ Ocultar detalle" : "▼ Ver detalle"}
                  </p>
                </button>

                {abierta && (
                  <div className="border-t border-gray-100 bg-gray-50 rounded-b-lg p-4">
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm mb-3">
                      <span className="font-semibold">#{o.numero}</span>
                      <EtiquetaEstado estado={o.estado} />
                      <span className="text-gray-600">{formatoFecha.format(new Date(o.fecha))}</span>
                    </div>
                    <DetalleOrden orden={o} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Desktop: tabla con filas expandibles */}
      {reporte && reporte.ordenes.length > 0 && (
        <div className="hidden md:block bg-white rounded-lg shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-gray-600">
              <tr>
                <th className="px-4 py-3 font-medium">N°</th>
                <th className="px-4 py-3 font-medium">Tipo</th>
                <th className="px-4 py-3 font-medium">Fecha</th>
                <th className="px-4 py-3 font-medium">Técnico</th>
                <th className="px-4 py-3 font-medium">Placa</th>
                <th className="px-4 py-3 font-medium">Cliente</th>
                <th className="px-4 py-3 font-medium text-right">Total</th>
                <th className="px-4 py-3 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {reporte.ordenes.map((o) => {
                const abierta = expandidas.has(o.numero);
                return (
                  <Fragment key={o.numero}>
                    <tr
                      onClick={() => alternar(o.numero)}
                      aria-expanded={abierta}
                      className={`whitespace-nowrap cursor-pointer hover:bg-gray-50 ${abierta ? "bg-gray-50" : ""}`}
                    >
                      <td className="px-4 py-3 font-semibold">
                        <span className="text-gray-400 mr-1">{abierta ? "▾" : "▸"}</span>#{o.numero}
                      </td>
                      <td className="px-4 py-3">
                        <EtiquetaTipo tipo={o.tipo} />
                      </td>
                      <td className="px-4 py-3 text-gray-600">{formatoFecha.format(new Date(o.fecha))}</td>
                      <td className="px-4 py-3">{o.tecnico || "—"}</td>
                      <td className="px-4 py-3">{o.placa || "—"}</td>
                      <td className="px-4 py-3">{o.cliente || "—"}</td>
                      <td className="px-4 py-3 text-right font-medium">{pesos(o.total)}</td>
                      <td className="px-4 py-3">
                        <EtiquetaEstado estado={o.estado} />
                      </td>
                    </tr>
                    {abierta && (
                      <tr className="bg-gray-50">
                        <td colSpan={8} className="px-4 pb-4 pt-1">
                          <div className="max-w-2xl">
                            <DetalleOrden orden={o} />
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
