// src/components/LogoutButton.jsx
import React from "react";
import { useNavigate } from "react-router-dom";

export default function LogoutButton({ onLogout }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    // Limpiar tokens
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    // Resetear estado del usuario en Home
    if (onLogout) onLogout();

    // Redirigir a login o página principal
    navigate("/login");
  };

  return <button onClick={handleLogout}>Cerrar sesión</button>;
}
