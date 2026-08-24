const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ||
    `${window.location.protocol}//${window.location.hostname}:5000/api`;

export default API_BASE_URL;
