import Link from "next/link";

import { formatDayMonth, formatDuration, formatTime, formatWeekday, isLiveNow } from "@/lib/format";
import type { LiveStream } from "@/lib/types";

interface Props {
  streams: LiveStream[];
  signedIn: boolean;
  renderedAt: number;
  past?: boolean;
}

const PLATFORM: Record<LiveStream["platform"], string> = {
  youtube: "YouTube",
  tiktok: "TikTok",
  other: "ไลฟ์",
};

export default function Timetable({ streams, signedIn, renderedAt, past = false }: Props) {
  if (streams.length === 0) {
    return (
      <p className="empty">
        {past ? "ยังไม่มีไลฟ์ที่ผ่านมา" : "ยังไม่มีไลฟ์ในตาราง ติดตามช่องไว้เพื่อรับแจ้งเตือนเมื่อมีไลฟ์ใหม่"}
      </p>
    );
  }

  return (
    <ol className="timetable">
      {streams.map((stream) => {
        const live = !past && isLiveNow(stream, renderedAt);
        const locked = stream.is_members_only && !signedIn;
        return (
          <li key={stream.id} className={`slot${live ? " is-live" : ""}`}>
            <div className="slot-day">
              {formatWeekday(stream.scheduled_at)}
              <span>{formatDayMonth(stream.scheduled_at)}</span>
            </div>
            <div className="slot-time">{formatTime(stream.scheduled_at)}</div>
            <div className="slot-body">
              <p className="slot-title">{stream.title}</p>
              {stream.description ? <p className="slot-desc">{stream.description}</p> : null}
              <div className="slot-tags">
                {live ? <span className="tag tag-live">กำลังไลฟ์</span> : null}
                {stream.status === "cancelled" ? <span className="tag">ยกเลิก</span> : null}
                <span className="tag">{PLATFORM[stream.platform]}</span>
                <span className="tag">{formatDuration(stream.duration_minutes)}</span>
                {stream.is_members_only ? <span className="tag tag-members">เฉพาะสมาชิก</span> : null}
              </div>
            </div>
            {past ? null : (
              <div className="slot-action">
                {locked ? (
                  <Link className="text-link" href="/login?next=/schedule">
                    เข้าสู่ระบบเพื่อดูลิงก์
                  </Link>
                ) : stream.stream_url ? (
                  <a
                    className={`button${live ? " button-live" : ""}`}
                    href={stream.stream_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {live ? "ดูไลฟ์" : "ตั้งเตือน"}
                    <span className="visually-hidden">: {stream.title}</span>
                  </a>
                ) : null}
              </div>
            )}
          </li>
        );
      })}
    </ol>
  );
}
