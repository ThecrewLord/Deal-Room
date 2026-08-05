import api from "../api/axiosClient";

export default {

    login(data) {
        return api.post("/auth/login", data)
            .then(r => r.data);
    },

    signup(data) {
        return api.post("/auth/signup", data)
            .then(r => r.data);
    },

    me() {
        return api.get("/auth/me")
            .then(r => r.data);
    },

    refresh() {
        return api.post("/auth/refresh")
            .then(r => r.data);
    },

    logout() {
        return api.post("/auth/logout");
    },

    selectRole(role) {
        return api.post(
            "/auth/select-role",
            { role }
        ).then(r => r.data);
    },
};