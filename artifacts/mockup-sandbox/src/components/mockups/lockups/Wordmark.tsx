export function Wordmark() {
  const amber = "#c2750a";
  const parchment = "#faf8f5";
  const ink = "#1c1917";
  const inkFaint = "#57534e";

  const Lockup = ({
    bg,
    textColor,
    subColor,
    ruleColor,
  }: {
    bg: string;
    textColor: string;
    subColor: string;
    ruleColor: string;
  }) => (
    <div
      style={{
        background: bg,
        borderRadius: 12,
        padding: "28px 36px",
        display: "flex",
        flexDirection: "column",
        gap: 28,
        minWidth: 360,
      }}
    >
      <div>
        <div
          style={{
            fontFamily: "'Lora', Georgia, serif",
            fontStyle: "italic",
            fontWeight: 400,
            fontSize: 11,
            letterSpacing: "0.1em",
            color: subColor,
            marginBottom: 1,
          }}
        >
          Beneath the
        </div>
        <div
          style={{
            fontFamily: "'Lora', Georgia, serif",
            fontWeight: 700,
            fontSize: 26,
            color: textColor,
            letterSpacing: "-0.025em",
            lineHeight: 1.1,
          }}
        >
          Org Chart
        </div>
        <div
          style={{
            marginTop: 10,
            height: 2,
            width: 28,
            background: ruleColor,
            borderRadius: 1,
          }}
        />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
          <span
            style={{
              fontFamily: "'Lora', Georgia, serif",
              fontStyle: "italic",
              fontWeight: 400,
              fontSize: 13,
              color: subColor,
            }}
          >
            Beneath the
          </span>
          <span
            style={{
              fontFamily: "'Lora', Georgia, serif",
              fontWeight: 700,
              fontSize: 13,
              color: textColor,
              letterSpacing: "-0.01em",
            }}
          >
            Org Chart
          </span>
        </div>
        <div style={{ height: 1, width: 14, background: ruleColor, borderRadius: 1 }} />
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
        <p style={{ fontSize: 11, color: "#a8a29e", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>Pure Wordmark</p>
        <Lockup bg="#ffffff" textColor={ink} subColor={inkFaint} ruleColor={amber} />
        <Lockup bg="#1c1917" textColor="#faf8f5" subColor="#a8a29e" ruleColor={amber} />
      </div>
    </>
  );
}
