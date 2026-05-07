export function Network() {
  const amber = "#c2750a";
  const parchment = "#faf8f5";
  const ink = "#1c1917";
  const inkFaint = "#57534e";

  const NetworkMark = ({ size = 36 }: { size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 36 36" fill="none" aria-hidden>
      <line x1="8" y1="28" x2="18" y2="10" stroke={amber} strokeWidth="1.5" strokeLinecap="round" />
      <line x1="18" y1="10" x2="28" y2="24" stroke={amber} strokeWidth="1.5" strokeLinecap="round" />
      <line x1="8" y1="28" x2="28" y2="24" stroke={amber} strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="18" cy="10" r="3.5" fill={amber} />
      <circle cx="28" cy="24" r="2.5" fill={amber} opacity="0.75" />
      <circle cx="8" cy="28" r="2.5" fill={amber} opacity="0.75" />
    </svg>
  );

  const Lockup = ({
    bg,
    textColor,
    subColor,
  }: {
    bg: string;
    textColor: string;
    subColor: string;
  }) => (
    <div
      style={{
        background: bg,
        borderRadius: 12,
        padding: "32px 40px",
        display: "flex",
        flexDirection: "column",
        gap: 32,
        minWidth: 380,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <NetworkMark size={38} />
        <div style={{ display: "flex", flexDirection: "column", lineHeight: 1 }}>
          <span
            style={{
              fontFamily: "'Lora', Georgia, serif",
              fontSize: 11,
              fontWeight: 400,
              fontStyle: "italic",
              letterSpacing: "0.08em",
              color: subColor,
              textTransform: "lowercase",
              marginBottom: 3,
            }}
          >
            Beneath the
          </span>
          <span
            style={{
              fontFamily: "'Lora', Georgia, serif",
              fontSize: 19,
              fontWeight: 700,
              color: textColor,
              letterSpacing: "-0.01em",
            }}
          >
            Org Chart
          </span>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <NetworkMark size={24} />
        <span
          style={{
            fontFamily: "'Lora', Georgia, serif",
            fontSize: 13,
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
          fontFamily: "Inter, system-ui, sans-serif",
        }}
      >
        <p style={{ fontSize: 11, color: "#a8a29e", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>Network Mark</p>
        <Lockup bg="#ffffff" textColor={ink} subColor={inkFaint} />
        <Lockup bg="#1c1917" textColor="#faf8f5" subColor="#a8a29e" />
      </div>
    </>
  );
}
