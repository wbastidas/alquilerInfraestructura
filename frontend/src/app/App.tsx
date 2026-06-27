import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AuthProvider } from "@/auth/AuthContext";
import { PaginaLogin } from "@/auth/PaginaLogin";
import { RutaProtegida } from "@/auth/RutaProtegida";
import { Layout } from "@/components/Layout";
import { ListaAlertas } from "@/features/alertas/ListaAlertas";
import { ListaContratos } from "@/features/contratos/ListaContratos";
import { FormularioOperadora } from "@/features/operadoras/FormularioOperadora";
import { ListaOperadoras } from "@/features/operadoras/ListaOperadoras";
import { PaginaPanel } from "@/features/panel/PaginaPanel";

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
                <Route path="/alertas" element={<ListaAlertas />} />
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
