const TZ = "Asia/Bangkok";

const dateFmt = new Intl.DateTimeFormat("th-TH", { timeZone: TZ, day: "numeric", month: "short", year: "numeric" });
const dayFmt = new Intl.DateTimeFormat("th-TH", { timeZone: TZ, weekday: "long" });
const shortDayFmt = new Intl.DateTimeFormat("th-TH", { timeZone: TZ, weekday: "short" });
const dayMonthFmt = new Intl.DateTimeFormat("th-TH", { timeZone: TZ, day: "numeric", month: "short" });
const timeFmt = new Intl.DateTimeFormat("th-TH", { timeZone: TZ, hour: "2-digit", minute: "2-digit", hour12: false });

export const formatDate = (iso: string) => dateFmt.format(new Date(iso));
export const formatWeekday = (iso: string) => dayFmt.format(new Date(iso));
export const formatShortWeekday = (iso: string) => shortDayFmt.format(new Date(iso));
export const formatDayMonth = (iso: string) => dayMonthFmt.format(new Date(iso));
export const formatTime = (iso: string) => `${timeFmt.format(new Date(iso))} น.`;

export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h && m) return `${h} ชม. ${m} นาที`;
  if (h) return `${h} ชม.`;
  return `${m} นาที`;
}

/** A stream counts as live if it is marked live, or now falls inside its time slot. */
export function isLiveNow(stream: { status: string; scheduled_at: string; ends_at: string }, now: number): boolean {
  if (stream.status === "live") return true;
  if (stream.status !== "scheduled") return false;
  return now >= Date.parse(stream.scheduled_at) && now < Date.parse(stream.ends_at);
}

export const paragraphs = (text: string) =>
  text
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);
