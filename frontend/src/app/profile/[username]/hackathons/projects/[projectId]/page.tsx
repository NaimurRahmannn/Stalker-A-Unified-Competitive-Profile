import { notFound } from "next/navigation";
import { PublicProjectDetail } from "@/features/profile/components/hackathons/public-project-detail";

type Props = { params: Promise<{ username: string; projectId: string }> };

export default async function ProjectPage({ params }: Props) {
  const { username, projectId: rawId } = await params;
  const projectId = Number(rawId);
  if (!Number.isSafeInteger(projectId) || projectId < 1) notFound();
  return <PublicProjectDetail key={`${username}-${projectId}`} username={username} projectId={projectId} />;
}
