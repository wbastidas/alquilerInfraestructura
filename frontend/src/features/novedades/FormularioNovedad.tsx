import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { listarContratos } from "@/api/contratos";
import { crearNovedad } from "@/api/novedades";
import { listarOperadoras } from "@/api/operadoras";
import { listarUnidadesNegocio } from "@/api/unidadesNegocio";
import type { TipoNovedad } from "@/api/tipos";

const OPCIONES_TIPO: TipoNovedad[] = ["INSPECCION_PROGRAMADA", "DANO_REPORTADO", "MANTENIMIENTO"];

export function FormularioNovedad() {
  const navegar = useNavigate();
  const queryClient = useQueryClient();

  const { data: operadoras } = useQuery({ queryKey: ["operadoras"], queryFn: listarOperadoras });
  const { data: contratos } = useQuery({ queryKey: ["contratos"], queryFn: listarContratos });
  const { data: unidadesNegocio } = useQuery({
    queryKey: ["unidades-negocio"],
    queryFn: listarUnidadesNegocio,
  });

  const [cableOperadoraId, setCableOperadoraId] = useState<number | "">("");
  const [contratoId, setContratoId] = useState<number | "">("");
  const [unidadNegocioId, setUnidadNegocioId] = useState<number | "">("");
  const [tipo, setTipo] = useState<TipoNovedad>("INSPECCION_PROGRAMADA");
  const [descripcion, setDescripcion] = useState("");
  const [fechaProgramada, setFechaProgramada] = useState("");
  const [latitud, setLatitud] = useState("");
  const [longitud, setLongitud] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mutacion = useMutation({
    mutationFn: crearNovedad,
    onSuccess: (novedad) => {
      void queryClient.invalidateQueries({ queryKey: ["novedades"] });
      navegar(`/novedades/${novedad.id}`);
    },
    onError: () => setError("No se pudo crear la novedad. Verifique los datos."),
  });

  function manejarEnvio(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    if (cableOperadoraId === "" || unidadNegocioId === "") {
      setError("Seleccione operadora y unidad de negocio.");
      return;
    }
    mutacion.mutate({
      cable_operadora_id: cableOperadoraId,
      contrato_id: contratoId === "" ? null : contratoId,
      unidad_negocio_id: unidadNegocioId,
      tipo,
      descripcion: descripcion || null,
      fecha_programada: fechaProgramada || null,
      latitud: latitud || null,
      longitud: longitud || null,
    });
  }

  return (
    <div>
      <h1>Nueva novedad</h1>
      <form className="formulario" onSubmit={manejarEnvio} style={{ maxWidth: "480px" }}>
        <label htmlFor="tipo">Tipo</label>
        <select id="tipo" value={tipo} onChange={(evento) => setTipo(evento.target.value as TipoNovedad)}>
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

        <label htmlFor="contrato">Contrato (opcional)</label>
        <select
          id="contrato"
          value={contratoId}
          onChange={(evento) => setContratoId(evento.target.value === "" ? "" : Number(evento.target.value))}
        >
          <option value="">Sin contrato asociado</option>
          {contratos
            ?.filter((contrato) => contrato.cable_operadora_id === cableOperadoraId)
            .map((contrato) => (
              <option key={contrato.id} value={contrato.id}>
                {contrato.numero_contrato}
              </option>
            ))}
        </select>

        <label htmlFor="unidad_negocio">Unidad de Negocio</label>
        <select
          id="unidad_negocio"
          value={unidadNegocioId}
          onChange={(evento) => setUnidadNegocioId(Number(evento.target.value))}
          required
        >
          <option value="" disabled>
            Seleccione…
          </option>
          {unidadesNegocio?.map((un) => (
            <option key={un.id} value={un.id}>
              {un.nombre}
            </option>
          ))}
        </select>

        <label htmlFor="descripcion">Descripción</label>
        <textarea
          id="descripcion"
          value={descripcion}
          onChange={(evento) => setDescripcion(evento.target.value)}
        />

        <label htmlFor="fecha_programada">Fecha programada</label>
        <input
          id="fecha_programada"
          type="date"
          value={fechaProgramada}
          onChange={(evento) => setFechaProgramada(evento.target.value)}
        />

        <label htmlFor="latitud">Latitud</label>
        <input id="latitud" value={latitud} onChange={(evento) => setLatitud(evento.target.value)} />

        <label htmlFor="longitud">Longitud</label>
        <input id="longitud" value={longitud} onChange={(evento) => setLongitud(evento.target.value)} />

        {error && <p className="mensaje-error">{error}</p>}

        <button type="submit" disabled={mutacion.isPending}>
          {mutacion.isPending ? "Guardando…" : "Guardar"}
        </button>
      </form>
    </div>
  );
}
