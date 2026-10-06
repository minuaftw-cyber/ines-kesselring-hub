import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { LoginForm } from "@/components/AuthForms";
import { getCurrentUser } from "@/lib/auth";

export const metadata: Metadata = { title: "เข้าสู่ระบบ" };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const { next } = await searchParams;
  if (await getCurrentUser()) redirect("/account");

  return (
    <div className="container auth-layout">
      <div className="auth-intro">
        <h1>ยินดีต้อนรับกลับมา</h1>
        <p>
          เข้าสู่ระบบด้วยอีเมลที่สมัครไว้ ทีมงานและแอดมินใช้หน้านี้ได้เหมือนกัน
          แล้วจะเห็นทางเข้าหลังบ้านในหน้าบัญชี
        </p>
      </div>
      <LoginForm next={next} />
    </div>
  );
}
