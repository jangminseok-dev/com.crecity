"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";
import type { ProfileFaq } from "@/lib/types";

/** 대시보드 FAQ 관리 — 프로필 아코디언에 노출될 Q&A(최대 10개). */
export default function FaqManager() {
  const queryClient = useQueryClient();
  // 단일 객체 상태 — 오류 메시지 (입력값은 FormData 패턴)
  const [ui, setUi] = useState<{ error: string | null }>({ error: null });

  const { data: faqs } = useQuery({
    queryKey: ["myFaqs"],
    queryFn: () => apiFetch<ProfileFaq[]>("/creator/my/faqs"),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["myFaqs"] });

  const add = useMutation({
    mutationFn: (body: { question: string; answer: string }) =>
      apiFetch<ProfileFaq>("/creator/my/faqs", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      setUi({ error: null });
      void invalidate();
    },
    onError: (error) =>
      setUi({ error: error instanceof ApiError ? error.detail : "등록에 실패했습니다." }),
  });

  const remove = useMutation({
    mutationFn: (faqId: number) =>
      apiFetch<void>(`/creator/my/faqs/${faqId}`, { method: "DELETE" }),
    onSuccess: invalidate,
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formElement = e.currentTarget;
    const form = new FormData(formElement);
    const question = String(form.get("question") ?? "").trim();
    const answer = String(form.get("answer") ?? "").trim();
    if (!question || !answer) {
      setUi({ error: "질문과 답변을 모두 입력해 주세요." });
      return;
    }
    add.mutate({ question, answer }, { onSuccess: () => formElement.reset() });
  };

  return (
    <Card>
      <CardContent className="p-6">
        <p className="font-semibold">자주 묻는 질문 (FAQ)</p>
        <p className="mt-1 text-sm text-muted-foreground">
          프로필에 아코디언으로 표시됩니다. 오디언스 구성·협업했던 브랜드처럼 브랜드가 궁금해할
          내용을 적어 두면 문의가 줄어듭니다. (최대 10개)
        </p>

        {faqs && faqs.length > 0 && (
          <div className="mt-4 grid gap-2">
            {faqs.map((faq) => (
              <div key={faq.id} className="flex items-start gap-3 rounded-lg border px-3 py-2.5">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{faq.question}</p>
                  <p className="mt-0.5 line-clamp-2 text-[13px] text-muted-foreground">
                    {faq.answer}
                  </p>
                </div>
                <button
                  type="button"
                  aria-label="FAQ 삭제"
                  onClick={() => remove.mutate(faq.id)}
                  className="inline-flex size-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-destructive"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 grid gap-3.5">
          <div className="grid gap-1.5">
            <Label htmlFor="faq-question">질문</Label>
            <Input
              id="faq-question"
              name="question"
              maxLength={200}
              placeholder="예: 오디언스는 어떤 분들인가요?"
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="faq-answer">답변</Label>
            <Textarea
              id="faq-answer"
              name="answer"
              rows={3}
              maxLength={2000}
              placeholder="예: 20~30대 여성이 70%이고, 스킨케어·성분 리뷰에 관심이 많습니다."
            />
          </div>
          {ui.error && <p className="text-sm text-destructive">{ui.error}</p>}
          <Button type="submit" disabled={add.isPending} className="justify-self-start">
            {add.isPending ? "등록 중…" : "FAQ 추가"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
