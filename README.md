# 🌟 Spout Backend

## 📖 Overview
Spout Backend is a Django-based web application designed to manage user interactions, vendor information, and bookings. This project utilizes PostgreSQL as the database and includes various features such as user authentication, role management, and email notifications.

## 📚 Table of Contents
- [Features](#features)
- [Technologies](#technologies)
- [Installation](#installation)
- [Usage](#usage)
- [WebSocket Documentation](#websocket-documentation)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Features
- **User registration and authentication**
- **Role-based access control**
- **Vendor management**
- **Booking management**
- **Custom email backend for notifications**
- **API endpoints for CRUD operations**

## 🛠️ Technologies
- **Django**: 5.1.1
- **Django REST Framework**: 3.15.1
- **PostgreSQL**: Database
- **Whitenoise**: For serving static files
- **Python**: 3.x
- **Other Libraries**: See `requirements.txt` for a complete list of dependencies.

## 📦 Installation

### Prerequisites
- Python 3.x
- PostgreSQL
- pip (Python package installer)

### Steps
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set Up Environment Variables**:
   Create a `.env` file in the root directory and add the necessary environment variables. Example:
   ```plaintext
   SECRET_KEY=your_secret_key
   DEBUG=True
   DATABASE_URL=postgres://username:password@localhost:5433/postgres
   ALLOWED_HOSTS=localhost,127.0.0.1
   EMAIL_HOST=your_email_host
   EMAIL_PORT=your_email_port
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your_email_user
   EMAIL_HOST_PASSWORD=your_email_password
   ```

6. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

7. **Create a Superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the Development Server ASGI**:
   ```bash
   daphne server.asgi:application
   ```

9. **Run the Development Server ASGI with hot-reload**:
   ```bash
   python watch_and_reload.py
   ```

10. **Run the Development Server WSGI**:
   ```bash
   python manage.py runserver
   ```

## 🖥️ Usage
- Access the application at `http://127.0.0.1:8000/`.

## 🌐 WebSocket Documentation

### 📜 Overview
The WebSocket API allows real-time communication for chat functionalities within the application. Users can connect to a specific chat room and exchange messages in real-time.

### 🔗 Connection URL
To connect to the WebSocket, use the following URL format:
```
ws://<your-domain>/ws/chat/<customer_id>/
```
**Note:** The `customer_id` is used as the `room_name`. This ID is crucial when a user sends a message from WhatsApp, as the WhatsApp webhook will include this ID in its call to your Django application.

### 🔒 Authentication
Ensure that you include a valid JWT token in the `Authorization` header when establishing the WebSocket connection.

### 📩 Message Formats
#### Sending a Message
When sending a message, use the following JSON format:
```
{
    "message": "Your message here"
}
```

#### Receiving a Message
Messages received from the WebSocket will be in the following format:
```
{
    "message": "Message content",
    "timestamp": "2023-01-01T12:00:00Z"
}
```

### 📅 Events
- **Message:** Triggered when a new message is received in the chat room.
- **User Joined:** Triggered when a user joins the chat room.
- **User Left:** Triggered when a user leaves the chat room.

### 💻 Example Code Snippet
Here’s an example of how to connect to the WebSocket and send a message using JavaScript:
```
const roomName = "your_customer_id"; // Replace with your customer ID
const chatSocket = new WebSocket(`ws://<your-domain>/ws/chat/${roomName}/`);

chatSocket.onopen = function(e) {
    console.log("Connection established!");
};

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log("Message received:", data);
};

chatSocket.onclose = function(e) {
    console.error("Chat socket closed unexpectedly");
};

// Sending a message
chatSocket.send(JSON.stringify({
    message: "Hello, World!"
}));
```

### ⚠️ Error Handling
Errors are communicated through the following format:
```
{
    "error": "Error message"
}
```

## 📄 API Documentation
Refer to the API documentation for details on available endpoints and their usage. You can use tools like Postman or Swagger UI to interact with the API.

## 🤝 Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Make your changes and commit them (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Create a new Pull Request.

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.