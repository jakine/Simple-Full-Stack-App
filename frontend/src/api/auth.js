const BASE_URL = "http://localhost:8000/api/auth";

async function getCsrfToken() {
  const cookie = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="));
  return cookie ? cookie.split("=")[1] : null;
}

export async function login(email, password) {
  const csrfToken = await getCsrfToken();
  const res = await fetch(`${BASE_URL}/login/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken || "",
    },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Login failed.");
  return data;
}

export async function logout() {
  const csrfToken = await getCsrfToken();
  await fetch(`${BASE_URL}/logout/`, {
    method: "POST",
    headers: { "X-CSRFToken": csrfToken || "" },
    credentials: "include",
  });
}

export async function getMe() {
  const res = await fetch(`${BASE_URL}/me/`, {
    credentials: "include",
  });
  if (!res.ok) return null;
  return res.json();
}