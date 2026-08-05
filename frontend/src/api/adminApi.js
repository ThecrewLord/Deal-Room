import api from "./axiosClient";

export default {

    getPending() {
        return api.get("/auth/admin/pending")
            .then(r => r.data);
    },

    getUsers() {
        return api.get("/auth/admin/users")
            .then(r => r.data);
    },

    approve(userId, roles) {
        return api.post(
            `/auth/admin/approve/${userId}`,
            { roles }
        ).then(r => r.data);
    },

    revoke(userId) {
        return api.post(
            `/auth/admin/revoke/${userId}`
        ).then(r => r.data);
    }

};