import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { listarContratos } from "@/api/contratos";
import { listarOperadoras } from "@/api/operadoras";
import { crearSolicitud } from "@/api/solicitudes";
import type { ContactoSolicitudCrear, CoberturaGeografica, RutaPropuestaCrear, TipoSolicitud } from "@/api/tipos";
import { useAuth } from "@/auth/AuthContext";

const OPCIONES_COBERTURA: CoberturaGeografica[] = ["NACIONAL", "REGIONAL", "LOCAL"];
const OPCIONES_TIPO: TipoSolicitud[] = ["NUEVO_CONTRATO", "AMPLIACION"];

function rutaVacia(): RutaPropuestaCrear {
  return { provincia: "", ciudad: "", postes_usados: 0, postes_nuevos: 0, total_postes: 0 };
}

function contactoVacio(): ContactoSolicitudCrear {
  return { rol_contacto: "", nombre: "", telefono: "", correo: "" };
}

export function FormularioSolicitud() {
  const navegar = useNavigate();
  const queryClient = useQueryClient();
  const { usuario } = useAuth();
  const esProveedor = usuario?.rol === "PROVEEDOR";

  const { data: operadoras } = useQuery({ queryKey: ["operadoras"], queryFn: listarOperadoras });
  const { data: contratos } = useQuery({ queryKey: ["contratos"], queryFn: listarContratos });

  const [cableOperadoraId, setCableOperadoraId] = useState<number | "">(
    esProveedor ? usuario?.cableOperadoraId ?? "" : "",
  );
  const [tipo, setTipo] = useState<TipoSolicitud>("NUEVO_CONTRATO");
  const [contratoId, setContratoId] = useState<number | "">("");
  const [cobertura, setCobertura] = useState<CoberturaGeografica>("LOCAL");
  const [provinciasInvolucradas, setProvinciasInvolucradas] = useState("");
  const [postesSolicitados, setPostesSolicitados] = useState(0);
  const [objetivoProyecto, setObjetivoProyecto] = useState("");
  const [rutas, setRutas] = useState<RutaPropuestaCrear[]>([rutaVacia()]);
  const [contactos, setContactos] = useState<ContactoSolicitudCrear[]>([contactoVacio()]);
  const [error, setError] = useState<string | null>(null);

  const mutacion = useMutation({
    mutationFn: crearSolicitud,
    onSuccess: (solicitud) => {
      void queryClient.invalidateQueries({ queryKey: ["solicitudes"] });
      navegar(`/solicitudes/${solicitud.id}`);
    },
    onError: () => setError("No se pudo crear la solicitud. Verifique los datos."),
  });

  function manejarEnvio(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    if (cableOperadoraId === "") {
      setError("Seleccione una operadora.");
      return;
    }
    if (tipo === "AMPLIACION" && contratoId === "") {
      setError("Seleccione el contrato a ampliar.");
      return;
    }
    mutacion.mutate({
      cable_operadora_id: cableOperadoraId,
      contrato_id: tipo === "AMPLIACION" ? (contratoId as number) : null,
      tipo,
      cobertura,
      provincias_involucradas: provinciasInvolucradas || null,
      postes_solicitados: postesSolicitados,
      objetivo_proyecto: objetivoProyecto || null,
      rutas_propuestas: rutas.filter((ruta) => ruta.provincia),
      contactos: contactos.filter((contacto) => contacto.nombre && contacto.rol_contacto),
    });
  }

  return (
    <div>
      <h1>Nueva solicitud</h1>
      <form className="formulario" onSubmit={manejarEnvio} style={{ maxWidth: "720px" }}>
        <label htmlFor="tipo">Tipo de solicitud</label>
        <select id="tipo" value={tipo} onChange={(evento) => setTipo(evento.target.value as TipoSolicitud)}>
          {OPCIONES_TIPO.map((opcion) => (
            <option key={opcion} value={opcion}>
              {opcion}
            </option>
          ))}
        </select>

        <label htmlFor="cable_operadora">Operadora</label>
        <select
          id="cable_operadora"
          value={cableOperadoraId}
          onChange={(evento) => setCableOperadoraId(Number(evento.target.value))}
          disabled={esProveedor}
          required
        >
          <option value="" disabled>
            Seleccione…
          </option>
          {operadoras?.map((operadora) => (
            <option key={operadora.id} value={operadora.id}>
              {operadora.nombre_empresa}
            </option>
          ))}
        </select>

        {tipo === "AMPLIACION" && (
          <>
            <label htmlFor="contrato">Contrato a ampliar</label>
            <select
              id="contrato"
              value={contratoId}
              onChange={(evento) => setContratoId(Number(evento.target.value))}
              required
            >
              <option value="" disabled>
                Seleccione…
              </option>
              {contratos
                ?.filter((contrato) => contrato.cable_operadora_id === cableOperadoraId)
                .map((contrato) => (
                  <option key={contrato.id} value={contrato.id}>
                    {contrato.numero_contrato}
                  </option>
                ))}
            </select>
          </>
        )}

        <label htmlFor="cobertura">Cobertura geográfica</label>
        <select
          id="cobertura"
          value={cobertura}
          onChange={(evento) => setCobertura(evento.target.value as CoberturaGeografica)}
        >
          {OPCIONES_COBERTURA.map((opcion) => (
            <option key={opcion} value={opcion}>
              {opcion}
            </option>
          ))}
        </select>

        <label htmlFor="provincias">Provincias involucradas</label>
        <input
          id="provincias"
          value={provinciasInvolucradas}
          onChange={(evento) => setProvinciasInvolucradas(evento.target.value)}
        />

        <label htmlFor="postes_solicitados">Postes solicitados</label>
        <input
          id="postes_solicitados"
          type="number"
          min="0"
          value={postesSolicitados}
          onChange={(evento) => setPostesSolicitados(Number(evento.target.value))}
        />

        <label htmlFor="objetivo">Objetivo del proyecto</label>
        <textarea
          id="objetivo"
          value={objetivoProyecto}
          onChange={(evento) => setObjetivoProyecto(evento.target.value)}
        />

        <h2>Rutas propuestas</h2>
        {rutas.map((ruta, indice) => (
          <div key={indice} style={{ display: "flex", gap: "0.5rem" }}>
            <input
              placeholder="Provincia"
              value={ruta.provincia}
              onChange={(evento) =>
                setRutas((filas) =>
                  filas.map((fila, i) => (i === indice ? { ...fila, provincia: evento.target.value } : fila)),
                )
              }
            />
            <input
              placeholder="Ciudad"
              value={ruta.ciudad ?? ""}
              onChange={(evento) =>
                setRutas((filas) =>
                  filas.map((fila, i) => (i === indice ? { ...fila, ciudad: evento.target.value } : fila)),
                )
              }
            />
            <input
              type="number"
              min="0"
              placeholder="Postes nuevos"
              value={ruta.postes_nuevos}
              onChange={(evento) =>
                setRutas((filas) =>
                  filas.map((fila, i) =>
                    i === indice ? { ...fila, postes_nuevos: Number(evento.target.value) } : fila,
                  ),
                )
              }
            />
            <button type="button" onClick={() => setRutas((filas) => filas.filter((_, i) => i !== indice))}>
              Quitar
            </button>
          </div>
        ))}
        <button type="button" onClick={() => setRutas((filas) => [...filas, rutaVacia()])}>
          Agregar ruta
        </button>

        <h2>Contactos</h2>
        {contactos.map((contacto, indice) => (
          <div key={indice} style={{ display: "flex", gap: "0.5rem" }}>
            <input
              placeholder="Rol (ej. Técnico)"
              value={contacto.rol_contacto}
              onChange={(evento) =>
                setContactos((filas) =>
                  filas.map((fila, i) => (i === indice ? { ...fila, rol_contacto: evento.target.value } : fila)),
                )
              }
            />
            <input
              placeholder="Nombre"
              value={contacto.nombre}
              onChange={(evento) =>
                setContactos((filas) =>
                  filas.map((fila, i) => (i === indice ? { ...fila, nombre: evento.target.value } : fila)),
                )
              }
            />
            <input
              placeholder="Teléfono"
              value={contacto.telefono ?? ""}
              onChange={(evento) =>
                setContactos((filas) =>
                  filas.map((fila, i) => (i === indice ? { ...fila, telefono: evento.target.value } : fila)),
                )
              }
            />
            <input
              placeholder="Correo"
              value={contacto.correo ?? ""}
              onChange={(evento) =>
                setContactos((filas) =>
                  filas.map((fila, i) => (i === indice ? { ...fila, correo: evento.target.value } : fila)),
                )
              }
            />
            <button
              type="button"
              onClick={() => setContactos((filas) => filas.filter((_, i) => i !== indice))}
            >
              Quitar
            </button>
          </div>
        ))}
        <button type="button" onClick={() => setContactos((filas) => [...filas, contactoVacio()])}>
          Agregar contacto
        </button>

        {error && <p className="mensaje-error">{error}</p>}

        <button type="submit" disabled={mutacion.isPending}>
          {mutacion.isPending ? "Guardando…" : "Guardar como borrador"}
        </button>
      </form>
    </div>
  );
}
