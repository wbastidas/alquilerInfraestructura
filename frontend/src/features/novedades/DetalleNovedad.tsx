import { useState, type ChangeEvent, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { descargarDocumento } from "@/api/documentos";
import { actualizarNovedad, obtenerNovedad, subirFotografiaNovedad } from "@/api/novedades";
import type { EstadoNovedad } from "@/api/tipos";
import { useAuth } from "@/auth/AuthContext";

const SIGUIENTE_ESTADO: Record<EstadoNovedad, EstadoNovedad | null> = {
  PROGRAMADA: "EN_PROCESO",
  EN_PROCESO: "EJECUTADA",
  EJECUTADA: "CERRADA",
  CERRADA: null,
};

export function DetalleNovedad() {
  const { id } = useParams<{ id: string }>();
  const novedadId = Number(id);
  const { usuario } = useAuth();
  const esProveedor = usuario?.rol === "PROVEEDOR";
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [fechaEjecucion, setFechaEjecucion] = useState("");
  const [latitudFoto, setLatitudFoto] = useState("");
  const [longitudFoto, setLongitudFoto] = useState("");

  const { data: novedad } = useQuery({
    queryKey: ["novedades", novedadId],
    queryFn: () => obtenerNovedad(novedadId),
  });

  function invalidar() {
    void queryClient.invalidateQueries({ queryKey: ["novedades", novedadId] });
    void queryClient.invalidateQueries({ queryKey: ["novedades"] });
  }

  const mutacionEstado = useMutation({
    mutationFn: (estado: EstadoNovedad) =>
      actualizarNovedad(
        novedadId,
        estado === "EJECUTADA" ? { estado, fecha_ejecucion: fechaEjecucion || null } : { estado },
      ),
    onSuccess: () => {
      setFechaEjecucion("");
      invalidar();
    },
    onError: () => setError("No se pudo actualizar el estado de la novedad."),
  });

  const mutacionFoto = useMutation({
    mutationFn: ({ archivo }: { archivo: File }) =>
      subirFotografiaNovedad(novedadId, archivo, latitudFoto || undefined, longitudFoto || undefined),
    onSuccess: () => {
      setLatitudFoto("");
      setLongitudFoto("");
      invalidar();
    },
    onError: () => setError("No se pudo subir la fotografía."),
  });

  async function descargar(documentoId: number) {
    const blob = await descargarDocumento(documentoId);
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = `fotografia-${documentoId}`;
    enlace.click();
    URL.revokeObjectURL(url);
  }

  function manejarArchivoSeleccionado(evento: ChangeEvent<HTMLInputElement>) {
    const archivo = evento.target.files?.[0];
    if (!archivo) return;
    mutacionFoto.mutate({ archivo });
    evento.target.value = "";
  }

  function manejarAvanzarEstado(evento: FormEvent, siguiente: EstadoNovedad) {
    evento.preventDefault();
    setError(null);
    mutacionEstado.mutate(siguiente);
  }

  if (!novedad) return <p>Cargando novedad…</p>;

  const siguienteEstado = SIGUIENTE_ESTADO[novedad.estado];

  return (
    <div>
      <div className="encabezado-seccion">
        <h1>Novedad {novedad.tipo}</h1>
        <span>{novedad.estado}</span>
      </div>

      <table className="tabla">
        <tbody>
          <tr>
            <td>Descripción</td>
            <td>{novedad.descripcion ?? "—"}</td>
          </tr>
          <tr>
            <td>Fecha programada</td>
            <td>{novedad.fecha_programada ?? "—"}</td>
          </tr>
          <tr>
            <td>Fecha de ejecución</td>
            <td>{novedad.fecha_ejecucion ?? "—"}</td>
          </tr>
          <tr>
            <td>Latitud</td>
            <td>{novedad.latitud ?? "—"}</td>
          </tr>
          <tr>
            <td>Longitud</td>
            <td>{novedad.longitud ?? "—"}</td>
          </tr>
        </tbody>
      </table>

      <h2>Fotografías</h2>
      <table className="tabla">
        <thead>
          <tr>
            <th>Latitud</th>
            <th>Longitud</th>
            <th>Acción</th>
          </tr>
        </thead>
        <tbody>
          {novedad.fotografias.map((foto) => (
            <tr key={foto.id}>
              <td>{foto.latitud ?? "—"}</td>
              <td>{foto.longitud ?? "—"}</td>
              <td>
                <button type="button" onClick={() => descargar(foto.documento_id)}>
                  Descargar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {novedad.fotografias.length === 0 && <p>Aún no se han cargado fotografías.</p>}

      {error && <p className="mensaje-error">{error}</p>}

      {!esProveedor && (
        <div style={{ marginTop: "1rem", maxWidth: "480px" }}>
          <h2>Subir fotografía</h2>
          <label htmlFor="latitud_foto">Latitud</label>
          <input id="latitud_foto" value={latitudFoto} onChange={(evento) => setLatitudFoto(evento.target.value)} />
          <label htmlFor="longitud_foto">Longitud</label>
          <input
            id="longitud_foto"
            value={longitudFoto}
            onChange={(evento) => setLongitudFoto(evento.target.value)}
          />
          <input type="file" accept="image/*" onChange={manejarArchivoSeleccionado} />
        </div>
      )}

      {!esProveedor && siguienteEstado && (
        <form
          className="formulario"
          onSubmit={(evento) => manejarAvanzarEstado(evento, siguienteEstado)}
          style={{ maxWidth: "480px", marginTop: "1rem" }}
        >
          <h2>Avanzar a {siguienteEstado}</h2>
          {siguienteEstado === "EJECUTADA" && (
            <>
              <label htmlFor="fecha_ejecucion">Fecha de ejecución</label>
              <input
                id="fecha_ejecucion"
                type="date"
                value={fechaEjecucion}
                onChange={(evento) => setFechaEjecucion(evento.target.value)}
              />
            </>
          )}
          <button type="submit" disabled={mutacionEstado.isPending}>
            {mutacionEstado.isPending ? "Guardando…" : `Marcar como ${siguienteEstado}`}
          </button>
        </form>
      )}
    </div>
  );
}
