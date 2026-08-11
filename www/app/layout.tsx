import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";
import SiteFooter from "@/components/site-footer";
import SiteHeader from "@/components/site-header";
import { SITE_URL } from "@/lib/site";

const TITLE = "crecity — 크리에이터 마켓플레이스";
const DESCRIPTION = "브랜드와 크리에이터를 잇는 셀프서브 마켓플레이스";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: TITLE, template: "%s | crecity" },
  description: DESCRIPTION,
  openGraph: {
    siteName: "crecity",
    type: "website",
    locale: "ko_KR",
    title: TITLE,
    description: DESCRIPTION,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="h-full font-sans antialiased">
      <body className="flex min-h-dvh flex-col">
        <Providers>
          <SiteHeader />
          <main className="flex-1">{children}</main>
          <SiteFooter />
        </Providers>
      </body>
    </html>
  );
}
