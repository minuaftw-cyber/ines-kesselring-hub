import type { Metadata } from "next";
import Link from "next/link";

import Thumb from "@/components/Thumb";
import VideoCard from "@/components/VideoCard";
import { getSeries, getVideos } from "@/lib/api";

export const metadata: Metadata = { title: "วิดีโอ" };

export default async function VideosPage({ searchParams }: { searchParams: Promise<{ page?: string }> }) {
  const { page: rawPage } = await searchParams;
  const page = Math.max(1, Number.parseInt(rawPage ?? "1", 10) || 1);
  const [videos, series] = await Promise.all([getVideos(page), page === 1 ? getSeries() : Promise.resolve([])]);

  return (
    <div className="container">
      <header className="page-head">
        <h1>วิดีโอ</h1>
        <p>วิดีโอทั้งหมดของช่อง เรียงจากใหม่ไปเก่า กดที่วิดีโอเพื่อดูบน YouTube</p>
      </header>

      {series.length > 0 ? (
        <section className="section" aria-labelledby="series-title" style={{ marginTop: 48 }}>
          <div className="section-head">
            <h2 id="series-title">ดูตามซีรีส์</h2>
          </div>
          <div className="shelf">
            {series.map((item) => (
              <Link key={item.id} className="shelf-item" href={`/series/${item.slug}`}>
                <Thumb src={item.thumbnail} title={item.title} sizes="300px">
                  <span className="count-badge">{item.video_count} วิดีโอ</span>
                </Thumb>
                <h3>{item.title}</h3>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      <section className="section" aria-labelledby="all-title">
        <div className="section-head">
          <h2 id="all-title">ทั้งหมด {videos.count} วิดีโอ</h2>
        </div>
        {videos.results.length === 0 ? (
          <p className="empty">ยังไม่มีวิดีโอในหน้านี้</p>
        ) : (
          <div className="video-grid">
            {videos.results.map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        )}
        <nav className="pager" aria-label="เปลี่ยนหน้า">
          {videos.previous ? (
            <Link className="button" href={`/videos?page=${page - 1}`}>
              หน้าก่อนหน้า
            </Link>
          ) : (
            <span />
          )}
          {videos.next ? (
            <Link className="button" href={`/videos?page=${page + 1}`}>
              หน้าถัดไป
            </Link>
          ) : null}
        </nav>
      </section>
    </div>
  );
}
