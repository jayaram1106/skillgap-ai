import { useEffect, useState } from "react";
import { API_BASE_URL, checkHealth, analyzeResume } from "./api";

export { API_BASE_URL, checkHealth, analyzeResume };

function App() {
  const [status, setStatus] = useState("Connecting...");
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [analyzeError, setAnalyzeError] = useState("");
  const [analyzeResult, setAnalyzeResult] = useState(null);

  useEffect(() => {
    setStatus("Connecting...");
    checkHealth()
      .then((data) => {
        setStatus(data.status);
      })
      .catch(() => {
        setStatus("Connection failed");
      });
  }, []);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!resumeFile) {
      setAnalyzeError("Please select a PDF resume file.");
      return;
    }
    if (!jobDescription.trim()) {
      setAnalyzeError("Please enter a job description.");
      return;
    }

    setAnalyzeLoading(true);
    setAnalyzeError("");
    setAnalyzeResult(null);

    try {
      const result = await analyzeResume(resumeFile, jobDescription);
      setAnalyzeResult(result);
    } catch (err) {
      setAnalyzeError(err.message || "Failed to analyze resume.");
    } finally {
      setAnalyzeLoading(false);
    }
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>SkillGap AI</h1>
      <p>Resume vs Job Description Analyser</p>

      <h2>Backend Connection</h2>

      <p>{status}</p>

      <h2>Analyze Resume</h2>
      <form onSubmit={handleAnalyze}>
        <div style={{ marginBottom: "16px" }}>
          <label style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>
            Resume (PDF):
          </label>
          <input
            type="file"
            name="resume"
            accept=".pdf,application/pdf"
            onChange={(e) => setResumeFile(e.target.files[0] || null)}
          />
        </div>

        <div style={{ marginBottom: "16px" }}>
          <label style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>
            Job Description:
          </label>
          <textarea
            name="job_description"
            rows="6"
            style={{ width: "100%", maxWidth: "600px", padding: "8px", boxSizing: "border-box" }}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste target job description text here..."
          />
        </div>

        <button type="submit" disabled={analyzeLoading} style={{ padding: "8px 16px", cursor: "pointer" }}>
          {analyzeLoading ? "Analyzing..." : "Analyze Gap"}
        </button>
      </form>

      {analyzeError && (
        <p style={{ color: "red", marginTop: "16px" }}>{analyzeError}</p>
      )}

      {analyzeResult && (
        <div style={{ marginTop: "20px" }}>
          <h3>Analysis Result</h3>
          <p><strong>Match Score:</strong> {analyzeResult.match_percentage}%</p>
          <p><strong>Summary:</strong> {analyzeResult.summary}</p>
          <p><strong>Matched Skills:</strong> {analyzeResult.matched_skills.join(", ") || "None"}</p>
          <p><strong>Missing Skills:</strong> {analyzeResult.missing_skills.join(", ") || "None"}</p>
          <p><strong>Additional Skills:</strong> {analyzeResult.additional_skills.join(", ") || "None"}</p>
        </div>
      )}
    </div>
  );
}

export default App;
