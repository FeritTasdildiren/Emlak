export const auth = {
  getToken: () => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("token");
    }
    return null;
  },
  setToken: (token: string) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("token", token);
    }
  },
  removeToken: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
    }
  },
  isAuthenticated: () => {
    if (typeof window !== "undefined") {
      return !!localStorage.getItem("token");
    }
    return false;
  }
};
