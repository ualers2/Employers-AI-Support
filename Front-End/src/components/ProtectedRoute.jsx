// ProtectedRoute.jsx
import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const ProtectedRoute = ({ children }) => {
  const { user } = useAuth(); // supondo que o AuthContext forneça 'user'

  if (!user) {
    // se não estiver logado, redireciona para login
    return <Navigate to="/" replace />;
  }

  return children;
};

export default ProtectedRoute;
