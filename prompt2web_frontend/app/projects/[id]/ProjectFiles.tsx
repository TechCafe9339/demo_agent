"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  apiGet,
} from "../../../lib/api";


type FileNode = {
  name: string;
  path: string;
  type:
    | "file"
    | "directory";
  children?: FileNode[];
};


type FilesResponse = {
  exists: boolean;
  files: FileNode[];
};


type FileResponse = {
  name: string;
  path: string;
  content: string;
};


type Props = {
  projectId: string;
};


function FileTreeItem({
  item,
  onSelect,
  selectedPath,
}: {
  item: FileNode;
  onSelect:
    (path: string) => void;
  selectedPath:
    string | null;
}) {
  const [
    expanded,
    setExpanded,
  ] =
    useState(
      item.path ===
        "frontend" ||
        item.path ===
        "backend"
    );

  if (
    item.type ===
    "directory"
  ) {
    return (
      <div>
        <button
          type="button"
          onClick={() =>
            setExpanded(
              !expanded
            )
          }
          className="
            flex
            w-full
            items-center
            gap-2
            rounded
            px-2
            py-1.5
            text-left
            text-sm
            text-slate-300
            hover:bg-slate-800
          "
        >
          <span>
            {expanded
              ? "▾"
              : "▸"}
          </span>

          <span>
            📁
          </span>

          <span>
            {item.name}
          </span>
        </button>

        {expanded && (
          <div className="ml-4 border-l border-slate-800 pl-2">

            {item.children?.map(
              (child) => (
                <FileTreeItem
                  key={
                    child.path
                  }
                  item={
                    child
                  }
                  onSelect={
                    onSelect
                  }
                  selectedPath={
                    selectedPath
                  }
                />
              )
            )}

          </div>
        )}
      </div>
    );
  }

  const selected =
    selectedPath ===
    item.path;

  return (
    <button
      type="button"
      onClick={() =>
        onSelect(
          item.path
        )
      }
      className={`
        flex
        w-full
        items-center
        gap-2
        rounded
        px-2
        py-1.5
        text-left
        text-sm
        ${
          selected
            ? "bg-blue-600/20 text-blue-300"
            : "text-slate-400 hover:bg-slate-800"
        }
      `}
    >
      <span>
        📄
      </span>

      <span className="truncate">
        {item.name}
      </span>
    </button>
  );
}


export default function ProjectFiles({
  projectId,
}: Props) {
  const [
    files,
    setFiles,
  ] =
    useState<FileNode[]>(
      []
    );

  const [
    selectedFile,
    setSelectedFile,
  ] =
    useState<
      FileResponse | null
    >(null);

  const [
    selectedPath,
    setSelectedPath,
  ] =
    useState<
      string | null
    >(null);

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    fileLoading,
    setFileLoading,
  ] =
    useState(false);

  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  useEffect(() => {
    async function loadFiles() {
      try {
        setError(null);

        const result =
          await apiGet<
            FilesResponse
          >(
            `/projects/${projectId}/files/`
          );

        setFiles(
          result.files
        );

      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Failed to load project files."
        );

      } finally {
        setLoading(false);
      }
    }

    loadFiles();

  }, [projectId]);


  async function openFile(
    path: string
  ) {
    try {
      setFileLoading(true);
      setError(null);
      setSelectedPath(
        path
      );

      const result =
        await apiGet<
          FileResponse
        >(
          `/projects/${projectId}/file/?path=${encodeURIComponent(
            path
          )}`
        );

      setSelectedFile(
        result
      );

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to open file."
      );

    } finally {
      setFileLoading(
        false
      );
    }
  }


  if (loading) {
    return (
      <div className="p-8 text-slate-400">
        Loading project files...
      </div>
    );
  }


  return (
    <div className="p-6">

      {error && (
        <div className="mb-4 rounded-lg border border-red-900 bg-red-950/40 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="grid min-h-[650px] grid-cols-[280px_1fr] overflow-hidden rounded-xl border border-slate-800 bg-slate-900">

        {/* Explorer */}

        <aside className="border-r border-slate-800">

          <div className="border-b border-slate-800 px-4 py-3">

            <h2 className="text-sm font-semibold">
              EXPLORER
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              Project #{projectId}
            </p>

          </div>

          <div className="max-h-[600px] overflow-y-auto p-2">

            {files.length ===
            0 ? (
              <p className="p-3 text-sm text-slate-500">
                No generated files yet.
              </p>
            ) : (
              files.map(
                (item) => (
                  <FileTreeItem
                    key={
                      item.path
                    }
                    item={
                      item
                    }
                    onSelect={
                      openFile
                    }
                    selectedPath={
                      selectedPath
                    }
                  />
                )
              )
            )}

          </div>

        </aside>


        {/* Editor */}

        <section className="min-w-0">

          {!selectedFile &&
          !fileLoading ? (
            <div className="flex h-full items-center justify-center text-slate-500">

              <div className="text-center">
                <div className="text-4xl">
                  &lt;/&gt;
                </div>

                <p className="mt-4">
                  Select a file to preview
                </p>
              </div>

            </div>
          ) : (
            <>
              <div className="border-b border-slate-800 px-5 py-3">

                <div className="text-sm font-medium">
                  {selectedFile?.name ??
                    "Loading..."}
                </div>

                <div className="mt-1 text-xs text-slate-500">
                  {selectedPath}
                </div>

              </div>

              {fileLoading ? (
                <div className="p-6 text-slate-400">
                  Loading file...
                </div>
              ) : (
                <pre className="max-h-[600px] overflow-auto p-5 text-sm leading-6 text-slate-300">
                  <code>
                    {
                      selectedFile?.content
                    }
                  </code>
                </pre>
              )}
            </>
          )}

        </section>

      </div>

    </div>
  );
}