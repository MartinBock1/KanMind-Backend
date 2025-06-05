# Django project - KanMind backend

**KanMind** is a task management and collaboration platform designed for teams and individuals to manage tasks, track progress, and collaborate effectively. The platform includes features like task assignment, comment threads, role-based access control, and user authentication. It's designed with an easy-to-use REST API to manage all operations related to tasks, users, and boards.

## Features

- **User Authentication**: Register, log in, and manage user profiles with token-based authentication.
- **Boards**: Create boards and manage members. Tasks are organized within boards.
- **Tasks**: Create, update, and delete tasks. Tasks can be assigned to users and can have reviewers.
- **Comments**: Add comments to tasks for easy collaboration and feedback.
- **Permissions**: Custom permissions to ensure that only board members or owners can update tasks.
- **User Profiles**: Create and manage user profiles with additional information (bio, location, etc.).
  
## API Endpoints

### Authentication

- **POST `/api/auth/login/`**: Log in and get an authentication token.
- **POST `/api/auth/registration/`**: Register a new user.

### Boards

- **GET `/api/boards/`**: List all boards.
- **POST `/api/boards/`**: Create a new board.
- **GET `/api/boards/{id}/`**: Retrieve a specific board.
- **PATCH `/api/boards/{id}/`**: Update a board.
- **DELETE `/api/boards/{id}/`**: Delete a board.

### Tasks

- **GET `/api/tasks/`**: List all tasks across boards.
- **POST `/api/tasks/`**: Create a new task.
- **GET `/api/tasks/{task_id}/`**: Retrieve a specific task.
- **PATCH `/api/tasks/{task_id}/`**: Update a specific task.
- **DELETE `/api/tasks/{task_id}/`**: Delete a specific task.

### Comments

- **GET `/api/tasks/{task_id}/comments/`**: List all comments for a specific task.
- **POST `/api/tasks/{task_id}/comments/`**: Create a new comment for a task.
- **DELETE `/api/tasks/{task_id}/comments/{comment_id}/`**: Delete a specific comment.

## Authentication and Permissions

**knamind** uses token-based authentication with the `django-rest-framework` package to authenticate users. Users must register and log in to access any of the platform’s features.

Custom permissions are applied to ensure that:

- Only members of a board or the board owner can perform updates on tasks.
- Task assignment and reviewer selection are restricted to board members.
- User profiles and task data are securely managed.

## Setup

### Prerequisites

Before you get started, make sure you have the following installed:

- Python 3.8 or later
- Django 3.2 or later
- PostgreSQL or another compatible database

### Installation

1. Clone the repository:

   ```bash
   git clone <REPOSITORY-LINK>
   cd <projectfolder>
   
2. Set up a virtual environment:

    ```bash
    python -m venv env
    env/Scripts/activate  # Windows
    source env/bin/activate  # macOS/Linux
Note: On macOS/Linux, python3 may have to be used instead of python.

3. Install the dependencies:

    ```bash
    pip install -r requirements.txt

4. Set up the database:

    ```bash
    python manage.py migrate

5. Create a superuser (admin):

    ```bash
    python manage.py createsuperuser

6. Run the server:

    ```bash
    python manage.py runserver
Tip: If errors occur, check the `settings.py` for paths, database settings or forgotten `.env` files.

Now, you can access the application at http://localhost:8000.

Testing
You can run tests to ensure everything is working as expected:

bash
Kopieren
Bearbeiten
python manage.py test
License
This project is licensed under the MIT License - see the LICENSE file for details.

knamind is built using Django, Django REST Framework, and a PostgreSQL database. It's designed to streamline task and project management for teams, making collaboration more efficient and organized.

For more information or to contribute, feel free to open an issue or send a pull request!