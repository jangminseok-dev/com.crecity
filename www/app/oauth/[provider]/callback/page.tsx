"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/auth-store";
import { consumeOAuthContext, oauthRedirectUri } from "@/lib/oauth";

type CallbackState =
  | { phase: "processing" }
  | { phase: "error"; message: string };

function CallbackContent() {
  const router = useRouter();
  const { provider } = useParams<{ provider: string }>();
  const searchParams = useSearchParams();
  const setSession = useAuthStore((s) => s.setSession);
  // 단일 객체 상태 — 처리 단계와 오류 메시지를 함께 담는다
  const [state, setState] = useState<CallbackState>({ phase: "processing" });
  // 개발 모드 StrictMode의 이펙트 이중 실행 가드 — 컨텍스트 소비·코드 교환은 1회만
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    const code = searchParams.get("code");
    const returnedState = searchParams.get("state");
    const context = consumeOAuthContext();

    if (!code) {
      setState({ phase: "error", message: "인가 코드가 없습니다 — 로그인을 다시 시도해 주세요." });
      return;
    }
    if (!context || context.provider !== provider || context.state !== returnedState) {
      setState({
        phase: "error",
        message: "로그인 요청 검증에 실패했습니다(state 불일치) — 처음부터 다시 시도해 주세요.",
      });
      return;
    }

    const login = async () => {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: context.provider,
          code,
          redirect_uri: oauthRedirectUri(context.provider),
          state: context.state,
          account_type: context.account_type,
        }),
      });
      const payload = await res.json();
      if (!res.ok) {
        const detail = typeof payload?.detail === "string" ? payload.detail : "로그인에 실패했습니다.";
        setState({ phase: "error", message: detail });
        return;
      }
      setSession(payload.access_token as string);
      router.replace("/");
    };
    void login();
    // searchParams·provider는 마운트 시점에 확정 — 1회만 실행한다
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (state.phase === "error") {
    return (
      <div className="mx-auto max-w-md px-4 py-20 text-center">
        <p className="text-lg font-semibold">로그인에 실패했습니다</p>
        <p className="mt-2 text-sm text-muted-foreground">{state.message}</p>
        <Button className="mt-6" render={<Link href="/login">다시 시도하기</Link>} />
      </div>
    );
  }
  return (
    <div className="mx-auto max-w-md px-4 py-20 text-center text-muted-foreground">
      로그인 처리 중입니다…
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense>
      <CallbackContent />
    </Suspense>
  );
}
