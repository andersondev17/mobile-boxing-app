import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function OAuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const access = params.get("access_token");
    const refresh = params.get("refresh_token");

    if (access && refresh) {
      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);
      navigate("/"); // redirige a Home
    } else {
      navigate("/login"); // si algo falla
    }
  }, [navigate]);

  return <div>Procesando login...</div>;
}



