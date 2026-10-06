import { formatDate } from "@/lib/format";
import type { Video } from "@/lib/types";

import Thumb from "./Thumb";

export default function VideoCard({ video }: { video: Video }) {
  const href = video.is_demo ? undefined : video.youtube_url;
  return (
    <a
      className="video-card"
      href={href}
      target={href ? "_blank" : undefined}
      rel={href ? "noopener noreferrer" : undefined}
      aria-disabled={href ? undefined : true}
    >
      <Thumb
        src={video.thumbnail}
        title={video.title}
        series={video.series?.title}
        sizes="(max-width: 640px) 100vw, (max-width: 960px) 50vw, 380px"
      />
      <div>
        <h3>{video.title}</h3>
        <p className="video-meta">
          {video.series ? `${video.series.title}, ` : ""}
          {formatDate(video.published_at)}
        </p>
      </div>
    </a>
  );
}
