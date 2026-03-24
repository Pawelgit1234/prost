import axios from "axios";

import { useAuthStore } from "../store/auth";
import router from "../router";

const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_ENDPOINT,
    // will be set true only by /auth/refresh/ (refresh token is httponly)
    withCredentials: false,
});

axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
        const authStore = useAuthStore();
        const originalRequest = error.config;

        // invalid refresh token
        if (error.response?.status === 401 && originalRequest.url === "/auth/refresh/") {
            await authStore.logout();
            router.push(router.currentRoute.value.fullPath);
        }
    
        // acces token expired
        else if (error.response?.status === 401 && originalRequest.url !== "/auth/refresh/") {
            try {
                const { data } = await axiosInstance.post("/auth/refresh/", {}, { withCredentials: true });
                authStore.accessToken = data.access_token;
                return axiosInstance(originalRequest);
            } catch (err) {
                await authStore.logout();
                router.push(router.currentRoute.value.fullPath);
            }
        }
        throw error;
  }
);

axiosInstance.interceptors.request.use((config) => {
  const authStore = useAuthStore();

  if (config.url === "/auth/refresh/") {
    // for refresh token
    config.withCredentials = true;
  } else if (authStore.accessToken) {
    // for other only access token
    config.headers.Authorization = `Bearer ${authStore.accessToken}`;
    config.withCredentials = false;
  }

  return config;
});

export default axiosInstance;
