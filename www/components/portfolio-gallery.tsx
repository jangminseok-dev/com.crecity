"use client";

import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { useEffect, useState } from "react";

import type { PortfolioItem } from "@/lib/types";

const PREVIEW_COUNT = 6; // 접힌 상태에서 보여줄 장수 — 나머지는 "사진 모두 보기"로

/** 포트폴리오 갤러리(§2.1-1) — 미리보기 그리드 + 전체 보기 라이트박스. */
export default function PortfolioGallery({
  photos,
  name,
}: {
  photos: PortfolioItem[];
  name: string;
}) {
  // 단일 객체 상태 — 펼침 여부 + 라이트박스에서 보고 있는 사진 index(null이면 닫힘)
  const [ui, setUi] = useState<{ expanded: boolean; lightboxIndex: number | null }>({
    expanded: false,
    lightboxIndex: null,
  });

  const openAt = (index: number) => setUi((prev) => ({ ...prev, lightboxIndex: index }));
  const close = () => setUi((prev) => ({ ...prev, lightboxIndex: null }));
  const move = (step: number) =>
    setUi((prev) => ({
      ...prev,
      lightboxIndex:
        prev.lightboxIndex === null
          ? null
          : (prev.lightboxIndex + step + photos.length) % photos.length,
    }));

  // 라이트박스가 열려 있는 동안 키보드 조작(Esc 닫기·좌우 이동)과 배경 스크롤 잠금
  useEffect(() => {
    if (ui.lightboxIndex === null) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
      if (event.key === "ArrowRight") move(1);
      if (event.key === "ArrowLeft") move(-1);
    };
    window.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ui.lightboxIndex, photos.length]);

  if (photos.length === 0) return null;

  const visible = ui.expanded ? photos : photos.slice(0, PREVIEW_COUNT);
  const hiddenCount = photos.length - visible.length;
  const current = ui.lightboxIndex === null ? null : photos[ui.lightboxIndex];

  return (
    <>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {visible.map((item, index) => (
          <button
            key={item.id}
            type="button"
            onClick={() => openAt(index)}
            aria-label={`${name} 포트폴리오 크게 보기`}
            className="aspect-square overflow-hidden rounded-xl"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`/api/backend${item.image_url}`}
              alt={`${name} 포트폴리오`}
              className="size-full object-cover transition-transform duration-200 hover:scale-[1.03]"
            />
          </button>
        ))}
      </div>

      {hiddenCount > 0 && (
        <button
          type="button"
          onClick={() => setUi((prev) => ({ ...prev, expanded: true }))}
          className="mt-4 inline-flex h-10 items-center rounded-lg border px-4 text-sm font-semibold transition-colors hover:bg-secondary"
        >
          사진 모두 보기 ({photos.length})
        </button>
      )}

      {current && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="포트폴리오 사진"
          className="fixed inset-0 z-100 flex items-center justify-center bg-black/85 p-4"
          onClick={close}
        >
          <button
            type="button"
            aria-label="닫기"
            onClick={close}
            className="absolute right-4 top-4 inline-flex size-11 items-center justify-center rounded-full text-white/80 transition-colors hover:bg-white/10 hover:text-white"
          >
            <X className="size-6" />
          </button>
          {photos.length > 1 && (
            <>
              <button
                type="button"
                aria-label="이전 사진"
                onClick={(event) => {
                  event.stopPropagation();
                  move(-1);
                }}
                className="absolute left-3 inline-flex size-12 items-center justify-center rounded-full text-white/80 transition-colors hover:bg-white/10 hover:text-white"
              >
                <ChevronLeft className="size-7" />
              </button>
              <button
                type="button"
                aria-label="다음 사진"
                onClick={(event) => {
                  event.stopPropagation();
                  move(1);
                }}
                className="absolute right-3 inline-flex size-12 items-center justify-center rounded-full text-white/80 transition-colors hover:bg-white/10 hover:text-white"
              >
                <ChevronRight className="size-7" />
              </button>
            </>
          )}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`/api/backend${current.image_url}`}
            alt={`${name} 포트폴리오`}
            onClick={(event) => event.stopPropagation()}
            className="max-h-[85dvh] max-w-full rounded-lg object-contain"
          />
          <p className="absolute bottom-5 text-sm text-white/70">
            {(ui.lightboxIndex ?? 0) + 1} / {photos.length}
          </p>
        </div>
      )}
    </>
  );
}
