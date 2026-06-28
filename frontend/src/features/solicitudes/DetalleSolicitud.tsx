import { useState, type ChangeEvent, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { descargarDocumento, subirDocumento, validarDocumento } from "@/api/documentos";
import {
  decidirSolicitud,
  enviarSolicitud,
  listarAutorizaciones,
  listarDocumentosSolicitud,
  obtenerChecklist,
  obtenerSolicitud,
  reenviarSolicitud,
} from "@/api/solicitudes";
import type { EtapaAutorizacion, TipoDocumento } from "@/api/tipos";
import { useAuth } from "@/auth/AuthContext";

const ETAPAS_ACTIVAS: EtapaAutorizacion[] = [
  "RECEPCION",
  "REVISION_TECNICA",
  "APROBACION_GERENCIAL",
  "REVISION_JURIDICA",
  "AUTORIZACION_FINAL",
];

export function DetalleSolicitud() {
  const { id } = useParams<{ id: string }>();
  const solicitudId = Number(id);
  const { usuario } = useAuth();
  const esProveedor = usuario?.rol === "PROVEEDOR";
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [estadoDecision, setEstadoDecision] = useState<"APROBADO" | "RECHAZADO" | "OBSERVADO">("APROBADO");
  const [comentarioDecision, setComentarioDecision] = useState("");

  const { data: solicitud } = useQuery({
    queryKey: ["solicitudes", solicitudId],
    queryFn: () => obtenerSolicitud(solicitudId),
  });
  const { data: autorizaciones } = useQuery({
    queryKey: ["solicitudes", solicitudId, "autorizaciones"],
    queryFn: () => listarAutorizaciones(solicitudId),
  });
  const { data: documentos } = useQuery({
    queryKey: ["solicitudes", solicitudId, "documentos"],
    queryFn: () => listarDocumentosSolicitud(solicitudId),
  });
  const { data: checklist } = useQuery({
    queryKey: ["solicitudes", solicitudId, "checklist"],
    queryFn: () => obtenerChecklist(solicitudId),
  });

  function invalidarTodo() {
    void queryClient.invalidateQueries({ queryKey: ["solicitudes", solicitudId] });
    void queryClient.invalidateQueries({ queryKey: ["solicitudes"] });
  }

  const mutacionEnviar = useMutation({
    mutationFn: () => enviarSolicitud(solicitudId),
    onSuccess: invalidarTodo,
    onError: () => setError("No se pudo enviar la solicitud."),
  });

  const mutacionReenviar = useMutation({
    mutationFn: () => reenviarSolicitud(solicitudId),
    onSuccess: invalidarTodo,
    onError: () => setError("No se pudo reenviar la solicitud."),
  });

  const mutacionDecidir = useMutation({
    mutationFn: () => decidirSolicitud(solicitudId, { estado: estadoDecision, comentario: comentarioDecision || null }),
    onSuccess: () => {
      setComentarioDecision("");
      invalidarTodo();
    },
    onError: () => setError("No se pudo registrar la decisión. Verifique el checklist de documentos."),
  });

  const mutacionSubir = useMutation({
    mutationFn: ({ tipo, archivo }: { tipo: TipoDocumento; archivo: File }) =>
      subirDocumento(solicitudId, tipo, archivo),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["solicitudes", solicitudId, "documentos"] });
      void queryClient.invalidateQueries({ queryKey: ["solicitudes", solicitudId, "checklist"] });
    },
    onError: () => setError("No se pudo subir el documento."),
  });

  const mutacionValidar = useMutation({
    mutationFn: ({
      documentoId,
      estado,
    }: {
      documentoId: number;
      estado: "VALIDADO" | "OBSERVADO" | "RECHAZADO";
    }) => validarDocumento(documentoId, { estado_validacion: estado }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["solicitudes", solicitudId, "documentos"] });
      void queryClient.invalidateQueries({ queryKey: ["solicitudes", solicitudId, "checklist"] });
    },
    onError: () => setError("No se pudo validar el documento."),
  });

  async function descargar(documentoId: number, nombreArchivo: string) {
    const blob = await descargarDocumento(documentoId);
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = nombreArchivo;
    enlace.click();
    URL.revokeObjectURL(url);
  }

  function manejarArchivoSeleccionado(tipo: TipoDocumento, evento: ChangeEvent<HTMLInputElement>) {
    const archivo = evento.target.files?.[0];
    if (!archivo) return;
    mutacionSubir.mutate({ tipo, archivo });
    evento.target.value = "";
  }

  function manejarDecision(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    mutacionDecidir.mutate();
  }

  if (!solicitud) return <p>Cargando solicitud…</p>;

  const puedeEnviar = solicitud.estado === "BORRADOR";
  const puedeReenviar = solicitud.estado === "OBSERVADA";
  const puedeDecidir = !esProveedor && ETAPAS_ACTIVAS.includes(solicitud.estado as EtapaAutorizacion);

  const documentoPorTipo = (tipo: TipoDocumento) =>
    documentos?.find((documento) => documento.tipo_documento === tipo);

  return (
    <div>
      <div className="encabezado-seccion">
        <h1>Solicitud {solicitud.numero_referencia}</h1>
        <span>{solicitud.estado}</span>
      </div>

      <h2>Datos generales</h2>
      <table className="tabla">
        <tbody>
          <tr>
            <td>Tipo</td>
            <td>{solicitud.tipo}</td>
          </tr>
          <tr>
            <td>Cobertura</td>
            <td>{solicitud.cobertura}</td>
          </tr>
          <tr>
            <td>Provincias involucradas</td>
            <td>{solicitud.provincias_involucradas ?? "—"}</td>
          </tr>
          <tr>
            <td>Postes solicitados</td>
            <td>{solicitud.postes_solicitados}</td>
          </tr>
          <tr>
            <td>Objetivo del proyecto</td>
            <td>{solicitud.objetivo_proyecto ?? "—"}</td>
          </tr>
          <tr>
            <td>Dirigida a</td>
            <td>{solicitud.dirigida_a}</td>
          </tr>
          <tr>
            <td>Fecha de creación</td>
            <td>{solicitud.fecha_creacion}</td>
          </tr>
        </tbody>
      </table>

      <h2>Rutas propuestas</h2>
      <table className="tabla">
        <thead>
          <tr>
            <th>Provincia</th>
            <th>Ciudad</th>
            <th>Postes usados</th>
            <th>Postes nuevos</th>
            <th>Total postes</th>
          </tr>
        </thead>
        <tbody>
          {solicitud.rutas_propuestas.map((ruta) => (
            <tr key={ruta.id}>
              <td>{ruta.provincia}</td>
              <td>{ruta.ciudad ?? "—"}</td>
              <td>{ruta.postes_usados}</td>
              <td>{ruta.postes_nuevos}</td>
              <td>{ruta.total_postes}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Contactos</h2>
      <table className="tabla">
        <thead>
          <tr>
            <th>Rol</th>
            <th>Nombre</th>
            <th>Teléfono</th>
            <th>Correo</th>
          </tr>
        </thead>
        <tbody>
          {solicitud.contactos.map((contacto) => (
            <tr key={contacto.id}>
              <td>{contacto.rol_contacto}</td>
              <td>{contacto.nombre}</td>
              <td>{contacto.telefono ?? "—"}</td>
              <td>{contacto.correo ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Historial de autorizaciones</h2>
      <table className="tabla">
        <thead>
          <tr>
            <th>Etapa</th>
            <th>Estado</th>
            <th>Comentario</th>
            <th>Fecha</th>
          </tr>
        </thead>
        <tbody>
          {autorizaciones?.map((autorizacion) => (
            <tr key={autorizacion.id}>
              <td>{autorizacion.etapa}</td>
              <td>{autorizacion.estado}</td>
              <td>{autorizacion.comentario ?? "—"}</td>
              <td>{autorizacion.fecha}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {autorizaciones?.length === 0 && <p>Aún no se ha registrado ninguna decisión.</p>}

      <h2>Checklist de documentos</h2>
      <table className="tabla">
        <thead>
          <tr>
            <th>Documento</th>
            <th>Estado</th>
            <th>Acción</th>
          </tr>
        </thead>
        <tbody>
          {checklist?.map((item) => {
            const documento = item.documento_id ? documentoPorTipo(item.tipo_documento) : undefined;
            return (
              <tr key={item.tipo_documento}>
                <td>{item.tipo_documento}</td>
                <td>{item.estado_validacion}</td>
                <td>
                  {!item.documento_id ? (
                    <input
                      type="file"
                      onChange={(evento) => manejarArchivoSeleccionado(item.tipo_documento, evento)}
                    />
                  ) : (
                    <>
                      {documento && (
                        <button type="button" onClick={() => descargar(documento.id, documento.nombre_archivo)}>
                          Descargar
                        </button>
                      )}
                      {!esProveedor && item.estado_validacion === "PENDIENTE" && item.documento_id && (
                        <button
                          type="button"
                          onClick={() =>
                            mutacionValidar.mutate({ documentoId: item.documento_id as number, estado: "VALIDADO" })
                          }
                        >
                          Validar
                        </button>
                      )}
                    </>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {error && <p className="mensaje-error">{error}</p>}

      <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
        {puedeEnviar && (
          <button type="button" onClick={() => mutacionEnviar.mutate()} disabled={mutacionEnviar.isPending}>
            Enviar solicitud
          </button>
        )}
        {puedeReenviar && (
          <button type="button" onClick={() => mutacionReenviar.mutate()} disabled={mutacionReenviar.isPending}>
            Reenviar solicitud
          </button>
        )}
      </div>

      {puedeDecidir && (
        <form className="formulario" onSubmit={manejarDecision} style={{ maxWidth: "480px", marginTop: "1rem" }}>
          <h2>Registrar decisión ({solicitud.estado})</h2>
          <label htmlFor="estado_decision">Decisión</label>
          <select
            id="estado_decision"
            value={estadoDecision}
            onChange={(evento) =>
              setEstadoDecision(evento.target.value as "APROBADO" | "RECHAZADO" | "OBSERVADO")
            }
          >
            <option value="APROBADO">APROBADO</option>
            <option value="OBSERVADO">OBSERVADO</option>
            <option value="RECHAZADO">RECHAZADO</option>
          </select>

          <label htmlFor="comentario_decision">Comentario</label>
          <textarea
            id="comentario_decision"
            value={comentarioDecision}
            onChange={(evento) => setComentarioDecision(evento.target.value)}
          />

          <button type="submit" disabled={mutacionDecidir.isPending}>
            {mutacionDecidir.isPending ? "Guardando…" : "Registrar decisión"}
          </button>
        </form>
      )}
    </div>
  );
}
