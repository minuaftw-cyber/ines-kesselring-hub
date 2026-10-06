import Link from "next/link";

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="container site-footer-inner">
        <p>© {new Date().getFullYear()} Ines Kesselring</p>
        <nav aria-label="ลิงก์ส่วนท้าย">
          <Link href="/videos">วิดีโอ</Link>
          <Link href="/schedule">ตารางไลฟ์</Link>
          <Link href="/news">ข่าวสาร</Link>
          <a href="https://www.youtube.com/@InesKesselring" target="_blank" rel="noopener noreferrer">
            YouTube
          </a>
        </nav>
      </div>
    </footer>
  );
}
