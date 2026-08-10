"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { ORDER_STATUS_LABELS, formatDeadline, formatKrw } from "@/lib/labels";
import type { Order } from "@/lib/types";

export default function DashboardOrdersPage() {
  const user = useAuthStore((s) => s.user);
  const { data: orders, isPending } = useQuery({
    queryKey: ["myOrders"],
    queryFn: () => apiFetch<Order[]>("/order/orders"),
  });

  if (isPending || !user) return <Skeleton className="h-64 w-full" />;
  if (!orders || orders.length === 0) {
    return (
      <p className="rounded-lg border border-dashed py-16 text-center text-muted-foreground">
        아직 주문이 없습니다.
      </p>
    );
  }

  return (
    <div className="grid gap-3">
      {orders.map((order) => {
        const isBrand = order.brand_user_id === user.id;
        return (
          <Link key={order.id} href={`/dashboard/orders/${order.id}`}>
            <Card className="transition-shadow hover:shadow-md">
              <CardContent className="flex items-center justify-between gap-4 p-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={
                        order.status === "COMPLETED"
                          ? "secondary"
                          : order.status === "REFUNDED" || order.status === "CANCELLED"
                            ? "destructive"
                            : "outline"
                      }
                    >
                      {ORDER_STATUS_LABELS[order.status]}
                    </Badge>
                    <p className="truncate font-medium">{order.package_title}</p>
                  </div>
                  <p className="mt-1 truncate text-sm text-muted-foreground">
                    주문 #{order.id} · {isBrand ? "내가 주문함" : "받은 주문"}
                    {order.deadline_at && ` · ${formatDeadline(order.deadline_at)}`}
                  </p>
                </div>
                <p className="shrink-0 font-semibold">
                  {formatKrw(isBrand ? order.brand_total_krw : order.creator_payout_krw)}
                </p>
              </CardContent>
            </Card>
          </Link>
        );
      })}
    </div>
  );
}
