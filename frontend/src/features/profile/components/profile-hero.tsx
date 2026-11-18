"use client";

/* eslint-disable @next/next/no-img-element */
import { useRef, useState } from "react";
import Link from "next/link";
import {
  BriefcaseBusiness,
  Building2,
  Camera,
  CodeXml,
  LayoutDashboard,
  Loader2,
  MapPin,
  Share2,
} from "lucide-react";
import { toast } from "sonner";
import { metricAccentStyles } from "@/features/dashboard/styles";
import { updateUserProfile } from "@/features/auth/api";
import { useAuth } from "@/hooks/use-auth";
import { getApiErrorMessage } from "@/lib/utils";
import type { ProfileHeroView, ProfileMetricView } from "../view-model";

const MAX_IMAGE_BYTES = 8 * 1024 * 1024; // 8 MB
const ALLOWED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

async function shareProfile() {
  try {
    if (navigator.share) {
      await navigator.share({ title: document.title, url: window.location.href });
      return;
    }
    await navigator.clipboard.writeText(window.location.href);
    toast.success("Profile link copied");
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") return;
    try {
      await navigator.clipboard.writeText(window.location.href);
      toast.success("Profile link copied");
    } catch {
      toast.error("Could not share this profile");
    }
  }
}

function DefaultLinkedInStalkerCover() {
  return (
    <div className="relative size-full overflow-hidden bg-[#a0b4b7]">
      {/* Exact LinkedIn Default Cover Photo Vector Geometry (862x218 ratio) */}
      <svg
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 size-full select-none"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 862 218"
        preserveAspectRatio="none"
      >
        {/* Left primary shape with rightward convex curve */}
        <path
          d="M 0,0 L 520,0 C 546,65 546,153 520,218 L 0,218 Z"
          fill="#a0b4b7"
        />
        {/* Middle accent separator band */}
        <path
          d="M 520,0 C 546,65 546,153 520,218 L 591,218 L 591,0 Z"
          fill="#d9e5e7"
        />
        {/* Right rectangular block */}
        <rect
          x="591"
          y="0"
          width="271"
          height="218"
          fill="#bfd3d6"
        />
      </svg>

      {/* STALKER Monochrome Variant Logo Watermark */}
      <div className="pointer-events-none absolute inset-y-0 right-4 flex items-center justify-end sm:right-8 md:right-12">
        <img
          src="/images/stalker_monochrome_variant_transparent_generated.png"
          alt="STALKER"
          className="h-9 w-auto max-w-[40vw] object-contain opacity-35 mix-blend-multiply sm:h-12 md:h-14"
        />
      </div>
    </div>
  );
}

