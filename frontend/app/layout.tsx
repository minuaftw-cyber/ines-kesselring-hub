import type { Metadata } from "next";

import "@fontsource/chakra-petch/600.css";
import "@fontsource/chakra-petch/700.css";
import "@fontsource-variable/anuphan";
import "./globals.css";

import SiteFooter from "@/components/SiteFooter";
import SiteHeader from "@/components/SiteHeader";

export const metadata: Metadata = {
  title: {
    default: "Ines Kesselring",
    template: "%s | Ines Kesselring",
  },
  description: "วิดีโอ ตารางไลฟ์ และข่าวสารของช่อง Ines Kesselring",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="th">
      <body>
        <a className="visually-hidden" href="#main">
          ข้ามไปยังเนื้อหา
        </a>
        <SiteHeader />
        <main id="main">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
