// src/App.jsx
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import OAuthCallback from "./pages/OAuthCallback";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Home />} /> {/* Login puede ir al mismo Home */}
        <Route path="/oauth-callback" element={<OAuthCallback />} />
      </Routes>
    </Router>
  );
}


