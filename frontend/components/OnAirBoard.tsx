"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { formatDayMonth, formatDuration, formatTime, formatWeekday, isLiveNow } from "@/lib/format";
import type { LiveStream } from "@/lib/types";

interface Props {
  streams: LiveStream[];
  /** Server time when the page was rendered, so server and browser start from the same value. */
  renderedAt: number;
  signedIn: boolean;
}

function splitDuration(ms: number) {
  const total = Math.max(0, Math.floor(ms / 1000));
  return {
    days: Math.floor(total / 86400),
    hours: Math.floor((total % 86400) / 3600),
    minutes: Math.floor((total % 3600) / 60),
    seconds: total % 60,
  };
}

const pad = (n: number) => String(n).padStart(2, "0");

export default function OnAirBoard({ streams, renderedAt, signedIn }: Props) {
  const [now, setNow] = useState(renderedAt);

  useEffect(() => {
    // Start from the visitor's clock, then tick every second.
    const tick = () => setNow(Date.now());
    const first = window.setTimeout(tick, 0);
    const timer = window.setInterval(tick, 1000);
    return () => {
      window.clearTimeout(first);
      window.clearInterval(timer);
    };
  }, []);

  const live = streams.find((s) => isLiveNow(s, now));
  const next = streams.find((s) => s.status === "scheduled" && Date.parse(s.scheduled_at) > now);
  const stream = live ?? next;

  if (!stream) {
    return (
      <section className="board board-empty" aria-labelledby="board-title">
        <span className="board-status">
          <span className="dot" aria-hidden="true" />
          ยังไม่มีไลฟ์ที่ประกาศไว้
        </span>
        <div>
          <h2 id="board-title">ไลฟ์ครั้งหน้ากำลังจะประกาศเร็ว ๆ นี้</h2>
          <p className="board-meta">กดติดตามช่อง YouTube ไว้ จะได้รู้ทันทีที่มีไลฟ์ใหม่</p>
          <div className="board-actions">
            <a
              className="button button-on-board"
              href="https://www.youtube.com/@InesKesselring"
              target="_blank"
              rel="noopener noreferrer"
            >
              ติดตามบน YouTube
            </a>
          </div>
        </div>
      </section>
    );
  }

  const isLive = stream === live;
  const remaining = splitDuration(Date.parse(stream.scheduled_at) - now);
  const locked = stream.is_members_only && !signedIn;
  const units = [
    { value: remaining.days, label: "วัน" },
    { value: remaining.hours, label: "ชั่วโมง" },
    { value: remaining.minutes, label: "นาที" },
    { value: remaining.seconds, label: "วินาที" },
  ];

  return (
    <section className={`board${isLive ? " is-live" : ""}`} aria-labelledby="board-title">
      <span className="board-status">
        <span className="dot" aria-hidden="true" />
        {isLive ? "กำลังไลฟ์อยู่ตอนนี้" : "ไลฟ์ถัดไป"}
      </span>

      {isLive ? null : (
        <div className="countdown" role="timer" aria-label="เวลาที่เหลือก่อนเริ่มไลฟ์">
          {units.map((unit, index) => (
            <div className="countdown-unit" key={unit.label}>
              <strong>{index === 0 ? unit.value : pad(unit.value)}</strong>
              <span>{unit.label}</span>
            </div>
          ))}
        </div>
      )}

      <div>
        <h2 id="board-title" className="board-title">
          {stream.title}
        </h2>
        <p className="board-meta">
          {formatWeekday(stream.scheduled_at)} {formatDayMonth(stream.scheduled_at)} เวลา {formatTime(stream.scheduled_at)}{" "}
          ยาวประมาณ {formatDuration(stream.duration_minutes)}
          {stream.is_members_only ? " (ไลฟ์เฉพาะสมาชิก)" : ""}
        </p>
        <div className="board-actions">
          {locked ? (
            <Link className="button button-on-board" href="/login?next=/">
              เข้าสู่ระบบเพื่อดูลิงก์ไลฟ์สมาชิก
            </Link>
          ) : stream.stream_url ? (
            <a className="button button-on-board" href={stream.stream_url} target="_blank" rel="noopener noreferrer">
              {isLive ? "เข้าไปดูไลฟ์" : "ตั้งเตือนบน YouTube"}
            </a>
          ) : null}
          <Link className="button" href="/schedule">
            ดูตารางทั้งหมด
          </Link>
        </div>
      </div>
    </section>
  );
}
