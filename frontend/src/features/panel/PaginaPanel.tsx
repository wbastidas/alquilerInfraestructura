import { useAuth } from "@/auth/AuthContext";

export function PaginaPanel() {
  const { usuario } = useAuth();

  return (
    <div>
      <h1>Panel</h1>
      <p>
        Bienvenido, <strong>{usuario?.username}</strong>. Rol: <strong>{usuario?.rol}</strong>
        {usuario?.unidadNegocioId && <> · Unidad de Negocio #{usuario.unidadNegocioId}</>}
      </p>
    </div>
  );
}
