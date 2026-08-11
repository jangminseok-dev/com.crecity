import { create } from "zustand";
import { persist } from "zustand/middleware";

// 쇼트리스트(찜)는 결제 전 탐색 단계의 개인 메모 — 서버 저장 없이 브라우저에 남긴다.
// 비교 표에 필요한 표시용 스냅샷만 담는다(가격·평점은 진입 시점 값).
export type ShortlistItem = {
  slug: string;
  name: string;
  primary_category: string;
  tagline: string;
  location: string | null;
  cover_image_url: string | null;
  price_from: number | null;
  rating_avg: number | null;
  rating_count: number;
};

type ShortlistState = {
  items: ShortlistItem[];
  toggle: (item: ShortlistItem) => void;
  remove: (slug: string) => void;
  clear: () => void;
};

export const useShortlistStore = create<ShortlistState>()(
  persist(
    (set) => ({
      items: [],
      toggle: (item) =>
        set((state) =>
          state.items.some((i) => i.slug === item.slug)
            ? { items: state.items.filter((i) => i.slug !== item.slug) }
            : { items: [...state.items, item] },
        ),
      remove: (slug) => set((state) => ({ items: state.items.filter((i) => i.slug !== slug) })),
      clear: () => set({ items: [] }),
    }),
    { name: "crecity-shortlist" },
  ),
);
