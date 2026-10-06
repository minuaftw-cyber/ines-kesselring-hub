import "server-only";

import { cookies } from "next/headers";
import { unstable_rethrow } from "next/navigation";
import { cache } from "react";

import { ApiError, apiRequest, TOKEN_COOKIE } from "./api";
import type { User } from "./types";

/** The signed-in user for this request, or null. Cached per request. */
export const getCurrentUser = cache(async (): Promise<User | null> => {
  const token = (await cookies()).get(TOKEN_COOKIE)?.value;
  if (!token) return null;
  try {
    return await apiRequest<User>("/api/auth/me/", { token });
  } catch (error) {
    unstable_rethrow(error);
    if (!(error instanceof ApiError && error.status === 401)) {
      console.error("[auth] could not load the current user:", error instanceof Error ? error.message : error);
    }
    return null;
  }
});

/** Django admin address that staff use (opened in the browser). */
export const BACKOFFICE_URL = process.env.BACKOFFICE_URL ?? "http://localhost:8000/admin/";
