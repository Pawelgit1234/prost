import axios from "axios";

import pinia from "../store"; 
import { useUserStore } from "../store/user";
import router from "../router";

const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_ENDPOINT,
    // will be set true only by /auth/refresh/ (refresh token is httponly)
    withCredentials: false,
});

axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
        const userStore = useUserStore(pinia);
        const originalRequest = error.config;

        // invalid refresh token
        if (error.response?.status === 401 && originalRequest.url === "/auth/refresh/") {
            await userStore.logout();
            router.push("/signin");
        }
    
        // acces token expired
        else if (error.response?.status === 401 && originalRequest.url !== "/auth/refresh/") {
            try {
                const { data } = await axiosInstance.post("/auth/refresh/", {}, { withCredentials: true });
                userStore.accessToken = data.access_token;
                return axiosInstance(originalRequest);
            } catch (err) {
                await userStore.logout();
                router.push("/signin");
            }
        }
        throw error;
  }
);

axiosInstance.interceptors.request.use((config) => {
  const userStore = useUserStore(pinia);

  if (config.url === "/auth/refresh/") {
    // for refresh token
    config.withCredentials = true;
  } else if (userStore.accessToken) {
    // for other only access token
    config.headers.Authorization = `Bearer ${userStore.accessToken}`;
    config.withCredentials = false;
  }

  return config;
});

export default axiosInstance;
