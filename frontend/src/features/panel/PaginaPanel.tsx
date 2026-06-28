import { useAuth } from "@/auth/AuthContext";
import { PaginaDashboard } from "@/features/dashboard/PaginaDashboard";

export function PaginaPanel() {
  const { usuario } = useAuth();
  const esProveedor = usuario?.rol === "PROVEEDOR";

  return (
    <div>
      <h1>Panel</h1>
      <p>
        Bienvenido, <strong>{usuario?.username}</strong>. Rol: <strong>{usuario?.rol}</strong>
        {usuario?.unidadNegocioId && <> · Unidad de Negocio #{usuario.unidadNegocioId}</>}
      </p>
      {!esProveedor && <PaginaDashboard />}
    </div>
  );
}
