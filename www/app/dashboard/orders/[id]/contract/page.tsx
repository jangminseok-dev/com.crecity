"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { formatKrw } from "@/lib/labels";
import type { Order } from "@/lib/types";

/**
 * 주문 계약 조건 확인서(§9.2 표준계약 조항, 갭 #52).
 *
 * 주문에 **이미 스냅샷된 값**(금액·수수료율·수정 횟수·사용권)만 조합한 파생 뷰다 —
 * 새 데이터를 만들지 않는다. 실명·사업자 정보는 플랫폼이 보관하지 않으므로
 * 당사자는 회원번호로 적고, 문서 성격을 하단에 명시한다.
 */

function formatDate(value: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`;
}

function Clause({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border-t py-4">
      <h2 className="text-[15px] font-bold">{title}</h2>
      <div className="mt-2 space-y-1.5 text-[14px] leading-relaxed text-muted-foreground">
        {children}
      </div>
    </section>
  );
}

export default function OrderContractPage() {
  const params = useParams<{ id: string }>();
  const user = useAuthStore((state) => state.user);
  const { data: order, isPending } = useQuery({
    queryKey: ["order", params.id],
    queryFn: () => apiFetch<Order>(`/order/orders/${params.id}`),
  });

  if (isPending) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <Skeleton className="h-8 w-52" />
        <Skeleton className="mt-4 h-64 w-full" />
      </div>
    );
  }
  if (!order) {
    return (
      <p className="mx-auto max-w-2xl px-4 py-16 text-center text-muted-foreground">
        주문을 찾을 수 없거나 열람 권한이 없습니다.
      </p>
    );
  }

  const myRole =
    user?.id === order.brand_user_id
      ? "브랜드"
      : user?.id === order.creator_user_id
        ? "크리에이터"
        : null;

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <div className="no-print mb-6 flex items-center justify-between">
        <Link
          href={`/dashboard/orders/${order.id}`}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          ← 주문으로 돌아가기
        </Link>
        <Button variant="outline" size="sm" onClick={() => window.print()}>
          인쇄
        </Button>
      </div>

      <header className="text-center">
        <h1 className="text-[22px] font-bold tracking-[-0.02em]">주문 계약 조건 확인서</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">
          주문번호 {order.id} · 체결일 {formatDate(order.created_at)}
        </p>
      </header>

      <Clause title="제1조 (당사자)">
        <p>
          발주자(브랜드): 회원번호 {order.brand_user_id}
          {myRole === "브랜드" && " (본인)"}
        </p>
        <p>
          수행자(크리에이터): 회원번호 {order.creator_user_id}
          {myRole === "크리에이터" && " (본인)"}
        </p>
        <p>중개자: 크리시티(통신판매중개자) — 거래 당사자가 아니며 대금을 예치·정산합니다.</p>
      </Clause>

      <Clause title="제2조 (계약 목적물)">
        <p>상품: {order.package_title}</p>
        {order.requirements && <p className="whitespace-pre-wrap">요구사항: {order.requirements}</p>}
      </Clause>

      <Clause title="제3조 (대금 및 수수료)">
        <p>계약 금액: {formatKrw(order.amount_krw)}</p>
        <p>
          발주자 결제 총액: {formatKrw(order.brand_total_krw)} (중개 수수료{" "}
          {order.brand_fee_percent}% 포함)
        </p>
        <p>
          수행자 수령 예정액: {formatKrw(order.creator_payout_krw)} (중개 수수료{" "}
          {order.creator_fee_percent}% 공제 후, 인출 시 사업소득 원천징수 3.3% 별도 공제)
        </p>
        <p className="text-foreground">
          위 요율은 주문 시점 값으로 고정되며 이후 요율이 변경되어도 이 주문에는 적용되지
          않습니다.
        </p>
      </Clause>

      <Clause title="제4조 (대금의 예치와 지급)">
        <p>
          발주자가 결제한 대금은 수행자에게 즉시 지급되지 않고 크리시티가 예치합니다.
          발주자가 결과물을 승인하는 시점에 수행자의 잔액으로 지급됩니다.
        </p>
        <p>
          수행자가 72시간 내에 주문을 수락하지 않거나 거절하면 계약은 성립하지 않으며 결제 대금
          전액이 발주자의 크레딧으로 환급됩니다.
        </p>
      </Clause>

      <Clause title="제5조 (납품 및 검수)">
        <p>수행자는 결과물(파일 또는 게시물 링크)을 플랫폼에 등록하는 방식으로 납품합니다.</p>
        <p>
          수행자는 게시 전 초안을 제출해 발주자의 컨펌을 받을 수 있으며, 발주자가 72시간 내에
          컨펌 또는 수정을 요청하지 않으면 초안은 자동으로 컨펌됩니다. 초안 단계는 선택 사항입니다.
        </p>
        <p>
          발주자는 납품일로부터 72시간 내에 승인 또는 수정을 요청해야 하며, 기간 내 조치가 없으면
          자동으로 승인 처리되어 대금이 지급됩니다.
        </p>
      </Clause>

      <Clause title="제6조 (수정 요청)">
        <p>
          발주자는 원 요구사항의 범위 내에서 {order.revision_limit}회까지 수정을 요청할 수
          있습니다. (현재 {order.revisions_used}회 사용)
        </p>
        {order.revision_limit === 0 && <p>이 주문은 수정 요청이 포함되지 않은 조건입니다.</p>}
      </Clause>

      <Clause title="제7조 (2차 활용 범위)">
        {order.usage_rights ? (
          <p className="whitespace-pre-wrap">{order.usage_rights}</p>
        ) : (
          <p>
            별도로 합의된 2차 활용 범위가 없습니다. 결과물의 활용 범위는 당사자 간 협의에
            따릅니다.
          </p>
        )}
      </Clause>

      <Clause title="제8조 (계약의 해지 및 분쟁)">
        <p>
          진행 중인 주문은 어느 일방이 취소를 요청하고 상대방이 동의한 경우에 한해 해지되며,
          해지 시 대금 전액이 발주자의 크레딧으로 환급됩니다.
        </p>
        <p>
          합의에 이르지 못한 경우 당사자는 분쟁을 신고할 수 있고, 크리시티는 납품물·대화·수정
          이력을 확인해 환급·지급·기각 중 하나로 판정합니다. 판정은 전액 단위로 이루어집니다.
        </p>
      </Clause>

      <Clause title="제9조 (광고 표시)">
        <p>
          수행자는 대가를 받은 콘텐츠에 「표시·광고의 공정화에 관한 법률」에 따른 경제적 이해관계
          표시(예: 광고, 협찬)를 명확히 해야 합니다.
        </p>
      </Clause>

      <footer className="border-t pt-4 text-[13px] leading-relaxed text-muted-foreground">
        <p>
          본 문서는 주문 시점에 확정된 거래 조건을 정리한 확인서입니다. 당사자의 실명·사업자
          정보는 플랫폼이 보관하지 않으므로 회원번호로 표기하며, 별도의 서명 절차는 없습니다.
          결제·승인·수정·해지 등 실제 이행 기록은 주문 상세 화면에 남습니다.
        </p>
        <p className="mt-2">출력일 {formatDate(new Date().toISOString())}</p>
      </footer>
    </div>
  );
}
