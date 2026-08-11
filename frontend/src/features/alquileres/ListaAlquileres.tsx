import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listarAlquileresAnuales } from "@/api/alquileresAnuales";
import { listarOperadoras } from "@/api/operadoras";
import { useAuth } from "@/auth/AuthContext";

export function ListaAlquileres() {
  const { usuario } = useAuth();
  const esSoloLectura = usuario?.rol === "MATRIZ_CONSULTA";
  const { data, isLoading, error } = useQuery({
    queryKey: ["alquileres-anuales"],
    queryFn: listarAlquileresAnuales,
  });
  const { data: operadoras } = useQuery({ queryKey: ["operadoras"], queryFn: listarOperadoras });

  const nombreOperadora = (id: number) =>
    operadoras?.find((operadora) => operadora.id === id)?.nombre_empresa ?? id;

  if (isLoading) return <p>Cargando alquileres anuales…</p>;
  if (error) return <p className="mensaje-error">No se pudo cargar el listado de alquileres anuales.</p>;

  return (
    <div>
      <div className="encabezado-seccion">
        <h1>Alquileres anuales</h1>
        {!esSoloLectura && (
          <Link to="/alquileres-anuales/nuevo" className="boton-primario">
            Nuevo alquiler anual
          </Link>
        )}
      </div>
      <table className="tabla">
        <thead>
          <tr>
            <th>Operadora</th>
            <th>Año</th>
            <th>Postes SIG</th>
            <th>Postes físicos</th>
            <th>Facturado</th>
            <th>Recaudado</th>
            <th>Pendiente</th>
            <th>Estado de pago</th>
          </tr>
        </thead>
        <tbody>
          {data?.map((alquiler) => (
            <tr key={alquiler.id}>
              <td>{nombreOperadora(alquiler.cable_operadora_id)}</td>
              <td>{alquiler.anio}</td>
              <td>
                {alquiler.postes_sig}
                {alquiler.postes_sig !== alquiler.postes_fisicos && (
                  <span className="mensaje-error" title="Discrepancia SIG vs. físico">
                    {" "}
                    ⚠
                  </span>
                )}
              </td>
              <td>{alquiler.postes_fisicos}</td>
              <td>{alquiler.monto_facturado}</td>
              <td>{alquiler.monto_recaudado}</td>
              <td>{alquiler.monto_pendiente_recaudar}</td>
              <td>{alquiler.estado_pago}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {data?.length === 0 && <p>No hay alquileres anuales registrados en su ámbito.</p>}
    </div>
  );
}
