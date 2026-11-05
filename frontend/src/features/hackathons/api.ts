import api from "@/lib/api";
import type { Achievement, DevpostImportDocument, DevpostImportRun, DevpostPreview, DuplicateReview, DuplicateReviewListing, EntryResponse, Event, EventFilters, Overview, Page, Participation, Project, ProjectFilters, Submission } from "./types";

const root = "/hackathons";
export const hackathonApi = {
  overview: async () => (await api.get<Overview>(`${root}/overview/`)).data,
  events: async (page = 1, name = "", filters?: EventFilters) => (await api.get<Page<Event>>(`${root}/events/`, { params: { page, ...(name ? { name } : {}), ...filters } })).data,
  projects: async (page = 1, pageSize = 20, title = "", filters?: ProjectFilters) => (await api.get<Page<Project>>(`${root}/projects/`, { params: { page, page_size: pageSize, ...(title ? { title } : {}), ...filters } })).data,
  entries: async (payload: object) => (await api.post<EntryResponse>(`${root}/entries/`, payload)).data,
  patchEvent: async (id: number, payload: object) => (await api.patch<Event>(`${root}/events/${id}/`, payload)).data,
  patchProject: async (id: number, payload: object) => (await api.patch<Project>(`${root}/projects/${id}/`, payload)).data,
  projectVisibility: async (id: number, isPublic: boolean) => (await api.patch<{ id: number; is_public: boolean }>(`${root}/projects/${id}/visibility/`, { is_public: isPublic })).data,
  patchParticipation: async (id: number, payload: object) => (await api.patch<Participation>(`${root}/participations/${id}/`, payload)).data,
  participationVisibility: async (id: number, isPublic: boolean) => (await api.patch<{ id: number; is_public: boolean }>(`${root}/participations/${id}/visibility/`, { is_public: isPublic })).data,
  patchSubmission: async (id: number, payload: object) => (await api.patch<Submission>(`${root}/submissions/${id}/`, payload)).data,
  addAchievement: async (payload: object) => (await api.post<Achievement>(`${root}/achievements/`, payload)).data,
  patchAchievement: async (id: number, payload: object) => (await api.patch<Achievement>(`${root}/achievements/${id}/`, payload)).data,
  remove: async (resource: "events" | "projects" | "participations" | "submissions" | "achievements", id: number) => { await api.delete(`${root}/${resource}/${id}/`); },
  previewDevpost: async (document: DevpostImportDocument) => (await api.post<DevpostPreview>(`${root}/devpost/imports/preview/`, document)).data,
  applyDevpost: async (document: DevpostImportDocument, previewToken: string) => (await api.post<DevpostImportRun>(`${root}/devpost/imports/`, { document, preview_token: previewToken })).data,
  devpostHistory: async (page = 1) => (await api.get<Page<DevpostImportRun>>(`${root}/devpost/imports/`, { params: { page } })).data,
  duplicateReviews: async (page = 1) => (await api.get<DuplicateReviewListing>(`${root}/duplicate-reviews/`, { params: { page } })).data,
  createDuplicateReview: async (payload: { record_type: "project" | "event"; manual_id: number; imported_id: number; decision: DuplicateReview["decision"] }) =>
    (await api.post<DuplicateReview>(`${root}/duplicate-reviews/`, payload)).data,
  updateDuplicateReview: async (id: number, decision: DuplicateReview["decision"]) =>
    (await api.patch<DuplicateReview>(`${root}/duplicate-reviews/${id}/`, { decision })).data,
};
