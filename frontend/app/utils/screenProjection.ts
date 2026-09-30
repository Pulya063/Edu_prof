export type ScreenPoint = { x: number; y: number };

type ScreenCorners = readonly [ScreenPoint, ScreenPoint, ScreenPoint, ScreenPoint];

export function createScreenProjection(corners: ScreenCorners, width: number, height: number) {
  const [topLeft, topRight, bottomRight, bottomLeft] = corners;
  const dx1 = topRight.x - bottomRight.x;
  const dx2 = bottomLeft.x - bottomRight.x;
  const dx3 = topLeft.x - topRight.x + bottomRight.x - bottomLeft.x;
  const dy1 = topRight.y - bottomRight.y;
  const dy2 = bottomLeft.y - bottomRight.y;
  const dy3 = topLeft.y - topRight.y + bottomRight.y - bottomLeft.y;
  const denominator = dx1 * dy2 - dx2 * dy1;

  if (Math.abs(denominator) < .001) return "none";

  const perspectiveX = (dx3 * dy2 - dx2 * dy3) / denominator;
  const perspectiveY = (dx1 * dy3 - dx3 * dy1) / denominator;
  const scaleX = topRight.x - topLeft.x + perspectiveX * topRight.x;
  const skewX = bottomLeft.x - topLeft.x + perspectiveY * bottomLeft.x;
  const skewY = topRight.y - topLeft.y + perspectiveX * topRight.y;
  const scaleY = bottomLeft.y - topLeft.y + perspectiveY * bottomLeft.y;

  return `matrix3d(${[
    scaleX / width, skewY / width, 0, perspectiveX / width,
    skewX / height, scaleY / height, 0, perspectiveY / height,
    0, 0, 1, 0,
    topLeft.x, topLeft.y, 0, 1,
  ].join(",")})`;
}
