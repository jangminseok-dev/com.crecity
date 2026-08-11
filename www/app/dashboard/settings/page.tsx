"use client";

import AccountDeletionSection from "@/components/account-deletion-section";
import { Card, CardContent } from "@/components/ui/card";
import { useAuthStore } from "@/lib/auth-store";

export default function DashboardSettingsPage() {
  const user = useAuthStore((s) => s.user);
  if (!user) return null;

  return (
    <div className="grid gap-6">
      <Card>
        <CardContent className="grid gap-2 p-6 text-sm">
          <p className="font-semibold">계정 정보</p>
          <p className="text-muted-foreground">
            이메일 <span className="text-foreground">{user.email}</span>
          </p>
          <p className="text-muted-foreground">
            계정 유형{" "}
            <span className="text-foreground">
              {user.account_type === "CREATOR" ? "크리에이터" : "브랜드"}
            </span>{" "}
            — 계정 유형은 가입 시 결정되며 변경할 수 없습니다.
          </p>
        </CardContent>
      </Card>
      <AccountDeletionSection />
    </div>
  );
}
