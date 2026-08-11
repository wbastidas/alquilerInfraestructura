import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { crearAlquilerAnual } from "@/api/alquileresAnuales";
import { listarOperadoras } from "@/api/operadoras";
import { listarUnidadesNegocio } from "@/api/unidadesNegocio";
import type { PostePorZonaCrear, TipoZona } from "@/api/tipos";

const OPCIONES_TIPO_ZONA: TipoZona[] = ["CAPITAL_PROVINCIAL", "CABECERA_CANTONAL", "OTRO_SECTOR"];

function filaVacia(): PostePorZonaCrear {
  return { provincia: "", canton: "", parroquia: "", tipo_zona: "CAPITAL_PROVINCIAL", cantidad_postes: 0 };
}

export function FormularioAlquilerAnual() {
  const navegar = useNavigate();
  const queryClient = useQueryClient();
  const { data: operadoras } = useQuery({ queryKey: ["operadoras"], queryFn: listarOperadoras });
  const { data: unidadesNegocio } = useQuery({
    queryKey: ["unidades-negocio"],
    queryFn: listarUnidadesNegocio,
  });

  const [cableOperadoraId, setCableOperadoraId] = useState<number | "">("");
  const [unidadNegocioId, setUnidadNegocioId] = useState<number | "">("");
  const [anio, setAnio] = useState(new Date().getFullYear());
  const [postesSig, setPostesSig] = useState(0);
  const [postesFisicos, setPostesFisicos] = useState(0);
  const [postesPorZona, setPostesPorZona] = useState<PostePorZonaCrear[]>([filaVacia()]);
  const [error, setError] = useState<string | null>(null);

  const mutacion = useMutation({
    mutationFn: crearAlquilerAnual,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["alquileres-anuales"] });
      navegar("/alquileres-anuales");
    },
    onError: () => setError("No se pudo crear el alquiler anual. Verifique los datos."),
  });

  function actualizarFila(indice: number, cambios: Partial<PostePorZonaCrear>) {
    setPostesPorZona((filas) =>
      filas.map((fila, i) => (i === indice ? { ...fila, ...cambios } : fila)),
    );
  }

  function agregarFila() {
    setPostesPorZona((filas) => [...filas, filaVacia()]);
  }

  function quitarFila(indice: number) {
    setPostesPorZona((filas) => filas.filter((_, i) => i !== indice));
  }

  function manejarEnvio(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    if (cableOperadoraId === "" || unidadNegocioId === "") {
      setError("Seleccione operadora y unidad de negocio.");
      return;
    }
    mutacion.mutate({
      cable_operadora_id: cableOperadoraId,
      unidad_negocio_id: unidadNegocioId,
      anio,
      postes_sig: postesSig,
      postes_fisicos: postesFisicos,
      postes_por_zona: postesPorZona.filter((fila) => fila.provincia && fila.canton),
    });
  }

  return (
    <div>
      <h1>Nuevo alquiler anual</h1>
      <form className="formulario" onSubmit={manejarEnvio} style={{ maxWidth: "720px" }}>
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

        <label htmlFor="anio">Año</label>
        <input
          id="anio"
          type="number"
          value={anio}
          onChange={(evento) => setAnio(Number(evento.target.value))}
          required
        />

        <label htmlFor="postes_sig">Postes según SIG</label>
        <input
          id="postes_sig"
          type="number"
          min="0"
          value={postesSig}
          onChange={(evento) => setPostesSig(Number(evento.target.value))}
        />

        <label htmlFor="postes_fisicos">Postes físicos verificados</label>
        <input
          id="postes_fisicos"
          type="number"
          min="0"
          value={postesFisicos}
          onChange={(evento) => setPostesFisicos(Number(evento.target.value))}
        />

        <h2>Postes por zona</h2>
        {postesPorZona.map((fila, indice) => (
          <div key={indice} style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <input
              placeholder="Provincia"
              value={fila.provincia}
              onChange={(evento) => actualizarFila(indice, { provincia: evento.target.value })}
            />
            <input
              placeholder="Cantón"
              value={fila.canton}
              onChange={(evento) => actualizarFila(indice, { canton: evento.target.value })}
            />
            <input
              placeholder="Parroquia"
              value={fila.parroquia ?? ""}
              onChange={(evento) => actualizarFila(indice, { parroquia: evento.target.value })}
            />
            <select
              value={fila.tipo_zona}
              onChange={(evento) =>
                actualizarFila(indice, { tipo_zona: evento.target.value as TipoZona })
              }
            >
              {OPCIONES_TIPO_ZONA.map((opcion) => (
                <option key={opcion} value={opcion}>
                  {opcion}
                </option>
              ))}
            </select>
            <input
              type="number"
              min="0"
              placeholder="Postes"
              value={fila.cantidad_postes}
              onChange={(evento) =>
                actualizarFila(indice, { cantidad_postes: Number(evento.target.value) })
              }
            />
            <button type="button" onClick={() => quitarFila(indice)}>
              Quitar
            </button>
          </div>
        ))}
        <button type="button" onClick={agregarFila}>
          Agregar zona
        </button>

        {error && <p className="mensaje-error">{error}</p>}

        <button type="submit" disabled={mutacion.isPending}>
          {mutacion.isPending ? "Guardando…" : "Guardar"}
        </button>
      </form>
    </div>
  );
}
