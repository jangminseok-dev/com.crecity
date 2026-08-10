"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { Button } from "@/components/ui/button";

function PayFailContent() {
  const searchParams = useSearchParams();
  const message = searchParams.get("message") ?? "결제가 취소되었거나 실패했습니다.";

  return (
    <div className="mx-auto max-w-md px-4 py-20 text-center">
      <p className="text-lg font-semibold">결제에 실패했습니다</p>
      <p className="mt-2 text-sm text-muted-foreground">{message}</p>
      <p className="mt-1 text-xs text-muted-foreground">청구된 금액은 없습니다.</p>
      <Button className="mt-6" nativeButton={false} render={<Link href="/">홈으로</Link>} />
    </div>
  );
}

export default function PayFailPage() {
  return (
    <Suspense>
      <PayFailContent />
    </Suspense>
  );
}
