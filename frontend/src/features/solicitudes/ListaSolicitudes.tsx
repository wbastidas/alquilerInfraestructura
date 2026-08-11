import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listarOperadoras } from "@/api/operadoras";
import { listarSolicitudes } from "@/api/solicitudes";
import { useAuth } from "@/auth/AuthContext";

export function ListaSolicitudes() {
  const { usuario } = useAuth();
  const esSoloLectura = usuario?.rol === "MATRIZ_CONSULTA";
  const { data, isLoading, error } = useQuery({
    queryKey: ["solicitudes"],
    queryFn: listarSolicitudes,
  });
  const { data: operadoras } = useQuery({ queryKey: ["operadoras"], queryFn: listarOperadoras });

  const nombreOperadora = (id: number) =>
    operadoras?.find((operadora) => operadora.id === id)?.nombre_empresa ?? id;

  if (isLoading) return <p>Cargando solicitudes…</p>;
  if (error) return <p className="mensaje-error">No se pudo cargar el listado de solicitudes.</p>;

  return (
    <div>
      <div className="encabezado-seccion">
        <h1>Solicitudes</h1>
        {!esSoloLectura && (
          <Link to="/solicitudes/nueva" className="boton-primario">
            Nueva solicitud
          </Link>
        )}
      </div>
      <table className="tabla">
        <thead>
          <tr>
            <th>N.° referencia</th>
            <th>Tipo</th>
            <th>Operadora</th>
            <th>Cobertura</th>
            <th>Dirigida a</th>
            <th>Estado</th>
            <th>Fecha</th>
          </tr>
        </thead>
        <tbody>
          {data?.map((solicitud) => (
            <tr key={solicitud.id}>
              <td>
                <Link to={`/solicitudes/${solicitud.id}`}>{solicitud.numero_referencia}</Link>
              </td>
              <td>{solicitud.tipo}</td>
              <td>{nombreOperadora(solicitud.cable_operadora_id)}</td>
              <td>{solicitud.cobertura}</td>
              <td>{solicitud.dirigida_a}</td>
              <td>{solicitud.estado}</td>
              <td>{solicitud.fecha_creacion}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {data?.length === 0 && <p>No hay solicitudes registradas en su ámbito.</p>}
    </div>
  );
}
