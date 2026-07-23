import { Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing";
import SessionPage from "./pages/SessionPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/session/:sessionId" element={<SessionPage />} />
    </Routes>
  );
}
