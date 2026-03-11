import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const backendBaseUrl = process.env.RELAYOPS_BACKEND_URL ?? "http://127.0.0.1:8022";
export const dynamic = "force-dynamic";
export const revalidate = 0;

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const targetUrl = new URL(`/api/${path.join("/")}`, backendBaseUrl);
  const requestUrl = new URL(request.url);
  requestUrl.searchParams.forEach((value, key) => targetUrl.searchParams.set(key, value));

  const forwardedHeaders = new Headers();
  request.headers.forEach((value, key) => {
    if (key.toLowerCase() === "host" || key.toLowerCase() === "content-length") {
      return;
    }
    forwardedHeaders.set(key, value);
  });

  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map(({ name, value }) => `${name}=${value}`)
    .join("; ");
  if (cookieHeader) {
    forwardedHeaders.set("cookie", cookieHeader);
  }

  const response = await fetch(targetUrl, {
    method: request.method,
    headers: forwardedHeaders,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.text(),
    redirect: "manual",
    cache: "no-store",
  });

  const body = await response.arrayBuffer();
  const nextResponse = new NextResponse(body, {
    status: response.status,
    headers: response.headers,
  });

  const setCookie = response.headers.get("set-cookie");
  if (setCookie) {
    nextResponse.headers.set("set-cookie", setCookie);
  }
  nextResponse.headers.set("cache-control", "no-store, no-cache, must-revalidate");

  return nextResponse;
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context);
}

export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context);
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context);
}
