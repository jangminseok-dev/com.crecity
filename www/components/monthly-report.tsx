"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { formatKrw } from "@/lib/labels";

type MonthlyReportRow = {
  month: number;
  entry_type: string;
  total_krw: number;
  count: number;
};

const CURRENT_YEAR = new Date().getFullYear();
const YEARS = [CURRENT_YEAR, CURRENT_YEAR - 1, CURRENT_YEAR - 2];

/* 계정 유형별로 의미 있는 원장 기입 유형 — 열 순서 그대로 표·CSV에 쓴다 */
const CREATOR_COLUMNS = [
  { type: "CREATOR_EARNING", label: "수익 적립" },
  { type: "WITHDRAWAL", label: "인출" },
  { type: "WITHDRAWAL_REVERSAL", label: "인출 복원" },
] as const;
const BRAND_COLUMNS = [
  { type: "ESCROW_DEPOSIT", label: "결제(예치)" },
  { type: "CREDIT_SPENT", label: "크레딧 사용" },
  { type: "BRAND_CREDIT_REFUND", label: "환불 크레딧" },
] as const;

function toCsv(months: number[], columns: readonly { type: string; label: string }[], sums: Map<string, number>, year: number): string {
  const header = ["월", ...columns.map((c) => `${c.label}(원)`)].join(",");
  const lines = months.map((month) =>
    [`${year}-${String(month).padStart(2, "0")}`, ...columns.map((c) => sums.get(`${month}:${c.type}`) ?? 0)].join(","),
  );
  const total = ["합계", ...columns.map((c) => months.reduce((acc, m) => acc + (sums.get(`${m}:${c.type}`) ?? 0), 0))].join(",");
  return [header, ...lines, total].join("\n");
}

/** 월별 수익(크리에이터)·지출(브랜드) 리포트(갭 #90) — 돈의 정본인 원장 기입을 집계한다. */
export default function MonthlyReport({ isCreator }: { isCreator: boolean }) {
  // 단일 값 상태 — 조회 연도
  const [year, setYear] = useState(CURRENT_YEAR);
  const columns = isCreator ? CREATOR_COLUMNS : BRAND_COLUMNS;

  const { data: rows } = useQuery({
    queryKey: ["monthlyReport", year],
    queryFn: () => apiFetch<MonthlyReportRow[]>(`/order/reports/${year}`),
  });

  const sums = new Map<string, number>();
  for (const row of rows ?? []) sums.set(`${row.month}:${row.entry_type}`, row.total_krw);
  // 표시 대상 유형에 기입이 있는 월만 그린다(0으로 채운 12행은 세무 자료로도 소음)
  const months = [...new Set((rows ?? []).filter((r) => columns.some((c) => c.type === r.entry_type)).map((r) => r.month))].sort((a, b) => a - b);

  const downloadCsv = () => {
    // 한글 헤더가 Excel에서 깨지지 않게 BOM을 붙인다
    const blob = new Blob(["﻿" + toCsv(months, columns, sums, year)], {
      type: "text/csv;charset=utf-8",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `crecity-${isCreator ? "수익" : "지출"}-리포트-${year}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  return (
    <Card className="mt-6">
      <CardContent className="p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-semibold">{isCreator ? "월별 수익 리포트" : "월별 지출 리포트"}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {isCreator
                ? "구매 확정으로 적립된 수익과 인출 내역의 월별 합계입니다. 원천징수 세액은 아래 지급명세서 기준입니다."
                : "주문 결제(에스크로 예치)와 크레딧 흐름의 월별 합계입니다. 경비 정리에 참고하세요."}
            </p>
          </div>
          <div className="flex gap-2">
            <select
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="h-9 rounded-md border border-input bg-transparent px-3 text-sm outline-none transition-colors focus:border-primary"
            >
              {YEARS.map((option) => (
                <option key={option} value={option}>
                  {option}년
                </option>
              ))}
            </select>
            {months.length > 0 && (
              <Button variant="outline" size="sm" className="h-9" onClick={downloadCsv}>
                CSV 내려받기
              </Button>
            )}
          </div>
        </div>

        {rows && months.length === 0 && (
          <p className="mt-5 rounded-xl border border-dashed py-8 text-center text-sm text-muted-foreground">
            {year}년에는 기록이 없습니다.
          </p>
        )}
        {months.length > 0 && (
          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-[420px] border-separate border-spacing-0 text-sm">
              <thead>
                <tr className="text-left text-muted-foreground">
                  <th className="border-b pb-2 pr-3 font-medium">월</th>
                  {columns.map((c) => (
                    <th key={c.type} className="border-b pb-2 pr-3 text-right font-medium">
                      {c.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {months.map((month) => (
                  <tr key={month}>
                    <td className="border-b py-2.5 pr-3">{month}월</td>
                    {columns.map((c) => {
                      const amount = sums.get(`${month}:${c.type}`);
                      return (
                        <td key={c.type} className="border-b py-2.5 pr-3 text-right">
                          {amount !== undefined ? formatKrw(amount) : "—"}
                        </td>
                      );
                    })}
                  </tr>
                ))}
                <tr className="font-semibold">
                  <td className="py-2.5 pr-3">합계</td>
                  {columns.map((c) => (
                    <td key={c.type} className="py-2.5 pr-3 text-right">
                      {formatKrw(months.reduce((acc, m) => acc + (sums.get(`${m}:${c.type}`) ?? 0), 0))}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
