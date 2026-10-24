"use client";
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import type { SuperDoc } from "superdoc";
import "superdoc/style.css";
import runtime from "@/lib/editor-runtime.json";
import { Notice } from "./ui";

export interface DocumentEditorHandle {
  snapshot(): Promise<Blob>;
  reveal(quote: string): Promise<void>;
  apply(quote: string, replacement: string): Promise<void>;
}

export default forwardRef<
  DocumentEditorHandle,
  {
    url: string;
    name: string;
    email: string;
    readOnly: boolean;
    onDirty: () => void;
    onReady: (url: string) => void;
  }
>(function DocumentEditor(
  { url, name, email, readOnly, onDirty, onReady },
  ref,
) {
  const host = useRef<HTMLDivElement>(null),
    toolbar = useRef<HTMLDivElement>(null),
    instance = useRef<SuperDoc | null>(null);
  const callbacks = useRef({ onDirty, onReady });
  callbacks.current = { onDirty, onReady };
  const [error, setError] = useState("");
  useImperativeHandle(
    ref,
    () => ({
      async snapshot() {
        if (!instance.current)
          throw new Error("The document is still opening.");
        return instance.current.export({ triggerDownload: false });
      },
      async reveal(quote) {
        const sd = instance.current;
        if (!sd) return;
        sd.ui.search.find(quote, { caseSensitive: true });
      },
      async apply(quote, replacement) {
        const sd = instance.current;
        if (!sd) throw new Error("Editor is unavailable.");
        const search = sd.ui.search;
        search.find(quote, { caseSensitive: true });
        const settled = await new Promise<
          ReturnType<typeof search.getSnapshot>
        >((resolve, reject) => {
          const deadline = Date.now() + 6000;
          const poll = () => {
            const state = search.getSnapshot();
            if (state.query === quote && state.total > 0) resolve(state);
            else if (Date.now() > deadline)
              reject(
                new Error(
                  "The exact text could not be located. Edit it manually and recheck.",
                ),
              );
            else setTimeout(poll, 80);
          };
          poll();
        });
        if (settled.total !== 1)
          throw new Error(
            "This phrase occurs more than once. Edit the intended occurrence manually and recheck.",
          );
        const result = await search.replace(replacement);
        if (!result.ok)
          throw new Error(
            "The editor could not apply this change. Edit it manually and recheck.",
          );
        callbacks.current.onDirty();
      },
    }),
    [],
  );
  useEffect(() => {
    let disposed = false;
    let sd: SuperDoc | null = null;
    let ready = false;
    const controller = new AbortController();
    (async () => {
      const [{ SuperDoc }, response] = await Promise.all([
        import("superdoc"),
        fetch(url, { credentials: "same-origin", signal: controller.signal }),
      ]);
      if (!response.ok)
        throw new Error("The saved document could not be opened.");
      const file = new File([await response.blob()], "document.docx", {
        type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      });
      if (disposed || !host.current || !toolbar.current) return;
      sd = new SuperDoc({
        selector: host.current,
        document: file,
        documentMode: readOnly ? "viewing" : "editing",
        user: { name, email },
        telemetry: { enabled: false },
        proofing: { enabled: false },
        hyperlinks: false,
        workerUrls: { document: runtime.documentWorker },
        workerStartupTimeoutMs: 60000,
        ui: {
          toolbar: { container: toolbar.current },
          search: true,
          comments: false,
        },
        zoom: { mode: "fit-width" },
        onReady: () => {
          if (disposed) return;
          ready = true;
          instance.current = sd;
          callbacks.current.onReady(url);
        },
        onEditorUpdate: () => {
          if (ready && !disposed && !readOnly) callbacks.current.onDirty();
        },
        onContentError: () => {
          if (!disposed)
            setError(
              "This document contains content the editor could not read. The original remains available.",
            );
        },
        onException: () => {
          if (!disposed)
            setError(
              "The document editor encountered an error. Keep a local copy of any unsaved edits.",
            );
        },
      });
      instance.current = sd;
    })().catch((e) => {
      if (!disposed)
        setError(e instanceof Error ? e.message : "Document could not open.");
    });
    return () => {
      disposed = true;
      controller.abort();
      instance.current = null;
      sd?.destroy();
    };
  }, [url, name, email, readOnly]);
  return (
    <div className="word-editor">
      {error && <Notice kind="error">{error}</Notice>}
      <div ref={toolbar} className="word-toolbar" />
      <div
        ref={host}
        className="word-canvas"
        aria-label="Word document editor"
      />
    </div>
  );
});
