import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { crearCatalogoCanon, listarCatalogoCanon } from "@/api/catalogoCanon";
import type { TipoZona } from "@/api/tipos";
import { useAuth } from "@/auth/AuthContext";

const OPCIONES_TIPO_ZONA: TipoZona[] = ["CAPITAL_PROVINCIAL", "CABECERA_CANTONAL", "OTRO_SECTOR"];

export function ListaCanon() {
  const { usuario } = useAuth();
  const esSuperadmin = usuario?.rol === "SUPERADMIN";
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["catalogo-canon"],
    queryFn: listarCatalogoCanon,
  });

  const [tipoZona, setTipoZona] = useState<TipoZona>("CAPITAL_PROVINCIAL");
  const [valor, setValor] = useState("");
  const [vigenteDesde, setVigenteDesde] = useState("");
  const [referenciaNormativa, setReferenciaNormativa] = useState("");
  const [errorFormulario, setErrorFormulario] = useState<string | null>(null);

  const mutacion = useMutation({
    mutationFn: crearCatalogoCanon,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["catalogo-canon"] });
      setValor("");
      setVigenteDesde("");
      setReferenciaNormativa("");
    },
    onError: () => setErrorFormulario("No se pudo crear el valor de canon. Verifique los datos."),
  });

  function manejarEnvio(evento: FormEvent) {
    evento.preventDefault();
    setErrorFormulario(null);
    mutacion.mutate({
      tipo_zona: tipoZona,
      valor,
      vigente_desde: vigenteDesde,
      referencia_normativa: referenciaNormativa || null,
    });
  }

  if (isLoading) return <p>Cargando catálogo de canon…</p>;
  if (error) return <p className="mensaje-error">No se pudo cargar el catálogo de canon.</p>;

  return (
    <div>
      <h1>Catálogo de canon</h1>
      <table className="tabla">
        <thead>
          <tr>
            <th>Tipo de zona</th>
            <th>Valor</th>
            <th>Vigente desde</th>
            <th>Vigente hasta</th>
            <th>Referencia normativa</th>
          </tr>
        </thead>
        <tbody>
          {data?.map((item) => (
            <tr key={item.id}>
              <td>{item.tipo_zona}</td>
              <td>{item.valor}</td>
              <td>{item.vigente_desde}</td>
              <td>{item.vigente_hasta ?? "—"}</td>
              <td>{item.referencia_normativa ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {data?.length === 0 && <p>No hay valores de canon registrados.</p>}

      {esSuperadmin && (
        <>
          <h2>Nuevo valor de canon</h2>
          <form className="formulario" onSubmit={manejarEnvio}>
            <label htmlFor="tipo_zona">Tipo de zona</label>
            <select
              id="tipo_zona"
              value={tipoZona}
              onChange={(evento) => setTipoZona(evento.target.value as TipoZona)}
            >
              {OPCIONES_TIPO_ZONA.map((opcion) => (
                <option key={opcion} value={opcion}>
                  {opcion}
                </option>
              ))}
            </select>

            <label htmlFor="valor">Valor (USD)</label>
            <input
              id="valor"
              type="number"
              step="0.01"
              min="0"
              value={valor}
              onChange={(evento) => setValor(evento.target.value)}
              required
            />

            <label htmlFor="vigente_desde">Vigente desde</label>
            <input
              id="vigente_desde"
              type="date"
              value={vigenteDesde}
              onChange={(evento) => setVigenteDesde(evento.target.value)}
              required
            />

            <label htmlFor="referencia_normativa">Referencia normativa</label>
            <input
              id="referencia_normativa"
              value={referenciaNormativa}
              onChange={(evento) => setReferenciaNormativa(evento.target.value)}
            />

            {errorFormulario && <p className="mensaje-error">{errorFormulario}</p>}

            <button type="submit" disabled={mutacion.isPending}>
              {mutacion.isPending ? "Guardando…" : "Guardar"}
            </button>
          </form>
        </>
      )}
    </div>
  );
}
