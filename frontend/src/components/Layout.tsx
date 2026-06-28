import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";

export function Layout() {
  const { usuario, salir } = useAuth();

  const esSoloLectura = usuario?.rol === "MATRIZ_CONSULTA";
  const esProveedor = usuario?.rol === "PROVEEDOR";

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
          {!esProveedor && <NavLink to="/alquileres-anuales">Alquileres</NavLink>}
          {!esProveedor && <NavLink to="/canon">Canon</NavLink>}
          <NavLink to="/facturas">Facturas</NavLink>
          <NavLink to="/solicitudes">Solicitudes</NavLink>
          {!esProveedor && <NavLink to="/alertas">Alertas</NavLink>}
          {!esProveedor && <NavLink to="/usuarios">Usuarios</NavLink>}
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
