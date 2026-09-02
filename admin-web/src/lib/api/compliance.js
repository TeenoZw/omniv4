import apiClient from "./http";

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

async function downloadBlob(path, filename, params) {
  const response = await apiClient.get(path, { params, responseType: "blob" });
  saveBlob(response.data, filename);
}

export async function fetchComplianceAttachmentBlob(attachmentId) {
  const response = await apiClient.get(`/compliance/attachments/${attachmentId}/download`, { responseType: "blob" });
  return response.data;
}

export async function fetchComplianceOverview() {
  const response = await apiClient.get("/compliance/overview");
  return response.data;
}

export async function fetchDataSubjectRequests({ search, status, requestType, page = 1, limit = 20 } = {}) {
  const params = { page, limit };
  if (search?.trim()) params.search = search.trim();
  if (status && status !== "all") params.status = status;
  if (requestType && requestType !== "all") params.request_type = requestType;
  const response = await apiClient.get("/compliance/requests", { params });
  return response.data;
}

export async function fetchDataSubjectRequestDetail(requestId) {
  const response = await apiClient.get(`/compliance/requests/${requestId}`);
  return response.data?.data ?? response.data;
}

export async function createDataSubjectRequest(payload) {
  const response = await apiClient.post("/compliance/requests", payload);
  return response.data?.data ?? response.data;
}

export async function updateDataSubjectRequest(requestId, payload) {
  const response = await apiClient.patch(`/compliance/requests/${requestId}`, payload);
  return response.data?.data ?? response.data;
}

export async function uploadDataSubjectRequestAttachment(requestId, { file, title, description } = {}) {
  const formData = new FormData();
  formData.append("file", file);
  if (title?.trim()) formData.append("title", title.trim());
  if (description?.trim()) formData.append("description", description.trim());
  const response = await apiClient.post(`/compliance/requests/${requestId}/attachments`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data?.data ?? response.data;
}

export async function exportDataSubjectRequestsCsv(params = {}) {
  return downloadBlob("/compliance/requests/export.csv", "omni-data-subject-requests.csv", params);
}

export async function exportDataSubjectRequestPdf(requestId) {
  return downloadBlob(`/compliance/requests/${requestId}/export.pdf`, `data-request-${requestId}.pdf`);
}

export async function exportDataSubjectRequestPack(requestId) {
  return downloadBlob(`/compliance/requests/${requestId}/export-pack`, `data-request-${requestId}-evidence-pack.zip`);
}

export async function fetchSecurityIncidents({ search, status, severity, incidentType, page = 1, limit = 20 } = {}) {
  const params = { page, limit };
  if (search?.trim()) params.search = search.trim();
  if (status && status !== "all") params.status = status;
  if (severity && severity !== "all") params.severity = severity;
  if (incidentType && incidentType !== "all") params.incident_type = incidentType;
  const response = await apiClient.get("/compliance/incidents", { params });
  return response.data;
}

export async function fetchSecurityIncidentDetail(incidentId) {
  const response = await apiClient.get(`/compliance/incidents/${incidentId}`);
  return response.data?.data ?? response.data;
}

export async function createSecurityIncident(payload) {
  const response = await apiClient.post("/compliance/incidents", payload);
  return response.data?.data ?? response.data;
}

export async function updateSecurityIncident(incidentId, payload) {
  const response = await apiClient.patch(`/compliance/incidents/${incidentId}`, payload);
  return response.data?.data ?? response.data;
}

export async function uploadSecurityIncidentAttachment(incidentId, { file, title, description } = {}) {
  const formData = new FormData();
  formData.append("file", file);
  if (title?.trim()) formData.append("title", title.trim());
  if (description?.trim()) formData.append("description", description.trim());
  const response = await apiClient.post(`/compliance/incidents/${incidentId}/attachments`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data?.data ?? response.data;
}

export async function exportSecurityIncidentsCsv(params = {}) {
  return downloadBlob("/compliance/incidents/export.csv", "omni-security-incidents.csv", params);
}

export async function exportSecurityIncidentPdf(incidentId) {
  return downloadBlob(`/compliance/incidents/${incidentId}/export.pdf`, `security-incident-${incidentId}.pdf`);
}

export async function exportSecurityIncidentPack(incidentId) {
  return downloadBlob(`/compliance/incidents/${incidentId}/export-pack`, `security-incident-${incidentId}-evidence-pack.zip`);
}

export async function downloadComplianceAttachment(attachmentId, fallbackName = `compliance-attachment-${attachmentId}`) {
  return downloadBlob(`/compliance/attachments/${attachmentId}/download`, fallbackName);
}

export async function deleteComplianceAttachment(attachmentId) {
  await apiClient.delete(`/compliance/attachments/${attachmentId}`);
}
