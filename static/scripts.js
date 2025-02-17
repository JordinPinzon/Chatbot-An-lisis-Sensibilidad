document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    chatBox.scrollTop = chatBox.scrollHeight; // Mantiene el scroll abajo
});

function validateForm() {
    var messageInput = document.getElementById("message");
    var message = messageInput.value.trim();
    if (message === "") {
        alert("Por favor, ingresa un mensaje.");
        return false;
    }
    return true;
}
