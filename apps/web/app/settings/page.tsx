"use client";

import { useState } from "react";

export default function SettingsPage() {
  const [obsidianPath, setObsidianPath] = useState("/Users/yosiki/Documents/Obsidian Vault/wiki/YouTube 자동화프로젝트");
  const [shareLink, setShareLink] = useState("https://share.note.sx/qynhdluo");
  const [model, setModel] = useState("gpt-5.4");
  const [backupModel, setBackupModel] = useState("gpt-4o");
  const [syncMode, setSyncMode] = useState("obsidian_first");
  const [ttsEngine, setTtsEngine] = useState("azure");
  const [thumbnailEngine, setThumbnailEngine] = useState("fal.ai");

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h2 className="text-xl font-semibold">설정</h2>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 className="font-semibold">Obsidian 연동</h3>
        <div className="mt-3 grid gap-3">
          <label className="block">
            <span className="text-xs font-medium text-slate-500">Vault 경로</span>
            <input value={obsidianPath} onChange={(e) => setObsidianPath(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy focus:outline-none" />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-slate-500">공유 링크</span>
            <input value={shareLink} onChange={(e) => setShareLink(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy focus:outline-none" />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-slate-500">동기화 모드</span>
            <select value={syncMode} onChange={(e) => setSyncMode(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="obsidian_first">Obsidian 우선 → Workspace 동기화</option>
              <option value="workspace_first">Workspace 우선</option>
              <option value="manual">수동</option>
            </select>
          </label>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 className="font-semibold">AI 모델</h3>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <label className="block">
            <span className="text-xs font-medium text-slate-500">기본 모델</span>
            <select value={model} onChange={(e) => setModel(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="gpt-5.4">gpt-5.5</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-5.4-mini">gpt-5.5 mini</option>
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-medium text-slate-500">백업 모델</span>
            <select value={backupModel} onChange={(e) => setBackupModel(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-5.4">gpt-5.5</option>
            </select>
          </label>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 className="font-semibold">엔진 설정</h3>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <label className="block">
            <span className="text-xs font-medium text-slate-500">TTS (나레이션)</span>
            <select value={ttsEngine} onChange={(e) => setTtsEngine(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="azure">Azure Neural TTS</option>
              <option value="elevenlabs">ElevenLabs</option>
              <option value="openai">OpenAI TTS</option>
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-medium text-slate-500">썸네일 이미지</span>
            <select value={thumbnailEngine} onChange={(e) => setThumbnailEngine(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="fal.ai">Fal.ai</option>
              <option value="replicate">Replicate</option>
            </select>
          </label>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 className="font-semibold">언어 설정</h3>
        <div className="mt-3 flex gap-3">
          {["한국어 (KO)", "English (EN)", "日本語 (JA)", "中文 (ZH)"].map((lang) => (
            <label key={lang} className="flex items-center gap-2 text-sm">
              <input type="checkbox" defaultChecked className="rounded" /> {lang}
            </label>
          ))}
        </div>
      </section>

      <button className="w-full rounded-lg bg-navy py-2.5 text-sm font-semibold text-white">저장</button>
    </div>
  );
}
