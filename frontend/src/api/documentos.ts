import { api } from "@/lib/cliente";
import type { Documento, DocumentoValidar, TipoDocumento } from "./tipos";

export function subirDocumento(solicitudId: number, tipoDocumento: TipoDocumento, archivo: File) {
  const datosFormulario = new FormData();
  datosFormulario.append("solicitud_id", String(solicitudId));
  datosFormulario.append("tipo_documento", tipoDocumento);
  datosFormulario.append("archivo", archivo);
  return api
    .post<Documento>("/documentos", datosFormulario, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((respuesta) => respuesta.data);
}

export function descargarDocumento(id: number) {
  return api.get(`/documentos/${id}`, { responseType: "blob" }).then((respuesta) => respuesta.data as Blob);
}

export function validarDocumento(id: number, datos: DocumentoValidar) {
  return api.post<Documento>(`/documentos/${id}/validar`, datos).then((respuesta) => respuesta.data);
}
