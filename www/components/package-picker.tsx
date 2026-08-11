"use client";

import { ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import ContactCreatorButton from "@/components/contact-creator-button";
import ShortlistButton from "@/components/shortlist-button";
import { useCartStore } from "@/lib/cart-store";
import { PLATFORM_LABELS, formatKrw } from "@/lib/labels";
import type { ShortlistItem } from "@/lib/shortlist-store";
import type { CreatorPackage } from "@/lib/types";

/** 프로필 우측 sticky 패키지 선택 사이드바 — 디자인 시스템 ProfileScreen의 aside. */
export default function PackagePicker({
  slug,
  packages,
  shortlistItem,
}: {
  slug: string;
  packages: CreatorPackage[];
  shortlistItem: ShortlistItem;
}) {
  // 단일 객체 상태 — 선택 패키지 + 플랫폼 탭(null=전체) + 카트 하이드레이션 완료 여부
  const [ui, setUi] = useState<{
    selectedId: number | null;
    platform: CreatorPackage["platform"] | null;
    cartReady: boolean;
  }>({
    selectedId: packages[0]?.id ?? null,
    platform: null,
    cartReady: false,
  });
  const cart = useCartStore();
  useEffect(() => setUi((prev) => ({ ...prev, cartReady: true })), []);

  // 플랫폼별 탭(§2.1-4) — 패키지가 있는 플랫폼만 탭으로 노출한다
  const tabs = [...new Set(packages.map((pkg) => pkg.platform))];
  const visible = ui.platform ? packages.filter((pkg) => pkg.platform === ui.platform) : packages;
  const selectedId = visible.some((pkg) => pkg.id === ui.selectedId)
    ? ui.selectedId
    : (visible[0]?.id ?? null); // 탭을 바꿔 선택이 사라지면 첫 패키지로

  const selectedPkg = packages.find((p) => p.id === selectedId);
  const inCart =
    ui.cartReady && selectedId !== null && cart.items.some((i) => i.package_id === selectedId);

  return (
    <aside className="top-24 flex flex-col gap-2.5 rounded-2xl border bg-card p-5 shadow-card lg:sticky">
      <h3 className="mb-1 text-lg font-semibold">패키지 선택</h3>

      {packages.length === 0 ? (
        <p className="rounded-xl border border-dashed py-8 text-center text-sm text-muted-foreground">
          아직 등록된 패키지가 없습니다.
        </p>
      ) : (
        <>
          {tabs.length > 1 && (
            <div className="mb-1 flex flex-wrap gap-1.5">
              {[null, ...tabs].map((platform) => {
                const active = ui.platform === platform;
                return (
                  <button
                    key={platform ?? "ALL"}
                    type="button"
                    onClick={() => setUi((prev) => ({ ...prev, platform }))}
                    className={`inline-flex h-8 items-center rounded-full px-3 text-[13px] font-medium transition-colors ${
                      active
                        ? "bg-primary text-primary-foreground"
                        : "bg-secondary text-secondary-foreground hover:bg-accent"
                    }`}
                  >
                    {platform ? PLATFORM_LABELS[platform] : "전체"}
                  </button>
                );
              })}
            </div>
          )}
          {visible.map((pkg) => {
            const selected = pkg.id === selectedId;
            return (
              <button
                key={pkg.id}
                type="button"
                onClick={() => setUi((prev) => ({ ...prev, selectedId: pkg.id }))}
                className={`flex w-full flex-col gap-1.5 rounded-xl border-[1.5px] p-4 text-left transition-colors ${
                  selected ? "border-primary bg-accent" : "hover:border-[#d1d6db]"
                }`}
              >
                <span className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold">{pkg.title}</span>
                  <span className="whitespace-nowrap text-[15px] font-bold">
                    {formatKrw(pkg.price_krw)}
                  </span>
                </span>
                <span className="text-[13px] leading-snug text-muted-foreground">
                  {pkg.description}
                </span>
                <span className="text-xs text-muted-foreground/70">
                  {PLATFORM_LABELS[pkg.platform]} · 수정 {pkg.revision_limit}회
                  {pkg.usage_rights ? ` · ${pkg.usage_rights}` : ""}
                </span>
              </button>
            );
          })}

          <div className="flex items-start gap-2 rounded-lg bg-[#f9fafb] px-3 py-2.5 text-xs leading-snug text-muted-foreground">
            <ShieldCheck className="size-4 shrink-0 text-primary" />
            결제 금액은 콘텐츠 승인 전까지 크리시티가 안전하게 보관해요
          </div>

          {selectedId && (
            <Link
              href={`/orders/new?slug=${slug}&package=${selectedId}`}
              className="inline-flex h-[52px] w-full items-center justify-center rounded-xl bg-primary text-[17px] font-semibold text-primary-foreground transition-colors hover:bg-accent-foreground"
            >
              패키지 구매
            </Link>
          )}
          {selectedPkg &&
            (inCart ? (
              <Link
                href="/cart"
                className="inline-flex h-11 w-full items-center justify-center rounded-xl border text-sm font-semibold text-muted-foreground transition-colors hover:bg-secondary"
              >
                ✓ 장바구니에 담김 — 보러 가기
              </Link>
            ) : (
              <button
                type="button"
                onClick={() =>
                  cart.add({
                    package_id: selectedPkg.id,
                    title: selectedPkg.title,
                    price_krw: selectedPkg.price_krw,
                    platform: selectedPkg.platform,
                    creator_slug: slug,
                  })
                }
                className="inline-flex h-11 w-full items-center justify-center rounded-xl border text-sm font-semibold transition-colors hover:bg-secondary"
              >
                장바구니 담기 — 여러 크리에이터 한 번에 결제
              </button>
            ))}
        </>
      )}

      <ContactCreatorButton slug={slug} />
      <ShortlistButton item={shortlistItem} withLabel />
    </aside>
  );
}
