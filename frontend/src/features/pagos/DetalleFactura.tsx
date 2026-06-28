import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { conciliarPago, obtenerFactura, registrarPago } from "@/api/facturas";
import type { MetodoPago, TipoPago } from "@/api/tipos";
import { useAuth } from "@/auth/AuthContext";

const OPCIONES_TIPO_PAGO: TipoPago[] = ["PARCIAL", "TOTAL"];
const OPCIONES_METODO_PAGO: MetodoPago[] = [
  "TRANSFERENCIA",
  "DEPOSITO",
  "CHEQUE",
  "TARJETA",
  "VENTANILLA",
  "PASARELA",
];

export function DetalleFactura() {
  const { id } = useParams<{ id: string }>();
  const facturaId = Number(id);
  const { usuario } = useAuth();
  const esProveedor = usuario?.rol === "PROVEEDOR";
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const [monto, setMonto] = useState("");
  const [tipo, setTipo] = useState<TipoPago>("PARCIAL");
  const [metodo, setMetodo] = useState<MetodoPago>("TRANSFERENCIA");
  const [referenciaTransaccion, setReferenciaTransaccion] = useState("");
  const [fechaPago, setFechaPago] = useState("");

  const { data: factura } = useQuery({
    queryKey: ["facturas", facturaId],
    queryFn: () => obtenerFactura(facturaId),
  });

  function invalidar() {
    void queryClient.invalidateQueries({ queryKey: ["facturas", facturaId] });
    void queryClient.invalidateQueries({ queryKey: ["facturas"] });
  }

  const mutacionPago = useMutation({
    mutationFn: () =>
      registrarPago({
        factura_id: facturaId,
        monto,
        tipo,
        metodo,
        referencia_transaccion: referenciaTransaccion || null,
        fecha_pago: fechaPago,
      }),
    onSuccess: () => {
      setMonto("");
      setReferenciaTransaccion("");
      setFechaPago("");
      invalidar();
    },
    onError: () => setError("No se pudo registrar el pago. Verifique los datos."),
  });

  const mutacionConciliar = useMutation({
    mutationFn: (pagoId: number) => conciliarPago(pagoId),
    onSuccess: invalidar,
    onError: () => setError("No se pudo conciliar el pago."),
  });

  function manejarRegistrarPago(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    mutacionPago.mutate();
  }

  if (!factura) return <p>Cargando factura…</p>;

  const totalPagado = factura.pagos.reduce((suma, pago) => suma + Number(pago.monto), 0);
  const saldoPendiente = Number(factura.total) - totalPagado;
  const puedeRegistrarPago =
    !esProveedor && factura.estado !== "ANULADA" && factura.estado !== "PAGADA";

  return (
    <div>
      <div className="encabezado-seccion">
        <h1>Factura {factura.numero_factura}</h1>
        <span>{factura.estado}</span>
      </div>

      <table className="tabla">
        <tbody>
          <tr>
            <td>Fecha de emisión</td>
            <td>{factura.fecha_emision}</td>
          </tr>
          <tr>
            <td>Fecha de vencimiento</td>
            <td>{factura.fecha_vencimiento}</td>
          </tr>
          <tr>
            <td>Monto</td>
            <td>{factura.monto}</td>
          </tr>
          <tr>
            <td>IVA</td>
            <td>{factura.iva}</td>
          </tr>
          <tr>
            <td>Total</td>
            <td>{factura.total}</td>
          </tr>
          <tr>
            <td>Saldo pendiente</td>
            <td>{saldoPendiente.toFixed(2)}</td>
          </tr>
        </tbody>
      </table>

      <h2>Pagos registrados</h2>
      <table className="tabla">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Monto</th>
            <th>Tipo</th>
            <th>Método</th>
            <th>Conciliado</th>
            <th>Acción</th>
          </tr>
        </thead>
        <tbody>
          {factura.pagos.map((pago) => (
            <tr key={pago.id}>
              <td>{pago.fecha_pago}</td>
              <td>{pago.monto}</td>
              <td>{pago.tipo}</td>
              <td>{pago.metodo}</td>
              <td>{pago.conciliado ? "Sí" : "No"}</td>
              <td>
                {!esProveedor && !pago.conciliado && (
                  <button type="button" onClick={() => mutacionConciliar.mutate(pago.id)}>
                    Conciliar
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {factura.pagos.length === 0 && <p>Aún no se han registrado pagos para esta factura.</p>}

      {error && <p className="mensaje-error">{error}</p>}

      {puedeRegistrarPago && (
        <form className="formulario" onSubmit={manejarRegistrarPago} style={{ maxWidth: "480px", marginTop: "1rem" }}>
          <h2>Registrar pago</h2>
          <label htmlFor="monto_pago">Monto</label>
          <input
            id="monto_pago"
            type="number"
            step="0.01"
            min="0"
            value={monto}
            onChange={(evento) => setMonto(evento.target.value)}
            required
          />

          <label htmlFor="tipo_pago">Tipo</label>
          <select id="tipo_pago" value={tipo} onChange={(evento) => setTipo(evento.target.value as TipoPago)}>
            {OPCIONES_TIPO_PAGO.map((opcion) => (
              <option key={opcion} value={opcion}>
                {opcion}
              </option>
            ))}
          </select>

          <label htmlFor="metodo_pago">Método</label>
          <select
            id="metodo_pago"
            value={metodo}
            onChange={(evento) => setMetodo(evento.target.value as MetodoPago)}
          >
            {OPCIONES_METODO_PAGO.map((opcion) => (
              <option key={opcion} value={opcion}>
                {opcion}
              </option>
            ))}
          </select>

          <label htmlFor="referencia_transaccion">Referencia de transacción</label>
          <input
            id="referencia_transaccion"
            value={referenciaTransaccion}
            onChange={(evento) => setReferenciaTransaccion(evento.target.value)}
          />

          <label htmlFor="fecha_pago">Fecha de pago</label>
          <input
            id="fecha_pago"
            type="date"
            value={fechaPago}
            onChange={(evento) => setFechaPago(evento.target.value)}
            required
          />

          <button type="submit" disabled={mutacionPago.isPending}>
            {mutacionPago.isPending ? "Guardando…" : "Registrar pago"}
          </button>
        </form>
      )}
    </div>
  );
}
