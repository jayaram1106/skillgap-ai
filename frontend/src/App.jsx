
import { useEffect, useState } from "react";

function App() {
  const [status, setStatus] = useState("Connecting...");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/health")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Backend error");
        }
        return response.json();
      })
      .then((data) => {
        setStatus(data.status);
      })
      .catch(() => {
        setStatus("Connection failed");
      });
  }, []);

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>SkillGap AI</h1>
      <p>Resume vs Job Description Analyser</p>

      <h2>Backend Connection</h2>

      <p>{status}</p>
    </div>
  );
}

export default App;
