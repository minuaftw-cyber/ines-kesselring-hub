import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { RegisterForm } from "@/components/AuthForms";
import { getCurrentUser } from "@/lib/auth";

export const metadata: Metadata = { title: "สมัครสมาชิก" };

export default async function RegisterPage() {
  if (await getCurrentUser()) redirect("/account");

  return (
    <div className="container auth-layout">
      <div className="auth-intro">
        <h1>สมัครสมาชิกฟรี</h1>
        <p>ใช้แค่อีเมลกับรหัสผ่าน ไม่มีค่าใช้จ่าย</p>
        <ul className="perks">
          <li>อ่านบทความเบื้องหลังฉบับเต็ม</li>
          <li>เห็นลิงก์ไลฟ์เฉพาะสมาชิก</li>
          <li>รู้ข่าวใหม่ของช่องก่อนใคร</li>
        </ul>
      </div>
      <RegisterForm />
    </div>
  );
}
