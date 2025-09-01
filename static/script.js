document.addEventListener("DOMContentLoaded", () => {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const fileList = document.getElementById("file-list");
  const statusMessage = document.getElementById("status-message");
  const chatBox = document.getElementById("chat-box");
  const userInput = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  const clearBtn = document.getElementById("clear-btn");

  // Prevent default drag behaviors
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  // Highlight drop zone when a file is dragged over it
  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(
      eventName,
      () => {
        dropZone.classList.add("highlight");
      },
      false
    );
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(
      eventName,
      () => {
        dropZone.classList.remove("highlight");
      },
      false
    );
  });

  // Handle dropped files
  dropZone.addEventListener("drop", handleDrop, false);

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    uploadFile(files[0]);
  }

  // Handle file input click
  dropZone.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", (e) => {
    const files = e.target.files;
    uploadFile(files[0]);
  });

  function uploadFile(file) {
    if (!file) {
      return;
    }

    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    if (!allowedTypes.includes(file.type)) {
      statusMessage.textContent =
        "Invalid file type. Please upload a .pdf or .docx file.";
      statusMessage.style.color = "red";
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    fileList.textContent = `Uploading: ${file.name}`;
    statusMessage.textContent = "";

    fetch("/upload", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          statusMessage.textContent = `Error: ${data.error}`;
          statusMessage.style.color = "red";
        } else {
          statusMessage.textContent = data.message;
          statusMessage.style.color = "green";
          fileList.textContent = "";
        }
      })
      .catch((error) => {
        statusMessage.textContent = "An error occurred during the upload.";
        statusMessage.style.color = "red";
        console.error("Error:", error);
      });
  }

  // --- Chat Interface Logic ---

  sendBtn.addEventListener("click", sendMessage);
  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  });

  function sendMessage() {
    const query = userInput.value.trim();
    if (query === "") return;

    displayMessage(query, "user");
    userInput.value = "";

    userInput.disabled = true;
    sendBtn.disabled = true;

    fetch("/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: query }),
    })
      .then((response) => response.json())
      .then((data) => {
        displayMessage(data.response, "bot");
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
      })
      .catch((error) => {
        console.error("Error:", error);
        displayMessage(
          "Sorry, an error occurred while processing your request.",
          "bot"
        );
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
      });
  }

  function displayMessage(message, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    messageDiv.textContent = message;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  // --- New Clear Document Logic ---
  clearBtn.addEventListener("click", clearDocument);

  function clearDocument() {
    fetch("/clear", {
      method: "POST",
    })
      .then((response) => response.json())
      .then((data) => {
        statusMessage.textContent = data.message;
        statusMessage.style.color = "green";
        fileList.textContent = "";
        chatBox.innerHTML = "";
        userInput.value = "";
      })
      .catch((error) => {
        console.error("Error:", error);
        statusMessage.textContent =
          "An error occurred while clearing the document.";
        statusMessage.style.color = "red";
      });
  }
});
