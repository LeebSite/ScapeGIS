import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.REACT_APP_API_URL || "/api/v1";

const http = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token && config.headers) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

http.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config;

    // Log errors for debugging
    if (err.response?.status === 401) {
      console.error('🔒 401 Unauthorized:', {
        url: originalRequest.url,
        method: originalRequest.method,
        hasAccessToken: !!localStorage.getItem("access_token"),
        hasRefreshToken: !!localStorage.getItem("refresh_token"),
      });
    }

    // Try to refresh token on 401
    if (err.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
          console.log('🔄 Attempting to refresh token...');
          const res = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          if (res.data.access_token) {
            console.log('✅ Token refreshed successfully');
            localStorage.setItem("access_token", res.data.access_token);
            originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
            return http(originalRequest); // Retry with new token
          }
        }
      } catch (refreshError) {
        console.error('❌ Token refresh failed:', refreshError);
        // Clear tokens but DON'T redirect
        // Let the component handle the error and show UI
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        // Just reject the promise, component will handle it
      }
    }

    // DON'T auto-redirect on 401
    // Let React components show error UI with retry options
    // Only redirect if explicitly on login endpoint to prevent login loop
    if (err.response?.status === 401) {
      const isLoginRequest = originalRequest.url?.includes('/auth/login');
      const isLoginPage = typeof window !== 'undefined' && window.location.pathname === '/login';

      // Only redirect if we're on login page and login failed (wrong credentials)
      // This prevents redirect loops
      if (isLoginRequest && isLoginPage) {
        // Don't redirect, just let login page show error
      }
    }

    // Return rejected promise, let component handle
    return Promise.reject(err);
  }
);

export default http;
