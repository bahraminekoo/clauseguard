
import React, { useRef, useState } from "react";

type Props = {
  apiBaseUrl: string;
  onUploaded: (docId: string) => void;
};

export default function UploadDropzone({ apiBaseUrl, onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    const file = files[0];
    setUploading(true);
    setMessage(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${apiBaseUrl}/upload`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || `Upload failed (${res.status})`);
      }
      const data = (await res.json()) as { doc_id: string };
      onUploaded(data.doc_id);
      setMessage(`Uploaded. doc_id: ${data.doc_id}`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-3">
      <div
        className="rounded-lg border border-dashed border-slate-700 bg-slate-900/20 p-6 text-sm text-slate-300"
        onDragOver={(e: React.DragEvent<HTMLDivElement>) => {
          e.preventDefault();
          e.stopPropagation();
        }}
        onDrop={(e: React.DragEvent<HTMLDivElement>) => {
          e.preventDefault();
          e.stopPropagation();
          handleFiles(e.dataTransfer?.files ?? null);
        }}
      >
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="font-medium text-slate-100">Upload PDF</div>
            <div className="text-xs text-slate-400">
              Drag & drop or select a PDF. A doc_id will be returned for retrieval.
            </div>
          </div>
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
            className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {uploading ? "Uploading..." : "Choose file"}
          </button>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            handleFiles(e.target.files)
          }
        />
      </div>
      {message ? <div className="text-xs text-slate-300">{message}</div> : null}
    </div>
  );
}
