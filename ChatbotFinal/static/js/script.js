const messageBar = document.querySelector(".bar-wrapper input");
const sendBtn = document.querySelector(".bar-wrapper button");
const messageBox = document.querySelector(".message-box");
let i = 0
const API_URL = "http://localhost:5000/search"; // Update with your Flask API endpoint

// Function to send message
const sendMessage = async () => {
    if (messageBar.value.length > 0) {
        const userTypedMessage = messageBar.value;
        messageBar.value = "";

        let message = `
      <div class="chat1 message">
        <img src="../static/img/user.jpg">
        <span>
          ${userTypedMessage}
        </span>
      </div>`;

        let response = `
      <div class="chat response">
        <img src="../static/img/chatbot.jpg">
        <span class= "new_${i}">Loading search results...</span>
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

            const chatBotResponse = document.querySelector(".response .new_" + i);
            if (!Array.isArray(data.results.searches)) {
                chatBotResponse.innerHTML = `<div class="card"><div class="card-body"><p>${data.results.searches}</p></div></div>`
            } else {

                chatBotResponse.innerHTML = `<div class="card">
                    <div class="card-body"><h5>Summary: </h5><p>${data.results.summary}</p>
                    </div></div>`

                const filteredResults = data.results.searches.filter(result => result.title !== '' && result.description !== '').slice(0, 5);
                filteredResults.forEach(result => {
                    chatBotResponse.innerHTML += `<div class="card">
                                          <div class="card-body">
                                                   <h5><img src="${result.og_image}"/> ${result.title}</h5>
                                                  <p class="card-text">${result.description}
                                                  </p>
                                              </div>
                                        </div>`;
                });
                window.query = data.results.query
                chatBotResponse.innerHTML += `<button class="btn-dark" onclick="navigateToExplore()">Explore</button>`

                fetch('/change_video_src?message=' + data.results.summary, {
                    method: 'GET',
                })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        // Get the iframe element by its ID
                        var iframe = document.getElementById('videoFrame');

                        iframe.src = '../static/img/testvid2.mp4'; // Replace 'new_video.mp4' with your desired video source

                    })
                    .catch(error => {
                        console.error('There was a problem with the AJAX request:', error);
                    });
            }

            i = i + 1;
        } catch (error) {
            console.error('Error:', error);
            const chatBotResponse = document.querySelector(".response .new_" + i);
            chatBotResponse.innerHTML = "Oops! An error occurred. Please try again";
            document.querySelector('.new-'+ i).remove();
        }
    }
};

function navigateToExplore() {
    window.location.href = "/result?query="+window.query
}

// Event listener for send button click
sendBtn.onclick = sendMessage;

// Event listener for Enter key press
messageBar.addEventListener("keypress", function (event) {
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
messageBar.addEventListener("keypress", async function (event) {
    if (event.key === "Enter") {
        await sendMessage();
        // await triggerVideoSourceChange();
    }
});
