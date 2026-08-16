import { CybersecConsole } from "@/components/cybersec-console";
import { getSystemStatus } from "@/lib/system-status";

export default async function Home() {
  const status = await getSystemStatus();

  return <CybersecConsole status={status} />;
}
