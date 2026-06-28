import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { listarAlertas, marcarAlertaLeida } from "@/api/alertas";
import type { SeveridadAlerta } from "@/api/tipos";

const ETIQUETAS_SEVERIDAD: Record<SeveridadAlerta, string> = {
  INFO: "Informativa",
  ADVERTENCIA: "Advertencia",
  CRITICA: "Crítica",
};

export function ListaAlertas() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["alertas"],
    queryFn: listarAlertas,
  });

  const mutacion = useMutation({
    mutationFn: marcarAlertaLeida,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["alertas"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard-consolidado"] });
    },
  });

  if (isLoading) return <p>Cargando alertas…</p>;
  if (error) return <p className="mensaje-error">No se pudo cargar el listado de alertas.</p>;

  return (
    <div>
      <h1>Alertas</h1>
      <table className="tabla">
        <thead>
          <tr>
            <th>Severidad</th>
            <th>Tipo</th>
            <th>Mensaje</th>
            <th>Generada</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data?.map((alerta) => (
            <tr key={alerta.id} className={alerta.leida ? undefined : "fila-no-leida"}>
              <td>
                <span className={`insignia-severidad insignia-severidad-${alerta.severidad.toLowerCase()}`}>
                  {ETIQUETAS_SEVERIDAD[alerta.severidad]}
                </span>
              </td>
              <td>{alerta.tipo}</td>
              <td>{alerta.mensaje}</td>
              <td>{new Date(alerta.fecha_generacion).toLocaleString()}</td>
              <td>{alerta.leida ? "Leída" : "No leída"}</td>
              <td>
                {!alerta.leida && (
                  <button
                    type="button"
                    onClick={() => mutacion.mutate(alerta.id)}
                    disabled={mutacion.isPending}
                  >
                    Marcar leída
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {data?.length === 0 && <p>No hay alertas registradas en su ámbito.</p>}
    </div>
  );
}
