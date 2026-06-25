import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";

export function Layout() {
  const { usuario, salir } = useAuth();

  const esSoloLectura = usuario?.rol === "MATRIZ_CONSULTA";

  return (
    <div className="diseno-app">
      <header className="cabecera">
        <span className="marca">SGAIE</span>
        <nav>
          <NavLink to="/" end>
            Panel
          </NavLink>
          <NavLink to="/operadoras">Operadoras</NavLink>
          <NavLink to="/contratos">Contratos</NavLink>
        </nav>
        <div className="usuario-actual">
          {esSoloLectura && <span className="insignia-solo-lectura">Solo lectura (Matriz)</span>}
          <span>{usuario?.username}</span>
          <button type="button" onClick={() => void salir()}>
            Cerrar sesión
          </button>
        </div>
      </header>
      <main className="contenido">
        <Outlet />
      </main>
    </div>
  );
}
