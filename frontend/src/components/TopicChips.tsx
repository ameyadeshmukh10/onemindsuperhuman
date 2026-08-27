type Props = {
  topics: string[];
  disabled: boolean;
  onPick: (topic: string) => void;
};

export default function TopicChips({ topics, disabled, onPick }: Props) {
  if (topics.length === 0) return null;
  return (
    <div>
      <p className="mb-2 text-[11px] uppercase tracking-wider text-gray-500">Suggested topics</p>
      <div className="flex flex-wrap gap-2">
        {topics.map((topic) => (
          <button
            key={topic}
            disabled={disabled}
            onClick={() => onPick(topic)}
            className="rounded-full border border-accent/50 px-3.5 py-1.5 text-[13px] text-accent-soft-2 transition hover:bg-accent/10 disabled:opacity-40"
          >
            {topic}
          </button>
        ))}
      </div>
    </div>
  );
}
