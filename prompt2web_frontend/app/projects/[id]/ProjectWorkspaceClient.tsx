"use client";

import Link from "next/link";
import ProjectFiles from "./ProjectFiles";
import ProjectChat from "./ProjectChat";
import {
  useEffect,
  useState,
} from "react";

import {
  apiGet,
} from "../../../lib/api";


type Project = {
  id: number;
  name: string;
  description: string;
  initial_prompt: string;
  status: string;
  created_at: string;
  updated_at: string;
};


type Specification = {
  id: number;
  name: string;
  description: string;
  application_type: string;
  stack: Record<
    string,
    unknown
  >;
  features: string[];
  entities: unknown[];
  pages: unknown[];
  user_roles: string[];
  assumptions: string[];
};


type PlanTask = {
  id: number;
  task_number: number;
  title: string;
  status: string;
};


type Plan = {
  id: number;
  tasks: PlanTask[];
};


type WorkspaceResponse = {
  project: Project;

  specification:
  | Specification
  | null;

  plan:
  | Plan
  | null;
};


type Props = {
  projectId: string;
};


export default function ProjectWorkspaceClient({
  projectId,
}: Props) {
  const [
    data,
    setData,
  ] =
    useState<
      WorkspaceResponse | null
    >(null);

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null
    );

  const [
    activeTab,
    setActiveTab,
  ] =
    useState<
      | "overview"
      | "chat"
      | "files"
      | "tests"
      | "builds"
      | "preview"
    >("overview");


  useEffect(() => {
    async function loadWorkspace() {
      try {
        setError(null);

        const result =
          await apiGet<
            WorkspaceResponse
          >(
            `/projects/${projectId}/workspace/`
          );

        setData(result);

      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Failed to load project."
        );

      } finally {
        setLoading(false);
      }
    }

    loadWorkspace();

  }, [projectId]);


  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 p-10 text-white">
        Loading project...
      </main>
    );
  }


  if (
    error ||
    !data
  ) {
    return (
      <main className="min-h-screen bg-slate-950 p-10 text-white">

        <div className="rounded-xl border border-red-900 bg-red-950/40 p-5 text-red-300">
          {error ??
            "Project not found."}
        </div>

      </main>
    );
  }


  const {
    project,
    specification,
    plan,
  } = data;


  return (
    <div className="min-h-screen bg-slate-950 text-white">

      <header className="border-b border-slate-800 bg-slate-900 px-8 py-5">

        <div className="flex items-center justify-between">

          <div>
            <Link
              href="/"
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              ← My Projects
            </Link>

            <h1 className="mt-2 text-2xl font-bold">
              {specification?.name ??
                project.name}
            </h1>

            <p className="mt-1 text-sm text-slate-400">
              Project #{project.id}
            </p>
          </div>

          <div className="rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm capitalize">
            {project.status}
          </div>

        </div>

      </header>


      <nav className="border-b border-slate-800 bg-slate-900 px-8">

        <div className="flex gap-8">

          <button
            onClick={() =>
              setActiveTab(
                "overview"
              )
            }
            className={
              activeTab ===
                "overview"
                ? "border-b-2 border-blue-500 py-4 text-sm font-medium text-blue-400"
                : "py-4 text-sm text-slate-400 hover:text-white"
            }
          >
            Overview
          </button>

          <button
            onClick={() =>
              setActiveTab(
                "chat"
              )
            }
            className={
              activeTab ===
                "chat"
                ? "border-b-2 border-blue-500 py-4 text-sm font-medium text-blue-400"
                : "py-4 text-sm text-slate-400 hover:text-white"
            }
          >
            Chat
          </button>

          <button
            onClick={() =>
              setActiveTab(
                "files"
              )
            }
            className={
              activeTab ===
                "files"
                ? "border-b-2 border-blue-500 py-4 text-sm font-medium text-blue-400"
                : "py-4 text-sm text-slate-400 hover:text-white"
            }
          >
            Files
          </button>

          <button
            onClick={() =>
              setActiveTab(
                "tests"
              )
            }
            className={
              activeTab ===
                "tests"
                ? "border-b-2 border-blue-500 py-4 text-sm font-medium text-blue-400"
                : "py-4 text-sm text-slate-400 hover:text-white"
            }
          >
            Tests
          </button>

          <button
            onClick={() =>
              setActiveTab(
                "builds"
              )
            }
            className={
              activeTab ===
                "builds"
                ? "border-b-2 border-blue-500 py-4 text-sm font-medium text-blue-400"
                : "py-4 text-sm text-slate-400 hover:text-white"
            }
          >
            Builds
          </button>

          <button
            onClick={() =>
              setActiveTab(
                "preview"
              )
            }
            className={
              activeTab ===
                "preview"
                ? "border-b-2 border-blue-500 py-4 text-sm font-medium text-blue-400"
                : "py-4 text-sm text-slate-400 hover:text-white"
            }
          >
            Preview
          </button>

        </div>

      </nav>


      {activeTab === "overview" && (
        <main className="mx-auto max-w-6xl p-8">

          <div className="grid gap-6 lg:grid-cols-3">


            <div className="space-y-6 lg:col-span-2">

              <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">

                <h2 className="text-lg font-semibold">
                  Initial Prompt
                </h2>

                <p className="mt-4 leading-7 text-slate-300">
                  {project.initial_prompt}
                </p>

              </section>


              <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">

                <h2 className="text-lg font-semibold">
                  Application Specification
                </h2>

                {!specification ? (
                  <p className="mt-4 text-slate-500">
                    Specification has not been generated yet.
                  </p>
                ) : (
                  <div className="mt-4 space-y-4">

                    <div>
                      <div className="text-xs uppercase text-slate-500">
                        Description
                      </div>

                      <p className="mt-1 text-slate-300">
                        {specification.description}
                      </p>
                    </div>


                    <div>
                      <div className="text-xs uppercase text-slate-500">
                        Application Type
                      </div>

                      <p className="mt-1 text-slate-300">
                        {specification.application_type}
                      </p>
                    </div>


                    <div>
                      <div className="text-xs uppercase text-slate-500">
                        Features
                      </div>

                      <div className="mt-2 flex flex-wrap gap-2">

                        {specification.features.map(
                          (
                            feature,
                            index
                          ) => (
                            <span
                              key={index}
                              className="rounded-lg bg-blue-500/10 px-3 py-1 text-sm text-blue-300"
                            >
                              {feature}
                            </span>
                          )
                        )}

                      </div>
                    </div>

                  </div>
                )}

              </section>


              <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">

                <h2 className="text-lg font-semibold">
                  Implementation Plan
                </h2>

                {!plan ? (
                  <p className="mt-4 text-slate-500">
                    Implementation plan has not been created yet.
                  </p>
                ) : (
                  <div className="mt-5 space-y-3">

                    {plan.tasks.map(
                      (task) => (
                        <div
                          key={task.id}
                          className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950 px-4 py-4"
                        >
                          <div className="flex items-center gap-4">

                            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-sm">
                              {task.task_number}
                            </div>

                            <div className="font-medium">
                              {task.title}
                            </div>

                          </div>

                          <span className="text-sm text-slate-400">
                            {task.status}
                          </span>

                        </div>
                      )
                    )}

                  </div>
                )}

              </section>

            </div>


            <aside className="space-y-6">

              <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">

                <h2 className="font-semibold">
                  Project Status
                </h2>

                <div className="mt-5 text-3xl font-bold capitalize text-blue-400">
                  {project.status}
                </div>

              </section>


              <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">

                <h2 className="font-semibold">
                  Tech Stack
                </h2>

                <div className="mt-4 space-y-2 text-sm text-slate-300">

                  <div>
                    Frontend: Next.js
                  </div>

                  <div>
                    Backend: Express.js
                  </div>

                  <div>
                    Database: MySQL
                  </div>

                </div>

              </section>


              <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">

                <h2 className="font-semibold">
                  Progress
                </h2>

                {!plan ? (
                  <p className="mt-4 text-sm text-slate-500">
                    No tasks available.
                  </p>
                ) : (
                  <div className="mt-4">

                    <div className="text-3xl font-bold">
                      {
                        plan.tasks.filter(
                          (task) =>
                            task.status ===
                            "completed"
                        ).length
                      }
                      /
                      {plan.tasks.length}
                    </div>

                    <p className="mt-1 text-sm text-slate-500">
                      tasks completed
                    </p>

                  </div>
                )}

              </section>

            </aside>

          </div>

        </main>)}

      {activeTab === "files" && (
        <ProjectFiles
          projectId={
            projectId
          }
        />
      )}

      {activeTab === "chat" && (
        <ProjectChat
          projectId={
            projectId
          }
        />
      )}

      {activeTab === "tests" && (
        <div className="p-8 text-slate-400">
          Test results will appear here.
        </div>
      )}

      {activeTab === "builds" && (
        <div className="p-8 text-slate-400">
          Build history will appear here.
        </div>
      )}

      {activeTab === "preview" && (
        <div className="p-8 text-slate-400">
          Application preview will appear here.
        </div>
      )}

    </div>
  );
}