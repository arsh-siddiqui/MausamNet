/** Root providers: TanStack Query + theme + auth bootstrap. */
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { clearSession, getToken, getUser, User } from "@/lib/api";

interface AuthCtx {
  user: User | null;
  token: string | null;
  ready: boolean;
  signOut: () => void;
  refresh: () => void;
}

const AuthContext = createContext<AuthCtx>({
  user: null,
  token: null,
  ready: false,
  signOut: () => {},
  refresh: () => {},
});

export const useAuth = () => useContext(AuthContext);

const ThemeContext = createContext<{ theme: "dark" | "light"; toggle: () => void }>({
  theme: "dark",
  toggle: () => {},
});
export const useTheme = () => useContext(ThemeContext);

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { staleTime: 15_000, retry: 1, refetchOnWindowFocus: false } },
      })
  );
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    setUser(getUser());
    setToken(getToken());
    const stored = (window.localStorage.getItem("mausamnet.theme") as "dark" | "light") || "dark";
    setTheme(stored);
    document.documentElement.classList.toggle("light", stored === "light");
    setReady(true);
  }, []);

  const auth = useMemo<AuthCtx>(
    () => ({
      user,
      token,
      ready,
      signOut: () => {
        clearSession();
        setUser(null);
        setToken(null);
        window.location.href = "/login";
      },
      refresh: () => {
        setUser(getUser());
        setToken(getToken());
      },
    }),
    [user, token, ready]
  );

  const themeCtx = useMemo(
    () => ({
      theme,
      toggle: () => {
        const next = theme === "dark" ? "light" : "dark";
        setTheme(next);
        window.localStorage.setItem("mausamnet.theme", next);
        document.documentElement.classList.toggle("light", next === "light");
      },
    }),
    [theme]
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={auth}>
        <ThemeContext.Provider value={themeCtx}>{children}</ThemeContext.Provider>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}
