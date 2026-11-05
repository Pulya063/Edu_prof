import type { Metadata } from "next";
import SitePage from "../components/SitePage";
import { ContactTopics, SiteHeroArt } from "../components/SiteInteractive";

export const metadata: Metadata = {
  title: "Contact",
  description: "Contact Fence about your account, billing, salary or tuition data corrections, or using Fence with your school.",
  alternates: { canonical: "/contact" },
};

const supportEmail = process.env.NEXT_PUBLIC_FENCE_SUPPORT_EMAIL;


export default function ContactPage() {
  return (
    <SitePage
      kicker="Fence / contact"
      title={<>Talk to <span className="site-mark">Fence.</span></>}
      lead="Questions about your account, billing or the numbers behind a calculation. Pick a topic, tell us what you were trying to do, and a person will get back to you."
      art={<SiteHeroArt items={[["Account", "sign-in & scenarios"], ["Billing", "handled by Stripe"], ["Data", "corrections welcome"]]} />}
    >
      <section className="site-section" aria-labelledby="email-title">
        <h2 id="email-title" className="site-section-title">Email</h2>
        {supportEmail ? (
          <a className="site-email" href={`mailto:${supportEmail}`}>{supportEmail}</a>
        ) : (
          <p className="site-notice" role="status">The support email is not configured yet. Set <code>NEXT_PUBLIC_FENCE_SUPPORT_EMAIL</code> to show it here.</p>
        )}
      </section>

      <section className="site-section site-section--dark" aria-labelledby="topics-title">
        <h2 id="topics-title" className="site-section-title">What is it about?</h2>
        <ContactTopics email={supportEmail} />
      </section>
    </SitePage>
  );
}
