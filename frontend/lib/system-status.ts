const apiBaseUrl =
  process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getSystemStatus(): Promise<"Operational" | "Degraded"> {
  try {
    const response = await fetch(`${apiBaseUrl}/health`, {
      cache: "no-store",
      next: { revalidate: 0 }
    });

    if (!response.ok) {
      return "Degraded";
    }

    return "Operational";
  } catch {
    return "Degraded";
  }
}
