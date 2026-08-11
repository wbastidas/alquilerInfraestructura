import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { listarAlquileresAnuales } from "@/api/alquileresAnuales";
import { listarContratos } from "@/api/contratos";
import { crearFactura } from "@/api/facturas";
import { listarOperadoras } from "@/api/operadoras";

export function FormularioFactura() {
  const navegar = useNavigate();
  const queryClient = useQueryClient();

  const { data: operadoras } = useQuery({ queryKey: ["operadoras"], queryFn: listarOperadoras });
  const { data: contratos } = useQuery({ queryKey: ["contratos"], queryFn: listarContratos });
  const { data: alquileres } = useQuery({
    queryKey: ["alquileres-anuales"],
    queryFn: listarAlquileresAnuales,
  });

  const [cableOperadoraId, setCableOperadoraId] = useState<number | "">("");
  const [contratoId, setContratoId] = useState<number | "">("");
  const [alquilerAnualId, setAlquilerAnualId] = useState<number | "">("");
  const [numeroFactura, setNumeroFactura] = useState("");
  const [fechaEmision, setFechaEmision] = useState("");
  const [fechaVencimiento, setFechaVencimiento] = useState("");
  const [monto, setMonto] = useState("");
  const [iva, setIva] = useState("0");
  const [error, setError] = useState<string | null>(null);

  const mutacion = useMutation({
    mutationFn: crearFactura,
    onSuccess: (factura) => {
      void queryClient.invalidateQueries({ queryKey: ["facturas"] });
      navegar(`/facturas/${factura.id}`);
    },
    onError: () => setError("No se pudo crear la factura. Verifique los datos."),
  });

  function manejarEnvio(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    if (cableOperadoraId === "" || contratoId === "" || alquilerAnualId === "") {
      setError("Seleccione operadora, contrato y alquiler anual.");
      return;
    }
    mutacion.mutate({
      cable_operadora_id: cableOperadoraId,
      contrato_id: contratoId,
      alquiler_anual_id: alquilerAnualId,
      numero_factura: numeroFactura,
      fecha_emision: fechaEmision,
      fecha_vencimiento: fechaVencimiento,
      monto,
      iva,
    });
  }

  return (
    <div>
      <h1>Nueva factura</h1>
      <form className="formulario" onSubmit={manejarEnvio} style={{ maxWidth: "480px" }}>
        <label htmlFor="cable_operadora">Operadora</label>
        <select
          id="cable_operadora"
          value={cableOperadoraId}
          onChange={(evento) => setCableOperadoraId(Number(evento.target.value))}
          required
        >
          <option value="" disabled>
            Seleccione…
          </option>
          {operadoras?.map((operadora) => (
            <option key={operadora.id} value={operadora.id}>
              {operadora.nombre_empresa}
            </option>
          ))}
        </select>

        <label htmlFor="contrato">Contrato</label>
        <select
          id="contrato"
          value={contratoId}
          onChange={(evento) => setContratoId(Number(evento.target.value))}
          required
        >
          <option value="" disabled>
            Seleccione…
          </option>
          {contratos
            ?.filter((contrato) => contrato.cable_operadora_id === cableOperadoraId)
            .map((contrato) => (
              <option key={contrato.id} value={contrato.id}>
                {contrato.numero_contrato}
              </option>
            ))}
        </select>

        <label htmlFor="alquiler_anual">Alquiler anual</label>
        <select
          id="alquiler_anual"
          value={alquilerAnualId}
          onChange={(evento) => setAlquilerAnualId(Number(evento.target.value))}
          required
        >
          <option value="" disabled>
            Seleccione…
          </option>
          {alquileres
            ?.filter((alquiler) => alquiler.cable_operadora_id === cableOperadoraId)
            .map((alquiler) => (
              <option key={alquiler.id} value={alquiler.id}>
                {alquiler.anio}
              </option>
            ))}
        </select>

        <label htmlFor="numero_factura">N.° de factura</label>
        <input
          id="numero_factura"
          value={numeroFactura}
          onChange={(evento) => setNumeroFactura(evento.target.value)}
          required
        />

        <label htmlFor="fecha_emision">Fecha de emisión</label>
        <input
          id="fecha_emision"
          type="date"
          value={fechaEmision}
          onChange={(evento) => setFechaEmision(evento.target.value)}
          required
        />

        <label htmlFor="fecha_vencimiento">Fecha de vencimiento</label>
        <input
          id="fecha_vencimiento"
          type="date"
          value={fechaVencimiento}
          onChange={(evento) => setFechaVencimiento(evento.target.value)}
          required
        />

        <label htmlFor="monto">Monto</label>
        <input
          id="monto"
          type="number"
          step="0.01"
          min="0"
          value={monto}
          onChange={(evento) => setMonto(evento.target.value)}
          required
        />

        <label htmlFor="iva">IVA</label>
        <input
          id="iva"
          type="number"
          step="0.01"
          min="0"
          value={iva}
          onChange={(evento) => setIva(evento.target.value)}
        />

        {error && <p className="mensaje-error">{error}</p>}

        <button type="submit" disabled={mutacion.isPending}>
          {mutacion.isPending ? "Guardando…" : "Guardar"}
        </button>
      </form>
    </div>
  );
}
