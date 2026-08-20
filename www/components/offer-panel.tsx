"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError, apiFetch } from "@/lib/api";
import { formatKrw } from "@/lib/labels";
import type { CustomOffer } from "@/lib/types";

/** 대화방 커스텀 오퍼 패널 — 크리에이터는 제안, 브랜드는 결제. */
export default function OfferPanel({
  conversationId,
  isCreator,
}: {
  conversationId: string;
  isCreator: boolean;
}) {
  const queryClient = useQueryClient();
  // 단일 값 상태 — 오퍼 작성 폼 열림 (입력값은 FormData 패턴)
  const [composing, setComposing] = useState(false);

  const { data: offers } = useQuery({
    queryKey: ["offers", conversationId],
    queryFn: () => apiFetch<CustomOffer[]>(`/chat/conversations/${conversationId}/offers`),
    refetchInterval: 10_000, // 상대가 보낸 오퍼·결제 상태 폴링
  });

  const send = useMutation({
    mutationFn: (body: {
      title: string;
      price_krw: number;
      revision_limit: number;
      usage_rights: string;
    }) =>
      apiFetch<CustomOffer>(`/chat/conversations/${conversationId}/offers`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["offers", conversationId] });
      setComposing(false);
    },
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const title = String(formData.get("title") ?? "").trim();
    const price = Number(formData.get("price_krw"));
    const revisionLimit = Number(formData.get("revision_limit") ?? 2);
    const usageRights = String(formData.get("usage_rights") ?? "").trim();
    if (!title || !Number.isInteger(price) || price <= 0) return;
    send.mutate({
      title,
      price_krw: price,
      revision_limit: revisionLimit,
      usage_rights: usageRights,
    });
  };

  if (!offers?.length && !isCreator) return null;

  return (
    <div className="border-b py-2">
      {offers?.map((offer) => (
        <div
          key={offer.id}
          className="mb-2 flex items-center justify-between gap-3 rounded-lg border bg-muted/40 px-3 py-2"
        >
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">💼 {offer.title}</p>
            <p className="text-sm text-muted-foreground">
              {formatKrw(offer.price_krw)} · 수정 {offer.revision_limit}회
              {offer.usage_rights ? ` · ${offer.usage_rights}` : ""}
            </p>
          </div>
          {offer.status === "PAID" ? (
            offer.order_id ? (
              <Button
                variant="outline"
                size="sm"
                nativeButton={false}
                render={<Link href={`/dashboard/orders/${offer.order_id}`}>주문 보기</Link>}
              />
            ) : (
              <span className="text-sm text-muted-foreground">결제 완료</span>
            )
          ) : isCreator ? (
            <span className="text-sm text-muted-foreground">결제 대기</span>
          ) : (
            <Button
              size="sm"
              nativeButton={false}
              render={
                <Link href={`/orders/new?offer=${offer.id}&conversation=${conversationId}`}>
                  결제하기
                </Link>
              }
            />
          )}
        </div>
      ))}

      {isCreator &&
        (composing ? (
          <form onSubmit={handleSubmit} className="flex flex-wrap items-center gap-2">
            <Input name="title" placeholder="오퍼 내용 (예: 릴스 2건 + 사진 5장)" className="flex-1" maxLength={100} />
            <Input name="price_krw" type="number" min={1} placeholder="가격(원)" className="w-32" />
            {/* 합의 조건(갭 #98) — 결제 시 주문 계약 조건으로 그대로 저장된다 */}
            <label className="flex items-center gap-1.5 text-sm text-muted-foreground">
              수정
              <select
                name="revision_limit"
                defaultValue="2"
                className="h-9 rounded-md border border-input bg-transparent px-2 text-sm"
              >
                {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((count) => (
                  <option key={count} value={count}>
                    {count}회
                  </option>
                ))}
              </select>
            </label>
            <Input
              name="usage_rights"
              placeholder="2차 활용 범위 (선택)"
              className="w-56"
              maxLength={300}
            />
            <Button type="submit" size="sm" disabled={send.isPending}>
              보내기
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={() => setComposing(false)}>
              취소
            </Button>
          </form>
        ) : (
          <Button variant="outline" size="sm" onClick={() => setComposing(true)}>
            💼 커스텀 오퍼 보내기
          </Button>
        ))}
      {send.error && (
        <p className="mt-1 text-xs text-destructive">
          {send.error instanceof ApiError ? send.error.detail : "오퍼 전송에 실패했습니다."}
        </p>
      )}
    </div>
  );
}
