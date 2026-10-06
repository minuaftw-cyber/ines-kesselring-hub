import Link from "next/link";

import { getCurrentUser } from "@/lib/auth";

import NavMenu from "./NavMenu";

export default async function SiteHeader() {
  const user = await getCurrentUser();
  const accountLabel = user ? user.display_name || "บัญชีของฉัน" : null;

  return (
    <header className="site-header">
      <div className="container site-header-inner">
        <Link href="/" className="wordmark">
          <span className="wordmark-signal" aria-hidden="true" />
          Ines Kesselring
        </Link>
        <NavMenu accountLabel={accountLabel} />
      </div>
    </header>
  );
}
