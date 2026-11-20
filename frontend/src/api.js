/**
 * SkillGap AI - Frontend API Service.
 *
 * Connects the React client to the FastAPI backend running at http://127.0.0.1:8000.
 */

export const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Perform health check against backend API.
 * Calls GET http://127.0.0.1:8000/api/health
 *
 * @returns {Promise<{status: string, application: string, backend: string}>}
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }

  return response.json();
}

/**
 * Submit candidate PDF resume and job description text for gap analysis.
 * Calls POST http://127.0.0.1:8000/api/analyze using multipart/form-data.
 *
 * @param {File|Blob} resumeFile - The PDF resume file to analyze.
 * @param {string} jobDescription - Target job description requirements text.
 * @returns {Promise<Object>} Analysis results including matched, missing, and additional skills.
 */
export async function analyzeResume(resumeFile, jobDescription) {
  if (!resumeFile) {
    throw new Error("Resume PDF file is required.");
  }
  if (!jobDescription || !jobDescription.trim()) {
    throw new Error("Job description text is required.");
  }

  // Construct multipart/form-data payload with exact expected field names
  const formData = new FormData();
  formData.append("resume", resumeFile);
  formData.append("job_description", jobDescription);

  // Note: Do NOT set Content-Type header manually; the browser will automatically
  // supply 'multipart/form-data; boundary=...' with the correct boundary string.
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = `Analysis request failed with status: ${response.status}`;
    try {
      const errData = await response.json();
      if (errData && errData.detail) {
        errorDetail = errData.detail;
      }
    } catch {
      // Fallback to generic message if response is not JSON
    }
    throw new Error(errorDetail);
  }

  return response.json();
}
