// v1 persona stage visual: a real image if backend/content/persona.* exists,
// otherwise a generated avatar orb. Pulse rings animate while speaking.
// (Replaced by an avatar video stream in roadmap v2/v3.)

type Props = {
  name: string;
  imageUrl?: string | null;
  speaking: boolean;
  size?: number;
};

export default function PersonaVisual({ name, imageUrl, speaking, size = 280 }: Props) {
  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      {speaking && (
        <>
          <span className="speaking-ring absolute inset-0 rounded-full border-2 border-accent/50" />
          <span
            className="speaking-ring absolute inset-0 rounded-full border border-accent/30"
            style={{ animationDelay: "0.5s" }}
          />
        </>
      )}
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={name}
          className="h-full w-full rounded-full border-2 border-line object-cover"
        />
      ) : (
        <div
          className="flex h-full w-full items-center justify-center rounded-full border-2 border-line"
          style={{
            background:
              "radial-gradient(circle at 35% 30%, #2dd4bf22 0%, transparent 45%), linear-gradient(140deg, #14532d 0%, #052e16 55%, #0b0f14 100%)",
          }}
        >
          <span className="select-none text-[38%] font-bold text-accent" style={{ fontSize: size * 0.34 }}>
            {name.charAt(0)}
          </span>
        </div>
      )}
    </div>
  );
}
