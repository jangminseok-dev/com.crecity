"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { formatKrw } from "@/lib/labels";

type PayoutStatement = {
  year: number;
  user_id: number;
  count: number;
  total_amount_krw: number;
  total_tax_krw: number;
  total_payout_krw: number;
  items: {
    withdrawal_id: number;
    amount_krw: number;
    tax_krw: number;
    payout_krw: number;
    settled_at: string | null;
  }[];
};

const CURRENT_YEAR = new Date().getFullYear();
const YEARS = [CURRENT_YEAR, CURRENT_YEAR - 1, CURRENT_YEAR - 2];

/** 연간 지급명세서(원천징수영수증 대용) — 지급 완료된 인출만 집계한다(갭 #2). */
export default function PayoutStatement() {
  // 단일 값 상태 — 조회 연도
  const [year, setYear] = useState(CURRENT_YEAR);

  const { data: statement } = useQuery({
    queryKey: ["payoutStatement", year],
    queryFn: () => apiFetch<PayoutStatement>(`/order/withdrawals/statements/${year}`),
  });

  return (
    <Card className="mt-6">
      <CardContent className="p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-semibold">지급명세서</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              지급이 완료된 금액과 원천징수 세액(3.3%)입니다. 종합소득세 신고 시 참고하세요.
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
            <Button variant="outline" size="sm" onClick={() => window.print()}>
              인쇄
            </Button>
          </div>
        </div>

        <div className="mt-4 grid gap-3 rounded-md bg-muted p-4 sm:grid-cols-3">
          <div>
            <p className="text-xs text-muted-foreground">지급 총액 (세전)</p>
            <p className="mt-1 font-semibold">{formatKrw(statement?.total_amount_krw ?? 0)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">원천징수 세액</p>
            <p className="mt-1 font-semibold">{formatKrw(statement?.total_tax_krw ?? 0)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">실지급액</p>
            <p className="mt-1 font-semibold">{formatKrw(statement?.total_payout_krw ?? 0)}</p>
          </div>
        </div>

        {(statement?.items.length ?? 0) === 0 ? (
          <p className="mt-4 text-sm text-muted-foreground">{year}년 지급 내역이 없습니다.</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[420px] text-sm">
              <thead>
                <tr className="border-b text-left text-xs text-muted-foreground">
                  <th className="py-2 font-normal">지급일</th>
                  <th className="py-2 text-right font-normal">지급액</th>
                  <th className="py-2 text-right font-normal">세액</th>
                  <th className="py-2 text-right font-normal">실지급</th>
                </tr>
              </thead>
              <tbody>
                {statement?.items.map((item) => (
                  <tr key={item.withdrawal_id} className="border-b">
                    <td className="py-2">
                      {item.settled_at
                        ? new Date(item.settled_at).toLocaleDateString("ko-KR")
                        : "—"}
                    </td>
                    <td className="py-2 text-right">{formatKrw(item.amount_krw)}</td>
                    <td className="py-2 text-right">{formatKrw(item.tax_krw)}</td>
                    <td className="py-2 text-right">{formatKrw(item.payout_krw)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
