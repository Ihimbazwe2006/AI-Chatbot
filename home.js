const container = document.querySelector(".container");
const chatsContainer = document.querySelector("#chatsContainer");
const promptForm = document.querySelector("#promptForm");
const promptInput = document.querySelector("#promptInput");
const fileInput = document.querySelector("#file-input");
const fileUploadWrapper = document.querySelector(".file-upload-wrapper");
const historyList = document.querySelector("#historyList");
let controller, typingInterval;
const userData = { message: "", file: {} };

// Function to create message elements
const createMessageElement = (content, ...classes) => {
  const div = document.createElement("div");
  div.classList.add("message", ...classes);
  div.innerHTML = content;
  return div;
};

// Scroll to the bottom of the container
const scrollToBottom = () => container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });

// Simulate typing effect for bot responses
const typingEffect = (text, textElement, botMsgDiv) => {
  textElement.textContent = "";
  const words = text.split(" ");
  let wordIndex = 0;
  
  typingInterval = setInterval(() => {
    if (wordIndex < words.length) {
      textElement.textContent += (wordIndex === 0 ? "" : " ") + words[wordIndex++];
      scrollToBottom();
    } else {
      clearInterval(typingInterval);
      botMsgDiv.classList.remove("loading");
      document.body.classList.remove("bot-responding");
    }
  }, 40);
};

// Load chat history from server
const loadChatHistory = async () => {
  try {
    const response = await fetch('/get_history');
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.history) {
        displayHistory(data.history);
      }
    }
  } catch (error) {
    console.error('Error loading chat history:', error);
  }
};

// Display history in sidebar
const displayHistory = (history) => {
  historyList.innerHTML = '';
  history.forEach(item => {
    const historyItem = document.createElement('div');
    historyItem.className = 'history-item';
    historyItem.innerHTML = `
      <p class="history-question">${item.user_message.substring(0, 30)}${item.user_message.length > 30 ? '...' : ''}</p>
      <small>${new Date(item.created_at).toLocaleString()}</small>
    `;
    historyItem.addEventListener('click', () => {
      displayChatFromHistory(item);
    });
    historyList.appendChild(historyItem);
  });
};

// Display a chat from history
const displayChatFromHistory = (item) => {
  chatsContainer.innerHTML = '';
  
  // User message
  const userMsgHTML = `<p class="message-text">${item.user_message}</p>`;
  const userMsgDiv = createMessageElement(userMsgHTML, "user-message");
  chatsContainer.appendChild(userMsgDiv);
  
  // Bot message
  const botMsgHTML = `<img class="avatar" src="gemini.svg" /> <p class="message-text">${item.ai_response}</p>`;
  const botMsgDiv = createMessageElement(botMsgHTML, "bot-message");
  chatsContainer.appendChild(botMsgDiv);
  
  scrollToBottom();
  document.body.classList.add("chats-active");
};

// Send message to server and get AI response
const sendMessage = async (message) => {
  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: message })
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.success) {
        return data.ai_response;
      }
    }
    return "Sorry, I couldn't process your request.";
  } catch (error) {
    console.error('Error sending message:', error);
    return "Sorry, there was an error connecting to the server.";
  }
};

// Handle the form submission
const handleFormSubmit = async (e) => {
  e.preventDefault();
  const userMessage = promptInput.value.trim();
  if (!userMessage || document.body.classList.contains("bot-responding")) return;
  
  userData.message = userMessage;
  promptInput.value = "";
  document.body.classList.add("chats-active", "bot-responding");
  fileUploadWrapper.classList.remove("file-attached", "img-attached", "active");
  
  // Display user message
  const userMsgHTML = `<p class="message-text">${userData.message}</p>`;
  const userMsgDiv = createMessageElement(userMsgHTML, "user-message");
  chatsContainer.appendChild(userMsgDiv);
  scrollToBottom();
  
  // Display loading message for bot
  const botMsgHTML = `<img  src="\static/images/mini-logo.png"> <p class="message-text">Analysing request...</p>`;
  const botMsgDiv = createMessageElement(botMsgHTML, "bot-message", "loading");
  chatsContainer.appendChild(botMsgDiv);
  scrollToBottom();
  
  try {
    // Get AI response
    const aiResponse = await sendMessage(userData.message);
    
    // Update bot message with actual response
    const textElement = botMsgDiv.querySelector(".message-text");
    typingEffect(aiResponse, textElement, botMsgDiv);
    
    // Reload history to include the new chat
    await loadChatHistory();
  } catch (error) {
    console.error('Error in chat:', error);
    botMsgDiv.querySelector(".message-text").textContent = "Sorry, an error occurred.";
    botMsgDiv.classList.remove("loading");
    document.body.classList.remove("bot-responding");
  }
};

// Handle file input change (file upload)
fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;
  const isImage = file.type.startsWith("image/");
  const reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = (e) => {
    fileInput.value = "";
    const base64String = e.target.result.split(",")[1];
    fileUploadWrapper.querySelector(".file-preview").src = e.target.result;
    fileUploadWrapper.classList.add("active", isImage ? "img-attached" : "file-attached");
    userData.file = { fileName: file.name, data: base64String, mime_type: file.type, isImage };
  };
});

// Cancel file upload
document.querySelector("#cancel-file-btn").addEventListener("click", () => {
  userData.file = {};
  fileUploadWrapper.classList.remove("file-attached", "img-attached", "active");
});

// Stop Bot Response
document.querySelector("#stop-response-btn").addEventListener("click", () => {
  controller?.abort();
  userData.file = {};
  clearInterval(typingInterval);
  const loadingMessage = chatsContainer.querySelector(".bot-message.loading");
  if (loadingMessage) {
    loadingMessage.querySelector(".message-text").textContent = "Response stopped.";
    loadingMessage.classList.remove("loading");
  }
  document.body.classList.remove("bot-responding");
});

// Handle suggestions click
document.querySelectorAll(".suggestions-item").forEach((suggestion) => {
  suggestion.addEventListener("click", () => {
    promptInput.value = suggestion.querySelector(".text").textContent;
    promptForm.dispatchEvent(new Event("submit"));
  });
});

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
  loadChatHistory();
});

// Add event listeners
promptForm.addEventListener("submit", handleFormSubmit);
document.querySelector("#add-file-btn").addEventListener("click", () => fileInput.click());