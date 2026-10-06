"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ApiError, apiRequest, TOKEN_COOKIE } from "@/lib/api";
import type { User } from "@/lib/types";

export interface AuthFormState {
  error?: string;
  fieldErrors?: Partial<Record<"email" | "password" | "display_name", string>>;
  values?: { email?: string; display_name?: string };
}

const THIRTY_DAYS = 60 * 60 * 24 * 30;

const KNOWN_MESSAGES: Record<string, string> = {
  "An account with this email already exists.": "อีเมลนี้มีบัญชีอยู่แล้ว ลองเข้าสู่ระบบแทน",
  "Incorrect email or password.": "อีเมลหรือรหัสผ่านไม่ถูกต้อง",
  "Enter a valid email address.": "รูปแบบอีเมลไม่ถูกต้อง",
  "This field may not be blank.": "กรุณากรอกช่องนี้",
  "This password is too common.": "รหัสผ่านนี้เดาง่ายเกินไป",
  "This password is entirely numeric.": "รหัสผ่านต้องมีตัวอักษร ไม่ใช่ตัวเลขอย่างเดียว",
};

function translate(message: string): string {
  if (KNOWN_MESSAGES[message]) return KNOWN_MESSAGES[message];
  if (message.startsWith("This password is too short")) return "รหัสผ่านต้องยาวอย่างน้อย 8 ตัวอักษร";
  if (message.startsWith("The password is too similar")) return "รหัสผ่านคล้ายกับอีเมลหรือชื่อมากเกินไป";
  return message;
}

function first(value: unknown): string | undefined {
  if (Array.isArray(value) && typeof value[0] === "string") return translate(value[0]);
  if (typeof value === "string") return translate(value);
  return undefined;
}

function toFormState(error: unknown, values: AuthFormState["values"]): AuthFormState {
  if (error instanceof ApiError) {
    if (error.status === 429) {
      return { error: "พยายามหลายครั้งเกินไป กรุณารอสักครู่แล้วลองใหม่", values };
    }
    if (error.status === 400 && error.data && typeof error.data === "object") {
      const data = error.data as Record<string, unknown>;
      const fieldErrors: AuthFormState["fieldErrors"] = {
        email: first(data.email),
        password: first(data.password),
        display_name: first(data.display_name),
      };
      return {
        error: first(data.non_field_errors),
        fieldErrors,
        values,
      };
    }
  }
  console.error("[auth] request failed:", error);
  return { error: "ระบบไม่สามารถเชื่อมต่อได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง", values };
}

async function startSession(token: string) {
  (await cookies()).set(TOKEN_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production" && process.env.INSECURE_COOKIES !== "1",
    path: "/",
    maxAge: THIRTY_DAYS,
  });
}

/** Only allow redirects to pages on this site. */
function safeNext(value: FormDataEntryValue | null): string {
  const next = typeof value === "string" ? value : "";
  return next.startsWith("/") && !next.startsWith("//") ? next : "/account";
}

export async function login(_prev: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const values = { email };

  if (!email || !password) {
    return { error: "กรุณากรอกอีเมลและรหัสผ่าน", values };
  }

  try {
    const { token } = await apiRequest<{ token: string; user: User }>("/api/auth/login/", {
      method: "POST",
      body: { email, password },
    });
    await startSession(token);
  } catch (error) {
    return toFormState(error, values);
  }
  redirect(safeNext(formData.get("next")));
}

export async function register(_prev: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const display_name = String(formData.get("display_name") ?? "").trim();
  const values = { email, display_name };

  if (!email || !password) {
    return { error: "กรุณากรอกอีเมลและรหัสผ่าน", values };
  }

  try {
    const { token } = await apiRequest<{ token: string; user: User }>("/api/auth/register/", {
      method: "POST",
      body: { email, password, display_name },
    });
    await startSession(token);
  } catch (error) {
    return toFormState(error, values);
  }
  redirect("/account?welcome=1");
}

export async function logout() {
  const store = await cookies();
  const token = store.get(TOKEN_COOKIE)?.value;
  if (token) {
    // Revoke the token on the server too; ignore failures (cookie is cleared anyway).
    await apiRequest("/api/auth/logout/", { method: "POST", token }).catch(() => undefined);
  }
  store.delete(TOKEN_COOKIE);
  redirect("/");
}
