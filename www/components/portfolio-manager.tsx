"use client";

import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, apiFetch } from "@/lib/api";
import type { PortfolioItem } from "@/lib/types";

/** 대시보드 포트폴리오 관리 — 업로드(최대 12장·5MB)와 삭제. */
export default function PortfolioManager({ slug }: { slug: string }) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  // 단일 객체 상태 — 업로드 진행·오류 메시지
  const [form, setForm] = useState<{ uploading: boolean; error: string | null }>({
    uploading: false,
    error: null,
  });

  const { data: items, isPending } = useQuery({
    queryKey: ["portfolio", slug],
    queryFn: () =>
      apiFetch<PortfolioItem[]>(`/creator/profiles/${encodeURIComponent(slug)}/portfolio`),
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["portfolio", slug] });

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // 같은 파일 재선택 허용
    if (!file) return;
    setForm({ uploading: true, error: null });
    const body = new FormData();
    body.append("file", file);
    try {
      await apiFetch("/creator/my/portfolio", { method: "POST", body });
      await refresh();
      setForm({ uploading: false, error: null });
    } catch (error) {
      setForm({
        uploading: false,
        error: error instanceof ApiError ? error.detail : "업로드에 실패했습니다.",
      });
    }
  };

  const handleDelete = async (itemId: number) => {
    try {
      await apiFetch(`/creator/my/portfolio/${itemId}`, { method: "DELETE" });
      await refresh();
    } catch (error) {
      setForm((prev) => ({
        ...prev,
        error: error instanceof ApiError ? error.detail : "삭제에 실패했습니다.",
      }));
    }
  };

  return (
    <section className="mt-8">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">포트폴리오</h2>
        <Button
          size="sm"
          disabled={form.uploading}
          onClick={() => fileInputRef.current?.click()}
        >
          {form.uploading ? "업로드 중…" : "사진 추가"}
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={handleUpload}
        />
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        공개 프로필에 갤러리로 노출됩니다 — JPG·PNG·WebP, 5MB 이하, 최대 12장.
      </p>
      {form.error && <p className="mt-2 text-sm text-destructive">{form.error}</p>}
      <div className="mt-4">
        {isPending ? (
          <Skeleton className="h-32 w-full" />
        ) : !items || items.length === 0 ? (
          <p className="rounded-lg border border-dashed py-10 text-center text-muted-foreground">
            아직 사진이 없습니다 — 대표 작업물을 올려 보세요.
          </p>
        ) : (
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
            {items.map((item) => (
              <div key={item.id} className="group relative aspect-square overflow-hidden rounded-lg border">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={`/api/backend${item.image_url}`}
                  alt="포트폴리오 사진"
                  className="size-full object-cover"
                />
                <button
                  type="button"
                  onClick={() => handleDelete(item.id)}
                  className="absolute right-1 top-1 hidden rounded-md bg-black/60 px-2 py-1 text-xs text-white group-hover:block"
                >
                  삭제
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
