export type Role = "member" | "staff" | "admin";

export interface User {
  id: number;
  email: string;
  display_name: string;
  role: Role;
  can_access_backoffice: boolean;
  date_joined: string;
}

export interface Video {
  id: number;
  youtube_id: string;
  title: string;
  description: string;
  thumbnail: string;
  youtube_url: string;
  published_at: string;
  position: number;
  is_demo: boolean;
  series: { slug: string; title: string } | null;
}

export interface Series {
  id: number;
  slug: string;
  title: string;
  description: string;
  thumbnail: string;
  video_count: number;
}

export interface SeriesDetail extends Series {
  videos: Video[];
}

export interface LiveStream {
  id: number;
  title: string;
  description: string;
  scheduled_at: string;
  ends_at: string;
  duration_minutes: number;
  platform: "youtube" | "tiktok" | "other";
  stream_url: string;
  status: "scheduled" | "live" | "ended" | "cancelled";
  is_members_only: boolean;
}

export interface ArticleSummary {
  id: number;
  slug: string;
  title: string;
  excerpt: string;
  cover_image: string;
  author_name: string;
  is_members_only: boolean;
  published_at: string;
}

export interface Article extends ArticleSummary {
  body: string;
  locked: boolean;
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
