"use client";

import { ChevronDown } from "lucide-react";
import { useState } from "react";

import type { ProfileFaq } from "@/lib/types";

/** 프로필 FAQ 아코디언(§2.1-9) — 한 번에 하나만 펼친다. */
export default function ProfileFaqAccordion({ faqs }: { faqs: ProfileFaq[] }) {
  // 단일 값 상태 — 펼쳐진 FAQ id(null이면 모두 접힘)
  const [openId, setOpenId] = useState<number | null>(null);

  if (faqs.length === 0) return null;

  return (
    <div className="divide-y rounded-xl border">
      {faqs.map((faq) => {
        const open = openId === faq.id;
        return (
          <div key={faq.id}>
            <button
              type="button"
              aria-expanded={open}
              onClick={() => setOpenId(open ? null : faq.id)}
              className="flex w-full items-center justify-between gap-3 px-4 py-3.5 text-left"
            >
              <span className="text-[15px] font-medium">{faq.question}</span>
              <ChevronDown
                className={`size-4 shrink-0 text-muted-foreground transition-transform ${
                  open ? "rotate-180" : ""
                }`}
              />
            </button>
            {open && (
              <p className="whitespace-pre-line px-4 pb-4 text-sm leading-relaxed text-muted-foreground">
                {faq.answer}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
