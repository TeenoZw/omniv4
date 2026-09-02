import apiClient from "./http";

export async function fetchEnquiries({ status } = {}) {
  const params = {};
  if (status && status !== "all") {
    params.status = status;
  }
  const response = await apiClient.get("/enquiries", { params });
  return response.data;
}

export async function updateEnquiry(enquiryId, payload) {
  const response = await apiClient.patch(`/enquiries/${enquiryId}`, payload);
  return response.data;
}
