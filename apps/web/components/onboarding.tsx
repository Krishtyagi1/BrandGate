"use client";
import { useState, type FormEvent } from "react";
import { Building2, Plus, Ticket, LogOut } from "lucide-react";
import type { Organisation } from "../../../packages/contracts";
import { api, message, send } from "@/lib/api";
import { Brand, Notice } from "./ui";

export default function Onboarding({
  organisations,
  onJoined,
  onLogout,
}: {
  organisations: Organisation[];
  onJoined: (id: string) => Promise<void>;
  onLogout: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>, join: boolean) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const data = new FormData(event.currentTarget);
    try {
      if (join) {
        const r = await api<{ org_id: string }>(
          "/invitations/accept",
          send("POST", { token: data.get("token") }),
        );
        await onJoined(r.org_id);
      } else {
        const r = await api<Organisation>(
          "/organisations",
          send("POST", { name: data.get("name") }),
        );
        await onJoined(r.id);
      }
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="onboarding">
      <header>
        <Brand />
        <button className="button ghost" onClick={onLogout}>
          <LogOut size={16} />
          Sign out
        </button>
      </header>
      <main>
        <div className="onboarding-intro">
          <span className="empty-icon">
            <Building2 size={28} />
          </span>
          <h1>Give your brand a home.</h1>
          <p>
            Create an organisation to keep your approved knowledge and team
            together.
          </p>
        </div>
        {error && <Notice kind="error">{error}</Notice>}
        {organisations.length > 0 && (
          <section className="panel existing-orgs">
            <h2>Your organisations</h2>
            {organisations.map((org) => (
              <button
                className="org-choice"
                key={org.id}
                onClick={() => onJoined(org.id)}
              >
                {org.name}
                <span>{org.role}</span>
              </button>
            ))}
          </section>
        )}
        <div className="onboarding-grid">
          <section className="panel">
            <Plus size={23} />
            <h2>Create an organisation</h2>
            <p className="muted">
              You’ll be its owner. Invite your team when you’re ready.
            </p>
            <form onSubmit={(e) => submit(e, false)}>
              <label>
                Organisation name
                <input
                  name="name"
                  required
                  maxLength={100}
                  placeholder="e.g. TechNova"
                />
              </label>
              <button className="button primary" disabled={busy}>
                Create organisation
              </button>
            </form>
          </section>
          <section className="panel">
            <Ticket size={23} />
            <h2>Join your team</h2>
            <p className="muted">
              Use an invitation code from your owner. Your account email must
              match the invitation.
            </p>
            <form onSubmit={(e) => submit(e, true)}>
              <label>
                Invitation code
                <input name="token" required minLength={20} />
              </label>
              <button className="button secondary" disabled={busy}>
                Accept invitation
              </button>
            </form>
          </section>
        </div>
        <p className="privacy-note">
          Your organisation’s knowledge is private to its members.
        </p>
      </main>
    </div>
  );
}
