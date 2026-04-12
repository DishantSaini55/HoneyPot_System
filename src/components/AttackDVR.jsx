import { useEffect, useMemo, useState } from "react";

function AttackDVR({ commands }) {
  const joined = useMemo(() => commands.join("\n$ "), [commands]);
  const fullText = useMemo(() => `$ ${joined}`, [joined]);
  const [index, setIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    if (!isPlaying) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      setIndex((prev) => {
        if (prev >= fullText.length) {
          return prev;
        }
        return prev + speed;
      });
    }, 28);

    return () => window.clearInterval(timer);
  }, [fullText.length, isPlaying, speed]);

  useEffect(() => {
    setIndex(0);
    setIsPlaying(false);
  }, [fullText]);

  return (
    <div>
      <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slateText">Attack DVR Session Replay</p>
      <div className="terminal-glow h-48 overflow-auto rounded-lg border border-cyan-500/40 bg-black p-3 font-mono text-xs text-green-300 scroll-thin">
        <pre className="whitespace-pre-wrap">{fullText.slice(0, index)}{isPlaying && index < fullText.length ? "_" : ""}</pre>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setIsPlaying(true)}
          className="rounded border border-cyan-400/60 bg-cyan-500/10 px-3 py-1 text-xs uppercase tracking-[0.14em] text-cyan-200"
        >
          Play
        </button>
        <button
          type="button"
          onClick={() => setIsPlaying(false)}
          className="rounded border border-slate-600 bg-slate-800 px-3 py-1 text-xs uppercase tracking-[0.14em] text-slate-200"
        >
          Pause
        </button>
        <button
          type="button"
          onClick={() => setSpeed(2)}
          className="rounded border border-botYellow/60 bg-botYellow/10 px-3 py-1 text-xs uppercase tracking-[0.14em] text-yellow-200"
        >
          Fast Forward 2x
        </button>
        <button
          type="button"
          onClick={() => setSpeed(4)}
          className="rounded border border-botYellow/60 bg-botYellow/10 px-3 py-1 text-xs uppercase tracking-[0.14em] text-yellow-200"
        >
          Fast Forward 4x
        </button>
        <button
          type="button"
          onClick={() => {
            setIndex(0);
            setSpeed(1);
            setIsPlaying(false);
          }}
          className="rounded border border-slate-600 bg-slate-800 px-3 py-1 text-xs uppercase tracking-[0.14em] text-slate-200"
        >
          Reset
        </button>
      </div>
    </div>
  );
}

export default AttackDVR;
