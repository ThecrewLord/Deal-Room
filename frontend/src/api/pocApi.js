import api from "./axiosClient";

export const getEligiblePocOpportunities = async () =>
    (await api.get("/poc/eligible-opportunities")).data;

export const requestPoc = async (payload) => (await api.post("/poc/request", payload)).data;
export const getPoc = async (id) => (await api.get(`/poc/${id}`)).data;
export const getPocsByOpportunity = async (opportunityId) =>
    (await api.get(`/poc/opportunity/${opportunityId}`)).data;
export const updatePocDesign = async (id, payload) =>
    (await api.patch(`/poc/${id}/design`, payload)).data;
export const startPocExecution = async (id, payload) =>
    (await api.post(`/poc/${id}/start-execution`, payload)).data;
export const submitPocResult = async (id, payload) =>
    (await api.post(`/poc/${id}/submit-result`, payload)).data;
export const completePoc = async (id, payload) =>
    (await api.post(`/poc/${id}/complete`, payload)).data;
export const deletePoc = async () => {
    throw new Error("POC deletion is disabled.");
};

export const downloadPoc = async (id) => {
    const response = await api.get(`/poc/${id}/download`, {
        responseType: "blob",
    });

    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement("a");

    link.href = url;
    link.download = `POC-${id}.pdf`;

    document.body.appendChild(link);
    link.click();
    link.remove();

    window.URL.revokeObjectURL(url);
};