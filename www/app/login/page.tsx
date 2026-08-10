"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { createOAuthContext, oauthRedirectUri, type OAuthContext } from "@/lib/oauth";

const ACCOUNT_TYPES = [
  {
    value: "CREATOR",
    title: "크리에이터로 시작",
    description: "프로필과 판매 패키지를 등록하고 브랜드의 주문을 받습니다.",
  },
  {
    value: "BRAND",
    title: "브랜드로 시작",
    description: "크리에이터를 찾아 콘텐츠 제작을 주문합니다.",
  },
] as const;

export default function LoginPage() {
  const authStatus = useAuthStore((s) => s.status);
  // 단일 값 상태 — 계정 유형 선택(신규 가입 시에만 의미, 기존 계정은 저장된 유형 유지)
  const [accountType, setAccountType] = useState<OAuthContext["account_type"]>("CREATOR");

  const startLogin = async (provider: OAuthContext["provider"]) => {
    const context = createOAuthContext(provider, accountType);
    const { authorize_url } = await apiFetch<{ authorize_url: string }>(
      `/auth/social/${provider}/authorize-url?` +
        new URLSearchParams({
          redirect_uri: oauthRedirectUri(provider),
          state: context.state,
        }),
    );
    window.location.href = authorize_url;
  };

  if (authStatus === "authenticated") {
    return (
      <div className="mx-auto max-w-md px-4 py-20 text-center">
        <p className="text-lg font-semibold">이미 로그인되어 있습니다.</p>
        <Button className="mt-4" render={<Link href="/">홈으로 가기</Link>} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md px-4 py-14">
      <h1 className="text-center text-2xl font-bold">시작하기</h1>
      <p className="mt-2 text-center text-sm text-muted-foreground">
        같은 이메일이면 어떤 소셜 계정으로 로그인해도 하나의 계정으로 이어집니다.
      </p>

      <div className="mt-8 grid gap-3">
        {ACCOUNT_TYPES.map((type) => (
          <Card
            key={type.value}
            className={
              accountType === type.value
                ? "cursor-pointer border-primary ring-2 ring-primary/30"
                : "cursor-pointer hover:border-foreground/30"
            }
            onClick={() => setAccountType(type.value)}
          >
            <CardContent className="p-4">
              <p className="font-semibold">{type.title}</p>
              <p className="mt-1 text-sm text-muted-foreground">{type.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-8 grid gap-2">
        <Button size="lg" onClick={() => void startLogin("naver")}>
          네이버로 계속하기
        </Button>
        <Button size="lg" variant="outline" onClick={() => void startLogin("google")}>
          구글로 계속하기
        </Button>
        <Button size="lg" variant="secondary" disabled>
          카카오로 계속하기 (준비 중)
        </Button>
      </div>

      <p className="mt-6 text-center text-xs text-muted-foreground">
        로그인하면 서비스 이용약관 및 개인정보 처리방침에 동의하는 것으로 간주됩니다.
      </p>
    </div>
  );
}
