"use client";

import Link from "next/link";
import { useActionState } from "react";

import { login, register, type AuthFormState } from "@/app/actions/auth";

function FieldError({ id, message }: { id: string; message?: string }) {
  return message ? (
    <p className="field-error" id={id}>
      {message}
    </p>
  ) : null;
}

export function LoginForm({ next }: { next?: string }) {
  const [state, action, pending] = useActionState<AuthFormState, FormData>(login, {});

  return (
    <form className="form-card" action={action} noValidate>
      <h2>เข้าสู่ระบบ</h2>
      {state.error ? (
        <p className="form-error" role="alert">
          {state.error}
        </p>
      ) : null}
      <input type="hidden" name="next" value={next ?? ""} />
      <div className="field">
        <label htmlFor="login-email">อีเมล</label>
        <input
          id="login-email"
          name="email"
          type="email"
          autoComplete="email"
          required
          defaultValue={state.values?.email}
          aria-invalid={state.fieldErrors?.email ? true : undefined}
          aria-describedby={state.fieldErrors?.email ? "login-email-error" : undefined}
        />
        <FieldError id="login-email-error" message={state.fieldErrors?.email} />
      </div>
      <div className="field">
        <label htmlFor="login-password">รหัสผ่าน</label>
        <input
          id="login-password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          aria-invalid={state.fieldErrors?.password ? true : undefined}
          aria-describedby={state.fieldErrors?.password ? "login-password-error" : undefined}
        />
        <FieldError id="login-password-error" message={state.fieldErrors?.password} />
      </div>
      <button className="button button-primary" type="submit" disabled={pending}>
        {pending ? "กำลังเข้าสู่ระบบ…" : "เข้าสู่ระบบ"}
      </button>
      <p className="form-switch">
        ยังไม่มีบัญชี?{" "}
        <Link className="text-link" href="/register">
          สมัครสมาชิกฟรี
        </Link>
      </p>
    </form>
  );
}

export function RegisterForm() {
  const [state, action, pending] = useActionState<AuthFormState, FormData>(register, {});

  return (
    <form className="form-card" action={action} noValidate>
      <h2>สมัครสมาชิก</h2>
      {state.error ? (
        <p className="form-error" role="alert">
          {state.error}
        </p>
      ) : null}
      <div className="field">
        <label htmlFor="reg-name">ชื่อที่แสดง</label>
        <input
          id="reg-name"
          name="display_name"
          type="text"
          autoComplete="nickname"
          maxLength={60}
          defaultValue={state.values?.display_name}
          aria-describedby="reg-name-hint"
        />
        <p className="field-hint" id="reg-name-hint">
          ไม่ใส่ก็ได้ ใช้แสดงในหน้าบัญชีของคุณ
        </p>
      </div>
      <div className="field">
        <label htmlFor="reg-email">อีเมล</label>
        <input
          id="reg-email"
          name="email"
          type="email"
          autoComplete="email"
          required
          defaultValue={state.values?.email}
          aria-invalid={state.fieldErrors?.email ? true : undefined}
          aria-describedby={state.fieldErrors?.email ? "reg-email-error" : undefined}
        />
        <FieldError id="reg-email-error" message={state.fieldErrors?.email} />
      </div>
      <div className="field">
        <label htmlFor="reg-password">รหัสผ่าน</label>
        <input
          id="reg-password"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          aria-invalid={state.fieldErrors?.password ? true : undefined}
          aria-describedby={state.fieldErrors?.password ? "reg-password-error reg-password-hint" : "reg-password-hint"}
        />
        <p className="field-hint" id="reg-password-hint">
          อย่างน้อย 8 ตัวอักษร และไม่ใช่ตัวเลขอย่างเดียว
        </p>
        <FieldError id="reg-password-error" message={state.fieldErrors?.password} />
      </div>
      <button className="button button-primary" type="submit" disabled={pending}>
        {pending ? "กำลังสมัคร…" : "สมัครสมาชิก"}
      </button>
      <p className="form-switch">
        มีบัญชีอยู่แล้ว?{" "}
        <Link className="text-link" href="/login">
          เข้าสู่ระบบ
        </Link>
      </p>
    </form>
  );
}
