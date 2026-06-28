import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AuthProvider } from "@/auth/AuthContext";
import { PaginaLogin } from "@/auth/PaginaLogin";
import { RutaProtegida } from "@/auth/RutaProtegida";
import { Layout } from "@/components/Layout";
import { ListaAlertas } from "@/features/alertas/ListaAlertas";
import { FormularioAlquilerAnual } from "@/features/alquileres/FormularioAlquilerAnual";
import { ListaAlquileres } from "@/features/alquileres/ListaAlquileres";
import { ListaCanon } from "@/features/canon/ListaCanon";
import { ListaContratos } from "@/features/contratos/ListaContratos";
import { FormularioOperadora } from "@/features/operadoras/FormularioOperadora";
import { ListaOperadoras } from "@/features/operadoras/ListaOperadoras";
import { PaginaPanel } from "@/features/panel/PaginaPanel";
import { FormularioUsuario } from "@/features/usuarios/FormularioUsuario";
import { ListaUsuarios } from "@/features/usuarios/ListaUsuarios";

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<PaginaLogin />} />
            <Route element={<RutaProtegida />}>
              <Route element={<Layout />}>
                <Route path="/" element={<PaginaPanel />} />
                <Route path="/operadoras" element={<ListaOperadoras />} />
                <Route path="/operadoras/nueva" element={<FormularioOperadora />} />
                <Route path="/contratos" element={<ListaContratos />} />
                <Route path="/alquileres-anuales" element={<ListaAlquileres />} />
                <Route path="/alquileres-anuales/nuevo" element={<FormularioAlquilerAnual />} />
                <Route path="/canon" element={<ListaCanon />} />
                <Route path="/alertas" element={<ListaAlertas />} />
                <Route path="/usuarios" element={<ListaUsuarios />} />
                <Route path="/usuarios/nuevo" element={<FormularioUsuario />} />
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
