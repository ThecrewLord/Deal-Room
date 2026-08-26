import api from "./axiosClient";

const encodeRoles = (roles = []) =>
    roles.map((role) => `role=${encodeURIComponent(role)}`).join("&");

export default {
    getPending() {
        return api.get("/auth/admin/pending").then((r) => r.data);
    },

    getUsers() {
        return api.get("/auth/admin/users").then((r) => r.data);
    },

    getManagerCandidates(userId, roles = []) {
        const query = encodeRoles(roles);
        return api.get(`/auth/admin/users/${userId}/manager-candidates${query ? `?${query}` : ""}`).then((r) => r.data);
    },

    approve(userId, roles, managerId = null) {
        return api.post(`/auth/admin/approve/${userId}`, { roles, manager_id: managerId }).then((r) => r.data);
    },

    revoke(userId) {
        return api.post(`/auth/admin/revoke/${userId}`).then((r) => r.data);
    },

    updateRoles(userId, roles, updatedAt, managerId) {
        const payload = { roles, updated_at: updatedAt };
        if (managerId !== undefined) payload.manager_id = managerId;
        return api.post(`/auth/admin/users/${userId}/roles`, payload).then((r) => r.data);
    },

    updateManager(userId, managerId, updatedAt) {
        return api.patch(`/auth/admin/users/${userId}/manager`, { manager_id: managerId, updated_at: updatedAt }).then((r) => r.data);
    },
};
