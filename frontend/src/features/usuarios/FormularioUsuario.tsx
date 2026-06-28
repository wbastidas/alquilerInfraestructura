import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { listarRoles } from "@/api/roles";
import type { TipoCuenta } from "@/api/tipos";
import { listarUnidadesNegocio } from "@/api/unidadesNegocio";
import { crearUsuario } from "@/api/usuarios";

const OPCIONES_TIPO_CUENTA: TipoCuenta[] = ["LOCAL", "AD", "PROVEEDOR"];

export function FormularioUsuario() {
  const navegar = useNavigate();
  const queryClient = useQueryClient();
  const { data: roles } = useQuery({ queryKey: ["roles"], queryFn: listarRoles });
  const { data: unidadesNegocio } = useQuery({
    queryKey: ["unidades-negocio"],
    queryFn: listarUnidadesNegocio,
  });

  const [username, setUsername] = useState("");
  const [nombreCompleto, setNombreCompleto] = useState("");
  const [correo, setCorreo] = useState("");
  const [tipoCuenta, setTipoCuenta] = useState<TipoCuenta>("LOCAL");
  const [password, setPassword] = useState("");
  const [rolId, setRolId] = useState<number | "">("");
  const [unidadNegocioId, setUnidadNegocioId] = useState<number | "">("");
  const [error, setError] = useState<string | null>(null);

  const mutacion = useMutation({
    mutationFn: crearUsuario,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["usuarios"] });
      navegar("/usuarios");
    },
    onError: () => setError("No se pudo crear el usuario. Verifique los datos."),
  });

  function manejarEnvio(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    if (rolId === "") {
      setError("Seleccione un rol.");
      return;
    }
    if (tipoCuenta !== "AD" && !password) {
      setError("La contraseña es obligatoria para cuentas LOCAL/PROVEEDOR.");
      return;
    }
    mutacion.mutate({
      username,
      nombre_completo: nombreCompleto,
      correo,
      tipo_cuenta: tipoCuenta,
      password: tipoCuenta === "AD" ? null : password,
      rol_id: rolId,
      unidad_negocio_id: unidadNegocioId === "" ? null : unidadNegocioId,
    });
  }

  return (
    <div>
      <h1>Nuevo usuario</h1>
      <form className="formulario" onSubmit={manejarEnvio}>
        <label htmlFor="username">Usuario</label>
        <input
          id="username"
          value={username}
          onChange={(evento) => setUsername(evento.target.value)}
          required
        />

        <label htmlFor="nombre_completo">Nombre completo</label>
        <input
          id="nombre_completo"
          value={nombreCompleto}
          onChange={(evento) => setNombreCompleto(evento.target.value)}
          required
        />

        <label htmlFor="correo">Correo</label>
        <input
          id="correo"
          type="email"
          value={correo}
          onChange={(evento) => setCorreo(evento.target.value)}
          required
        />

        <label htmlFor="tipo_cuenta">Tipo de cuenta</label>
        <select
          id="tipo_cuenta"
          value={tipoCuenta}
          onChange={(evento) => setTipoCuenta(evento.target.value as TipoCuenta)}
        >
          {OPCIONES_TIPO_CUENTA.map((opcion) => (
            <option key={opcion} value={opcion}>
              {opcion}
            </option>
          ))}
        </select>

        {tipoCuenta !== "AD" && (
          <>
            <label htmlFor="password">Contraseña</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(evento) => setPassword(evento.target.value)}
            />
          </>
        )}

        <label htmlFor="rol">Rol</label>
        <select
          id="rol"
          value={rolId}
          onChange={(evento) => setRolId(Number(evento.target.value))}
          required
        >
          <option value="" disabled>
            Seleccione…
          </option>
          {roles?.map((rol) => (
            <option key={rol.id} value={rol.id}>
              {rol.nombre}
            </option>
          ))}
        </select>

        <label htmlFor="unidad_negocio">Unidad de Negocio</label>
        <select
          id="unidad_negocio"
          value={unidadNegocioId}
          onChange={(evento) =>
            setUnidadNegocioId(evento.target.value === "" ? "" : Number(evento.target.value))
          }
        >
          <option value="">Ninguna (alcance global)</option>
          {unidadesNegocio?.map((un) => (
            <option key={un.id} value={un.id}>
              {un.nombre}
            </option>
          ))}
        </select>

        {error && <p className="mensaje-error">{error}</p>}

        <button type="submit" disabled={mutacion.isPending}>
          {mutacion.isPending ? "Guardando…" : "Guardar"}
        </button>
      </form>
    </div>
  );
}
