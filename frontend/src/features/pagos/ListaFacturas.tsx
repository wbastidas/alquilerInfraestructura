import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listarFacturas } from "@/api/facturas";
import { listarOperadoras } from "@/api/operadoras";
import { useAuth } from "@/auth/AuthContext";

export function ListaFacturas() {
  const { usuario } = useAuth();
  const esProveedor = usuario?.rol === "PROVEEDOR";
  const { data, isLoading, error } = useQuery({
    queryKey: ["facturas"],
    queryFn: listarFacturas,
  });
  const { data: operadoras } = useQuery({ queryKey: ["operadoras"], queryFn: listarOperadoras });

  const nombreOperadora = (id: number) =>
    operadoras?.find((operadora) => operadora.id === id)?.nombre_empresa ?? id;

  if (isLoading) return <p>Cargando facturas…</p>;
  if (error) return <p className="mensaje-error">No se pudo cargar el listado de facturas.</p>;

  return (
    <div>
      <div className="encabezado-seccion">
        <h1>Facturas</h1>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <Link to="/facturas/morosidad">Reporte de morosidad</Link>
          {!esProveedor && (
            <Link to="/facturas/nueva" className="boton-primario">
              Nueva factura
            </Link>
          )}
        </div>
      </div>
      <table className="tabla">
        <thead>
          <tr>
            <th>N.° factura</th>
            <th>Operadora</th>
            <th>Emisión</th>
            <th>Vencimiento</th>
            <th>Monto</th>
            <th>IVA</th>
            <th>Total</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {data?.map((factura) => (
            <tr key={factura.id}>
              <td>
                <Link to={`/facturas/${factura.id}`}>{factura.numero_factura}</Link>
              </td>
              <td>{nombreOperadora(factura.cable_operadora_id)}</td>
              <td>{factura.fecha_emision}</td>
              <td>{factura.fecha_vencimiento}</td>
              <td>{factura.monto}</td>
              <td>{factura.iva}</td>
              <td>{factura.total}</td>
              <td>{factura.estado}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {data?.length === 0 && <p>No hay facturas registradas en su ámbito.</p>}
    </div>
  );
}
