import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getArticle } from "@/lib/api";
import { formatDate, paragraphs } from "@/lib/format";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const article = await getArticle((await params).slug).catch(() => null);
  return { title: article?.title ?? "ไม่พบข่าว", description: article?.excerpt };
}

export default async function ArticlePage({ params }: Props) {
  const { slug } = await params;
  const article = await getArticle(slug);
  if (!article) notFound();

  return (
    <article className="container article">
      <Link className="back-link" href="/news">
        กลับไปหน้าข่าวสาร
      </Link>
      <div className="article-meta">
        <time dateTime={article.published_at}>{formatDate(article.published_at)}</time>
        <span>โดย {article.author_name}</span>
        {article.is_members_only ? <span className="tag tag-members">เฉพาะสมาชิก</span> : null}
      </div>
      <h1>{article.title}</h1>

      {article.cover_image ? (
        // Uploaded through the backoffice and served by Django.
        // eslint-disable-next-line @next/next/no-img-element
        <img className="article-cover" src={article.cover_image} alt="" />
      ) : null}

      <div className="article-body">
        {paragraphs(article.body).map((text, index) => (
          <p key={index}>{text}</p>
        ))}
      </div>

      {article.locked ? (
        <aside className="locked-note">
          <h2>อ่านต่อได้เมื่อเป็นสมาชิก</h2>
          <p>บทความนี้เปิดให้อ่านฉบับเต็มเฉพาะสมาชิก สมัครฟรีและใช้เวลาไม่ถึงนาที</p>
          <div className="board-actions" style={{ marginTop: 0 }}>
            <Link className="button button-primary" href="/register">
              สมัครสมาชิก
            </Link>
            <Link className="button" href={`/login?next=/news/${article.slug}`}>
              เข้าสู่ระบบ
            </Link>
          </div>
        </aside>
      ) : null}
    </article>
  );
}
