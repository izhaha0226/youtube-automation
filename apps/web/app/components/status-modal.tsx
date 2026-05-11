"use client";

type StatusModalTone = "error" | "info" | "success";

type StatusModalProps = {
  open: boolean;
  title?: string;
  message: string | null;
  tone?: StatusModalTone;
  onClose: () => void;
};

const TONE_STYLES: Record<StatusModalTone, { badge: string; title: string; button: string; label: string }> = {
  error: {
    badge: "bg-rose-100 text-rose-700",
    title: "text-rose-700",
    button: "bg-rose-600 hover:bg-rose-700 focus:ring-rose-200",
    label: "오류",
  },
  info: {
    badge: "bg-blue-100 text-blue-700",
    title: "text-blue-700",
    button: "bg-navy hover:bg-slate-950 focus:ring-blue-200",
    label: "알림",
  },
  success: {
    badge: "bg-emerald-100 text-emerald-700",
    title: "text-emerald-700",
    button: "bg-emerald-600 hover:bg-emerald-700 focus:ring-emerald-200",
    label: "완료",
  },
};

export default function StatusModal({ open, title, message, tone = "error", onClose }: StatusModalProps) {
  if (!open || !message) return null;

  const style = TONE_STYLES[tone];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-6 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="status-modal-title">
      <div className="w-full max-w-md overflow-hidden rounded-[28px] border border-white/80 bg-white shadow-[0_28px_90px_-36px_rgba(15,23,42,0.75)]">
        <div className="p-6">
          <div className={`inline-flex rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${style.badge}`}>{style.label}</div>
          <h2 id="status-modal-title" className={`mt-4 text-xl font-semibold tracking-[-0.03em] ${style.title}`}>{title ?? style.label}</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-600">{message}</p>
          <button
            type="button"
            onClick={onClose}
            className={`mt-6 w-full rounded-2xl px-4 py-3 text-sm font-semibold text-white shadow-sm outline-none transition focus:ring-4 ${style.button}`}
          >
            확인
          </button>
        </div>
      </div>
    </div>
  );
}
