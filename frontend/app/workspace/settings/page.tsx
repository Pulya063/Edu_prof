import type { Metadata } from "next";
import { Icon, Topography, WorkspacePageHeader } from "../WorkspaceUI";

export const metadata: Metadata = { title: "Workspace settings" };

export default function SettingsPage() {
  return (
    <main className="sketch-page">
      <WorkspacePageHeader section="Settings" title="Workspace settings" highlight="Workspace" description="Personalize your experience and manage your data, privacy and security." />
      <form className="settings-grid" noValidate>
        <div className="settings-column">
          <section className="sketch-card settings-panel"><h2>General preferences</h2><p>Customize how Fence looks and works for you.</p>
            <label className="settings-row"><span><strong>Language</strong><span>Choose the language for the interface.</span></span><select defaultValue="English"><option>English</option><option>Українська</option></select></label>
            <label className="settings-row"><span><strong>Currency</strong><span>Set your preferred currency for costs and calculations.</span></span><select defaultValue="USD"><option value="USD">USD (US Dollar)</option><option value="EUR">EUR (Euro)</option><option value="PLN">PLN (Polish Złoty)</option></select></label>
            <label className="settings-row"><span><strong>Theme</strong><span>Choose your visual theme.</span></span><select defaultValue="Fence default"><option>Fence default</option></select></label>
          </section>
          <section className="sketch-card settings-panel"><h2>Security</h2><p>Keep your account safe and in your control.</p>
            <div className="settings-row"><span><strong>Email address</strong><span>Update your account email and verify the new address.</span></span><button type="button">Change email</button></div>
            <div className="settings-row"><span><strong>Password</strong><span>Update your password regularly to keep your account secure.</span></span><button type="button">Change password</button></div>
            <div className="settings-row"><span><strong>Active sessions</strong><span>Manage where you&apos;re signed in.</span></span><button type="button">Manage sessions</button></div>
          </section>
        </div>
        <div className="settings-column">
          <section className="sketch-card sketch-card-dark settings-panel data-sources"><Topography/><h2>Connected data sources</h2><p>Link your data sources to get more relevant insights.</p>
            <div className="source-row"><span className="source-logo">▶</span><div><strong>YouTube</strong><span>Use YouTube content to support your learning and career exploration.</span></div><span className="sketch-chip">Not connected</span><Icon name="arrow" size={17}/></div>
            <div className="source-row"><span className="source-logo">GH</span><div><strong>GitHub</strong><span>Connect your GitHub profile to add your projects.</span></div><button type="button">Connect GitHub</button><Icon name="arrow" size={17}/></div>
            <div className="source-row"><span className="source-logo">in</span><div><strong>LinkedIn</strong><span>Connect your LinkedIn profile to add career information.</span></div><button type="button">Connect LinkedIn</button><Icon name="arrow" size={17}/></div>
            <button type="button" className="manage-sources"><Icon name="settings"/><span>Manage source preferences</span><Icon name="arrow" size={17}/></button>
          </section>
          <aside className="sketch-card sketch-card-violet settings-note"><Icon name="info" size={28}/><div><strong>Your data stays in your control</strong>You decide which sources to connect. Fence only uses connected content to improve your experience.</div></aside>
          <button type="button" className="settings-save">Save changes</button><p className="settings-save-note">Your settings will be saved to your account.</p>
        </div>
      </form>
    </main>
  );
}
