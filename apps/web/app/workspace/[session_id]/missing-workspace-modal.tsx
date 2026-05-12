"use client";

import StatusModal from "../../components/status-modal";

const MISSING_WORKSPACE_MESSAGE = "해당 세션의 워크스페이스를 찾지 못했어. 먼저 홈에서 리서치 → 주제 선택 → 시나리오 생성까지 한 번 돌려줘.";

export default function MissingWorkspaceModal() {
  return (
    <StatusModal
      open
      title="워크스페이스를 찾지 못했어"
      message={MISSING_WORKSPACE_MESSAGE}
      tone="error"
      onClose={() => {
        window.location.href = "/";
      }}
    />
  );
}
