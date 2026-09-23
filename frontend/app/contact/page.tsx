const supportEmail = process.env.NEXT_PUBLIC_FENCE_SUPPORT_EMAIL;

export default function ContactPage() {
  return <main className="legal-page"><a href="/">← Back to Fence</a><p className="legal-kicker">Fence / contact</p><h1>Contact Fence</h1>{supportEmail ? <p>Write to <a href={`mailto:${supportEmail}`}>{supportEmail}</a>.</p> : <p>Contact email is awaiting <code>NEXT_PUBLIC_FENCE_SUPPORT_EMAIL</code> configuration.</p>}</main>;
}
