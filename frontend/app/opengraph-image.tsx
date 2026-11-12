import { ImageResponse } from "next/og";

export const alt = "Fence — know when your degree pays you back";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const runtime = "edge";

/** Social preview in the site palette: ink outlines, lime and violet blocks. */
export default function OpengraphImage() {
  const card = (label: string, value: string, background: string, color = "#171819") => (
    <div style={{ display: "flex", flexDirection: "column", padding: "22px 26px", border: "4px solid #171819", borderRadius: 28, background, color, boxShadow: "0 8px 0 #171819" }}>
      <div style={{ fontSize: 20, fontWeight: 700, letterSpacing: 2, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 52, fontWeight: 800, letterSpacing: -2 }}>{value}</div>
    </div>
  );
  return new ImageResponse(
    (
      <div style={{ display: "flex", width: "100%", height: "100%", padding: 64, background: "#f7f7f3", color: "#171819", fontFamily: "sans-serif" }}>
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", width: 640 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 56, height: 56, borderRadius: 12, background: "#b7ff2a", fontSize: 30, fontWeight: 800 }}>F</div>
            <div style={{ fontSize: 34, fontWeight: 800, letterSpacing: -1 }}>Fence</div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", fontSize: 84, fontWeight: 800, lineHeight: 0.95, letterSpacing: -4 }}>
            <div>Know when your</div>
            <div style={{ display: "flex" }}><span style={{ background: "#d7c7ff", padding: "0 12px" }}>degree</span></div>
            <div>pays you back.</div>
          </div>
          <div style={{ fontSize: 26, color: "#3c3f44" }}>Education ROI calculator · Poland &amp; Ukraine · example figures</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", gap: 26, marginLeft: 40, width: 400 }}>
          {card("PAYBACK", "51 months", "#b7ff2a")}
          {card("10-YEAR ROI", "+157%", "#d7c7ff")}
          {card("INVESTMENT", "201 852 PLN", "#171819", "#f7f7f3")}
        </div>
      </div>
    ),
    size,
  );
}
