import Image from "next/image";

interface ThumbProps {
  src: string;
  title: string;
  series?: string | null;
  sizes: string;
  priority?: boolean;
  children?: React.ReactNode;
}

/** 16:9 thumbnail. Sample videos without a YouTube image get a broadcast slate instead. */
export default function Thumb({ src, title, series, sizes, priority, children }: ThumbProps) {
  return (
    <div className="thumb">
      {src ? (
        <Image src={src} alt="" fill sizes={sizes} preload={priority} style={{ objectFit: "cover" }} />
      ) : (
        <div className="slate" aria-hidden="true">
          {series ? <span className="slate-series">{series}</span> : null}
          <span className="slate-title">{title}</span>
        </div>
      )}
      {children}
    </div>
  );
}
