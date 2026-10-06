import type { Metadata } from "next";
import Link from "next/link";

import NewsList from "@/components/NewsList";
import { getArticles } from "@/lib/api";

export const metadata: Metadata = { title: "ข่าวสาร" };

export default async function NewsPage({ searchParams }: { searchParams: Promise<{ page?: string }> }) {
  const { page: rawPage } = await searchParams;
  const page = Math.max(1, Number.parseInt(rawPage ?? "1", 10) || 1);
  const articles = await getArticles(page);

  return (
    <div className="container">
      <header className="page-head">
        <h1>ข่าวสาร</h1>
        <p>อัปเดตของช่อง ประกาศไลฟ์ และบทความเบื้องหลัง</p>
      </header>
      <section className="section" style={{ marginTop: 48 }} aria-label="รายการข่าว">
        <NewsList articles={articles.results} />
        <nav className="pager" aria-label="เปลี่ยนหน้า">
          {articles.previous ? (
            <Link className="button" href={`/news?page=${page - 1}`}>
              หน้าก่อนหน้า
            </Link>
          ) : (
            <span />
          )}
          {articles.next ? (
            <Link className="button" href={`/news?page=${page + 1}`}>
              หน้าถัดไป
            </Link>
          ) : null}
        </nav>
      </section>
    </div>
  );
}
