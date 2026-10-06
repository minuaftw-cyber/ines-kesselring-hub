import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import Thumb from "@/components/Thumb";
import { getSeriesDetail } from "@/lib/api";
import { formatDate } from "@/lib/format";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const series = await getSeriesDetail((await params).slug).catch(() => null);
  return { title: series?.title ?? "ไม่พบซีรีส์" };
}

export default async function SeriesPage({ params }: Props) {
  const { slug } = await params;
  const series = await getSeriesDetail(slug);
  if (!series) notFound();

  const first = series.videos[0];

  return (
    <div className="container">
      <div className="series-head">
        <div>
          <Link className="back-link" href="/videos">
            กลับไปหน้าวิดีโอ
          </Link>
          <h1>{series.title}</h1>
          {series.description ? <p>{series.description}</p> : null}
          <p>{series.video_count} วิดีโอ</p>
        </div>
        {first ? (
          <Thumb src={series.thumbnail} title={series.title} sizes="(max-width: 960px) 100vw, 420px" priority />
        ) : null}
      </div>

      <section className="section" aria-label="รายการวิดีโอ" style={{ marginTop: 48 }}>
        {series.videos.length === 0 ? (
          <p className="empty">ซีรีส์นี้ยังไม่มีวิดีโอ</p>
        ) : (
          <ol className="episode-list">
            {series.videos.map((video, index) => {
              const href = video.is_demo ? undefined : video.youtube_url;
              return (
                <li key={video.id} className="episode">
                  <span className="episode-no">{String(index + 1).padStart(2, "0")}</span>
                  <Thumb src={video.thumbnail} title={video.title} sizes="220px" />
                  <a href={href} target={href ? "_blank" : undefined} rel={href ? "noopener noreferrer" : undefined}>
                    <h3>{video.title}</h3>
                    <p className="video-meta">{formatDate(video.published_at)}</p>
                  </a>
                </li>
              );
            })}
          </ol>
        )}
      </section>
    </div>
  );
}
