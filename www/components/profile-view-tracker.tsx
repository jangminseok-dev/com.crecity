"use client";

import { useEffect, useRef } from "react";

/**
 * 프로필 조회 기록(갭 #57) — 브라우저에서 부르므로 크롤러 트래픽이 대체로 빠진다.
 *
 * 화면에 아무것도 그리지 않는다. 실패해도 무시한다(집계가 열람을 방해하면 안 된다).
 * 개발 중 StrictMode의 이중 실행을 ref로 막아 한 번만 보낸다.
 */
export default function ProfileViewTracker({ slug }: { slug: string }) {
  const sent = useRef(false);

  useEffect(() => {
    if (sent.current) return;
    sent.current = true;
    void fetch(`/api/backend/creator/profiles/${encodeURIComponent(slug)}/views`, {
      method: "POST",
    }).catch(() => {});
  }, [slug]);

  return null;
}
