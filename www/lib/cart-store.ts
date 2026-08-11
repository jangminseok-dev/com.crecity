import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { CreatorPackage } from "@/lib/types";

// 장바구니는 결제 전 임시 상태 — 가격·주문 가능 여부는 결제 준비 시 서버가 전부 재확정한다.
// 표시용 스냅샷만 담고, localStorage에 남긴다(로그인 전에도 담기 가능).
export type CartItem = {
  package_id: number;
  title: string;
  price_krw: number;
  platform: CreatorPackage["platform"];
  creator_slug: string;
};

type CartState = {
  items: CartItem[];
  add: (item: CartItem) => void;
  remove: (packageId: number) => void;
  clear: () => void;
};

export const useCartStore = create<CartState>()(
  persist(
    (set) => ({
      items: [],
      add: (item) =>
        set((state) =>
          state.items.some((i) => i.package_id === item.package_id)
            ? state
            : { items: [...state.items, item] },
        ),
      remove: (packageId) =>
        set((state) => ({ items: state.items.filter((i) => i.package_id !== packageId) })),
      clear: () => set({ items: [] }),
    }),
    { name: "crecity-cart" },
  ),
);
