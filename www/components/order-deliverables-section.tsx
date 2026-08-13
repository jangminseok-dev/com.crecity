"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ApiError, apiFetch } from "@/lib/api";
import type { Deliverable } from "@/lib/types";

const ACCEPT =
  "image/jpeg,image/png,image/webp,video/mp4,video/quicktime,application/pdf,application/zip";

function errorMessage(error: unknown): string | null {
  if (!error) return null;
  return error instanceof ApiError ? error.detail : "처리에 실패했습니다.";
}

/** 납품물 목록 + (IN_PROGRESS 크리에이터에게만) 파일·링크 등록 — 제출의 실체가 되는 결과물. */
export default function OrderDeliverablesSection({
  orderId,
  canUpload,
}: {
  orderId: number;
  canUpload: boolean;
}) {
  const queryClient = useQueryClient();

  const { data: deliverables } = useQuery({
    queryKey: ["deliverables", orderId],
    queryFn: () => apiFetch<Deliverable[]>(`/order/orders/${orderId}/deliverables`),
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["deliverables", orderId] });

  const uploadFile = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return apiFetch<Deliverable>(`/order/orders/${orderId}/deliverables/files`, {
        method: "POST",
        body: form,
      });
    },
    onSuccess: invalidate,
  });

  const addLink = useMutation({
    mutationFn: (body: { url: string; caption: string | null }) =>
      apiFetch<Deliverable>(`/order/orders/${orderId}/deliverables/links`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: invalidate,
  });

  const handleLinkSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formElement = e.currentTarget;
    const form = new FormData(formElement);
    const url = String(form.get("url") ?? "").trim();
    if (!url) return;
    const caption = String(form.get("caption") ?? "").trim();
    addLink.mutate(
      { url, caption: caption || null },
      { onSuccess: () => formElement.reset() },
    );
  };

  const error = errorMessage(uploadFile.error) ?? errorMessage(addLink.error);
  // 광고 표기 미확인 링크 — 차단하지 않고 경고만 한다(공정위 표시·광고 심사지침).
  const undisclosed =
    deliverables?.filter((deliverable) => deliverable.ad_disclosure_ok === false) ?? [];

  if (!canUpload && (deliverables?.length ?? 0) === 0) return null;

  return (
    <Card>
      <CardContent className="grid gap-4 p-6">
        <div>
          <p className="font-semibold">납품물</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {canUpload
              ? "결과물 파일 또는 게시된 콘텐츠 링크를 등록해야 제출할 수 있습니다."
              : "크리에이터가 인도한 결과물입니다 — 승인·수정 요청 판단의 근거가 됩니다."}
          </p>
        </div>

        {undisclosed.length > 0 && (
          <p className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
            ⚠️ 광고 표기가 확인되지 않은 링크 {undisclosed.length}건이 있습니다 —{" "}
            {canUpload
              ? "게시물 본문에 “광고·협찬” 등 대가성 표시를 넣어 주세요(표시광고법)."
              : "승인 전에 게시물에 광고·협찬 표기가 있는지 확인해 주세요."}
          </p>
        )}

        {(deliverables?.length ?? 0) > 0 && (
          <ul className="grid gap-2">
            {deliverables?.map((deliverable) => (
              <li key={deliverable.id} className="rounded-md border px-3 py-2 text-sm">
                {deliverable.kind === "FILE" ? (
                  <a
                    href={`/api/backend${deliverable.file_url}`}
                    target="_blank"
                    rel="noreferrer"
                    className="underline underline-offset-2"
                  >
                    📎 {deliverable.original_name ?? "파일"}
                  </a>
                ) : (
                  <>
                    <a
                      href={deliverable.url ?? "#"}
                      target="_blank"
                      rel="noreferrer"
                      className="break-all underline underline-offset-2"
                    >
                      🔗 {deliverable.url}
                    </a>
                    <span
                      className={`ml-2 whitespace-nowrap text-xs ${
                        deliverable.ad_disclosure_ok
                          ? "text-muted-foreground"
                          : "text-destructive"
                      }`}
                    >
                      {deliverable.ad_disclosure_ok ? "광고 표기 확인" : "광고 표기 미확인"}
                    </span>
                    {deliverable.caption && (
                      <p className="mt-1 whitespace-pre-wrap text-xs text-muted-foreground">
                        {deliverable.caption}
                      </p>
                    )}
                  </>
                )}
              </li>
            ))}
          </ul>
        )}

        {canUpload && (
          <div className="grid gap-2">
            <label
              className={`inline-flex cursor-pointer justify-self-start rounded-md border px-3 py-2 text-sm transition-colors hover:bg-secondary ${
                uploadFile.isPending ? "pointer-events-none opacity-50" : ""
              }`}
            >
              {uploadFile.isPending ? "업로드 중…" : "파일 업로드 (이미지·영상·PDF·ZIP, 100MB 이하)"}
              <input
                type="file"
                accept={ACCEPT}
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) uploadFile.mutate(file);
                  e.target.value = ""; // 같은 파일 재선택 허용
                }}
              />
            </label>
            <form onSubmit={handleLinkSubmit} className="grid gap-2">
              <div className="flex gap-2">
                <input
                  name="url"
                  type="url"
                  placeholder="게시된 콘텐츠 링크 (https://…)"
                  className="h-9 flex-1 rounded-md border border-input bg-transparent px-3 text-sm outline-none transition-colors focus:border-primary"
                />
                <Button type="submit" variant="outline" disabled={addLink.isPending}>
                  링크 등록
                </Button>
              </div>
              <textarea
                name="caption"
                rows={3}
                maxLength={3000}
                placeholder="게시물 본문 붙여넣기 (선택) — “광고·협찬” 표기가 있는지 자동 검수합니다"
                className="rounded-md border border-input bg-transparent px-3 py-2 text-sm outline-none transition-colors focus:border-primary"
              />
            </form>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
