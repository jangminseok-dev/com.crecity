import Link from "next/link";

/** 404 — 없는 주소이거나 삭제·비공개된 프로필에 닿았을 때(갭 #60). */
export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center px-4 py-24 text-center">
      <p className="text-[13px] font-semibold text-primary">404</p>
      <h1 className="mt-2 text-2xl font-bold tracking-[-0.02em]">
        찾으시는 페이지가 없습니다
      </h1>
      <p className="mt-3 text-[15px] leading-relaxed text-muted-foreground">
        주소가 바뀌었거나 삭제된 페이지일 수 있습니다. 크리에이터 프로필이라면 심사 중이거나
        공개가 중단된 경우일 수도 있어요.
      </p>
      <div className="mt-7 flex flex-wrap justify-center gap-2">
        <Link
          href="/"
          className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-accent-foreground"
        >
          크리에이터 둘러보기
        </Link>
        <Link
          href="/how-it-works"
          className="inline-flex h-10 items-center justify-center rounded-md border px-5 text-sm font-semibold transition-colors hover:bg-secondary"
        >
          이용 방법
        </Link>
      </div>
    </div>
  );
}
