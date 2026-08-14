"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { formatFollowers } from "@/lib/labels";
import type { CreatorPackage, PortfolioItem, ProfileAnalytics, ProfileFaq } from "@/lib/types";

/**
 * 크리에이터 온보딩 진행률(갭 #58).
 *
 * 심사(갭 #16)는 채널 지표와 콘텐츠 품질을 함께 본다 — 여기서는 **무엇이 비어 있는지**만
 * 알려주고 통과 여부를 예단하지 않는다(기준값은 백엔드 설정이고 최종 판단은 운영자 몫).
 */
export default function OnboardingChecklist({ slug }: { slug: string }) {
  const packages = useQuery({
    queryKey: ["myPackages", slug],
    queryFn: () => apiFetch<CreatorPackage[]>(`/creator/profiles/${slug}/packages`),
  });
  const analytics = useQuery({
    queryKey: ["myAnalytics"],
    queryFn: () => apiFetch<ProfileAnalytics[]>("/creator/my/analytics"),
  });
  const portfolio = useQuery({
    queryKey: ["portfolio", slug],
    queryFn: () => apiFetch<PortfolioItem[]>(`/creator/profiles/${slug}/portfolio`),
  });
  const faqs = useQuery({
    queryKey: ["myFaqs"],
    queryFn: () => apiFetch<ProfileFaq[]>("/creator/my/faqs"),
  });

  // 하나라도 아직 안 왔으면 그리지 않는다(반쯤 채워진 진행률은 오해를 부른다)
  if (!packages.data || !analytics.data || !portfolio.data || !faqs.data) return null;

  const followers = analytics.data.reduce((sum, item) => sum + item.followers_count, 0);
  const items = [
    { done: true, label: "프로필 등록", hint: "완료", href: null },
    {
      done: packages.data.length > 0,
      label: "판매 패키지",
      hint: packages.data.length > 0 ? `${packages.data.length}개 등록` : "가격을 공개해야 팔립니다",
      href: "/dashboard/packages",
    },
    {
      done: analytics.data.length > 0,
      label: "채널 지표",
      hint:
        analytics.data.length > 0
          ? `${analytics.data.length}개 채널 · 팔로워 합계 ${formatFollowers(followers)}`
          : "심사에서 확인하는 항목입니다",
      href: null,
    },
    {
      done: portfolio.data.length > 0,
      label: "포트폴리오",
      hint: portfolio.data.length > 0 ? `사진 ${portfolio.data.length}장` : "결과물 품질을 보여줍니다",
      href: null,
    },
    {
      done: faqs.data.length > 0,
      label: "자주 묻는 질문",
      hint: faqs.data.length > 0 ? `${faqs.data.length}개` : "선택 — 있으면 문의가 줄어요",
      href: null,
    },
  ];

  const done = items.filter((item) => item.done).length;
  const percent = Math.round((done / items.length) * 100);

  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">프로필 완성도</h3>
          <span className="text-sm font-semibold">
            {done}/{items.length}
          </span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-secondary">
          <div className="h-full rounded-full bg-primary" style={{ width: `${percent}%` }} />
        </div>
        <ul className="mt-4 grid gap-2">
          {items.map((item) => (
            <li key={item.label} className="flex items-start gap-2 text-sm">
              <span
                className={`mt-0.5 inline-flex size-4.5 shrink-0 items-center justify-center rounded-full text-[11px] ${
                  item.done
                    ? "bg-primary text-primary-foreground"
                    : "border border-input text-muted-foreground"
                }`}
              >
                {item.done ? "✓" : ""}
              </span>
              <span className={item.done ? "" : "font-medium"}>
                {item.label}
                <span className="ml-1.5 text-[13px] text-muted-foreground">{item.hint}</span>
                {!item.done && item.href && (
                  <Link
                    href={item.href}
                    className="ml-1.5 text-[13px] font-semibold text-primary hover:underline"
                  >
                    등록하기
                  </Link>
                )}
              </span>
            </li>
          ))}
        </ul>
        {done < items.length && (
          <p className="mt-3 text-xs text-muted-foreground">
            아래 각 섹션에서 바로 등록할 수 있어요. 채우면 심사와 브랜드 탐색에 모두 유리합니다.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
