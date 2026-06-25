import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { crearOperadora } from "@/api/operadoras";
import { listarUnidadesNegocio } from "@/api/unidadesNegocio";
import type { CoberturaGeografica } from "@/api/tipos";

const OPCIONES_COBERTURA: CoberturaGeografica[] = ["NACIONAL", "REGIONAL", "LOCAL"];

export function FormularioOperadora() {
  const navegar = useNavigate();
  const queryClient = useQueryClient();
  const { data: unidadesNegocio } = useQuery({
    queryKey: ["unidades-negocio"],
    queryFn: listarUnidadesNegocio,
  });

  const [numeroRegistro, setNumeroRegistro] = useState("");
  const [nombreEmpresa, setNombreEmpresa] = useState("");
  const [ruc, setRuc] = useState("");
  const [cobertura, setCobertura] = useState<CoberturaGeografica>("LOCAL");
  const [unidadNegocioId, setUnidadNegocioId] = useState<number | "">("");
  const [error, setError] = useState<string | null>(null);

  const mutacion = useMutation({
    mutationFn: crearOperadora,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["operadoras"] });
      navegar("/operadoras");
    },
    onError: () => setError("No se pudo crear la operadora. Verifique los datos."),
  });

  function manejarEnvio(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    if (unidadNegocioId === "") {
      setError("Seleccione una Unidad de Negocio.");
      return;
    }
    mutacion.mutate({
      numero_registro: numeroRegistro,
      nombre_empresa: nombreEmpresa,
      ruc: ruc || null,
      cobertura_geografica: cobertura,
      tipo_contrato: cobertura,
      unidad_negocio_id: unidadNegocioId,
    });
  }

  return (
    <div>
      <h1>Nueva operadora</h1>
      <form className="formulario" onSubmit={manejarEnvio}>
        <label htmlFor="numero_registro">N.° de registro</label>
        <input
          id="numero_registro"
          value={numeroRegistro}
          onChange={(evento) => setNumeroRegistro(evento.target.value)}
          required
        />

        <label htmlFor="nombre_empresa">Nombre de la empresa</label>
        <input
          id="nombre_empresa"
          value={nombreEmpresa}
          onChange={(evento) => setNombreEmpresa(evento.target.value)}
          required
        />

        <label htmlFor="ruc">RUC</label>
        <input id="ruc" value={ruc} onChange={(evento) => setRuc(evento.target.value)} />

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

        {error && <p className="mensaje-error">{error}</p>}

        <button type="submit" disabled={mutacion.isPending}>
          {mutacion.isPending ? "Guardando…" : "Guardar"}
        </button>
      </form>
    </div>
  );
}
