import React, { useEffect, useState } from "react";
import api from "../api";
import LoginForm from "../components/LoginForm";
import RegisterForm from "../components/RegisterForm";
import GoogleLoginButton from "../components/GoogleLoginButton";
import LogoutButton from "../components/LogoutButton";

export default function Home() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showRegister, setShowRegister] = useState(false);

  const fetchUser = () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api.get("/auth/protected")
      .then(res => setUser(res.data))
      .catch(err => {
        console.error(err);
        setUser(null);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const handleLoginSuccess = () => fetchUser();
  const handleRegisterSuccess = () => setShowRegister(false);

  if (loading) return <div>Cargando...</div>;

  return (
    <div>
      {user ? (
        <>
          <h1>Hola {user.message}</h1>
          <LogoutButton onLogout={() => setUser(null)} />
        </>
      ) : (
        <>
          {showRegister ? (
            <>
              <h1>Registro</h1>
              <RegisterForm onRegister={handleRegisterSuccess} />
              <button onClick={() => setShowRegister(false)}>Volver al login</button>
            </>
          ) : (
            <>
              <h1>Inicia sesión</h1>
              <LoginForm onLogin={handleLoginSuccess} />
              <button onClick={() => setShowRegister(true)}>Registrarse</button>
            </>
          )}
          <hr />
          <GoogleLoginButton />
        </>
      )}
    </div>
  );
}


