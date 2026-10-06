import Link from "next/link";

import NewsList from "@/components/NewsList";
import OnAirBoard from "@/components/OnAirBoard";
import Thumb from "@/components/Thumb";
import Timetable from "@/components/Timetable";
import VideoCard from "@/components/VideoCard";
import { getArticles, getSchedule, getSeries, getVideos, requestTime } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth";
import { formatDate } from "@/lib/format";

export default async function HomePage() {
  const [schedule, videos, series, articles, user] = await Promise.all([
    getSchedule(),
    getVideos(),
    getSeries(),
    getArticles(),
    getCurrentUser(),
  ]);
  const renderedAt = await requestTime();
  const [latest, ...more] = videos.results;
  const weekAhead = schedule.filter((s) => Date.parse(s.scheduled_at) < renderedAt + 7 * 86400000);

  return (
    <div className="container">
      <div className="hero">
        <OnAirBoard streams={schedule} renderedAt={renderedAt} signedIn={Boolean(user)} />

        {latest ? (
          <a
            className="feature-video"
            href={latest.is_demo ? undefined : latest.youtube_url}
            target={latest.is_demo ? undefined : "_blank"}
            rel={latest.is_demo ? undefined : "noopener noreferrer"}
          >
            <Thumb
              src={latest.thumbnail}
              title={latest.title}
              series={latest.series?.title}
              sizes="(max-width: 960px) 100vw, 560px"
              priority
            />
            <div>
              <p className="kicker">
                วิดีโอล่าสุด, {formatDate(latest.published_at)}
              </p>
              <h2>{latest.title}</h2>
            </div>
          </a>
        ) : (
          <div className="empty">ยังไม่มีวิดีโอ</div>
        )}
      </div>

      {series.length > 0 ? (
        <section className="section" aria-labelledby="series-title">
          <div className="section-head">
            <div>
              <h2 id="series-title">ซีรีส์</h2>
              <p>เลือกดูตามแนวที่ชอบ ตั้งแต่ไลฟ์คุยเล่นไปจนถึงเบื้องหลังการสร้าง AI VTuber</p>
            </div>
            <Link className="text-link" href="/videos">
              ดูวิดีโอทั้งหมด
            </Link>
          </div>
          <div className="shelf">
            {series.map((item) => (
              <Link key={item.id} className="shelf-item" href={`/series/${item.slug}`}>
                <Thumb src={item.thumbnail} title={item.title} sizes="300px">
                  <span className="count-badge">{item.video_count} วิดีโอ</span>
                </Thumb>
                <div>
                  <h3>{item.title}</h3>
                  {item.description ? <p>{item.description}</p> : null}
                </div>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      {more.length > 0 ? (
        <section className="section" aria-labelledby="videos-title">
          <div className="section-head">
            <h2 id="videos-title">วิดีโอใหม่</h2>
            <Link className="text-link" href="/videos">
              ดูทั้งหมด
            </Link>
          </div>
          <div className="video-grid">
            {more.slice(0, 6).map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        </section>
      ) : null}

      <section className="section" aria-labelledby="week-title">
        <div className="section-head">
          <div>
            <h2 id="week-title">ไลฟ์ 7 วันข้างหน้า</h2>
            <p>เวลาทั้งหมดเป็นเวลาประเทศไทย</p>
          </div>
          <Link className="text-link" href="/schedule">
            ตารางทั้งหมด
          </Link>
        </div>
        <Timetable streams={weekAhead} signedIn={Boolean(user)} renderedAt={renderedAt} />
      </section>

      {user ? null : (
        <section className="section members-band" aria-labelledby="members-title">
          <div>
            <h2 id="members-title">เป็นสมาชิกฟรี แล้วไม่พลาดอะไรเลย</h2>
            <p>สมาชิกอ่านบทความเบื้องหลังฉบับเต็ม และเห็นลิงก์ไลฟ์เฉพาะสมาชิกได้ทันที</p>
          </div>
          <Link className="button button-primary" href="/register">
            สมัครสมาชิก
          </Link>
        </section>
      )}

      <section className="section" aria-labelledby="news-title">
        <div className="section-head">
          <h2 id="news-title">ข่าวสาร</h2>
          <Link className="text-link" href="/news">
            ข่าวทั้งหมด
          </Link>
        </div>
        <NewsList articles={articles.results.slice(0, 3)} />
      </section>
    </div>
  );
}
