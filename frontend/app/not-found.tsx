import Link from "next/link";

export default function NotFound() {
  return (
    <div className="container page-head">
      <h1>ไม่พบหน้านี้</h1>
      <p>ลิงก์อาจถูกย้ายหรือพิมพ์ผิด ลองกลับไปที่หน้าแรกหรือดูวิดีโอทั้งหมด</p>
      <div className="board-actions">
        <Link className="button button-primary" href="/">
          กลับหน้าแรก
        </Link>
        <Link className="button" href="/videos">
          ดูวิดีโอ
        </Link>
      </div>
    </div>
  );
}
