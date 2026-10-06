import "server-only";

import { cookies } from "next/headers";
import { unstable_rethrow } from "next/navigation";
import { connection } from "next/server";

import type {
  Article,
  ArticleSummary,
  LiveStream,
  Page,
  Series,
  SeriesDetail,
  Video,
} from "./types";

/** Where the Next.js server reaches Django (never exposed to the browser). */
export const API_URL = (process.env.API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export const TOKEN_COOKIE = "ines_token";

export class ApiError extends Error {
  constructor(
    public status: number,
    public data: unknown,
  ) {
    super(`API request failed with status ${status}`);
  }
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  token?: string | null;
}

/** Low-level call to the Django API. Throws ApiError for non-2xx responses. */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  await connection(); // always render with fresh data at request time

  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.token) headers.Authorization = `Token ${options.token}`;

  const response = await fetch(`${API_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    cache: "no-store",
    signal: AbortSignal.timeout(8000),
  });

  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, data);
  return data as T;
}

async function sessionToken(): Promise<string | null> {
  return (await cookies()).get(TOKEN_COOKIE)?.value ?? null;
}

/**
 * Read public content. Sends the visitor's token when present (members see
 * members-only links and full articles). Returns `fallback` if the API is down,
 * so one failing section never takes the whole page down.
 */
async function read<T>(path: string, fallback: T): Promise<T> {
  try {
    return await apiRequest<T>(path, { token: await sessionToken() });
  } catch (error) {
    unstable_rethrow(error); // let Next.js handle its own control-flow signals
    if (error instanceof ApiError && error.status === 401) {
      // Stale token: retry as a guest.
      try {
        return await apiRequest<T>(path);
      } catch {
        return fallback;
      }
    }
    console.error(`[api] ${path} failed:`, error instanceof Error ? error.message : error);
    return fallback;
  }
}

/** Like read(), but distinguishes "not found" (null) for detail pages. */
async function readOne<T>(path: string): Promise<T | null> {
  try {
    return await apiRequest<T>(path, { token: await sessionToken() });
  } catch (error) {
    unstable_rethrow(error);
    if (error instanceof ApiError && error.status === 401) {
      return apiRequest<T>(path).catch(() => null);
    }
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

const emptyPage = <T,>(): Page<T> => ({ count: 0, next: null, previous: null, results: [] });

export const getSeries = () => read<Series[]>("/api/series/", []);
export const getSeriesDetail = (slug: string) =>
  readOne<SeriesDetail>(`/api/series/${encodeURIComponent(slug)}/`);
export const getVideos = (page = 1) => read<Page<Video>>(`/api/videos/?page=${page}`, emptyPage<Video>());
export const getSchedule = () => read<LiveStream[]>("/api/schedule/", []);
export const getPastStreams = () => read<LiveStream[]>("/api/schedule/?past=1", []);
export const getArticles = (page = 1) =>
  read<Page<ArticleSummary>>(`/api/articles/?page=${page}`, emptyPage<ArticleSummary>());
export const getArticle = (slug: string) => readOne<Article>(`/api/articles/${encodeURIComponent(slug)}/`);

/** The time of the current request (pages render per request, see apiRequest). */
export async function requestTime(): Promise<number> {
  await connection();
  return Date.now();
}
