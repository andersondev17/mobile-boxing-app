// src/pages/Home.jsx
import React, { useEffect, useState } from "react";
import api from "../api";
import GoogleLoginButton from "../components/GoogleLoginButton";

export default function Home() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }

    api.get("/user/me")
      .then((res) => setUser(res.data))
      .catch((err) => {
        console.error(err);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Cargando...</div>;

  return (
    <div>
      {user ? (
        <h1>Hola {user.message}</h1>
      ) : (
        <>
          <h1>Hola invitado</h1>
          <GoogleLoginButton />
        </>
      )}
    </div>
  );
}
