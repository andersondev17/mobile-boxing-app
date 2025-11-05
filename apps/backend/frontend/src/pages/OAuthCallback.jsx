import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

export default function OAuthCallback() {
  const navigate = useNavigate();
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const params = new URLSearchParams(window.location.search);
    const auth_code = params.get("auth_code");

    if (auth_code) {
      api.post("/auth/exchange-token", { auth_code })
        .then(res => {
          localStorage.setItem("access_token", res.data.access_token);
          localStorage.setItem("refresh_token", res.data.refresh_token);
          navigate("/");
        })
        .catch(err => {
          console.error("Token exchange failed", err);
          navigate("/login");
        });
    } else {
      navigate("/login");
    }
  }, [navigate]);

  return <div>Procesando login...</div>;
}




