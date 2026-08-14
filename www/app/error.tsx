"use client";

import { useEffect } from "react";

/**
 * 예기치 못한 오류의 마지막 방어선(갭 #60) — 흰 화면 대신 다시 시도할 길을 준다.
 *
 * Next 16의 error 경계는 `reset`이 아니라 `retry`를 넘긴다.
 */
export default function Error({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    // 수집 서비스는 아직 없다 — 콘솔에 남겨 개발 중 원인을 잡는다
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto flex max-w-lg flex-col items-center px-4 py-24 text-center">
      <h1 className="text-2xl font-bold tracking-[-0.02em]">문제가 생겼습니다</h1>
      <p className="mt-3 text-[15px] leading-relaxed text-muted-foreground">
        잠시 후 다시 시도해 주세요. 계속 같은 화면이 보이면 잠깐 뒤에 다시 방문해 주세요.
      </p>
      {error.digest && (
        <p className="mt-2 text-xs text-muted-foreground">오류 코드 {error.digest}</p>
      )}
      <button
        type="button"
        onClick={() => retry()}
        className="mt-7 inline-flex h-10 items-center justify-center rounded-md bg-primary px-5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-accent-foreground"
      >
        다시 시도
      </button>
    </div>
  );
}
