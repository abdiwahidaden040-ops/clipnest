const form = document.getElementById("download-form");
const input = document.getElementById("video-url");
const button = document.getElementById("download-btn");
const pasteButton = document.getElementById("paste-btn");
const statusBox = document.getElementById("status");

function showStatus(message, type = "info") {
  statusBox.textContent = message;
  statusBox.className = `status show ${type}`;
}
function isTikTokUrl(value) {
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    return ["tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"]
      .some(domain => host === domain || host.endsWith("." + domain));
  } catch { return false; }
}
pasteButton.addEventListener("click", async () => {
  try {
    input.value = await navigator.clipboard.readText();
    input.focus();
    showStatus("Link pasted. Select Download video when you're ready.", "success");
  } catch {
    input.focus();
    showStatus("Clipboard access isn't available here. Paste your link into the field.", "info");
  }
});
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const url = input.value.trim();
  if (!isTikTokUrl(url)) {
    showStatus("Please enter a valid TikTok video URL.", "error");
    return;
  }
  button.disabled = true;
  button.querySelector("span:first-child").textContent = "Preparing your video…";
  showStatus("Checking the public video link. This may take a moment.", "info");
  try {
    const response = await fetch("/api/download", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({url})
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "The download could not be completed.");
    }
    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match ? match[1] : "clipnest-video.mp4";
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(objectUrl);
    showStatus("Your download is ready. Please respect the creator's rights when using the video.", "success");
  } catch (error) {
    showStatus(error.message || "Something went wrong. Please try another public TikTok link.", "error");
  } finally {
    button.disabled = false;
    button.querySelector("span:first-child").textContent = "Download video";
  }
});
