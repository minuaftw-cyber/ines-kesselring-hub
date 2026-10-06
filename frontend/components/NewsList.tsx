import Link from "next/link";

import { formatDate } from "@/lib/format";
import type { ArticleSummary } from "@/lib/types";

export default function NewsList({ articles }: { articles: ArticleSummary[] }) {
  if (articles.length === 0) {
    return <p className="empty">ยังไม่มีข่าวสาร</p>;
  }
  return (
    <ul className="news-list">
      {articles.map((article) => (
        <li key={article.id} className="news-item">
          <time className="news-date" dateTime={article.published_at}>
            {formatDate(article.published_at)}
          </time>
          <div>
            <Link href={`/news/${article.slug}`}>
              <h3>{article.title}</h3>
            </Link>
            {article.excerpt ? <p>{article.excerpt}</p> : null}
            {article.is_members_only ? (
              <div className="slot-tags">
                <span className="tag tag-members">เฉพาะสมาชิก</span>
              </div>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}
