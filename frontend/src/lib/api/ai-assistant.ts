import { apiFetch } from "./fetcher";

export type AssistantChatRequest = {
  readonly message: string;
};

export type AssistantChatResponse = {
  readonly reply: string;
  readonly tool: string | null;
  readonly toolResult: Record<string, unknown> | null;
};

export async function assistantChat(input: AssistantChatRequest): Promise<AssistantChatResponse> {
  return apiFetch<AssistantChatResponse>("/ai/assistant/chat", { method: "POST", json: input });
}

