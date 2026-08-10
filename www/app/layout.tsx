import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";

const TITLE = "crecity — 크리에이터 마켓플레이스";
const DESCRIPTION = "브랜드와 크리에이터를 잇는 셀프서브 마켓플레이스";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="h-full antialiased">
      <body className="min-h-full">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
