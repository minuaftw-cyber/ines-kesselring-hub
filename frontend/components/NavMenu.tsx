"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const LINKS = [
  { href: "/videos", label: "วิดีโอ" },
  { href: "/schedule", label: "ตารางไลฟ์" },
  { href: "/news", label: "ข่าวสาร" },
];

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function NavMenu({ accountLabel }: { accountLabel: string | null }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  const close = () => setOpen(false);
  const series = pathname.startsWith("/series/");

  return (
    <>
      <button
        type="button"
        className="nav-toggle"
        aria-expanded={open}
        aria-controls="site-nav"
        aria-label={open ? "ปิดเมนู" : "เปิดเมนู"}
        onClick={() => setOpen((value) => !value)}
      >
        <span />
        <span />
        <span />
      </button>

      <nav id="site-nav" className={`site-nav${open ? " is-open" : ""}`} aria-label="เมนูหลัก">
        {LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            onClick={close}
            aria-current={isActive(pathname, link.href) || (series && link.href === "/videos") ? "page" : undefined}
          >
            {link.label}
          </Link>
        ))}
        <Link
          href={accountLabel ? "/account" : "/login"}
          className="nav-account"
          onClick={close}
          aria-current={isActive(pathname, "/account") || isActive(pathname, "/login") ? "page" : undefined}
        >
          {accountLabel ?? "เข้าสู่ระบบ"}
        </Link>
      </nav>
    </>
  );
}
