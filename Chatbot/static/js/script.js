const messageBar = document.querySelector(".bar-wrapper input");
const sendBtn = document.querySelector(".bar-wrapper button");
const messageBox = document.querySelector(".message-box");

const API_URL = "http://localhost:5000/search"; // Update with your Flask API endpoint

// Function to send message
const sendMessage = async () => {
  if (messageBar.value.length > 0) {
    const userTypedMessage = messageBar.value;
    messageBar.value = "";

    let message = `
      <div class="chat1 message">
        <img src="img/user.jpg">
        <span>
          ${userTypedMessage}
        </span>
      </div>`;

    let response = `
      <div class="chat response">
        <img src="img/chatbot.jpg">
        <span class= "new">Loading search results...</span>
      </div>`;

    messageBox.insertAdjacentHTML("beforeend", message);
    messageBox.insertAdjacentHTML("beforeend", response);

    const requestOptions = {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        "message": userTypedMessage 
      })
    };

    try {
      const res = await fetch(API_URL, requestOptions);
      if (!res.ok) {
        throw new Error('Failed to fetch data');
      }
      const data = await res.json();
      const chatBotResponse = document.querySelector(".response .new");
      chatBotResponse.innerHTML = '';

      data.results.forEach(result => {
        chatBotResponse.innerHTML += `<div class="result">
                                        <h3>${result.title}</h3>
                                        <p>${result.description}</p>
                                      </div>`;
      });
      chatBotResponse.classList.remove("new"); // Remove the "Loading search results..." message
    } catch (error) {
      console.error('Error:', error);
      const chatBotResponse = document.querySelector(".response .new");
      chatBotResponse.innerHTML = "Oops! An error occurred. Please try again";
      chatBotResponse.classList.remove("new"); // Remove the "Loading search results..." message
    }
  }
};

// Event listener for send button click
sendBtn.onclick = sendMessage;

// Event listener for Enter key press
messageBar.addEventListener("keypress", function(event) {
  if (event.key === "Enter") {
    sendMessage();
  }
});

// Function to trigger video source change after sending message
// const triggerVideoSourceChange = async () => {
//   try {
//     const userTypedMessage = messageBar.value;
//     const response = await fetch('/change_video_src', {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json'
//       },
//       body: JSON.stringify({
//         message: userTypedMessage
//       })
//     });
//     if (!response.ok) {
//       throw new Error('Failed to trigger video source change');
//     }
//   } catch (error) {
//     console.error('Error triggering video source change:', error);
//   }
// };

// Trigger video source change after sending message
sendBtn.onclick = async () => {
  await sendMessage();
  // await triggerVideoSourceChange();
};

// Trigger video source change after pressing Enter key
messageBar.addEventListener("keypress", async function(event) {
  if (event.key === "Enter") {
    await sendMessage();
    // await triggerVideoSourceChange();
  }
});
