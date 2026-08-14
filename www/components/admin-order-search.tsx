"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { ORDER_STATUS_LABELS, formatKrw } from "@/lib/labels";

type AdminOrder = {
  id: number;
  package_title: string;
  brand_user_id: number;
  creator_user_id: number;
  amount_krw: number;
  status: string;
  accept_expired: boolean;
  cancel_requested_by: number | null;
  revisions_used: number;
  revision_limit: number;
  deadline_at: string | null;
  created_at: string | null;
};

type SearchResponse = { items: AdminOrder[]; total: number };

const PAGE_SIZE = 20;

/** 검색 조건 — 폼 제출로 한 번에 확정한다(입력마다 조회하지 않는다). */
type Criteria = { order_id: string; status: string; user_id: string; offset: number };

const EMPTY: Criteria = { order_id: "", status: "", user_id: "", offset: 0 };

function toQuery(criteria: Criteria): string {
  const params = new URLSearchParams({ limit: String(PAGE_SIZE) });
  if (criteria.order_id) params.set("order_id", criteria.order_id);
  if (criteria.status) params.set("status", criteria.status);
  if (criteria.user_id) params.set("user_id", criteria.user_id);
  if (criteria.offset > 0) params.set("offset", String(criteria.offset));
  return params.toString();
}

/** 운영 주문 검색(갭 #56) — 문의 대응용 읽기 전용. order.search 권한. */
export default function AdminOrderSearch() {
  // 단일 객체 상태 — 검색 조건 묶음(REACT_RULES 단일 객체 패턴)
  const [criteria, setCriteria] = useState<Criteria>(EMPTY);

  const { data, isFetching } = useQuery({
    queryKey: ["adminOrders", criteria],
    queryFn: () => apiFetch<SearchResponse>(`/admin/orders?${toQuery(criteria)}`),
  });

  const orders = data?.items ?? [];
  const total = data?.total ?? 0;
  const page = Math.floor(criteria.offset / PAGE_SIZE) + 1;
  const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <section className="mt-12">
      <h2 className="text-xl font-bold tracking-[-0.02em]">주문 검색</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        문의가 들어온 주문을 번호·상태·회원 번호로 찾습니다. 조회 전용이라 여기서 상태를 바꿀 수는
        없습니다.
      </p>

      <form
        className="mt-4 flex flex-wrap items-center gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          setCriteria({
            order_id: String(form.get("order_id") ?? "").trim(),
            status: String(form.get("status") ?? ""),
            user_id: String(form.get("user_id") ?? "").trim(),
            offset: 0,
          });
        }}
      >
        <input
          name="order_id"
          type="number"
          min={1}
          defaultValue={criteria.order_id}
          placeholder="주문 번호"
          className="h-10 w-32 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-primary"
        />
        <input
          name="user_id"
          type="number"
          min={1}
          defaultValue={criteria.user_id}
          placeholder="회원 번호"
          className="h-10 w-32 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-primary"
        />
        <select
          name="status"
          defaultValue={criteria.status}
          className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm"
        >
          <option value="">상태 전체</option>
          {Object.entries(ORDER_STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <Button type="submit" size="sm">
          검색
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={() => setCriteria(EMPTY)}>
          초기화
        </Button>
        <span className="text-sm text-muted-foreground">
          {isFetching ? "조회 중…" : `${total}건`}
        </span>
      </form>

      {orders.length === 0 ? (
        <p className="mt-4 rounded-xl border border-dashed py-10 text-center text-sm text-muted-foreground">
          조건에 맞는 주문이 없습니다.
        </p>
      ) : (
        <div className="mt-4 grid gap-2">
          {orders.map((order) => (
            <Card key={order.id}>
              <CardContent className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 p-4">
                <div>
                  <p className="text-sm font-semibold">
                    #{order.id} · {order.package_title}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    브랜드 {order.brand_user_id} → 크리에이터 {order.creator_user_id} ·{" "}
                    {formatKrw(order.amount_krw)} · 수정 {order.revisions_used}/
                    {order.revision_limit}
                    {order.created_at && ` · ${order.created_at.slice(0, 10)}`}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-1.5">
                  {order.cancel_requested_by !== null && (
                    <span className="rounded-full bg-secondary px-2.5 py-1 text-xs">취소 요청됨</span>
                  )}
                  {order.accept_expired && (
                    <span className="rounded-full bg-secondary px-2.5 py-1 text-xs">수락 만료</span>
                  )}
                  <span className="rounded-full bg-accent px-2.5 py-1 text-xs font-semibold text-accent-foreground">
                    {ORDER_STATUS_LABELS[order.status as keyof typeof ORDER_STATUS_LABELS] ??
                      order.status}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {lastPage > 1 && (
        <div className="mt-4 flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() =>
              setCriteria({ ...criteria, offset: Math.max(0, criteria.offset - PAGE_SIZE) })
            }
          >
            이전
          </Button>
          <span className="text-sm text-muted-foreground">
            {page} / {lastPage}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= lastPage}
            onClick={() => setCriteria({ ...criteria, offset: criteria.offset + PAGE_SIZE })}
          >
            다음
          </Button>
        </div>
      )}
    </section>
  );
}
