"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";
import { PROFILE_STATUS_LABELS } from "@/lib/labels";
import type { CreatorProfile } from "@/lib/types";

const profileSchema = z.object({
  slug: z
    .string()
    .min(3, "주소는 3자 이상이어야 합니다.")
    .max(30, "주소는 30자 이하여야 합니다.")
    .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "주소는 영문 소문자·숫자·하이픈(-)만 쓸 수 있습니다."),
  name: z.string().min(1, "이름을 입력해 주세요.").max(100),
  tagline: z.string().min(1, "한 줄 소개를 입력해 주세요.").max(200),
  bio: z.string().min(1, "상세 소개를 입력해 주세요."),
  location: z.string().max(100),
  primary_category: z.string().min(1, "카테고리를 입력해 주세요.").max(50),
});

async function fetchMyProfile(): Promise<CreatorProfile | null> {
  try {
    return await apiFetch<CreatorProfile>("/creator/my/profile");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

function ProfileRegistrationForm() {
  const queryClient = useQueryClient();
  // 단일 객체 상태 — 제출 진행·오류 메시지 (입력값은 FormData 패턴, uncontrolled)
  const [form, setForm] = useState<{ submitting: boolean; error: string | null }>({
    submitting: false,
    error: null,
  });

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const parsed = profileSchema.safeParse(Object.fromEntries(formData.entries()));
    if (!parsed.success) {
      setForm({ submitting: false, error: parsed.error.issues[0].message });
      return;
    }
    setForm({ submitting: true, error: null });
    try {
      await apiFetch("/creator/profiles", {
        method: "POST",
        body: JSON.stringify({ ...parsed.data, location: parsed.data.location || null }),
      });
      await queryClient.invalidateQueries({ queryKey: ["myProfile"] });
    } catch (error) {
      setForm({
        submitting: false,
        error: error instanceof ApiError ? error.detail : "등록에 실패했습니다.",
      });
    }
  };

  return (
    <div>
      <h2 className="text-lg font-semibold">프로필 등록</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        등록하면 심사 후 마켓플레이스 목록에 노출됩니다.
      </p>
      <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
        <div className="grid gap-1.5">
          <Label htmlFor="slug">프로필 주소 (영문)</Label>
          <Input id="slug" name="slug" placeholder="my-creator-name" />
          <p className="text-xs text-muted-foreground">crecity.com/creators/주소 형태로 공개됩니다.</p>
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="name">활동명</Label>
          <Input id="name" name="name" placeholder="김뷰티" />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="tagline">한 줄 소개</Label>
          <Input id="tagline" name="tagline" placeholder="20대 스킨케어·K뷰티 성분 리뷰" />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="bio">상세 소개</Label>
          <Textarea id="bio" name="bio" rows={5} placeholder="어떤 콘텐츠를 만드는지 소개해 주세요." />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="primary_category">대표 카테고리</Label>
            <Input id="primary_category" name="primary_category" placeholder="뷰티" />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="location">활동 지역 (선택)</Label>
            <Input id="location" name="location" placeholder="서울" />
          </div>
        </div>
        {form.error && <p className="text-sm text-destructive">{form.error}</p>}
        <Button type="submit" disabled={form.submitting}>
          {form.submitting ? "등록 중…" : "프로필 등록하기"}
        </Button>
      </form>
    </div>
  );
}

const editSchema = profileSchema.omit({ slug: true });

function ProfileEditForm({ profile, onDone }: { profile: CreatorProfile; onDone: () => void }) {
  const queryClient = useQueryClient();
  // 단일 객체 상태 — 제출 진행·오류 (입력값은 FormData 패턴)
  const [form, setForm] = useState<{ submitting: boolean; error: string | null }>({
    submitting: false,
    error: null,
  });

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const parsed = editSchema.safeParse(Object.fromEntries(new FormData(e.currentTarget).entries()));
    if (!parsed.success) {
      setForm({ submitting: false, error: parsed.error.issues[0].message });
      return;
    }
    setForm({ submitting: true, error: null });
    try {
      await apiFetch("/creator/my/profile", {
        method: "PUT",
        body: JSON.stringify({ ...parsed.data, location: parsed.data.location || null }),
      });
      await queryClient.invalidateQueries({ queryKey: ["myProfile"] });
      onDone();
    } catch (error) {
      setForm({
        submitting: false,
        error: error instanceof ApiError ? error.detail : "수정에 실패했습니다.",
      });
    }
  };

  return (
    <div>
      <h2 className="text-lg font-semibold">프로필 수정</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        프로필 주소(/creators/{profile.slug})는 공개 링크라 변경할 수 없습니다.
      </p>
      <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
        <div className="grid gap-1.5">
          <Label htmlFor="name">활동명</Label>
          <Input id="name" name="name" defaultValue={profile.name} />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="tagline">한 줄 소개</Label>
          <Input id="tagline" name="tagline" defaultValue={profile.tagline} />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="bio">상세 소개</Label>
          <Textarea id="bio" name="bio" rows={5} defaultValue={profile.bio} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="primary_category">대표 카테고리</Label>
            <Input id="primary_category" name="primary_category" defaultValue={profile.primary_category} />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="location">활동 지역 (선택)</Label>
            <Input id="location" name="location" defaultValue={profile.location ?? ""} />
          </div>
        </div>
        {form.error && <p className="text-sm text-destructive">{form.error}</p>}
        <div className="flex gap-2">
          <Button type="submit" disabled={form.submitting}>
            {form.submitting ? "저장 중…" : "저장하기"}
          </Button>
          <Button type="button" variant="ghost" onClick={onDone}>
            취소
          </Button>
        </div>
      </form>
    </div>
  );
}

function ProfileView({ profile, onEdit }: { profile: CreatorProfile; onEdit: () => void }) {
  return (
    <Card>
      <CardContent className="grid gap-4 p-6">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-bold">{profile.name}</h2>
          <Badge variant={profile.status === "APPROVED" ? "secondary" : "outline"}>
            {PROFILE_STATUS_LABELS[profile.status] ?? profile.status}
          </Badge>
        </div>
        <p className="text-muted-foreground">{profile.tagline}</p>
        <p className="whitespace-pre-line text-sm">{profile.bio}</p>
        <div className="flex gap-2 text-sm text-muted-foreground">
          <span>{profile.primary_category}</span>
          {profile.location && <span>· {profile.location}</span>}
        </div>
        {profile.status === "PENDING" && (
          <p className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
            심사 대기 중입니다 — 승인되면 마켓플레이스 목록에 노출됩니다. 프로필 링크 공유는
            지금도 가능합니다.
          </p>
        )}
        <div className="flex gap-2">
          <Button size="sm" onClick={onEdit}>
            수정하기
          </Button>
          <Button
            variant="outline"
            size="sm"
            nativeButton={false} render={<Link href={`/creators/${profile.slug}`}>공개 페이지 보기</Link>}
          />
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardProfilePage() {
  // 단일 값 상태 — 보기/수정 모드
  const [editing, setEditing] = useState(false);
  const { data: profile, isPending } = useQuery({
    queryKey: ["myProfile"],
    queryFn: fetchMyProfile,
  });

  if (isPending) return <Skeleton className="h-64 w-full" />;
  if (!profile) return <ProfileRegistrationForm />;
  return editing ? (
    <ProfileEditForm profile={profile} onDone={() => setEditing(false)} />
  ) : (
    <ProfileView profile={profile} onEdit={() => setEditing(true)} />
  );
}
