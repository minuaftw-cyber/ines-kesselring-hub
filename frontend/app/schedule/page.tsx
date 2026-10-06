import type { Metadata } from "next";

import Timetable from "@/components/Timetable";
import { getPastStreams, getSchedule, requestTime } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth";

export const metadata: Metadata = { title: "ตารางไลฟ์" };

export default async function SchedulePage() {
  const [upcoming, past, user] = await Promise.all([getSchedule(), getPastStreams(), getCurrentUser()]);
  const renderedAt = await requestTime();

  return (
    <div className="container">
      <header className="page-head">
        <h1>ตารางไลฟ์</h1>
        <p>เวลาทั้งหมดเป็นเวลาประเทศไทย ไลฟ์เฉพาะสมาชิกจะแสดงลิงก์เมื่อเข้าสู่ระบบแล้ว</p>
      </header>

      <section className="section" aria-labelledby="upcoming-title" style={{ marginTop: 48 }}>
        <div className="section-head">
          <h2 id="upcoming-title">กำลังจะมาถึง</h2>
        </div>
        <Timetable streams={upcoming} signedIn={Boolean(user)} renderedAt={renderedAt} />
      </section>

      {past.length > 0 ? (
        <section className="section" aria-labelledby="past-title">
          <div className="section-head">
            <h2 id="past-title">ไลฟ์ที่ผ่านมา</h2>
          </div>
          <Timetable streams={past} signedIn={Boolean(user)} renderedAt={renderedAt} past />
        </section>
      ) : null}
    </div>
  );
}
