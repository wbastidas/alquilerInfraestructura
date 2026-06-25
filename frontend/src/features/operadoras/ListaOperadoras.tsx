import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listarOperadoras } from "@/api/operadoras";
import { useAuth } from "@/auth/AuthContext";

export function ListaOperadoras() {
  const { usuario } = useAuth();
  const { data, isLoading, error } = useQuery({
    queryKey: ["operadoras"],
    queryFn: listarOperadoras,
  });

  const puedeEscribir = usuario?.rol !== "MATRIZ_CONSULTA";

  if (isLoading) return <p>Cargando operadoras…</p>;
  if (error) return <p className="mensaje-error">No se pudo cargar el listado de operadoras.</p>;

  return (
    <div>
      <div className="encabezado-seccion">
        <h1>Operadoras de cable</h1>
        {puedeEscribir && (
          <Link to="/operadoras/nueva" className="boton-primario">
            Nueva operadora
          </Link>
        )}
      </div>
      <table className="tabla">
        <thead>
          <tr>
            <th>N.° registro</th>
            <th>Empresa</th>
            <th>RUC</th>
            <th>Cobertura</th>
            <th>Estado del contrato</th>
          </tr>
        </thead>
        <tbody>
          {data?.map((operadora) => (
            <tr key={operadora.id}>
              <td>{operadora.numero_registro}</td>
              <td>{operadora.nombre_empresa}</td>
              <td>{operadora.ruc ?? "—"}</td>
              <td>{operadora.cobertura_geografica}</td>
              <td>{operadora.estado_contrato}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {data?.length === 0 && <p>No hay operadoras registradas en su ámbito.</p>}
    </div>
  );
}
