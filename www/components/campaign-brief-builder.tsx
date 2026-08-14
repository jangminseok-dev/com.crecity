"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  BRIEF_GOALS,
  BRIEF_SECTIONS,
  EMPTY_BRIEF,
  buildBrief,
  type BriefFields,
} from "@/lib/campaign-brief";

/** 브리프 템플릿(갭 #49) — 입력하는 즉시 결과가 갱신되므로 단일 객체 상태 패턴. */
export default function CampaignBriefBuilder() {
  const [state, setState] = useState<{ fields: BriefFields; copied: boolean }>({
    fields: EMPTY_BRIEF,
    copied: false,
  });

  const brief = buildBrief(state.fields);
  const update = (key: keyof BriefFields, value: string) =>
    setState((prev) => ({ fields: { ...prev.fields, [key]: value }, copied: false }));

  return (
    <div className="mt-8 grid gap-8">
      <section className="grid gap-4">
        <div className="grid gap-1.5">
          <Label htmlFor="goal">캠페인 목표</Label>
          <select
            id="goal"
            value={state.fields.goal}
            onChange={(event) => update("goal", event.target.value)}
            className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm"
          >
            {BRIEF_GOALS.map((goal) => (
              <option key={goal} value={goal}>
                {goal}
              </option>
            ))}
          </select>
        </div>

        {BRIEF_SECTIONS.map((section) => (
          <div key={section.key} className="grid gap-1.5">
            <Label htmlFor={section.key}>{section.label}</Label>
            {section.multiline ? (
              <Textarea
                id={section.key}
                rows={2}
                value={state.fields[section.key]}
                onChange={(event) => update(section.key, event.target.value)}
                placeholder={section.placeholder}
              />
            ) : (
              <Input
                id={section.key}
                value={state.fields[section.key]}
                onChange={(event) => update(section.key, event.target.value)}
                placeholder={section.placeholder}
              />
            )}
            <p className="text-xs text-muted-foreground">{section.hint}</p>
          </div>
        ))}
      </section>

      <section>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-bold tracking-[-0.02em]">완성된 브리프</h2>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                await navigator.clipboard.writeText(brief);
                setState((prev) => ({ ...prev, copied: true }));
              }}
            >
              {state.copied ? "복사됨 ✓" : "복사"}
            </Button>
            <Button
              size="sm"
              nativeButton={false}
              render={<Link href="/dashboard/campaigns">공고 등록하러 가기</Link>}
            />
          </div>
        </div>
        <pre className="mt-3 max-h-[420px] overflow-auto whitespace-pre-wrap rounded-xl border bg-card p-5 text-[13px] leading-relaxed">
          {brief}
        </pre>
        <p className="mt-2 text-xs text-muted-foreground">
          복사한 브리프는 공고 등록 화면의 상세 내용에 붙여 넣거나, 채팅으로 크리에이터에게
          그대로 전달할 수 있습니다.
        </p>
      </section>
    </div>
  );
}
