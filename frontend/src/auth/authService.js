import authApi from "./authApi";

const authService = {

    login(credentials) {
        return authApi.login(credentials);
    },

    signup(payload) {
        return authApi.signup(payload);
    },

    selectRole(role) {
        return authApi.selectRole(role);
    },

    me() {
        return authApi.me();
    },

    logout() {
        return authApi.logout();
    },

};

export default authService;