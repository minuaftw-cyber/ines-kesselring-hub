import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { logout } from "@/app/actions/auth";
import { BACKOFFICE_URL, getCurrentUser } from "@/lib/auth";
import { formatDate } from "@/lib/format";

export const metadata: Metadata = { title: "บัญชีของฉัน" };

const ROLE_LABEL = { member: "สมาชิก", staff: "ทีมงาน", admin: "แอดมิน" } as const;

export default async function AccountPage({ searchParams }: { searchParams: Promise<{ welcome?: string }> }) {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/account");
  const { welcome } = await searchParams;

  return (
    <div className="container">
      <header className="page-head">
        <h1>สวัสดี {user.display_name || "สมาชิกใหม่"}</h1>
        {welcome ? (
          <p className="notice">สมัครสมาชิกเรียบร้อย ตอนนี้อ่านบทความเฉพาะสมาชิกและดูลิงก์ไลฟ์สมาชิกได้แล้ว</p>
        ) : null}
      </header>

      <div className="account-grid">
        <section className="panel" aria-labelledby="profile-title">
          <h2 id="profile-title">ข้อมูลบัญชี</h2>
          <dl>
            <dt>อีเมล</dt>
            <dd>{user.email}</dd>
            <dt>สถานะ</dt>
            <dd>
              <span className="role-badge">{ROLE_LABEL[user.role]}</span>
            </dd>
            <dt>สมัครเมื่อ</dt>
            <dd>{formatDate(user.date_joined)}</dd>
          </dl>
          <form action={logout} style={{ marginTop: 24 }}>
            <button className="button" type="submit">
              ออกจากระบบ
            </button>
          </form>
        </section>

        {user.can_access_backoffice ? (
          <section className="panel panel-backoffice" aria-labelledby="backoffice-title">
            <h2 id="backoffice-title">หลังบ้าน</h2>
            <p>
              {user.role === "admin"
                ? "จัดการวิดีโอ ตารางไลฟ์ ข่าวสาร และบัญชีผู้ใช้ทั้งหมด"
                : "จัดการวิดีโอ ตารางไลฟ์ และข่าวสาร"}
              {" "}ระบบหลังบ้านจะให้เข้าสู่ระบบอีกครั้งด้วยอีเมลและรหัสผ่านเดียวกัน
            </p>
            <a className="button" href={BACKOFFICE_URL} target="_blank" rel="noopener noreferrer">
              เปิดหลังบ้าน
            </a>
          </section>
        ) : (
          <section className="panel" aria-labelledby="perks-title">
            <h2 id="perks-title">สิทธิ์ของสมาชิก</h2>
            <ul className="perks" style={{ marginTop: 0 }}>
              <li>อ่านบทความเบื้องหลังฉบับเต็ม</li>
              <li>เห็นลิงก์ไลฟ์เฉพาะสมาชิกในตารางไลฟ์</li>
            </ul>
          </section>
        )}
      </div>
    </div>
  );
}
