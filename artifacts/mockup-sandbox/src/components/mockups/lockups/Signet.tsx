export function Signet() {
  const amber = "#c2750a";
  const amberLight = "#fef3c7";
  const parchment = "#faf8f5";
  const ink = "#1c1917";
  const inkFaint = "#57534e";

  const SignetMark = ({ size = 40, invert = false }: { size?: number; invert?: boolean }) => (
    <div
      style={{
        width: size,
        height: size,
        background: invert ? "#faf8f5" : amber,
        borderRadius: Math.round(size * 0.22),
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <svg width={size * 0.55} height={size * 0.6} viewBox="0 0 22 24" fill="none" aria-hidden>
        <text
          x="11"
          y="19"
          textAnchor="middle"
          fontFamily="'Lora', Georgia, serif"
          fontSize="20"
          fontStyle="italic"
          fontWeight="700"
          fill={invert ? amber : "#faf8f5"}
        >
          B
        </text>
      </svg>
    </div>
  );

  const Lockup = ({
    bg,
    textColor,
    subColor,
    invert = false,
  }: {
    bg: string;
    textColor: string;
    subColor: string;
    invert?: boolean;
  }) => (
    <div
      style={{
        background: bg,
        borderRadius: 12,
        padding: "28px 36px",
        display: "flex",
        flexDirection: "column",
        gap: 24,
        minWidth: 340,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <SignetMark size={44} invert={invert} />
        <div style={{ display: "flex", flexDirection: "column", lineHeight: 1 }}>
          <span
            style={{
              fontFamily: "'Lora', Georgia, serif",
              fontStyle: "italic",
              fontWeight: 400,
              fontSize: 10,
              letterSpacing: "0.08em",
              color: subColor,
              marginBottom: 4,
            }}
          >
            Beneath the
          </span>
          <span
            style={{
              fontFamily: "'Lora', Georgia, serif",
              fontWeight: 700,
              fontSize: 19,
              color: textColor,
              letterSpacing: "-0.015em",
            }}
          >
            Org Chart
          </span>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <SignetMark size={22} invert={invert} />
        <span
          style={{
            fontFamily: "'Lora', Georgia, serif",
            fontStyle: "italic",
            fontSize: 12,
            color: textColor,
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
        <p style={{ fontSize: 11, color: "#a8a29e", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>Signet Mark</p>
        <Lockup bg="#ffffff" textColor={ink} subColor={inkFaint} invert={false} />
        <Lockup bg="#1c1917" textColor="#faf8f5" subColor="#a8a29e" invert={true} />
      </div>
    </>
  );
}
