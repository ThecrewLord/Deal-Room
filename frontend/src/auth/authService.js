import authApi from "./authApi";
import authStorage from "./authStorage";

const authService = {

    async login(data) {
        const res = await authApi.login(data);

        authStorage.saveTokens(
            res.access_token,
            res.refresh_token,
        );

        return res;
    },

    async signup(data) {
        return authApi.signup(data);
    },

    async me() {
        return authApi.me();
    },

    async refresh() {

        const token = await authApi.refresh();

        authStorage.setAccessToken(
            token.access_token,
        );

        return token;
    },

    logoutLocal() {
        authStorage.clear();
    },
};

export default authService;