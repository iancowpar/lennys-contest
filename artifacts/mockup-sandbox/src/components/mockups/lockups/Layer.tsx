export function Layer() {
  const amber = "#c2750a";
  const parchment = "#faf8f5";
  const ink = "#1c1917";
  const inkFaint = "#57534e";

  const LayerMark = ({ size = 36, light = false }: { size?: number; light?: boolean }) => {
    const barColor = amber;
    const barLight = light ? "rgba(194,117,10,0.35)" : "rgba(194,117,10,0.25)";
    const unit = size / 36;
    return (
      <svg width={size} height={size} viewBox="0 0 36 36" fill="none" aria-hidden>
        <rect x={4} y={10} width={22} height={4} rx={2} fill={barColor} opacity={0.35} />
        <rect x={8} y={17} width={22} height={4} rx={2} fill={barColor} opacity={0.65} />
        <rect x={4} y={24} width={28} height={4} rx={2} fill={barColor} />
      </svg>
    );
  };

  const Lockup = ({
    bg,
    textColor,
    subColor,
    compact = false,
  }: {
    bg: string;
    textColor: string;
    subColor: string;
    compact?: boolean;
  }) => (
    <div
      style={{
        background: bg,
        borderRadius: 12,
        padding: compact ? "20px 28px" : "28px 36px",
        display: "flex",
        flexDirection: "column",
        gap: compact ? 20 : 28,
        minWidth: compact ? 280 : 360,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <LayerMark size={compact ? 28 : 36} />
        <div style={{ display: "flex", flexDirection: "column", lineHeight: 1 }}>
          <span
            style={{
              fontFamily: "'Lora', Georgia, serif",
              fontSize: compact ? 9 : 10,
              fontWeight: 400,
              fontStyle: "italic",
              letterSpacing: "0.1em",
              color: subColor,
              marginBottom: 4,
            }}
          >
            Beneath the
          </span>
          <span
            style={{
              fontFamily: "'Lora', Georgia, serif",
              fontSize: compact ? 16 : 20,
              fontWeight: 700,
              color: textColor,
              letterSpacing: "-0.02em",
            }}
          >
            Org Chart
          </span>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <LayerMark size={20} />
        <span
          style={{
            fontFamily: "'Lora', Georgia, serif",
            fontSize: 12,
            fontStyle: "italic",
            color: textColor,
            letterSpacing: "-0.005em",
          }}
        >
          Beneath the Org Chart
        </span>
      </div>
    </div>
  );

  return (
    <>
      <link
        rel="stylesheet"
        media="print"
        onLoad={(e) => { (e.target as HTMLLinkElement).media = "all"; }}
        href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;0,700;1,400;1,600&display=swap"
      />
      <div
        style={{
          minHeight: "100vh",
          background: parchment,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 24,
          padding: 32,
        }}
      >
        <p style={{ fontSize: 11, color: "#a8a29e", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>Layer Mark</p>
        <Lockup bg="#ffffff" textColor={ink} subColor={inkFaint} />
        <Lockup bg="#1c1917" textColor="#faf8f5" subColor="#a8a29e" />
      </div>
    </>
  );
}
