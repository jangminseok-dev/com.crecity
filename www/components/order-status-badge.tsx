import { ORDER_STATUS_LABELS } from "@/lib/labels";
import type { Order } from "@/lib/types";

/* 주문 상태 색 — 디자인 시스템 tokens/colors.css의 status 토큰 */
const STATUS_STYLES: Record<Order["status"], string> = {
  PENDING_ACCEPT: "bg-[#f2f4f6] text-[#6b7684]",
  IN_PROGRESS: "bg-[#eef2ff] text-[#2743d6]",
  IN_REVIEW: "bg-[#fef3e0] text-[#c07908]",
  COMPLETED: "bg-[#e6f7f0] text-[#0fa066]",
  REFUNDED: "bg-[#fdebec] text-[#e5484d]",
  CANCELLED: "bg-[#fdebec] text-[#e5484d]",
};

export default function OrderStatusBadge({ status }: { status: Order["status"] }) {
  return (
    <span
      className={`inline-flex h-6 shrink-0 items-center whitespace-nowrap rounded-md px-2 text-xs font-semibold ${STATUS_STYLES[status]}`}
    >
      {ORDER_STATUS_LABELS[status]}
    </span>
  );
}
