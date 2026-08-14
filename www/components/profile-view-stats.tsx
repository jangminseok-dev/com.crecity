"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

type ProfileViews = {
  days: number;
  total: number;
  daily: { view_date: string; view_count: number }[];
};

/** 내 프로필 조회수 추이(갭 #57) — 본인만 본다. 막대 높이는 최댓값 기준 상대값. */
export default function ProfileViewStats() {
  const { data } = useQuery({
    queryKey: ["myProfileViews"],
    queryFn: () => apiFetch<ProfileViews>("/creator/my/profile/views"),
  });

  if (!data) return null;

  const peak = Math.max(1, ...data.daily.map((day) => day.view_count));
  const last7 = data.daily.slice(-7).reduce((sum, day) => sum + day.view_count, 0);

  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-baseline justify-between">
          <h3 className="font-semibold">프로필 조회수</h3>
          <p className="text-sm text-muted-foreground">
            최근 {data.days}일 <span className="font-semibold text-foreground">{data.total}</span>
            {" · "}최근 7일 <span className="font-semibold text-foreground">{last7}</span>
          </p>
        </div>

        {data.total === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            아직 조회 기록이 없습니다. 프로필을 채우고 공개 링크를 공유해 보세요.
          </p>
        ) : (
          <div className="mt-4 flex h-20 items-end gap-[3px]">
            {data.daily.map((day) => (
              <div
                key={day.view_date}
                title={`${day.view_date} · ${day.view_count}회`}
                className="flex-1 rounded-t-sm bg-primary/70 transition-colors hover:bg-primary"
                style={{
                  height: `${Math.max(2, (day.view_count / peak) * 100)}%`,
                }}
              />
            ))}
          </div>
        )}
        <p className="mt-2 text-xs text-muted-foreground">
          같은 사람이 여러 번 열어도 각각 집계됩니다(순 방문자 수가 아닙니다).
        </p>
      </CardContent>
    </Card>
  );
}
