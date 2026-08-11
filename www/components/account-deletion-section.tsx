"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/lib/auth-store";

const CONFIRM_TEXT = "탈퇴합니다";

/** 계정 삭제(§3.8) — 진행 중 주문·잔액이 있으면 서버가 막는다(409). */
export default function AccountDeletionSection() {
  const router = useRouter();
  const { accessToken, clearSession } = useAuthStore();
  // 단일 객체 상태 — 진행·오류 (확인 문구는 FormData 패턴)
  const [ui, setUi] = useState<{ submitting: boolean; error: string | null }>({
    submitting: false,
    error: null,
  });

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const confirmText = String(new FormData(e.currentTarget).get("confirm") ?? "").trim();
    if (confirmText !== CONFIRM_TEXT) {
      setUi({ submitting: false, error: `확인을 위해 "${CONFIRM_TEXT}"를 입력해 주세요.` });
      return;
    }
    setUi({ submitting: true, error: null });
    const response = await fetch("/api/auth/delete", {
      method: "POST",
      headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({ detail: "탈퇴에 실패했습니다." }));
      setUi({ submitting: false, error: payload.detail ?? "탈퇴에 실패했습니다." });
      return;
    }
    clearSession();
    router.replace("/");
  };

  return (
    <Card>
      <CardContent className="p-6">
        <p className="font-semibold text-destructive">계정 탈퇴</p>
        <p className="mt-1 text-sm text-muted-foreground">
          탈퇴하면 프로필이 공개 목록에서 내려가고 로그인할 수 없게 됩니다. 진행 중인 주문이나
          남은 잔액이 있으면 탈퇴할 수 없습니다. 거래·정산 기록은 법령에 따라 일정 기간
          보존됩니다.
        </p>
        <form onSubmit={handleSubmit} className="mt-4 grid gap-3">
          <div className="grid gap-1.5">
            <Label htmlFor="confirm">확인을 위해 &quot;{CONFIRM_TEXT}&quot;를 입력하세요</Label>
            <Input id="confirm" name="confirm" placeholder={CONFIRM_TEXT} className="max-w-xs" />
          </div>
          {ui.error && <p className="text-sm text-destructive">{ui.error}</p>}
          <Button
            type="submit"
            variant="destructive"
            disabled={ui.submitting}
            className="justify-self-start"
          >
            {ui.submitting ? "탈퇴 처리 중…" : "계정 탈퇴"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
