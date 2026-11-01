import type { DevpostImportDocument } from "./types";

export const DEVPOST_DOCUMENT_LIMIT = 1_048_576;
export const DEVPOST_REQUEST_LIMIT = DEVPOST_DOCUMENT_LIMIT + 16_384;

export function exampleDocument(handle: string): DevpostImportDocument {
  return {
    format_version: 1,
    profile_url: `https://devpost.com/${handle}`,
    projects: [{
      project_url: "https://devpost.com/software/replace-with-your-project-slug",
      title: "REPLACE_WITH_YOUR_PROJECT_TITLE",
      description: "DEMO DATA: Replace every placeholder with your own project and event details.",
      repository_url: "https://example.com/replace-with-your-repository-url",
      technologies: ["REPLACE_WITH_YOUR_TECHNOLOGY"],
      submissions: [{
        hackathon_name: "REPLACE_WITH_YOUR_HACKATHON_NAME",
        hackathon_url: "https://replace-with-your-hackathon.devpost.com/",
        status: "draft",
      }],
    }],
  };
}

export function hasExamplePlaceholders(document: DevpostImportDocument): boolean {
  return document.profile_url.includes("replace_with_your_handle") || document.projects.some((project) =>
    project.title.includes("REPLACE_WITH_") ||
    project.description?.includes("DEMO DATA:") ||
    project.project_url.includes("replace-with-your-") ||
    project.repository_url?.includes("replace-with-your-") ||
    project.demo_url?.includes("replace-with-your-") ||
    project.technologies?.some((technology) => technology.includes("REPLACE_WITH_")) ||
    project.submissions?.some((submission) =>
      submission.hackathon_name.includes("REPLACE_WITH_") ||
      submission.hackathon_url.includes("replace-with-your-")
    )
  );
}
