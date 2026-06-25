import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "./AuthContext";

type ModoLogin = "local" | "dominio";

export function PaginaLogin() {
  const { usuario, cargando, entrarLocal, entrarDominio } = useAuth();
  const navegar = useNavigate();
  const ubicacion = useLocation();
  const [modo, setModo] = useState<ModoLogin>("local");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (usuario) {
    const destino = (ubicacion.state as { desde?: string } | null)?.desde ?? "/";
    return <Navigate to={destino} replace />;
  }

  async function manejarEnvio(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    try {
      if (modo === "local") {
        await entrarLocal(username, password);
      } else {
        await entrarDominio(username, password);
      }
      navegar("/", { replace: true });
    } catch {
      setError("Usuario o contraseña incorrectos.");
    }
  }

  return (
    <div className="pagina-login">
      <form className="tarjeta-login" onSubmit={manejarEnvio}>
        <h1>SGAIE</h1>
        <p className="subtitulo">Sistema de Gestión de Arriendo de Infraestructura Eléctrica</p>

        <div className="selector-modo">
          <button
            type="button"
            className={modo === "local" ? "activo" : ""}
            onClick={() => setModo("local")}
          >
            Usuario local / proveedor
          </button>
          <button
            type="button"
            className={modo === "dominio" ? "activo" : ""}
            onClick={() => setModo("dominio")}
          >
            Cuenta de dominio (CNEL EP)
          </button>
        </div>

        <label htmlFor="username">Usuario</label>
        <input
          id="username"
          value={username}
          onChange={(evento) => setUsername(evento.target.value)}
          autoComplete="username"
          required
        />

        <label htmlFor="password">Contraseña</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(evento) => setPassword(evento.target.value)}
          autoComplete="current-password"
          required
        />

        {error && <p className="mensaje-error">{error}</p>}

        <button type="submit" disabled={cargando}>
          {cargando ? "Ingresando…" : "Ingresar"}
        </button>
      </form>
    </div>
  );
}
