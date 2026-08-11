import { useQuery } from "@tanstack/react-query";

import { obtenerConsolidado } from "@/api/dashboard";

export function PaginaDashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-consolidado"],
    queryFn: () => obtenerConsolidado(),
  });

  if (isLoading) return <p>Cargando dashboard…</p>;
  if (error) return <p className="mensaje-error">No se pudo cargar el dashboard consolidado.</p>;
  if (!data) return null;

  return (
    <div>
      <h2>Consolidado {data.anio}</h2>
      <div className="rejilla-tarjetas">
        <article className="tarjeta-metrica">
          <span className="etiqueta-metrica">Operadoras</span>
          <span className="valor-metrica">{data.total_operadoras}</span>
        </article>
        <article className="tarjeta-metrica">
          <span className="etiqueta-metrica">Contratos vigentes</span>
          <span className="valor-metrica">{data.total_contratos_vigentes}</span>
        </article>
        <article className="tarjeta-metrica">
          <span className="etiqueta-metrica">Monto facturado</span>
          <span className="valor-metrica">${data.monto_facturado}</span>
        </article>
        <article className="tarjeta-metrica">
          <span className="etiqueta-metrica">Monto recaudado</span>
          <span className="valor-metrica">${data.monto_recaudado}</span>
        </article>
        <article className="tarjeta-metrica">
          <span className="etiqueta-metrica">Pendiente por recaudar</span>
          <span className="valor-metrica">${data.monto_pendiente_recaudar}</span>
        </article>
        <article className="tarjeta-metrica">
          <span className="etiqueta-metrica">Solicitudes pendientes</span>
          <span className="valor-metrica">{data.solicitudes_pendientes}</span>
        </article>
        <article className="tarjeta-metrica">
          <span className="etiqueta-metrica">Novedades abiertas</span>
          <span className="valor-metrica">{data.novedades_abiertas}</span>
        </article>
        <article className="tarjeta-metrica tarjeta-metrica-alerta">
          <span className="etiqueta-metrica">Facturas vencidas</span>
          <span className="valor-metrica">{data.facturas_vencidas}</span>
        </article>
        <article className="tarjeta-metrica tarjeta-metrica-alerta">
          <span className="etiqueta-metrica">Alertas no leídas</span>
          <span className="valor-metrica">{data.alertas_no_leidas}</span>
        </article>
      </div>
    </div>
  );
}
