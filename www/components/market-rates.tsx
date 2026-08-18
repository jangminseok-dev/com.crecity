"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { PLATFORM_LABELS, formatKrw } from "@/lib/labels";

type MarketRate = {
  category: string;
  platform: string;
  sample_count: number;
  median_krw: number;
  p25_krw: number;
  p75_krw: number;
};

function platformLabel(platform: string): string {
  return platform in PLATFORM_LABELS
    ? PLATFORM_LABELS[platform as keyof typeof PLATFORM_LABELS]
    : platform;
}

/**
 * 실거래 시세(갭 #89) — crecity 완료 거래 기반 카테고리×플랫폼 중앙값·범위.
 * 계산기의 시장 참고치와 달리 **플랫폼 안에서 실제로 성사된 가격**이다.
 * 표본 미달 조합은 서버가 아예 내려주지 않는다(소표본 왜곡 방지).
 */
export default function MarketRates() {
  const { data: rates } = useQuery({
    queryKey: ["marketRates"],
    queryFn: () => apiFetch<MarketRate[]>("/creator/market-rates"),
  });

  if (!rates) return null;

  if (rates.length === 0) {
    return (
      <p className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
        아직 공개할 만큼 거래가 쌓이지 않았습니다 — 거래가 쌓이는 대로 카테고리·플랫폼별
        실거래 시세가 여기에 표시됩니다.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[480px] border-separate border-spacing-0 text-sm">
        <thead>
          <tr className="text-left text-muted-foreground">
            <th className="border-b pb-2 pr-3 font-medium">카테고리</th>
            <th className="border-b pb-2 pr-3 font-medium">플랫폼</th>
            <th className="border-b pb-2 pr-3 font-medium">거래가 중앙값</th>
            <th className="border-b pb-2 pr-3 font-medium">주요 범위</th>
            <th className="border-b pb-2 font-medium">표본</th>
          </tr>
        </thead>
        <tbody>
          {rates.map((rate) => (
            <tr key={`${rate.category}-${rate.platform}`}>
              <td className="border-b py-2.5 pr-3">{rate.category}</td>
              <td className="border-b py-2.5 pr-3">{platformLabel(rate.platform)}</td>
              <td className="border-b py-2.5 pr-3 font-semibold">{formatKrw(rate.median_krw)}</td>
              <td className="border-b py-2.5 pr-3 text-muted-foreground">
                {formatKrw(rate.p25_krw)} ~ {formatKrw(rate.p75_krw)}
              </td>
              <td className="border-b py-2.5 text-muted-foreground">{rate.sample_count}건</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-muted-foreground">
        crecity에서 완료된 거래의 실제 가격 기준입니다(범위는 거래가의 가운데 절반).
        표본이 적은 조합은 표시하지 않으며, 시장 전체가 아닌 플랫폼 내 거래 통계입니다.
      </p>
    </div>
  );
}
