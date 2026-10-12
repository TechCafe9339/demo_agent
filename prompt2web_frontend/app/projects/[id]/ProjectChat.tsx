"use client";

import {
    FormEvent,
    useEffect,
    useRef,
    useState,
} from "react";

import {
    apiGet,
    apiPost,
} from "../../../lib/api";


type Message = {
    id: number;
    role: "user" | "assistant";
    content: string;
    timestamp: string;
};


type ChatResponse = {
    conversation_id: number;
    messages: Message[];
};


type Props = {
    projectId: string;
};

type SendMessageResponse = {
    user_message: Message;
    assistant_message: Message;
};


export default function ProjectChat({
    projectId,
}: Props) {
    const [
        messages,
        setMessages,
    ] =
        useState<Message[]>([]);

    const [
        message,
        setMessage,
    ] =
        useState("");

    const [
        loading,
        setLoading,
    ] =
        useState(true);

    const [
        sending,
        setSending,
    ] =
        useState(false);

    const [
        error,
        setError,
    ] =
        useState<string | null>(
            null
        );

    const bottomRef =
        useRef<HTMLDivElement | null>(
            null
        );


    async function loadMessages() {
        try {
            setError(null);

            const result =
                await apiGet<
                    ChatResponse
                >(
                    `/projects/${projectId}/chat/`
                );

            setMessages(
                result.messages
            );

        } catch (error) {
            setError(
                error instanceof Error
                    ? error.message
                    : "Failed to load chat."
            );

        } finally {
            setLoading(false);
        }
    }


    useEffect(() => {
        loadMessages();
    }, [projectId]);


    useEffect(() => {
        bottomRef.current?.scrollIntoView({
            behavior: "smooth",
        });
    }, [messages]);


    async function handleSubmit(
        event:
            FormEvent<HTMLFormElement>
    ) {
        event.preventDefault();

        const content =
            message.trim();

        if (
            !content ||
            sending
        ) {
            return;
        }

        try {
            setSending(true);
            setError(null);

            const result =
                await apiPost<
                    SendMessageResponse
                >(
                    `/projects/${projectId}/chat/`,
                    {
                        content,
                    }
                );

            setMessages(
                (current) => [
                    ...current,
                    result.user_message,
                    result.assistant_message,
                ]
            );

            setMessage("");

        } catch (error) {
            setError(
                error instanceof Error
                    ? error.message
                    : "Failed to send message."
            );

        } finally {
            setSending(false);
        }
    }


    return (
        <div className="flex h-[calc(100vh-215px)] flex-col bg-slate-950">

            {/* Messages */}

            <div className="flex-1 overflow-y-auto px-6 py-8">

                <div className="mx-auto max-w-4xl">

                    {loading ? (
                        <p className="text-slate-500">
                            Loading conversation...
                        </p>

                    ) : messages.length === 0 ? (
                        <div className="flex min-h-[420px] items-center justify-center">

                            <div className="max-w-lg text-center">

                                <div className="text-4xl">
                                    ✦
                                </div>

                                <h2 className="mt-5 text-2xl font-semibold">
                                    Continue building this project
                                </h2>

                                <p className="mt-3 leading-7 text-slate-400">
                                    Ask Prompt2Web to explain the
                                    project or request a change.
                                </p>

                                <div className="mt-6 space-y-2 text-left">

                                    <button
                                        type="button"
                                        onClick={() =>
                                            setMessage(
                                                "Explain the architecture of this project."
                                            )
                                        }
                                        className="w-full rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300 hover:border-slate-600"
                                    >
                                        Explain the project architecture
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() =>
                                            setMessage(
                                                "Add dark mode to this application."
                                            )
                                        }
                                        className="w-full rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300 hover:border-slate-600"
                                    >
                                        Add dark mode
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() =>
                                            setMessage(
                                                "What features are still missing?"
                                            )
                                        }
                                        className="w-full rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300 hover:border-slate-600"
                                    >
                                        Find missing features
                                    </button>

                                </div>

                            </div>

                        </div>
                    ) : (
                        <div className="space-y-8">

                            {messages.map(
                                (item) => (
                                    <div
                                        key={item.id}
                                        className={
                                            item.role === "user"
                                                ? "flex justify-end"
                                                : "flex justify-start"
                                        }
                                    >

                                        <div
                                            className={
                                                item.role === "user"
                                                    ? "max-w-[75%] rounded-2xl bg-blue-600 px-5 py-3 text-white"
                                                    : "max-w-[80%] rounded-2xl border border-slate-800 bg-slate-900 px-5 py-4 text-slate-200"
                                            }
                                        >
                                            <div className="whitespace-pre-wrap leading-7">
                                                {item.content}
                                            </div>

                                            <div
                                                className={
                                                    item.role === "user"
                                                        ? "mt-2 text-xs text-blue-200"
                                                        : "mt-2 text-xs text-slate-500"
                                                }
                                            >
                                                {new Date(
                                                    item.timestamp
                                                ).toLocaleString()}
                                            </div>
                                        </div>

                                    </div>
                                )
                            )}

                            <div
                                ref={bottomRef}
                            />

                        </div>
                    )}

                </div>

            </div>


            {/* Error */}

            {error && (
                <div className="mx-auto mb-3 w-full max-w-4xl px-6">

                    <div className="rounded-lg border border-red-900 bg-red-950/40 p-3 text-sm text-red-300">
                        {error}
                    </div>

                </div>
            )}


            {/* Prompt input */}

            <div className="border-t border-slate-800 bg-slate-950 px-6 py-5">

                <form
                    onSubmit={handleSubmit}
                    className="mx-auto max-w-4xl"
                >

                    <div className="rounded-2xl border border-slate-700 bg-slate-900 p-3">

                        <textarea
                            value={message}
                            onChange={(event) =>
                                setMessage(
                                    event.target.value
                                )
                            }
                            placeholder="Ask Prompt2Web to modify this project..."
                            rows={3}
                            className="w-full resize-none bg-transparent p-2 text-white outline-none placeholder:text-slate-600"
                        />

                        <div className="flex items-center justify-between border-t border-slate-800 pt-3">

                            <span className="text-xs text-slate-500">
                                Project #{projectId}
                            </span>

                            <button
                                type="submit"
                                disabled={
                                    sending ||
                                    !message.trim()
                                }
                                className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                {sending
                                    ? "Prompt2Web is thinking..."
                                    : "Send"}
                            </button>

                        </div>

                    </div>

                </form>

            </div>

        </div>
    );
}