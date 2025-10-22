import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "./components/ui/toaster";
import { Toaster as Sonner } from "./components/ui/toaster";
import Login from "./components/pages/Login";
import Dashboard from "./components/pages/Dashboard";
import CorteCaja from "./components/pages/CorteCaja";


const qc = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/corte" element={<CorteCaja />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
