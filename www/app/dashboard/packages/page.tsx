"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { z } from "zod";

import PackagePriceHelper from "@/components/package-price-helper";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";
import { PLATFORM_LABELS, formatKrw } from "@/lib/labels";
import type { CreatorPackage, CreatorProfile } from "@/lib/types";

const packageSchema = z.object({
  platform: z.enum(["INSTAGRAM", "YOUTUBE", "TIKTOK", "NAVER_BLOG", "UGC"]),
  title: z.string().min(1, "패키지 이름을 입력해 주세요.").max(100),
  description: z.string().min(1, "상세 설명을 입력해 주세요."),
  price_krw: z.coerce
    .number()
    .int("가격은 정수(원)로 입력해 주세요.")
    .positive("가격은 0보다 커야 합니다."),
  revision_limit: z.coerce.number().int().min(0).max(10),
  usage_rights: z.string().max(300).optional(),
});

async function fetchMyProfile(): Promise<CreatorProfile | null> {
  try {
    return await apiFetch<CreatorProfile>("/creator/my/profile");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

// 폼 UI 상태 — 수정 대상·제출 진행·오류를 단일 객체로 (입력값은 FormData 패턴)
type FormUiState = {
  editing: CreatorPackage | null;
  // 단가 도우미(갭 #51)가 볼 현재 선택 플랫폼 — 미선택이면 editing 값/기본값을 쓴다
  platform?: string;
  submitting: boolean;
  error: string | null;
};

function PackageForm({ slug, ui, setUi }: {
  slug: string;
  ui: FormUiState;
  setUi: React.Dispatch<React.SetStateAction<FormUiState>>;
}) {
  const queryClient = useQueryClient();
  // 추천 단가를 넣을 대상 — 상태가 아니라 DOM 참조라 FormData 패턴을 유지한다
  const priceRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formElement = e.currentTarget;
    const parsed = packageSchema.safeParse(Object.fromEntries(new FormData(formElement).entries()));
    if (!parsed.success) {
      setUi((prev) => ({ ...prev, error: parsed.error.issues[0].message }));
      return;
    }
    setUi((prev) => ({ ...prev, submitting: true, error: null }));
    try {
      if (ui.editing) {
        await apiFetch(`/creator/packages/${ui.editing.id}`, {
          method: "PUT",
          body: JSON.stringify(parsed.data),
        });
      } else {
        await apiFetch(`/creator/profiles/${slug}/packages`, {
          method: "POST",
          body: JSON.stringify(parsed.data),
        });
        formElement.reset();
      }
      setUi({ editing: null, submitting: false, error: null });
      await queryClient.invalidateQueries({ queryKey: ["myPackages", slug] });
    } catch (error) {
      setUi((prev) => ({
        ...prev,
        submitting: false,
        error: error instanceof ApiError ? error.detail : "저장에 실패했습니다.",
      }));
    }
  };

  return (
    <Card>
      <CardContent className="p-6">
        <h3 className="font-semibold">{ui.editing ? `패키지 수정 — ${ui.editing.title}` : "새 패키지 등록"}</h3>
        {/* key로 수정 대상 전환 시 defaultValue를 리셋한다 */}
        <form key={ui.editing?.id ?? "new"} onSubmit={handleSubmit} className="mt-4 grid gap-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-1.5">
              <Label htmlFor="platform">플랫폼</Label>
              <select
                id="platform"
                name="platform"
                defaultValue={ui.editing?.platform ?? "INSTAGRAM"}
                onChange={(event) =>
                  setUi((prev) => ({ ...prev, platform: event.target.value }))
                }
                className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
              >
                {Object.entries(PLATFORM_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="price_krw">가격 (원)</Label>
              <Input
                id="price_krw"
                name="price_krw"
                ref={priceRef}
                type="number"
                min={1}
                defaultValue={ui.editing?.price_krw ?? ""}
                placeholder="300000"
              />
            </div>
          </div>
          <PackagePriceHelper
            platform={ui.platform ?? ui.editing?.platform ?? "INSTAGRAM"}
            onPick={(price) => {
              if (priceRef.current) priceRef.current.value = String(price);
            }}
          />
          <div className="grid gap-1.5">
            <Label htmlFor="title">패키지 이름</Label>
            <Input
              id="title"
              name="title"
              defaultValue={ui.editing?.title ?? ""}
              placeholder="인스타그램 릴스 1개"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-1.5">
              <Label htmlFor="revision_limit">수정 요청 허용 횟수</Label>
              <Input
                id="revision_limit"
                name="revision_limit"
                type="number"
                min={0}
                max={10}
                defaultValue={ui.editing?.revision_limit ?? 2}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="usage_rights">2차 활용 범위 (선택)</Label>
              <Input
                id="usage_rights"
                name="usage_rights"
                maxLength={300}
                defaultValue={ui.editing?.usage_rights ?? ""}
                placeholder="SNS 게시 6개월, 유료 광고 별도 협의"
              />
            </div>
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="description">상세 설명 (납품물 등)</Label>
            <Textarea
              id="description"
              name="description"
              rows={3}
              defaultValue={ui.editing?.description ?? ""}
              placeholder="60초 이내 릴스 1건 제작·게시, 원본 파일 제공"
            />
          </div>
          {ui.error && <p className="text-sm text-destructive">{ui.error}</p>}
          <div className="flex gap-2">
            <Button type="submit" disabled={ui.submitting}>
              {ui.submitting ? "저장 중…" : ui.editing ? "수정 저장" : "패키지 등록"}
            </Button>
            {ui.editing && (
              <Button
                type="button"
                variant="ghost"
                onClick={() => setUi({ editing: null, submitting: false, error: null })}
              >
                수정 취소
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

export default function DashboardPackagesPage() {
  const queryClient = useQueryClient();
  const [ui, setUi] = useState<FormUiState>({ editing: null, submitting: false, error: null });

  const { data: profile, isPending: profilePending } = useQuery({
    queryKey: ["myProfile"],
    queryFn: fetchMyProfile,
  });
  const slug = profile?.slug;
  const { data: packages, isPending: packagesPending } = useQuery({
    queryKey: ["myPackages", slug],
    queryFn: () => apiFetch<CreatorPackage[]>(`/creator/profiles/${slug}/packages`),
    enabled: Boolean(slug),
  });

  const removePackage = useMutation({
    mutationFn: (packageId: number) =>
      apiFetch(`/creator/packages/${packageId}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["myPackages", slug] }),
  });

  if (profilePending) return <Skeleton className="h-64 w-full" />;
  if (!profile) {
    return (
      <div className="rounded-xl border border-dashed py-16 text-center">
        <p className="text-muted-foreground">패키지를 등록하려면 먼저 프로필이 필요합니다.</p>
        <Button className="mt-4" nativeButton={false} render={<Link href="/dashboard/profile">프로필 등록하러 가기</Link>} />
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <PackageForm slug={profile.slug} ui={ui} setUi={setUi} />

      <div>
        <h3 className="mb-3 font-semibold">등록된 패키지 {packages && `(${packages.length})`}</h3>
        {packagesPending ? (
          <Skeleton className="h-32 w-full" />
        ) : !packages || packages.length === 0 ? (
          <p className="rounded-xl border border-dashed py-10 text-center text-sm text-muted-foreground">
            아직 등록된 패키지가 없습니다 — 위에서 첫 패키지를 등록해 보세요.
          </p>
        ) : (
          <div className="grid gap-3">
            {packages.map((pkg) => (
              <Card key={pkg.id}>
                <CardContent className="flex items-center justify-between gap-4 p-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{PLATFORM_LABELS[pkg.platform]}</Badge>
                      <p className="truncate font-medium">{pkg.title}</p>
                    </div>
                    <p className="mt-1 truncate text-sm text-muted-foreground">{pkg.description}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <p className="font-semibold">{formatKrw(pkg.price_krw)}</p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setUi({ editing: pkg, submitting: false, error: null })}
                    >
                      수정
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      disabled={removePackage.isPending}
                      onClick={() => {
                        if (window.confirm(`"${pkg.title}" 패키지를 삭제할까요?`)) {
                          removePackage.mutate(pkg.id);
                        }
                      }}
                    >
                      삭제
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
