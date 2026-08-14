import { ImageResponse } from "next/og";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

import { formatFollowers, formatKrw } from "@/lib/labels";
import { backendGet } from "@/lib/server/backend-api";
import type { CreatorPackage, CreatorProfile } from "@/lib/types";

/* 프로필 공유 카드(§2.3-2, 갭 #46) — SNS·메신저에 링크를 붙였을 때 뜨는 이미지 */
export const alt = "crecity 크리에이터 프로필";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/* 색은 디자인 시스템 토큰과 같은 값(globals.css) — CSS 변수를 쓸 수 없어 리터럴로 둔다 */
const INK = "#191f28";
const MUTED = "#6b7684";
const PRIMARY = "#3556ee";
const ACCENT = "#eef2ff";
const ACCENT_INK = "#2743d6";
const BORDER = "#e5e8eb";

// 폰트는 요청 데이터와 무관하므로 모듈 스코프에서 한 번만 읽는다(Next 문서 권장)
const [bold, regular] = await Promise.all([
  readFile(join(process.cwd(), "assets/Pretendard-Bold.otf")),
  readFile(join(process.cwd(), "assets/Pretendard-Regular.otf")),
]);

function Badge({ text, filled = false }: { text: string; filled?: boolean }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        height: 62,
        padding: "0 28px",
        borderRadius: 999,
        fontSize: 28,
        fontWeight: filled ? 700 : 400,
        color: filled ? ACCENT_INK : MUTED,
        background: filled ? ACCENT : "#ffffff",
        border: `2px solid ${filled ? ACCENT : BORDER}`,
      }}
    >
      {text}
    </div>
  );
}

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const profile = await backendGet<CreatorProfile>(
    `/creator/profiles/${encodeURIComponent(slug)}`
  );
  // 최저가는 프로필 카드와 같은 기준(판매 패키지 중 최저) — 없으면 배지를 빼고 그린다
  const packages = profile
    ? await backendGet<CreatorPackage[]>(`/creator/profiles/${encodeURIComponent(slug)}/packages`)
    : null;
  const priceFrom = packages?.length
    ? Math.min(...packages.map((pkg) => pkg.price_krw))
    : null;

  const name = profile?.name ?? "crecity";
  const tagline = profile
    ? profile.tagline.length > 46
      ? `${profile.tagline.slice(0, 46)}…`
      : profile.tagline
    : "가격이 공개된 크리에이터를 찾고, 에스크로로 안전하게 협업하세요";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "70px 80px",
          background: "linear-gradient(180deg, #f9fafb 0%, #ffffff 60%)",
          fontFamily: "Pretendard",
        }}
      >
        {/* 워드마크 */}
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 52,
              height: 52,
              borderRadius: 16,
              background: PRIMARY,
              color: "#ffffff",
              fontSize: 32,
              fontWeight: 700,
            }}
          >
            c
          </div>
          <div style={{ fontSize: 34, fontWeight: 700, color: PRIMARY }}>crecity</div>
        </div>

        {/* 아래쪽 한 덩이 — 이름과 신뢰 신호가 떨어져 보이지 않게 묶는다 */}
        <div style={{ display: "flex", flexDirection: "column", gap: 48 }}>
          {/* 이니셜 아바타 + 이름·소개 */}
          <div style={{ display: "flex", alignItems: "center", gap: 44 }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: 184,
                height: 184,
                borderRadius: 64,
                background: ACCENT,
                color: ACCENT_INK,
                fontSize: 92,
                fontWeight: 700,
              }}
            >
              {name.slice(0, 1)}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 18, maxWidth: 760 }}>
              <div
                style={{
                  fontSize: name.length > 10 ? 62 : 78,
                  fontWeight: 700,
                  color: INK,
                  lineHeight: 1.15,
                }}
              >
                {name}
              </div>
              {tagline && (
                <div style={{ fontSize: 34, color: MUTED, lineHeight: 1.35 }}>{tagline}</div>
              )}
            </div>
          </div>

          {/* 신뢰 신호 — 있는 것만 그린다(없는 값을 지어내지 않는다) */}
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {profile && <Badge text={`${profile.primary_category} 크리에이터`} />}
            {profile?.location && <Badge text={profile.location} />}
            {profile && profile.followers_total > 0 && (
              <Badge text={`팔로워 ${formatFollowers(profile.followers_total)}`} />
            )}
            {priceFrom !== null && <Badge text={`${formatKrw(priceFrom)}부터`} filled />}
          </div>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        { name: "Pretendard", data: bold, style: "normal", weight: 700 },
        { name: "Pretendard", data: regular, style: "normal", weight: 400 },
      ],
    }
  );
}
