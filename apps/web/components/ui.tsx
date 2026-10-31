import { LoaderCircle, Layers3, Check, AlertCircle } from "lucide-react";
import type { ReactNode } from "react";
import Image from "next/image";

export function Mark({ small = false }: { small?: boolean }) {
  return (
    <span className={`brand-mark ${small ? "small" : ""}`} aria-hidden="true">
      <span />
      <span />
      <span />
    </span>
  );
}
export function Brand() {
  return (
    <div className="brand">
      <span>Brand Content Review</span>
    </div>
  );
}
export function Loading({
  text = "Loading your workspace…",
}: {
  text?: string;
}) {
  return (
    <div className="loading" role="status">
      <LoaderCircle className="spin" size={22} />
      {text}
    </div>
  );
}
export function Notice({
  children,
  kind = "info",
}: {
  children: ReactNode;
  kind?: "error" | "success" | "info";
}) {
  return (
    <div
      className={`notice ${kind}`}
      role={kind === "error" ? "alert" : "status"}
    >
      {kind === "error" ? (
        <AlertCircle size={18} />
      ) : kind === "success" ? (
        <Check size={18} />
      ) : (
        <Layers3 size={18} />
      )}
      <span>{children}</span>
    </div>
  );
}
export function Badge({
  children,
  variant = "neutral",
}: {
  children: ReactNode;
  variant?: string;
}) {
  return <span className={`badge ${variant}`}>{children}</span>;
}
export function Empty({
  icon = <Layers3 size={28} />,
  title,
  children,
  action,
}: {
  icon?: ReactNode;
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <div className="empty-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{children}</p>
      {action}
    </div>
  );
}
export function PageHeading({
  title,
  children,
  action,
}: {
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div className="heading-art" aria-hidden="true">
        <Image
          src={
            title === "Tracking"
              ? "/art/section-ribbon.webp"
              : "/art/section-halo.webp"
          }
          alt=""
          fill
          sizes="(max-width: 650px) 100vw, 720px"
        />
      </div>
      <div>
        <h1>{title}</h1>
        <p>{children}</p>
      </div>
      {action}
    </div>
  );
}
