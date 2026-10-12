const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000/api";

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers =
    new Headers(options.headers);

  headers.set(
    "Content-Type",
    "application/json"
  );

  // Add authentication token
  if (
    typeof window !== "undefined"
  ) {
    const token =
      localStorage.getItem(
        "token"
      );

    if (token) {
      headers.set(
        "Authorization",
        `Token ${token}`
      );
    }
  }

  const response =
    await fetch(
      `${API_BASE_URL}${path}`,
      {
        ...options,
        headers,
      }
    );

  if (!response.ok) {
    let message =
      `Request failed: ${response.status}`;

    try {
      const data =
        await response.json();

      if (
        data &&
        typeof data === "object"
      ) {
        if (
          "detail" in data
        ) {
          message =
            String(data.detail);
        } else if (
          "error" in data
        ) {
          message =
            String(data.error);
        } else {
          message =
            JSON.stringify(data);
        }
      }

    } catch {
      // Ignore JSON parsing errors
    }

    throw new Error(
      message
    );
  }

  if (
    response.status === 204
  ) {
    return undefined as T;
  }

  return response.json();
}

export function apiGet<T>(
  path: string
): Promise<T> {
  return apiRequest<T>(
    path,
    {
      method: "GET",
    }
  );
}

export function apiPost<T>(
  path: string,
  body: unknown
): Promise<T> {
  return apiRequest<T>(
    path,
    {
      method: "POST",

      body:
        JSON.stringify(
          body
        ),
    }
  );
}

export function apiPut<T>(
  path: string,
  body: unknown
): Promise<T> {
  return apiRequest<T>(
    path,
    {
      method: "PUT",

      body:
        JSON.stringify(
          body
        ),
    }
  );
}

export function apiDelete<T>(
  path: string
): Promise<T> {
  return apiRequest<T>(
    path,
    {
      method: "DELETE",
    }
  );
}