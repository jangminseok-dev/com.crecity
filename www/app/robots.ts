import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // 로그인 필요·개인 영역은 색인 제외
      disallow: ["/dashboard", "/admin", "/chat", "/orders", "/notifications", "/oauth", "/api"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
