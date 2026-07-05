import { PublicProfilePageContent } from "@/features/profile/components/public-profile-page-content";

type PublicProfilePageProps = {
  params: Promise<{
    username: string;
  }>;
};

export default async function PublicProfilePage({
  params,
}: PublicProfilePageProps) {
  const { username } = await params;

  return <PublicProfilePageContent username={username} />;
}
