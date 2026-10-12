"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  apiGet,
  apiPost,
} from "../lib/api";

type Project = {
  id: number;
  initial_prompt: string;
  status: string;
  created_at?: string;
  updated_at?: string;
};

export default function Home() {
  const [
    prompt,
    setPrompt,
  ] = useState("");

  const [
    projects,
    setProjects,
  ] = useState<Project[]>([]);

  const [
    loadingProjects,
    setLoadingProjects,
  ] = useState(true);

  const [
    generating,
    setGenerating,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );

  async function loadProjects() {
    try {
      setError(null);

      const data =
        await apiGet<
          Project[] |
          {
            results: Project[];
          }
        >("/projects/");

      if (
        Array.isArray(data)
      ) {
        setProjects(data);
      } else {
        setProjects(
          data.results
        );
      }

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Could not load projects."
      );

    } finally {
      setLoadingProjects(false);
    }
  }

  useEffect(() => {
    loadProjects();
  }, []);

  async function handleSend() {
    const cleanedPrompt =
      prompt.trim();

    if (!cleanedPrompt) {
      return;
    }

    try {
      setGenerating(true);
      setError(null);

      // Step 1:
      // Create Django project
      const project =
        await apiPost<Project>(
          "/projects/",
          {
            initial_prompt:
              cleanedPrompt,
          }
        );

      setProjects(
        (current) => [
          project,
          ...current,
        ]
      );

      // Step 2:
      // Trigger AI analysis + planning
      await apiPost(
        `/projects/${project.id}/prepare/`,
        {}
      );

      // Step 3:
      // Reload project so sidebar
      // shows latest status
      await loadProjects();

      setPrompt("");

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Project preparation failed."
      );

    } finally {
      setGenerating(false);
    }
  }

  function projectTitle(
    project: Project
  ) {
    const text =
      project.initial_prompt;

    if (text.length <= 32) {
      return text;
    }

    return (
      text.slice(0, 32) +
      "..."
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-white">

      {/* Sidebar */}

      <aside className="flex w-72 flex-col border-r border-slate-800 bg-slate-900">

        <div className="border-b border-slate-800 p-5">
          <h1 className="text-xl font-bold">
            Prompt2Web
          </h1>

          <p className="mt-1 text-sm text-slate-400">
            AI Full-Stack Builder
          </p>
        </div>

        <div className="p-4">
          <button
            onClick={() =>
              setPrompt("")
            }
            className="
              w-full
              rounded-lg
              bg-blue-600
              px-4
              py-3
              font-medium
              hover:bg-blue-500
            "
          >
            + New Project
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3">

          <p className="mb-3 px-2 text-xs font-semibold uppercase text-slate-500">
            My Projects
          </p>

          {loadingProjects ? (
            <p className="px-2 text-sm text-slate-500">
              Loading...
            </p>
          ) : projects.length === 0 ? (
            <p className="px-2 text-sm text-slate-500">
              No projects yet.
            </p>
          ) : (
            <div className="space-y-2">

              {projects.map(
                (project) => (
                  <Link
                    key={project.id}
                    href={`/projects/${project.id}`}
                    className="
    block
    w-full
    rounded-lg
    px-3
    py-3
    text-left
    hover:bg-slate-800
  "
                  >
                    <div className="truncate font-medium">
                      {projectTitle(project)}
                    </div>

                    <div className="mt-1 flex items-center justify-between">
                      <span className="text-xs text-slate-500">
                        Project #{project.id}
                      </span>

                      <span className="text-xs text-slate-400">
                        {project.status}
                      </span>
                    </div>
                  </Link>
                )
              )}

            </div>
          )}
        </div>

        <div className="border-t border-slate-800 p-4">

          <div className="text-sm text-slate-400">
            Prompt2Web
          </div>

          <div className="text-xs text-slate-600">
            Qwen3:8B
          </div>

        </div>
      </aside>

      {/* Main content */}

      <main className="flex flex-1 flex-col">

        <header className="flex h-16 items-center justify-between border-b border-slate-800 px-6">

          <div>
            <h2 className="font-semibold">
              New Project
            </h2>

            <p className="text-xs text-slate-500">
              Describe what you want to build
            </p>
          </div>

          <div className="rounded-full bg-green-500/10 px-3 py-1 text-xs text-green-400">
            Backend Connected
          </div>

        </header>

        <section className="flex flex-1 flex-col items-center justify-center px-6">

          <div className="w-full max-w-3xl">

            <div className="mb-10 text-center">

              <div className="mb-4 text-5xl">
                ✦
              </div>

              <h2 className="text-3xl font-bold">
                What should we build?
              </h2>

              <p className="mt-3 text-slate-400">
                Describe your application and
                Prompt2Web will plan, generate,
                test and repair it.
              </p>

            </div>

            <div className="rounded-2xl border border-slate-700 bg-slate-900 p-3 shadow-xl">

              <textarea
                value={prompt}
                onChange={(
                  event
                ) =>
                  setPrompt(
                    event.target.value
                  )
                }
                placeholder="Build a finance management application..."
                rows={5}
                className="
                  w-full
                  resize-none
                  bg-transparent
                  p-3
                  text-white
                  outline-none
                  placeholder:text-slate-600
                "
              />

              <div className="flex items-center justify-between border-t border-slate-800 pt-3">

                <div className="text-xs text-slate-500">
                  Next.js + Express + MySQL
                </div>

                <button
                  onClick={
                    handleSend
                  }
                  disabled={
                    generating
                  }
                  className="
                    rounded-lg
                    bg-blue-600
                    px-5
                    py-2
                    font-medium
                    hover:bg-blue-500
                    disabled:cursor-not-allowed
                    disabled:opacity-50
                  "
                >
                  {generating
                    ? "Analyzing & Planning..."
                    : "Generate"}
                </button>

              </div>
            </div>

            {error && (
              <div className="mt-4 rounded-lg border border-red-900 bg-red-950/50 p-4 text-sm text-red-300">
                {error}
              </div>
            )}

            <div className="mt-5 grid grid-cols-2 gap-3">

              <button
                onClick={() =>
                  setPrompt(
                    "Build a finance management application"
                  )
                }
                className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-left text-sm text-slate-300 hover:border-slate-600"
              >
                💰 Finance Manager
              </button>

              <button
                onClick={() =>
                  setPrompt(
                    "Build a multi-vendor e-commerce marketplace"
                  )
                }
                className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-left text-sm text-slate-300 hover:border-slate-600"
              >
                🛒 E-Commerce Platform
              </button>

              <button
                onClick={() =>
                  setPrompt(
                    "Build a student management system"
                  )
                }
                className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-left text-sm text-slate-300 hover:border-slate-600"
              >
                🎓 Student Management
              </button>

              <button
                onClick={() =>
                  setPrompt(
                    "Build an inventory management application"
                  )
                }
                className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-left text-sm text-slate-300 hover:border-slate-600"
              >
                📦 Inventory System
              </button>

            </div>

          </div>
        </section>
      </main>
    </div>
  );
}