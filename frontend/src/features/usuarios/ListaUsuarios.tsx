import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listarRoles } from "@/api/roles";
import { actualizarUsuario, listarUsuarios } from "@/api/usuarios";
import { listarUnidadesNegocio } from "@/api/unidadesNegocio";
import { useAuth } from "@/auth/AuthContext";

export function ListaUsuarios() {
  const { usuario: usuarioActual } = useAuth();
  const queryClient = useQueryClient();
  const esSuperadmin = usuarioActual?.rol === "SUPERADMIN";

  const { data: usuarios, isLoading, error } = useQuery({
    queryKey: ["usuarios"],
    queryFn: listarUsuarios,
  });
  const { data: roles } = useQuery({ queryKey: ["roles"], queryFn: listarRoles });
  const { data: unidadesNegocio } = useQuery({
    queryKey: ["unidades-negocio"],
    queryFn: listarUnidadesNegocio,
  });

  const mutacionActivo = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) =>
      actualizarUsuario(id, { activo }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["usuarios"] }),
  });

  if (isLoading) return <p>Cargando usuarios…</p>;
  if (error) return <p className="mensaje-error">No se pudo cargar el listado de usuarios.</p>;

  const nombreRol = (rolId: number) => roles?.find((rol) => rol.id === rolId)?.nombre ?? rolId;
  const nombreUn = (unId: number | null) =>
    unId ? unidadesNegocio?.find((un) => un.id === unId)?.nombre ?? unId : "—";

  return (
    <div>
      <div className="encabezado-seccion">
        <h1>Usuarios</h1>
        {esSuperadmin && (
          <Link to="/usuarios/nuevo" className="boton-primario">
            Nuevo usuario
          </Link>
        )}
      </div>
      <table className="tabla">
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Nombre completo</th>
            <th>Correo</th>
            <th>Tipo de cuenta</th>
            <th>Rol</th>
            <th>Unidad de Negocio</th>
            <th>Estado</th>
            {esSuperadmin && <th></th>}
          </tr>
        </thead>
        <tbody>
          {usuarios?.map((usuario) => (
            <tr key={usuario.id}>
              <td>{usuario.username}</td>
              <td>{usuario.nombre_completo}</td>
              <td>{usuario.correo}</td>
              <td>{usuario.tipo_cuenta}</td>
              <td>{nombreRol(usuario.rol_id)}</td>
              <td>{nombreUn(usuario.unidad_negocio_id)}</td>
              <td>{usuario.activo ? "Activo" : "Inactivo"}</td>
              {esSuperadmin && (
                <td>
                  <button
                    type="button"
                    disabled={mutacionActivo.isPending}
                    onClick={() =>
                      mutacionActivo.mutate({ id: usuario.id, activo: !usuario.activo })
                    }
                  >
                    {usuario.activo ? "Desactivar" : "Activar"}
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      {usuarios?.length === 0 && <p>No hay usuarios registrados en su ámbito.</p>}
    </div>
  );
}
