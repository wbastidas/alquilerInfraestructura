import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "./AuthContext";

interface PropiedadesRutaProtegida {
  /** Si se indica, restringe el acceso a estos roles (además de requerir sesión). */
  rolesPermitidos?: string[];
}

export function RutaProtegida({ rolesPermitidos }: PropiedadesRutaProtegida) {
  const { usuario } = useAuth();

  if (!usuario) {
    return <Navigate to="/login" replace />;
  }

  if (rolesPermitidos && !rolesPermitidos.includes(usuario.rol)) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