export function ProfileHero({
  hero,
  metrics,
  onProfileUpdated,
}: {
  hero: ProfileHeroView;
  metrics: ProfileMetricView[];
  onProfileUpdated?: () => void;
}) {
  const { user, refreshUser } = useAuth();
  const isOwner = Boolean(user && user.username.toLowerCase() === hero.username.toLowerCase());
  const isLocalArtwork = hero.avatarUrl === "/images/testuser-profile.jpg";

  const [avatarOverride, setAvatarOverride] = useState<{ source: string | null; url: string | null } | null>(null);
  const [coverOverride, setCoverOverride] = useState<{ source: string | null; url: string | null } | null>(null);
  const [failedCoverUrl, setFailedCoverUrl] = useState<string | null>(null);
  const avatarUrl = avatarOverride?.source === hero.avatarUrl ? avatarOverride.url : hero.avatarUrl;
  const coverUrl = coverOverride?.source === hero.coverUrl ? coverOverride.url : hero.coverUrl;
  const coverImageFailed = failedCoverUrl === coverUrl;

  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [isUploadingCover, setIsUploadingCover] = useState(false);

  const avatarInputRef = useRef<HTMLInputElement>(null);
  const coverInputRef = useRef<HTMLInputElement>(null);

  async function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!ALLOWED_IMAGE_TYPES.has(file.type)) {
      toast.error("Please upload a JPG, PNG, or WebP image.");
      e.target.value = "";
      return;
    }

    if (file.size > MAX_IMAGE_BYTES) {
      toast.error("Avatar image must be smaller than 8 MB.");
      e.target.value = "";
      return;
    }

    const previousUrl = avatarUrl;
    const previewUrl = URL.createObjectURL(file);
    setAvatarOverride({ source: hero.avatarUrl, url: previewUrl });
    setIsUploadingAvatar(true);

    try {
      const formData = new FormData();
      formData.append("avatar_image", file);
      const updatedUser = await updateUserProfile(formData);
      setAvatarOverride({ source: hero.avatarUrl, url: updatedUser.avatar ?? previewUrl });
      await refreshUser();
      onProfileUpdated?.();
      toast.success("Profile photo updated successfully");
    } catch (err) {
      setAvatarOverride({ source: hero.avatarUrl, url: previousUrl });
      toast.error(getApiErrorMessage(err, "Failed to update profile photo"));
    } finally {
      setIsUploadingAvatar(false);
      if (e.target) e.target.value = "";
    }
  }

  async function handleCoverChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!ALLOWED_IMAGE_TYPES.has(file.type)) {
      toast.error("Please upload a JPG, PNG, or WebP image.");
      e.target.value = "";
      return;
    }

    if (file.size > MAX_IMAGE_BYTES) {
      toast.error("Cover image must be smaller than 8 MB.");
      e.target.value = "";
      return;
    }

    const previousUrl = coverUrl;
    const previewUrl = URL.createObjectURL(file);
    setCoverOverride({ source: hero.coverUrl, url: previewUrl });
    setFailedCoverUrl(null);
    setIsUploadingCover(true);

    try {
      const formData = new FormData();
      formData.append("cover_image", file);
      const updatedUser = await updateUserProfile(formData);
      setCoverOverride({ source: hero.coverUrl, url: updatedUser.cover_photo ?? previewUrl });
      await refreshUser();
      onProfileUpdated?.();
      toast.success("Cover photo updated successfully");
    } catch (err) {
      setCoverOverride({ source: hero.coverUrl, url: previousUrl });
      toast.error(getApiErrorMessage(err, "Failed to update cover photo"));
    } finally {
      setIsUploadingCover(false);
      if (e.target) e.target.value = "";
    }
  }

  return (
    <section className="bg-white">
      {/* Cover Photo Banner (LinkedIn default cover structure / custom user image) */}
      <div className="relative h-36 w-full overflow-hidden sm:h-44 md:h-48">
        {/* Background Layer */}
        <div className="absolute inset-0">
          {coverUrl && !coverImageFailed ? (
            <img
              src={coverUrl}
              alt={`${hero.displayName}'s cover photo`}
              className="size-full object-cover object-center"
              onError={() => setFailedCoverUrl(coverUrl)}
            />
          ) : (
            <DefaultLinkedInStalkerCover />
          )}
        </div>

        {/* Top Action Bar: Cover Upload Button */}
        <div className="relative z-10 mx-auto flex h-full max-w-310 items-start justify-end px-5 pt-3.5 sm:px-8 sm:pt-4">
          {isOwner ? (
            <div>
              <input
                ref={coverInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={handleCoverChange}
                className="sr-only"
                aria-label="Upload cover photo"
              />
              <button
                type="button"
                onClick={() => coverInputRef.current?.click()}
                disabled={isUploadingCover}
                className="ui-button ui-button-secondary ui-button-sm bg-white/95"
              >
                {isUploadingCover ? (
                  <Loader2 aria-hidden="true" className="size-3.5 animate-spin text-primary" />
                ) : (
                  <Camera aria-hidden="true" className="size-3.5 text-primary" />
                )}
                <span>{isUploadingCover ? "Uploading..." : coverUrl ? "Change cover" : "Upload cover photo"}</span>
              </button>
            </div>
          ) : null}
        </div>
      </div>

      {/* Main Profile Info Section */}
      <div className="mx-auto max-w-310 px-5 pb-2 sm:px-8 sm:pb-4">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex min-w-0 flex-col gap-4 sm:flex-row sm:items-end sm:gap-6">
            {/* Circular Avatar Container matching LinkedIn style */}
            <div className="relative -mt-14 sm:-mt-17">
              <div
                onClick={() => {
                  if (isOwner && !isUploadingAvatar) avatarInputRef.current?.click();
                }}
                onKeyDown={(event) => {
                  if (isOwner && !isUploadingAvatar && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); avatarInputRef.current?.click(); }
                }}
                role={isOwner ? "button" : undefined}
                tabIndex={isOwner ? 0 : undefined}
                aria-label={isOwner ? "Change profile picture" : undefined}
                title={isOwner ? "Click to change profile picture" : undefined}
                className={`group relative grid size-28 shrink-0 place-items-center overflow-hidden rounded-full border-4 border-white bg-slate-100 text-3xl font-bold text-[#16436c] shadow-[0_10px_28px_rgba(7,18,34,.18)] sm:size-34 ${
                  isOwner ? "cursor-pointer" : ""
                }`}
              >
                {avatarUrl ? (
                  <img
                    src={avatarUrl}
                    alt={`${hero.displayName}'s avatar`}
                    className={`size-full object-cover ${isLocalArtwork ? "object-right" : "object-center"}`}
                  />
                ) : (
                  <div className="relative grid size-full place-items-center bg-[#e4eaec] text-slate-700">
                    <span aria-label={`${hero.displayName} initials`} className="font-bold text-[#102c46]">
                      {hero.initials}
                    </span>
                  </div>
                )}

                {/* Hover camera overlay for owner */}
                {isOwner && !isUploadingAvatar ? (
                  <div className="absolute inset-0 grid place-items-center bg-black/35 opacity-0 transition group-hover:opacity-100">
                    <Camera aria-hidden="true" className="size-7 text-white drop-shadow-md" />
                  </div>
                ) : null}

                {/* Uploading Spinner Overlay */}
                {isUploadingAvatar ? (
                  <div className="absolute inset-0 grid place-items-center bg-black/50 backdrop-blur-xs">
                    <Loader2 aria-hidden="true" className="size-8 animate-spin text-white" />
                  </div>
                ) : null}
              </div>

              {/* Owner Avatar Upload Button */}
              {isOwner ? (
                <>
                  <input
                    ref={avatarInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={handleAvatarChange}
                    className="sr-only"
                    aria-label="Upload profile picture"
                  />
                  <button
                    type="button"
                    onClick={() => avatarInputRef.current?.click()}
                    disabled={isUploadingAvatar}
                    aria-label="Upload profile picture"
                    title="Upload profile picture"
                    className="absolute bottom-0 right-0 z-20 grid size-10 place-items-center rounded-full border-2 border-white bg-primary text-white shadow-sm transition-colors hover:bg-primary-hover sm:size-11"
                  >
                    {isUploadingAvatar ? (
                      <Loader2 aria-hidden="true" className="size-4.5 animate-spin" />
                    ) : (
                      <Camera aria-hidden="true" className="size-4.5" />
                    )}
                  </button>
                </>
              ) : null}
            </div>

            {/* Display Name and Username */}
            <div className="min-w-0 sm:pb-2">
              <h1 className="wrap-break-word text-[30px] font-semibold leading-tight tracking-tight text-foreground sm:text-[40px]">
                {hero.displayName}
              </h1>
              <p className="mt-1 text-sm font-medium text-slate-500">@{hero.username}</p>
            </div>
          </div>

          {/* Action Buttons: Share & Dashboard */}
          <div className="flex flex-wrap gap-2 lg:pt-6">
            <button
              type="button"
              onClick={() => void shareProfile()}
              className={`ui-button ui-button-lg ${isOwner ? "ui-button-secondary" : "ui-button-primary"}`}
            >
              <Share2 aria-hidden="true" className="size-4" />
              Share profile
            </button>
            {isOwner ? (
              <Link
                href="/dashboard"
                className="ui-button ui-button-primary ui-button-lg"
              >
                <LayoutDashboard aria-hidden="true" className="size-4" />
                View dashboard
              </Link>
            ) : null}
          </div>
        </div>

        {hero.bio ? <p className="mt-6 max-w-2xl text-sm leading-6 text-slate-600">{hero.bio}</p> : null}
        {hero.country || hero.institution || hero.socialLinks.length > 0 ? (
          <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-[13px] text-slate-600">
            {hero.country ? (
              <span className="inline-flex items-center gap-1.5">
                <MapPin aria-hidden="true" className="size-4 text-[#357db5]" />
                {hero.country}
              </span>
            ) : null}
            {hero.institution ? (
              <span className="inline-flex items-center gap-1.5">
                <Building2 aria-hidden="true" className="size-4 text-[#357db5]" />
                {hero.institution}
              </span>
            ) : null}
            {hero.socialLinks.map((link) => {
              const Icon = link.kind === "github" ? CodeXml : BriefcaseBusiness;
              return (
                <a
                  key={link.kind}
                  href={link.href}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 font-medium text-primary hover:underline"
                >
                  <Icon aria-hidden="true" className="size-4" />
                  {link.label}
                </a>
              );
            })}
          </div>
        ) : null}

        <dl className="mt-9 grid grid-cols-2 gap-x-7 gap-y-7 border-y border-slate-200 py-6 lg:grid-cols-4 lg:gap-x-10">
          {metrics.map((metric) => {
            const Icon = metric.icon;
            const style = metricAccentStyles[metric.accent];
            return (
              <div key={metric.label} className="min-w-0">
                <dt className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">
                  <Icon aria-hidden="true" className={`size-4 shrink-0 ${style.icon}`} />
                  {metric.label}
                </dt>
                <dd
                  className={`mt-2 wrap-break-word font-mono font-semibold leading-tight tracking-tight tabular-nums text-foreground ${
                    metric.label === "Last Synced" ? "text-xl sm:text-2xl" : "text-[29px] sm:text-[34px]"
                  }`}
                >
                  {metric.value}
                </dd>
              </div>
            );
          })}
        </dl>
      </div>
    </section>
  );
}
