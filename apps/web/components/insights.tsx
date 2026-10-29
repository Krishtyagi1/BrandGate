"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, date, message } from "@/lib/api";
import { Loading, Notice, PageHeading } from "./ui";
interface Count {
  finding_type: string;
  key: string;
  label: string;
  status: string;
  drafts: number;
}
interface Insights {
  reviewed_drafts: number;
  drafts_with_findings: number;
  incomplete_drafts: number;
  period_start: string;
  period_end: string;
  denominator: string;
  question_limit_reached: boolean;
  finding_types: Count[];
  by_channel: Count[];
  by_creator: Count[];
  by_campaign: Count[];
  guideline_gaps: {
    kind: string;
    question: string;
    drafts: number;
    draft_ids: string[];
  }[];
}
export default function InsightsPage({ orgId }: { orgId: string }) {
  const [days, setDays] = useState(30),
    [data, setData] = useState<Insights | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setData(null);
    setError("");
    api<Insights>(`/organisations/${orgId}/insights?days=${days}`)
      .then((value) => {
        if (active) setData(value);
      })
      .catch((e) => {
        if (active) setError(message(e));
      });
    return () => {
      active = false;
    };
  }, [orgId, days]);
  return (
    <>
      <Link className="back-link" href={`/org/${orgId}/content`}>
        Back to Tracking
      </Link>
      <PageHeading title="Recurring issues & guideline gaps">
        Observed review findings to help owners clarify guidance. These are not
        creator performance scores.
      </PageHeading>
      <label className="insights-period">
        Reporting period
        <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </label>
      {error && <Notice kind="error">{error}</Notice>}
      {!data && !error && <Loading />}
      {data && (
        <>
          <section className="panel insights-summary">
            <h2>{data.reviewed_drafts} distinct reviewed drafts</h2>
            <p>
              {data.drafts_with_findings} with findings ·{" "}
              {data.incomplete_drafts} latest checks in this period unfinished
              or incomplete
            </p>
            <p>
              {date(data.period_start)} to {date(data.period_end)}
            </p>
            <small>{data.denominator}</small>
          </section>
          <div className="insights-grid">
            {(
              [
                ["Finding types", data.finding_types],
                ["By channel", data.by_channel],
                ["By creator", data.by_creator],
                ["By campaign", data.by_campaign],
              ] as const
            ).map(([heading, rows]) => (
              <section className="panel" key={heading}>
                <h2>{heading}</h2>
                {rows.length ? (
                  <div
                    className="insights-table"
                    tabIndex={0}
                    role="region"
                    aria-label={`${heading} table`}
                  >
                    <table>
                      <thead>
                        <tr>
                          <th scope="col">{heading}</th>
                          <th scope="col">Type</th>
                          <th scope="col">Finding status</th>
                          <th scope="col">Drafts</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((row) => (
                          <tr
                            key={`${row.key}/${row.finding_type}/${row.status}`}
                          >
                            <td>{row.label.replaceAll("_", " ")}</td>
                            <td>{row.finding_type.replaceAll("_", " ")}</td>
                            <td>{row.status.replaceAll("_", " ")}</td>
                            <td>{row.drafts}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p>No observations in this period.</p>
                )}
              </section>
            ))}
          </div>
          <section className="panel guideline-gaps">
            <h2>Questions the guidelines could not answer</h2>
            <p>
              Unverified claims and assistant abstentions are signals for owner
              review. An unsupported question can also cause abstention; it does
              not prove a rule is missing.
            </p>
            {data.question_limit_reached && (
              <Notice>
                Only the latest 5,000 unanswered questions are included.
              </Notice>
            )}
            {!data.guideline_gaps.length ? (
              <p>No recorded gaps in this period.</p>
            ) : (
              <ol>
                {data.guideline_gaps.map((gap, i) => (
                  <li key={i}>
                    <strong>{gap.question}</strong>
                    <p>
                      {gap.kind.replaceAll("_", " ")} · {gap.drafts} distinct
                      drafts
                    </p>
                    <div className="form-actions">
                      {gap.draft_ids.map((id, j) => (
                        <Link key={id} href={`/org/${orgId}/reviews/${id}`}>
                          Open review {j + 1}
                        </Link>
                      ))}
                    </div>
                  </li>
                ))}
              </ol>
            )}
            <Link className="button secondary" href={`/org/${orgId}/brand`}>
              Review approved rules
            </Link>
          </section>
        </>
      )}
    </>
  );
}
