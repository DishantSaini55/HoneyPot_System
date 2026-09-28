export function PageHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <header className="mb-7"><p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan-400">{eyebrow}</p><h1 className="mt-2 text-3xl font-semibold text-white">{title}</h1><p className="mt-2 max-w-3xl text-sm text-slate-400">{description}</p></header>;
}

