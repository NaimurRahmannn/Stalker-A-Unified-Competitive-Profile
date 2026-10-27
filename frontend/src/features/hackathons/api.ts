import api from "@/lib/api";
import type { Achievement, EntryResponse, Event, Overview, Page, Participation, Project, Submission } from "./types";

const root = "/hackathons";
export const hackathonApi = {
  overview: async () => (await api.get<Overview>(`${root}/overview/`)).data,
  events: async (page = 1) => (await api.get<Page<Event>>(`${root}/events/`, { params: { page } })).data,
  projects: async (page = 1, pageSize = 20) => (await api.get<Page<Project>>(`${root}/projects/`, { params: { page, page_size: pageSize } })).data,
  entries: async (payload: object) => (await api.post<EntryResponse>(`${root}/entries/`, payload)).data,
  patchEvent: async (id: number, payload: object) => (await api.patch<Event>(`${root}/events/${id}/`, payload)).data,
  patchProject: async (id: number, payload: object) => (await api.patch<Project>(`${root}/projects/${id}/`, payload)).data,
  patchParticipation: async (id: number, payload: object) => (await api.patch<Participation>(`${root}/participations/${id}/`, payload)).data,
  patchSubmission: async (id: number, payload: object) => (await api.patch<Submission>(`${root}/submissions/${id}/`, payload)).data,
  addAchievement: async (payload: object) => (await api.post<Achievement>(`${root}/achievements/`, payload)).data,
  patchAchievement: async (id: number, payload: object) => (await api.patch<Achievement>(`${root}/achievements/${id}/`, payload)).data,
  remove: async (resource: "events" | "projects" | "participations" | "submissions" | "achievements", id: number) => { await api.delete(`${root}/${resource}/${id}/`); },
};
