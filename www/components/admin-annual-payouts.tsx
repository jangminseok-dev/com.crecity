"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { formatKrw } from "@/lib/labels";

type AnnualPayout = {
  creator_user_id: number;
  account_holder: string;
  count: number;
  total_amount_krw: number;
  total_tax_krw: number;
  total_payout_krw: number;
};

const CURRENT_YEAR = new Date().getFullYear();
const YEARS = [CURRENT_YEAR, CURRENT_YEAR - 1, CURRENT_YEAR - 2];

/** 연간 지급 집계 — 국세청 지급명세서 제출 자료(withdrawal.settle 권한, 갭 #2). */
export default function AdminAnnualPayouts() {
  // 단일 값 상태 — 조회 연도
  const [year, setYear] = useState(CURRENT_YEAR);

  const { data: rows } = useQuery({
    queryKey: ["annualPayouts", year],
    queryFn: () => apiFetch<AnnualPayout[]>(`/admin/withdrawals/annual-summary/${year}`),
  });

  const totals = (rows ?? []).reduce(
    (acc, row) => ({
      amount: acc.amount + row.total_amount_krw,
      tax: acc.tax + row.total_tax_krw,
      payout: acc.payout + row.total_payout_krw,
    }),
    { amount: 0, tax: 0, payout: 0 },
  );

  return (
    <section className="mt-12">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold tracking-[-0.02em]">연간 지급 집계</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            지급명세서 제출용 — 지급이 완료된 인출을 크리에이터별로 합산합니다.
          </p>
        </div>
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
      </div>

      <Card className="mt-4">
        <CardContent className="p-5">
          {!rows || rows.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              {year}년 지급 완료 내역이 없습니다.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[520px] text-sm">
                <thead>
                  <tr className="border-b text-left text-xs text-muted-foreground">
                    <th className="py-2 font-normal">크리에이터</th>
                    <th className="py-2 text-right font-normal">건수</th>
                    <th className="py-2 text-right font-normal">지급 총액</th>
                    <th className="py-2 text-right font-normal">원천징수</th>
                    <th className="py-2 text-right font-normal">실지급</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.creator_user_id} className="border-b">
                      <td className="py-2">
                        {row.account_holder}
                        <span className="ml-2 text-xs text-muted-foreground">
                          user #{row.creator_user_id}
                        </span>
                      </td>
                      <td className="py-2 text-right">{row.count}</td>
                      <td className="py-2 text-right">{formatKrw(row.total_amount_krw)}</td>
                      <td className="py-2 text-right">{formatKrw(row.total_tax_krw)}</td>
                      <td className="py-2 text-right">{formatKrw(row.total_payout_krw)}</td>
                    </tr>
                  ))}
                  <tr className="font-semibold">
                    <td className="py-2">합계</td>
                    <td className="py-2 text-right">
                      {rows.reduce((sum, row) => sum + row.count, 0)}
                    </td>
                    <td className="py-2 text-right">{formatKrw(totals.amount)}</td>
                    <td className="py-2 text-right">{formatKrw(totals.tax)}</td>
                    <td className="py-2 text-right">{formatKrw(totals.payout)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
