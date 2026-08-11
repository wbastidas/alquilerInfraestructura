import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { reporteMorosidad } from "@/api/facturas";
import { listarOperadoras } from "@/api/operadoras";

export function ReporteMorosidad() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["facturas", "morosidad"],
    queryFn: reporteMorosidad,
  });
  const { data: operadoras } = useQuery({ queryKey: ["operadoras"], queryFn: listarOperadoras });

  const nombreOperadora = (id: number) =>
    operadoras?.find((operadora) => operadora.id === id)?.nombre_empresa ?? id;

  if (isLoading) return <p>Cargando reporte de morosidad…</p>;
  if (error) return <p className="mensaje-error">No se pudo cargar el reporte de morosidad.</p>;

  return (
    <div>
      <h1>Reporte de morosidad</h1>
      <table className="tabla">
        <thead>
          <tr>
            <th>N.° factura</th>
            <th>Operadora</th>
            <th>Vencimiento</th>
            <th>Días de mora</th>
            <th>Saldo pendiente</th>
            <th>Interés por mora</th>
          </tr>
        </thead>
        <tbody>
          {data?.map((item) => (
            <tr key={item.factura_id}>
              <td>
                <Link to={`/facturas/${item.factura_id}`}>{item.numero_factura}</Link>
              </td>
              <td>{nombreOperadora(item.cable_operadora_id)}</td>
              <td>{item.fecha_vencimiento}</td>
              <td>{item.dias_mora}</td>
              <td>{item.saldo_pendiente}</td>
              <td>{item.interes_mora}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {data?.length === 0 && <p>No hay facturas en mora.</p>}
    </div>
  );
}
