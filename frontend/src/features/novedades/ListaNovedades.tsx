import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listarNovedades } from "@/api/novedades";
import { listarOperadoras } from "@/api/operadoras";
import { useAuth } from "@/auth/AuthContext";

export function ListaNovedades() {
  const { usuario } = useAuth();
  const esProveedor = usuario?.rol === "PROVEEDOR";
  const { data, isLoading, error } = useQuery({
    queryKey: ["novedades"],
    queryFn: listarNovedades,
  });
  const { data: operadoras } = useQuery({ queryKey: ["operadoras"], queryFn: listarOperadoras });

  const nombreOperadora = (id: number) =>
    operadoras?.find((operadora) => operadora.id === id)?.nombre_empresa ?? id;

  if (isLoading) return <p>Cargando novedades…</p>;
  if (error) return <p className="mensaje-error">No se pudo cargar el listado de novedades.</p>;

  return (
    <div>
      <div className="encabezado-seccion">
        <h1>Novedades</h1>
        {!esProveedor && (
          <Link to="/novedades/nueva" className="boton-primario">
            Nueva novedad
          </Link>
        )}
      </div>
      <table className="tabla">
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Operadora</th>
            <th>Fecha programada</th>
            <th>Fecha ejecución</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {data?.map((novedad) => (
            <tr key={novedad.id}>
              <td>
                <Link to={`/novedades/${novedad.id}`}>{novedad.tipo}</Link>
              </td>
              <td>{nombreOperadora(novedad.cable_operadora_id)}</td>
              <td>{novedad.fecha_programada ?? "—"}</td>
              <td>{novedad.fecha_ejecucion ?? "—"}</td>
              <td>{novedad.estado}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {data?.length === 0 && <p>No hay novedades registradas en su ámbito.</p>}
    </div>
  );
}
