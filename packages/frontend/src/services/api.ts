/**
 * API client layer - Axios wrapper with interceptors.
 */
import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = "/api/v1";

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: attach auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor: handle errors globally
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or unauthorized - redirect to login
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export default apiClient;
