import { create } from "zustand";
import type { User } from "./types";
import http from "./api/http";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isInitialized: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
  initializeAuth: () => Promise<void> | void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isInitialized: false,
  setUser: (user) => {
    set({ user, isAuthenticated: !!user });
  },
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false });
  },
  initializeAuth: async () => {
    if (typeof window === "undefined") return;

    // We now use HttpOnly cookies, so we just try to fetch the current user.
    // Ensure we import getCurrentUser from authService.
    try {
      const { getCurrentUser } = await import("./api/authService");
      const user = await getCurrentUser();
      set({ user, isAuthenticated: true, isInitialized: true });
    } catch (err) {
      // If 401 or network error, user is not authenticated.
      set({ user: null, isAuthenticated: false, isInitialized: true });
    }
  },
}));

interface SidebarState {
  isCollapsed: boolean;
  toggleSidebar: () => void;
  setCollapsed: (collapsed: boolean) => void;
}

export const useSidebarStore = create<SidebarState>((set) => ({
  isCollapsed: false,
  toggleSidebar: () => set((state) => ({ isCollapsed: !state.isCollapsed })),
  setCollapsed: (collapsed) => set({ isCollapsed: collapsed }),
}));

interface WorkspaceState {
  currentWorkspace: import("./types").Workspace | null;
  workspaces: import("./types").Workspace[];
  setWorkspaces: (workspaces: import("./types").Workspace[]) => void;
  setCurrentWorkspace: (workspace: import("./types").Workspace) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  currentWorkspace: null,
  workspaces: [],
  setWorkspaces: (workspaces) => set({ workspaces }),
  setCurrentWorkspace: (workspace) => {
    localStorage.setItem("current_workspace_id", workspace.id);
    set({ currentWorkspace: workspace });
  },
}));


