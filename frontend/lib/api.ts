/**
 * API client for backend communication.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface PresignedUrlResponse {
  upload_url: string;
  video_key: string;
  expires_in: number;
}

export interface UploadConfirmResponse {
  success: boolean;
  video_url: string;
}

/**
 * Request a presigned URL for uploading a video to S3.
 */
export async function getPresignedUploadUrl(
  sessionId: string,
  contentType: string = "video/webm"
): Promise<PresignedUrlResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/videos/presigned-url`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
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
  const response = await fetch(`${API_BASE_URL}/api/v1/videos/confirm-upload`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
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
    videoBlob.type
  );

  // Step 2: Upload to S3
  await uploadVideoToS3(upload_url, videoBlob, onProgress);

  // Step 3: Confirm upload
  const { video_url } = await confirmVideoUpload(sessionId, video_key);

  return video_url;
}
