"use client";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="container page-head">
      <h1>โหลดหน้านี้ไม่สำเร็จ</h1>
      <p>เซิร์ฟเวอร์ตอบกลับไม่ทัน ลองโหลดใหม่อีกครั้ง ถ้ายังไม่ได้ ระบบอาจกำลังปรับปรุงอยู่</p>
      <div className="board-actions">
        <button className="button button-primary" type="button" onClick={reset}>
          ลองใหม่
        </button>
      </div>
    </div>
  );
}
