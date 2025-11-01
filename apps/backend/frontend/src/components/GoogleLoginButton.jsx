// src/components/GoogleLoginButton.jsx
import React from "react";

export default function GoogleLoginButton() {
  const handleLogin = () => {
    window.location.href = "http://localhost:8000/auth/login/google";
  };

  return <button onClick={handleLogin}>Login con Google</button>;
}

