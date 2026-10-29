"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Settings, LogOut, Plus } from "lucide-react";
import type { Organisation, User } from "../../../packages/contracts";
import { api, ApiError, message, send } from "@/lib/api";
import { Auth } from "./auth";
import Onboarding from "./onboarding";
import SourceSetup from "./source-setup";
import { SettingsPage } from "./settings";
import ReviewWorkspace from "./review-workspace";
import ContentLibrary from "./content-library";
import Tutorial from "./tutorial";
import InsightsPage from "./insights";
import { Badge, Brand, Empty, Loading, Notice } from "./ui";
const nav = [
  ["brand", "Rules"],
  ["reviews/new", "New review"],
  ["content", "Tracking"],
] as const;
export default function Workspace() {
  const pathname = usePathname(),
    router = useRouter();
  const [user, setUser] = useState<User | null>(null),
    [orgs, setOrgs] = useState<Organisation[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const parts = pathname.split("/").filter(Boolean),
    orgId = parts[0] === "org" ? parts[1] : undefined,
    section = parts[2] || "brand",
    org = orgs.find((o) => o.id === orgId);
  const refresh = useCallback(async () => {
    const current = await api<User>("/auth/me"),
      organisations = await api<Organisation[]>("/organisations");
    setUser(current);
    setOrgs(organisations);
    return organisations;
  }, []);
  useEffect(() => {
    let active = true;
    void refresh()
      .catch((e) => {
        if (active) {
          if (e instanceof ApiError && e.status === 401) setUser(null);
          else setError(message(e));
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [refresh]);
  useEffect(() => {
    if (loading || error) return;
    if (!user && pathname !== "/login") router.replace("/login");
    else if (user && (pathname === "/" || pathname === "/login"))
      router.replace(orgs.length ? `/org/${orgs[0].id}/brand` : "/onboarding");
    else if (
      user &&
      orgId &&
      ["dashboard", "overview", "activity", "approvals"].includes(section)
    )
      router.replace(
        `/org/${orgId}/content${section === "approvals" ? "?queue=assigned" : ""}`,
      );
  }, [loading, error, user, pathname, orgs, orgId, section, router]);
  async function login() {
    const organisations = await refresh();
    router.push(
      organisations.length
        ? `/org/${organisations[0].id}/brand`
        : "/onboarding",
    );
  }
  async function joined(id: string) {
    await refresh();
    router.push(`/org/${id}/brand`);
  }
  async function logout() {
    try {
      await api("/auth/logout", send("POST"));
      setUser(null);
      setOrgs([]);
      router.push("/login");
    } catch (e) {
      setError(message(e));
    }
  }
  if (loading) return <Loading />;
  if (error)
    return (
      <main className="fatal">
        <Notice kind="error">{error}</Notice>
        <button className="button secondary" onClick={() => location.reload()}>
          Try again
        </button>
      </main>
    );
  if (!user) return <Auth onLogin={login} />;
  if (!orgId)
    return (
      <Onboarding organisations={orgs} onJoined={joined} onLogout={logout} />
    );
  if (!org)
    return (
      <main className="fatal">
        <Empty
          title="Organisation unavailable"
          action={
            <Link className="button primary" href="/onboarding">
              Choose an organisation
            </Link>
          }
        >
          Choose an organisation you belong to.
        </Empty>
      </main>
    );
  const base = `/org/${org.id}`;
  return (
    <div className="simple-workspace">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="simple-header">
        <Link href={`${base}/brand`} className="brand-home">
          <Brand />
        </Link>
        <div className="workspace-tools">
          <label className="workspace-org">
            <span className="sr-only">Organisation</span>
            <select
              value={org.id}
              onChange={(e) => router.push(`/org/${e.target.value}/brand`)}
            >
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </label>
          <Badge variant="role">{org.role}</Badge>
          <Tutorial onExample={refresh} />
          <details className="settings-menu">
            <summary>
              <Settings size={17} />
              <span>Settings</span>
            </summary>
            <div>
              <Link href={`${base}/settings`}>Team, account & privacy</Link>
              <Link href="/onboarding">
                <Plus size={15} />
                Add or join organisation
              </Link>
              <button onClick={logout}>
                <LogOut size={15} />
                Sign out {user.name}
              </button>
            </div>
          </details>
        </div>
      </header>
      <nav className="primary-tabs" aria-label="Main navigation">
        {nav.map(([route, title]) => {
          const active =
            route === "reviews/new"
              ? section === "reviews"
              : section === route ||
                (route === "content" && section === "insights");
          return (
            <Link
              href={`${base}/${route}`}
              key={route}
              aria-current={active ? "page" : undefined}
            >
              {title}
            </Link>
          );
        })}
      </nav>
      <main id="main" className="main simple-main" key={`${org.id}/${section}`}>
        {section === "brand" ? (
          <SourceSetup org={org} />
        ) : section === "settings" ? (
          <SettingsPage org={org} onUpdated={refresh} />
        ) : section === "insights" ? (
          <InsightsPage orgId={org.id} />
        ) : section === "reviews" ? (
          <ReviewWorkspace
            key={parts[3] || "new"}
            org={org}
            user={user}
            id={parts[3] || "new"}
          />
        ) : (
          <ContentLibrary org={org} userId={user.id} />
        )}
      </main>
      <footer className="simple-footer">
        <span>Private organisation workspace</span>
        <span>AI findings are advisory. Human approval required.</span>
      </footer>
    </div>
  );
}
