export type ScenarioContext = {
  title: string;
  role: string;
  description: string;
  agent_id?: string;
};

export type CoachTip = {
  id: string;
  text: string;
  time: string;
  priority: "high" | "medium" | "low";
  category: string;
};

export type PostMortemMetric = {
  label: string;
  score: number;
  change: number;
};

export type PostMortemMoment = {
  time: string;
  desc: string;
  type: "positive" | "negative";
};

export type PostMortemResult = {
  overallScore: number;
  strengths: string[];
  improvements: string[];
  metrics: PostMortemMetric[];
  keyMoments: PostMortemMoment[];
};

export type VideoSession = {
  session_id: string;
  created_at: string;
};

export type VideoLink = {
  id: string;
  link: string;
  created_at?: string;
};

const DEFAULT_API_BASE = "http://localhost:8000";

const getApiBaseUrl = () =>
  process.env.NEXT_PUBLIC_API_BASE_URL ?? `${DEFAULT_API_BASE}/api/v1`;

const getServerApiBaseUrl = () => process.env.API_BASE_URL ?? getApiBaseUrl();

export const getWsBaseUrl = () => {
  const base = process.env.NEXT_PUBLIC_WS_BASE_URL ?? DEFAULT_API_BASE;
  const normalized = base.replace(/\/$/, "");
  return normalized.replace(/^http/, "ws");
};

export async function createScenarioContext(keywords: string) {
  const response = await fetch(`${getApiBaseUrl()}/scenario_context`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ keywords }),
  });

  if (!response.ok) {
    throw new Error("Scenario context request failed");
  }

  return (await response.json()) as ScenarioContext;
}

export async function createVideoSession(link: string) {
  const response = await fetch(`${getApiBaseUrl()}/videos/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ link }),
  });

  if (!response.ok) {
    throw new Error("Video session request failed");
  }

  return (await response.json()) as VideoSession;
}

export async function fetchVideoLinks() {
  const response = await fetch(`${getApiBaseUrl()}/videos/links`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Video links fetch failed");
  }

  return (await response.json()) as { videos: VideoLink[] };
}

export async function requestPostMortem(sessionId: string) {
  const response = await fetch(`${getApiBaseUrl()}/post_mortem`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!response.ok) {
    throw new Error("Post-mortem request failed");
  }

  return response.json();
}

export async function fetchPostMortem(sessionId: string) {
  const response = await fetch(
    `${getServerApiBaseUrl()}/post_mortem/${sessionId}`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error("Post-mortem fetch failed");
  }

  return (await response.json()) as PostMortemResult;
}

// =============================================================================
// S3 Video Upload Functions
// =============================================================================

export type PresignedUrlResponse = {
  upload_url: string;
  video_key: string;
  expires_in: number;
};

export type UploadConfirmResponse = {
  success: boolean;
  video_url: string;
};

/**
 * Request a presigned URL for uploading a video to S3.
 */
export async function getPresignedUploadUrl(
  sessionId: string,
  contentType: string = "video/webm"
): Promise<PresignedUrlResponse> {
  const response = await fetch(`${getApiBaseUrl()}/videos/presigned-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      content_type: contentType,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to get presigned URL: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Upload a video blob directly to S3 using a presigned URL.
 */
export async function uploadVideoToS3(
  presignedUrl: string,
  videoBlob: Blob,
  onProgress?: (progress: number) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable && onProgress) {
        const progress = (event.loaded / event.total) * 100;
        onProgress(progress);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new Error(`Upload failed with status ${xhr.status}`));
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Upload failed due to network error"));
    });

    xhr.open("PUT", presignedUrl);
    xhr.setRequestHeader("Content-Type", videoBlob.type);
    xhr.send(videoBlob);
  });
}

/**
 * Confirm that a video upload completed successfully.
 */
export async function confirmVideoUpload(
  sessionId: string,
  videoKey: string
): Promise<UploadConfirmResponse> {
  const response = await fetch(`${getApiBaseUrl()}/videos/confirm-upload`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      video_key: videoKey,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to confirm upload: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Full upload flow: get presigned URL, upload to S3, confirm upload.
 */
export async function uploadNegotiationVideo(
  sessionId: string,
  videoBlob: Blob,
  onProgress?: (progress: number) => void
): Promise<string> {
  // Step 1: Get presigned URL
  const { upload_url, video_key } = await getPresignedUploadUrl(
    sessionId,
    videoBlob.type || "video/webm"
  );

  // Step 2: Upload to S3
  await uploadVideoToS3(upload_url, videoBlob, onProgress);

  // Step 3: Confirm upload
  const { video_url } = await confirmVideoUpload(sessionId, video_key);

  return video_url;
}

/**
 * Get a presigned download URL for viewing a video.
 */
export async function getVideoDownloadUrl(
  sessionId: string,
  expiresIn: number = 3600
): Promise<{ download_url: string; expires_in: number }> {
  const response = await fetch(
    `${getApiBaseUrl()}/videos/download-url/${sessionId}?expires_in=${expiresIn}`
  );

  if (!response.ok) {
    throw new Error(`Failed to get download URL: ${response.statusText}`);
  }

  return response.json();
}
