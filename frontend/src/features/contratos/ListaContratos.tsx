import { useQuery } from "@tanstack/react-query";

import { listarContratos } from "@/api/contratos";

export function ListaContratos() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["contratos"],
    queryFn: listarContratos,
  });

  if (isLoading) return <p>Cargando contratos…</p>;
  if (error) return <p className="mensaje-error">No se pudo cargar el listado de contratos.</p>;

  return (
    <div>
      <h1>Contratos</h1>
      <table className="tabla">
        <thead>
          <tr>
            <th>N.° contrato</th>
            <th>Cobertura</th>
            <th>Estado</th>
            <th>Postes</th>
            <th>Ductos (m)</th>
            <th>Canon anual</th>
          </tr>
        </thead>
        <tbody>
          {data?.map((contrato) => (
            <tr key={contrato.id}>
              <td>{contrato.numero_contrato}</td>
              <td>{contrato.tipo_cobertura}</td>
              <td>{contrato.estado}</td>
              <td>{contrato.total_postes}</td>
              <td>{contrato.total_ductos_m}</td>
              <td>{contrato.canon_anual_total}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {data?.length === 0 && <p>No hay contratos registrados en su ámbito.</p>}
    </div>
  );
}
