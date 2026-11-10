/**
 * Upload Your Resume — interaction layer.
 *
 * Responsibilities:
 *  1. open the native file picker from the whole dropzone (click + keyboard)
 *  2. accept drag & drop with visual feedback
 *  3. validate type / size, surface errors, and show the chosen file name + size
 *  4. wire "Last step" and "Finish"
 *
 * No dependencies; the file is never uploaded anywhere in this demo.
 */
(() => {
  "use strict";

  const MAX_BYTES = 10 * 1024 * 1024; // 10 MB
  const ALLOWED_EXTENSIONS = ["pdf", "doc", "docx", "png", "jpg", "jpeg"];

  const dropzone = document.getElementById("dropzone");
  const input = document.getElementById("file-input");
  const fileNameEl = document.getElementById("file-name");
  const nameEl = fileNameEl.querySelector(".dropzone__file-name");
  const sizeEl = fileNameEl.querySelector(".dropzone__file-size");
  const hintEl = document.getElementById("dropzone-hint");
  const errorEl = document.getElementById("form-error");
  const form = document.getElementById("upload-form");
  const backBtn = document.getElementById("btn-back");
  const toastEl = document.getElementById("toast");

  /** @type {File|null} */
  let selectedFile = null;
  let toastTimer = null;

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------
  const extensionOf = (name) => (name.includes(".") ? name.split(".").pop().toLowerCase() : "");

  const formatBytes = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const showError = (message) => {
    errorEl.textContent = message;
    errorEl.hidden = false;
    dropzone.classList.add("is-invalid");
    dropzone.setAttribute("aria-invalid", "true");
  };

  const clearError = () => {
    errorEl.hidden = true;
    errorEl.textContent = "";
    dropzone.classList.remove("is-invalid");
    dropzone.removeAttribute("aria-invalid");
  };

  const showToast = (message, variant = "default") => {
    toastEl.textContent = message;
    toastEl.hidden = false;
    toastEl.classList.toggle("is-success", variant === "success");
    // Force a frame so the transition runs when the node was hidden.
    requestAnimationFrame(() => toastEl.classList.add("is-visible"));

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toastEl.classList.remove("is-visible");
      setTimeout(() => { toastEl.hidden = true; }, 220);
    }, 2600);
  };

  const validate = (file) => {
    const ext = extensionOf(file.name);
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported file type “.${ext || "unknown"}”. Upload a PDF, DOC, DOCX, PNG or JPG.`;
    }
    if (file.size > MAX_BYTES) {
      return `File is ${formatBytes(file.size)} — the limit is 10 MB.`;
    }
    if (file.size === 0) {
      return "That file is empty. Please choose another one.";
    }
    return "";
  };

  // ---------------------------------------------------------------------------
  // State transitions
  // ---------------------------------------------------------------------------
  const setFile = (file) => {
    selectedFile = file;
    dropzone.classList.add("has-file");
    nameEl.textContent = file.name;
    sizeEl.textContent = `${formatBytes(file.size)} · click to replace`;
    fileNameEl.hidden = false;
    hintEl.hidden = true;
    clearError();
    dropzone.setAttribute("aria-label", `Selected file ${file.name}. Click to replace it.`);
  };

  const resetFile = () => {
    selectedFile = null;
    input.value = "";
    dropzone.classList.remove("has-file");
    fileNameEl.hidden = true;
    hintEl.hidden = false;
    clearError();
    dropzone.setAttribute("aria-label", "Choose a resume file to upload");
  };

  /**
   * Central entry point: validates, then commits or reports.
   * @param {File|null|undefined} file
   */
  const handleFile = (file) => {
    if (!file) return;

    const error = validate(file);
    if (error) {
      resetFile();
      showError(error);
      return;
    }
    setFile(file);
    showToast(`${file.name} selected`, "success");
  };

  // ---------------------------------------------------------------------------
  // Picker / keyboard
  // ---------------------------------------------------------------------------
  const openPicker = () => input.click();

  dropzone.addEventListener("click", (event) => {
    // The input lives inside the dropzone; ignore its own click to avoid a loop.
    if (event.target === input) return;
    openPicker();
  });

  dropzone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openPicker();
    }
  });

  input.addEventListener("change", () => handleFile(input.files && input.files[0]));

  // ---------------------------------------------------------------------------
  // Drag & drop
  // ---------------------------------------------------------------------------
  let dragDepth = 0; // dragenter/dragleave fire per child node; count them.

  ["dragenter", "dragover", "dragleave", "drop"].forEach((type) => {
    dropzone.addEventListener(type, (event) => {
      event.preventDefault();
      event.stopPropagation();
    });
  });

  dropzone.addEventListener("dragenter", () => {
    dragDepth += 1;
    dropzone.classList.add("is-dragover");
  });

  dropzone.addEventListener("dragover", (event) => {
    if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
  });

  dropzone.addEventListener("dragleave", () => {
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) dropzone.classList.remove("is-dragover");
  });

  dropzone.addEventListener("drop", (event) => {
    dragDepth = 0;
    dropzone.classList.remove("is-dragover");
    const files = event.dataTransfer && event.dataTransfer.files;
    if (files && files.length > 1) {
      showToast("Only the first file is used");
    }
    handleFile(files && files[0]);
  });

  // Stop the browser from navigating away when a file is dropped outside the zone.
  ["dragover", "drop"].forEach((type) => {
    window.addEventListener(type, (event) => {
      if (!dropzone.contains(event.target)) event.preventDefault();
    });
  });

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------
  form.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!selectedFile) {
      showError("Choose a resume file before finishing.");
      dropzone.focus();
      return;
    }

    // Demo only: a real app would POST FormData to an endpoint here.
    showToast(`Uploaded ${selectedFile.name}`, "success");
    document.dispatchEvent(new CustomEvent("resume:submit", { detail: { file: selectedFile } }));
  });

  backBtn.addEventListener("click", () => {
    if (history.length > 1) {
      history.back();
      return;
    }
    showToast("This demo starts at step 3 — nothing to go back to");
  });
})();
