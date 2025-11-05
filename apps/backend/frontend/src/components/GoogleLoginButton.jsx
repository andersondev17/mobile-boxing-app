// src/components/GoogleLoginButton.jsx
import React from "react";

export default function GoogleLoginButton() {
  const handleLogin = () => {
    window.location.href = `${import.meta.env.VITE_API_URL}/auth/login/google`;
  };

  return <button onClick={handleLogin}>Login con Google</button>;
}


