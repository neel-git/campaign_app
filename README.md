# Practice Campaign Management Backend

## Overview

    A Django REST Framework and SQLAlchemy-based backend system for managing practices, users, and communication campaigns. The system supports role-based access control with three user types: Super Admin, Admin, and Practice User.

## Technology Stack

    - Python 3.11+
    - Django REST Framework
    - SQLAlchemy (ORM)
    - PostgreSQL
    - Alembic (for database migrations)
    - Session-based Authentication

## Architecture

The system follows a modular architecture with clear separation of concerns:

- **Authentication Module**: Handles user authentication, authorization, session management, role change and registration requests
- **Practice Management Module**: Manages practice-related operations
- **Campaign Module**: Handles communication campaign creation, scheduling, and delivery
- **Usermessage Module** : Handles message related operation for each user
- **Core Module**: Contains shared utilities

## Core Features

### User Authentication & Authorization

- Secure session-based authentication
- Role-based access control (Super Admin, Admin, Practice User)
- User registration with practice and role preference
- Password policies and security measures
- Approval and rejection of registration and role change requests

### Practice Management

- Practice creation and configuration
- Practice status management (Active/Inactive)

### Campaign Management

- Campaign creation and scheduling
- Support for immediate and scheduled delivery
- Campaign templates and customization
- Campaign analytics and reporting
- Multi-practice campaign support

### Messaging System

- Message inbox for each user
- Read status tracking
- Delete message operation
- Bulk message operations

## API Documentation

Our API provides comprehensive endpoints for:

- User Management
- Practice Operations
- Campaign Management
- Messaging Functions

### Installation & Setup

1. Installation & Setup

```bash
git clone [repository-url]
cd practice-management-backend

2. Create and activate virtual environment
  python -m venv venv
  source venv/bin/activate

3. Install dependencies
  pip install -r requirements.txt
```
