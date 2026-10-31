import { api } from "./client";

export async function register(email, password) {
  return api("/auth/register/", {
    method: "POST",
    body: { email, password },
  });
}

export async function login(email, password) {
  return api("/auth/login/", {
    method: "POST",
    body: { email, password },
  });
}

export async function logout() {
  await api("/auth/logout/", { method: "POST" });
}

export async function getMe() {
  try {
    return await api("/auth/me/");
  } catch {
    return null;
  }
}
