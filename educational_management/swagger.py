from django.urls import path, include
from django.contrib import admin
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Educational Management  API",
        default_version="v1",
        description="""

        The educational_management Quiz System API provides a comprehensive platform for managing educational institutions, curriculum structures, quizzes, and quiz attempts. It supports global and local curriculum hierarchies, quiz question banks, quiz creation, student participation, teacher grading, and user enrollments. The API uses token-based authentication and integrates with a frontend application for seamless user interaction.

        ## System Overview
        - **Institution App**: Manages institutions, their curriculum structure, and user enrollments.
          - **Global Curriculum Entities**: Reusable components (`GlobalCurriculumTrack`, `GlobalStream`, `GlobalSubject`, `GlobalModule`, `GlobalUnit`, `GlobalLesson`, `GlobalMicroLesson`).
          - **Local Curriculum Entities**: Institution-specific (`InstitutionInfo`, `CurriculumTrack`, `Stream`, `Subject`, `Module`, `Unit`, `Lesson`, `MicroLesson`).
          - **Institution Types**: `pre_cadet`, `kindergarten`, `primary_school`, `high_school`, `higher_secondary`, `university`, `coaching`, `individual`, `others`.
          - **Enrollments**: Links students to `MicroLesson` and teachers to `Subject` for access and management.
        - **Quiz App**: Manages global quiz questions (`GlobalQuizQuestion`), quiz containers (`QuizContainer`), attempts (`QuizAttempt`), and responses (`QuizResponse`).
          - Questions are linked to global curriculum entities.
          - Quizzes are tied to local curriculum entities and reference global questions.

        ## Postman Workflow for Frontend Integration

        This section provides a serialized workflow for the frontend team to test the API using Postman or integrate with the frontend. It covers **Institution** (including enrollments) and **Quiz** APIs, ensuring clarity on authentication, ID fetching, and data creation. All endpoints assume the base URL is `http://localhost:8000/`. Use the `Authorization: Token <token>` header for authenticated requests.

        ### Prerequisites
        - **Base URL**: `http://localhost:8000`
        - **Authentication**:
          - Obtain tokens via `/auth/token/` (assumed implemented in `user_management.urls.authentication`).
          - Roles: Institution Admin (`is_institution=true`), Teacher (`is_teacher=true`), Student (`is_student=true`).
        - **Environment Variables**:
          - `institution_token`: Token for institution admin.
          - `teacher_token`: Token for teacher user.
          - `student_token`: Token for student user.
        - **Institution Setup**:
          - Create institution and curriculum entities via API or Django admin.
          - Ensure students and teachers are enrolled in relevant curriculum entities for quiz access.

        ### Authentication, Invitation, Admission WORKFLOW

        
        #### Authentication Workflow
        
        - **User Registration:**
          - `/auth/register/`:
            ```json
            // Email
            {
              "email": "user@example.com",
              "password": "SecurePass123!",
              "role": "user"
            }
            // Phone
            {
              "phone_number": "8801234567890",
              "password": "SecurePass123!",
              "role": "user"
            }
            // Institution
            {
              "phone_number": "8801234567890",
              "password": "SecurePass123!",
              "role": "institution"
            }
            ```
            - **Description**: Registers a user with role `institution` or `user`. Phone registration requires OTP verification. Returns user details, OTP (if phone), and tokens (after verification for phone).
            - **Logged in as**: None.
            - **Outcome**: Creates user, sets role flags, sends OTP for phone, returns details.
        - **OTP Verification:**
          - `/auth/verify-otp/`:
            ```json
            {
              "identifier": "8801234567890",
              "otp": "123456"
            }
            ```
            - **Description**: Verifies OTP to activate phone-registered user. Returns tokens.
            - **Logged in as**: None.
            - **Outcome**: Activates user, clears OTP, returns tokens.
        - **Forget Password:**
          - `/auth/forget-password/`:
            ```json
            {
              "email": "user@example.com"
            }
            // or
            {
              "phone_number": "8801234567890"
            }
            ```
            - **Description**: Sends OTP for password reset.
            - **Logged in as**: None.
            - **Outcome**: Sends OTP, returns success message.
        - **Reset Password:**
          - `/auth/reset-password/`:
            ```json
            {
              "email": "user@example.com",
              "otp": "123456",
              "new_password": "NewPass123!"
            }
            // or
            {
              "phone_number": "8801234567890",
              "otp": "123456",
              "new_password": "NewPass123!"
            }
            ```
            - **Description**: Resets password after OTP verification.
            - **Logged in as**: None.
            - **Outcome**: Resets password, returns success message.
        - **Change Password:**
          - `/auth/change-password/`:
            ```json
            {
              "old_password": "SecurePass123!",
              "new_password": "NewPass123!"
            }
            ```
            - **Description**: Changes password after verifying current password.
            - **Logged in as**: Authenticated user.
            - **Outcome**: Updates password, returns success message.
        - **User Role Information:**
          - `/auth/user-info/` (GET):
            ```json
            {
              "is_teacher": false,
              "is_student": false,
              "is_institution": false,
              "is_parents": false,
              "is_admission_seeker": true
            }
            ```
            - **Description**: Retrieves user role flags.
            - **Logged in as**: Authenticated user.
            - **Outcome**: Returns role flags.
            - **Success Response (200 OK)**:
              ```json
              {
                "is_teacher": false,
                "is_student": false,
                "is_institution": false,
                "is_parents": false,
                "is_admission_seeker": true
              }
              ```
        
        - **User Profile:**
          - `/auth/profile/`:
            ```json
            {
              "first_name": "John",
              "last_name": "Doe",
              "gender": "male",
              "birth_date": "1990-01-01",
              "profile_image": "<file>"
            }
            ```
            - **Description**: Creates (POST) or updates (PATCH) user profile. Required fields for creation.
            - **Logged in as**: Authenticated user.
            - **Outcome**: Saves profile, returns user details.
        - **User Existence Check:**
          - `/auth/users/check/`:
            ```json
            {
              "email": "user@example.com"
            }
            // or
            {
              "phone_number": "8801234567890"
            }
            ```
            - **Description**: Checks user existence by email or phone. Returns existence and active status.
            - **Logged in as**: None.
            - **Outcome**: Returns `{ "exists": true, "is_active": true }` or `{ "exists": false }`.
        
        - **Invitation:**
          - `/auth/invitations/`:
            ```json
            // Email
            {
              "email": "teacher@example.com",
              "role": "teacher"
            }
            // Phone
            {
              "phone_number": "8801234567890",
              "role": "teacher"
            }
            ```
            - **Description**: Creates invitation to join institution as teacher or student. Sends link via email or SMS.
            - **Logged in as**: Authenticated institution user.
            - **Outcome**: Creates invitation, sends link, returns details.
        - **Invitation Acceptance:**
          - `/auth/invitations/accept/`:
            ```json
            {
              "token": "550e8400-e29b-41d4-a716-446655440000"
            }
            ```
            - **Description**: Accepts invitation via API, assigns role and membership.
            - **Logged in as**: Authenticated user with matching email/phone.
            - **Outcome**: Creates membership, updates role flags, returns details.
        - **Admission Request:**
          - `/auth/admissions/`:
            ```json
            {
              "institution_id": "550e8400-e29b-41d4-a716-446655440000"
            }
            ```
            - **Description**: Creates admission request to join institution as student.
            - **Logged in as**: Authenticated user with `is_admission_seeker=true`.
            - **Outcome**: Creates request, returns details.
        - **Admission Approval:**
          - `/auth/admissions/<uuid:pk>/approve/`:
            ```json
            {}
            ```
            - **Description**: Approves admission request, assigns student role.
            - **Logged in as**: Authenticated institution admin.
            - **Outcome**: Updates request to approved, creates membership, sets `is_student=true`.
        - **Admission Rejection:**
          - `/auth/admissions/<uuid:pk>/reject/`:
            ```json
            {}
            ```
            - **Description**: Rejects admission request.
            - **Logged in as**: Authenticated institution admin.
            - **Outcome**: Updates request to rejected.
        - **Institution Requests:**
          - `/admission_seeker/institution-requests/` (GET):
            ```json
            []
            ```
            - **Description**: Lists invitations sent to the user.
            - **Logged in as**: Authenticated user.
            - **Outcome**: Returns list of invitations with institution details.
            - **Success Response (200 OK)**:
              ```json
              [{"institution": {"id": "550e8400-e29b-41d4-a716-446655440000", "name": "Example University"}, "role": "student", "status": "pending", "token": "550e8400-e29b-41d4-a716-446655440000", "created_at": "2025-01-01T00:00:00Z", "expires_at": "2025-01-08T00:00:00Z"}]
              ```
            - **Error Responses**:
              - **401 Unauthorized**: `{ "detail": "Authentication credentials were not provided." }`.
        - **Institution Approvals:**
          - `/admission_seeker/institution-approvals/` (GET):
            ```json
            []
            ```
            - **Description**: Lists users with invitations or admission requests for admin’s institution.
            - **Logged in as**: Authenticated institution admin.
            - **Outcome**: Returns list of users with request details.
            - **Success Response (200 OK)**:
              ```json
              [{"type": "invitation", "user": {"id": "550e8400-e29b-41d4-a716-446655440001", "email": "user@example.com", "first_name": "John", "last_name": "Doe"}, "status": "accepted", "role": "student", "created_at": "2025-01-01T00:00:00Z", "expires_at": "2025-01-08T00:00:00Z"}]
              ```
            - **Error Responses**:
              - **401 Unauthorized**: `{ "detail": "Authentication credentials were not provided." }`.
              - **403 Forbidden**: `{ "error": "Only institution admins can access this endpoint" }`.
              - **400 Bad Request**: `{ "error": "No institution found for this admin" }`.
        - **Parent-Child Relationship:**
          - `/auth/parent-child/`:
            ```json
            {
              "child_id": "550e8400-e29b-41d4-a716-446655440000"
            }
            ```
            - **Description**: Links parent to student child. Sets `is_parents=true` for parent.
            - **Logged in as**: Authenticated user (`is_institution=false`).
            - **Outcome**: Creates relationship, returns details.
            - **Success Response (201 Created)**:
              ```json
              {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "parent": "550e8400-e29b-41d4-a716-446655440001",
                "child": "550e8400-e29b-41d4-a716-446655440000"
              }
              ```
            - **Error Responses**:
              - **400 Bad Request**: Invalid `child_id`, non-student child, or institution parent.
              - **401 Unauthorized**: Missing/invalid token.
              - **404 Not Found**: Child not found.
        

        
        
        ### Institution API Workflow

        The institution API manages global and local curriculum entities, user enrollments, and educational hierarchies.

        #### 1. Register an Institution User
        - **Purpose**: Create a user with the `institution` role to act as the institution admin.
        - **Endpoint**: `POST /auth/register/`
        - **Authentication**: None (public endpoint).
        - **Request Body**:
          ```json
          {
            "phone_number": "8801234567890",
            "password": "SecurePass123!",
            "role": "institution"
          }
          ```
        - **Response** (201 Created):
          ```json
          {
            "id": "<user_id>",
            "phone_number": "8801234567890",
            "role": "institution",
            "otp": "123456",
            "is_active": false
          }
          ```
        - **Action**: Store `<user_id>` and note the OTP for verification.
        - **Frontend Note**: Display an OTP input field for verification.

        #### 2. Verify OTP for Institution User
        - **Purpose**: Activate the institution user account.
        - **Endpoint**: `POST /auth/verify-otp/`
        - **Authentication**: None.
        - **Request Body**:
          ```json
          {
            "identifier": "8801234567890",
            "otp": "123456"
          }
          ```
        - **Response** (200 OK):
          ```json
          {
            "access": "<institution_token>",
            "refresh": "<refresh_token>",
            "user": {
              "id": "<user_id>",
              "is_institution": true
            }
          }
          ```
        - **Action**: Store `<institution_token>` for authenticated requests.
        - **Frontend Note**: Redirect to institution creation page after OTP verification.

        #### 3. Create an Institution
        - **Purpose**: Create an educational institution.
        - **Prerequisite**: Valid `institution_type` values: `pre_cadet`, `kindergarten`, `primary_school`, `high_school`, `higher_secondary`, `university`, `coaching`, `individual`, `others`.
        - **Endpoint**: `POST /institution/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **Request Body**:
          ```json
          {
            "name": "Test School",
            "description": "A premier educational institution",
            "short_code": "TS001",
            "address": "123 Main St, City",
            "institution_type": "high_school",
            "admin": "<user_id>"
          }
          ```
        - **Response** (201 Created):
          ```json
          {
            "id": "<institution_id>",
            "name": "Test School",
            "description": "A premier educational institution",
            "short_code": "TS001",
            "address": "123 Main St, City",
            "institution_type": "high_school",
            "institution_type_display": "High School",
            "is_active": true,
            "admin": "<user_id>",
            "created_at": "2025-05-26T12:54:00+06:00",
            "updated_at": "2025-05-26T12:54:00+06:00"
          }
          ```
       
        - **Action**: Store `<institution_id>` for curriculum creation.
        - **Frontend Note**: Provide a form for institution details, ensuring `short_code` is unique.

        #### To get the institution info
        - **Purpose**: Retrieve the institution information.
        - **Endpoint**: `GET /institution/my-institution/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **Response** (200 OK):
          ```json
          {
            "id": "<institution_id>",
            "name": "Test School",
            "description": "A premier educational institution",
            "short_code": "TS001",
            "address": "123 Main St, City",
            "institution_type": "high_school",
            "institution_type_display": "High School",
            "is_active": true,
            "admin": "<user_id>",
            "created_at": "2025-05-26T12:54:00+06:00",
            "updated_at": "2025-05-26T12:54:00+06:00"
          }
        
        #### To get all the institutions that a Teacher or a Student has membership with
        - **Purpose**: Retrieve the institutions of the logged in teacher or student.
        - **Endpoint**: `GET auth/my-institution-memberships/`
        - **Authentication**: `Authorization: Token <teacher_token> or <student_token> ` 
        - **Response** (200 OK):
          ```json
          [
              {
                  "id": "1915f7ee-43bc-4eb1-b4d2-a7afaf6de25f",
                  "name": "Secret"
              },
              {
                  "id": "33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67",
                  "name": "Brac University"
              }
          ]
          ```
        
        #### 4. Create a Global Curriculum Track
        - **Purpose**: Create a global curriculum track (e.g., "Class 9").
        - **Endpoint**: `POST /institution/global-curriculum-tracks/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **Request Body**:
          ```json
          {
            "name": "Class 9",
            "description": "Ninth grade curriculum",
            "institution_type":"high_school",
            "is_active": true
          }
          ```
        - **Response** (201 Created):
          ```json
          {
            "id": "<global_curriculum_track_id>",
            "name": "Class 9",
            "description": "Ninth grade curriculum",
            "institution_type": "high_school",
            "institution_type_display": "High School",
            "is_active": true,
          }
          ```
        - **Action**: Store `<global_curriculum_track_id>` for local curriculum and question creation.
        - **Frontend Note**: Include in a curriculum setup wizard.

        #### 5. Create a Local Curriculum Track
        
        
        
        - **Purpose**: Create a local curriculum track linked to the institution and global track.
        - **Prerequisite**: Use `<global_curriculum_track_id>` from step 4. The `institution_info` is automatically set based on the authenticated admin.
        - **Endpoint**: `POST /institution/curriculum-tracks/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **Request Body**:
          ```json
          {
            "name": "<global_curriculum_track_id>"
          }
          ```
        - **Response** (201 Created):
          ```json
          {
            {
              "id": "8017b8b9-42bd-4605-ba34-9cbb4e68e8e7",
              "institution_info": "0bee8131-77a6-4937-8d90-da4bd51c6ac4",
              "name": "f5aefe6d-eea2-4765-b98b-e578a3b6ad66",
              "name_detail": "Class 9",
              "is_active": true,
              "order": 0
            }
          }
          ```
          
        - **GET THE ENROLLED CURRICULUM TRACKS**
        
        - **Endpoint**: `GET  institution/my-curriculum-tracks/`

        #### 5.1 Create a Section under a Local Curriculum Track
        - **Purpose**: Create a section under the local curriculum track.
        - **Endpoint**: `POST /institution/sections/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **Request Body**:
          ```json
          {
              "curriculum_track": "8017b8b9-42bd-4605-ba34-9cbb4e68e8e7",
              "name": "Section A"
          }
          ```
        - **Response** (201 Created):
          ```json
          {
              "id": "647ffc8c-3177-46ec-ac41-005b223f2f37",
              "curriculum_track": "8017b8b9-42bd-4605-ba34-9cbb4e68e8e7",
              "curriculum_track_name": "Class 9",
              "name": "Section A",
              "is_active": true,
              "order": 0
          }
          ```
          
        - **GET THE ENROLLED SECTIONS**
        
        - **Endpoint**: `GET  institution/my-sections/`

        #### 6. Create a Global Stream
        - **Purpose**: Create a global stream (e.g., "Science").
        - **Endpoint**: `POST /institution/global-streams/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **Request Body**:
          ```json
          {
            "name": "Science",
            "description": "Science stream for high school",
            "institution_type":"high_school"
          }
          ```
        - **Response** (201 Created):
          ```json
          {
              "id": "4d0ea95c-6c1e-4881-b207-2a3e017dd0aa",
              "name": "Science",
              "institution_type": "high_school",
              "institution_type_display": "High School",
              "is_active": true
          }
          ```
        - **Action**: Store `<global_stream_id>` for local stream creation.
        - **Frontend Note**: Allow stream definition in setup.

        #### 7. Create a Local Stream
        - **Purpose**: Create a local stream linked to the curriculum track.
        - **Prerequisite**: Use `<curriculum_track_id>` from step 5 and `<global_stream_id>` from step 6.
        - **Endpoint**: `POST /institution/streams/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **Request Body**:
          ```json
          {
            "curriculum_track": "<curriculum_track_id>",
            "section": "647ffc8c-3177-46ec-ac41-005b223f2f37",
            "name": "<global_stream_id>"
          }
          ```
        - **Response** (201 Created):
          ```json
          {
              "id": "4104a959-2f43-41d9-a721-21d586d5fa87",
              "curriculum_track": "8017b8b9-42bd-4605-ba34-9cbb4e68e8e7",
              "curriculum_track_name": "Class 9",
              "section": "647ffc8c-3177-46ec-ac41-005b223f2f37",
              "section_name": "Section A",
              "name": "4d0ea95c-6c1e-4881-b207-2a3e017dd0aa",
              "name_detail": "Science",
              "is_active": true,
              "order": 0
          }
          ```
        - **Action**: Store `<stream_id>` for subject creation.
        - **Frontend Note**: Link streams to curriculum tracks in UI.

        #### 8. Create Global and Local Entities (Subject, Module, Unit, Lesson, MicroLesson)
        - **Purpose**: Set up the remaining curriculum hierarchy.
        - **Endpoints**:
          - `POST /institution/global-subjects/` → `<global_subject_id>`
          - `POST /institution/subjects/` → `<subject_id>`
          - `POST /institution/global-modules/` → `<global_module_id>`
          - `POST /institution/modules/` → `<module_id>`
          - `POST /institution/global-units/` → `<global_unit_id>`
          - `POST /institution/units/` → `<unit_id>`
          - `POST /institution/global-lessons/` → `<global_lesson_id>`
          - `POST /institution/lessons/` → `<lesson_id>`
          - `POST /institution/global-micro-lessons/` → `<global_micro_lesson_id>`
          - `POST /institution/micro-lessons/` → `<micro_lesson_id>`
        - **Example (Global Subject)**:
          - **Request**: `POST /institution/global-subjects/`
            ```json
            {
              "name": "Mathematics",
              "description": "Mathematics for Class 9",
              "code": "MTH101",
              "institution_type":"high_school"
            }
            ```
          - **Response**:
            ```json
            {
                "id": "96f47a8f-fde5-4b90-ab27-59676d732844",
                "name": "Mathematics",
                "code": "MTH101",
                "institution_type": "high_school",
                "institution_type_display": "High School",
                "is_active": true
            }
            ```
        - **Example (Local Subject)**:
        
          - **GET Local Subject Data under a Stream**
    
          - **Endpoint**: `GET /institution/subjects/?streams=<local_stream_id>`
        
          - **Request**: `POST /institution/subjects/`
            ```json
            {
              "stream": "<stream_id>",
              "name": "<global_subject_id>"
            }
            ```
          - **Response**:
            ```json
            {
                "id": "00268557-6e03-4233-95a8-3e82f54d7883",
                "stream": "02ca80f8-6be9-412f-9792-71adf929b3c4",
                "stream_name": "Science",
                "name": "96f47a8f-fde5-4b90-ab27-59676d732844",
                "name_detail": "Mathematics",
                "is_active": true,
                "order": 0
            }
            ```
        
        - **GET THE ENROLLED SUBJECTS**
        
        - **Endpoint**: `GET  institution/my-subjects/`
        
        - **Example (Global Module)**:
          - **Request**: `POST /institution/global-modules/`
            ```json
            {
              "title": "Differential Calculus",
              "description": "Calculus module",
              "institution_type": "high_school"
            }
            ```
          - **Response**:
            ```json
            {
                "id": "f58ab497-a0fe-4bec-bd60-40f0435647a1",
                "title": "Differential Calculus",
                "institution_type": "high_school",
                "institution_type_display": "High School",
                "is_active": true
            }
            ```
        - **Example (Local Module)**:

          - **GET Local Module Data under a Subject**
          
          - **Endpoint**: `GET /institution/modules/?subjects=<local_subject_id>`
          
          - **Request**: `POST /institution/modules/?institution_id=33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67` FOR TEACHERS
          - **Request**: `POST /institution/modules/` FOR INSTITUTION ADMIN
            ```json
            {
              "subject": "<subject_id>",
              "title": "<global_module_id>"
            }
            ```
          - **Response**:
            ```json
            {
                "id": "bdaa09d1-3e78-43d9-8eaa-03f2b4dfbd58",
                "subject": "00268557-6e03-4233-95a8-3e82f54d7883",
                "subject_name": "Mathematics",
                "title": "f58ab497-a0fe-4bec-bd60-40f0435647a1",
                "title_detail": "Differential Calculus",
                "is_active": true,
                "order": 0
            }
            ```
        
        
        
        - **Example (Global Unit)**:
          - **Request**: `POST /institution/global-units/`
            ```json
            {
              "title": "Limits",
              "description": "Unit on limits",
              "institution_type": "high_school"
            }
            ```
          - **Response**:
            ```json
            {
                "id": "57014168-dcf6-484a-8856-a7bef20bae9e",
                "title": "What is Limit",
                "institution_type": "high_school",
                "institution_type_display": "High School",
                "is_active": true
            }
            ```
        - **Example (Local Unit)**:
        
          - **GET Local Unit Data under a Module**
          
          - **Endpoint**: `GET /institution/units/?modules=<local_module_id>`
          
          - **Request**: `POST /institution/units/` FOR TEACHERS
          - **Request**: `POST /institution/units/?institution_id=33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67` FOR INSTITUTION ADMIN

            ```json
            {
              "module": "<module_id>",
              "title": "<global_unit_id>"
            }
            ```
          - **Response**:
            ```json
            {
                "id": "530c76ff-1821-4bcf-8a9a-d0fa91e23144",
                "module": "bdaa09d1-3e78-43d9-8eaa-03f2b4dfbd58",
                "module_title": "Differential Calculus",
                "title": "57014168-dcf6-484a-8856-a7bef20bae9e",
                "title_detail": "What is Limit",
                "is_active": true,
                "order": 0
            }
            ```
            
        
        
        
        - **Example (Global Lesson)**:
          - **Request**: `POST /institution/global-lessons/`
            ```json
            {
              "title": "What is a Limit?",
              "description": "Lesson on limits",
              "institution_type": "high_school"
            }
            ```
          - **Response**:
            ```json
            {
                "id": "c1f8b2d3-4e5f-4a6b-8c9d-0e1f2a3b4c5d",
                "title": "What is a Limit?",
                "institution_type": "high_school",
                "institution_type_display": "High School",
                "is_active": true
            }
            ```
        - **Example (Local Lesson)**:
        
          - **GET Local Lesson Data under a Unit**
          
          - **Endpoint**: `GET /institution/lessons/?units=<local_unit_id>`
          
          - **Request**: `POST /institution/lessons/`FOR INSTITUTION ADMIN
          - **Request**: `POST /institution/lessons/?institution_id=33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67` FOR TEACHERS
            ```json
            {
              "unit": "<unit_id>",
              "title": "<global_lesson_id>"
            }
            ```
          - **Response**:
            ```json
            {
                "id": "b54b6467-12b0-4c40-a1df-bc1290a2b81d",
                "unit": "530c76ff-1821-4bcf-8a9a-d0fa91e23144",
                "unit_title": "What is Limit",
                "title": "916c471b-ff55-4524-a3e1-df7c459184c4",
                "title_detail": "What is a Limit?",
                "is_active": true,
                "order": 0
            }
            ```
        
        
        
        - **Example (Global Micro Lesson)**:
          - **Request**: `POST /institution/global-micro-lessons/`
            ```json
            {
              "title": "Chain Rule",
              "content_type": "quiz",
              "content": "Introduction to chain rule"
            }
            ```
          - **Response**:
            ```json
            {
                "id": "c0523663-03e6-4cf5-8cb6-9bd875940dc4",
                "title": "Chain Rule",
                "content_type": "quiz",
                "institution_type": "high_school",
                "institution_type_display": "High School",
                "is_active": true
            }
            ```
        - **Example (Local Micro Lesson)**:
        
          - **GET Local Micro Lesson Data under a Module**
          
          - **Endpoint**: `GET /institution/micro-lessons/?lessons=<local_lesson_id>`
        
          - **Request**: `POST /institution/micro-lessons/` FOR INSTITUTION ADMIN
          - **Request**: `POST /institution/micro-lessons/?institution_id=33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67` FOR TEACHERS
            ```json
            {
              "lesson": "<lesson_id>",
              "title": "<global_micro_lesson_id>"
            }
            ```
          - **Response**:
            ```json
            {
                "id": "92b849fa-1974-4364-9c72-b09c2b97cd17",
                "lesson": "b54b6467-12b0-4c40-a1df-bc1290a2b81d",
                "lesson_title": "What is a Limit?",
                "title": "c0523663-03e6-4cf5-8cb6-9bd875940dc4",
                "title_detail": "Chain Rule",
                "is_active": true,
                "order": 0
            }
            ```
        
        
  

        #### 9. Register a Teacher User
        - **Purpose**: Create a teacher to manage quizzes and content.
        - **Endpoint**: `POST /auth/register/`
        - **Authentication**: None.
        - **Request Body**:
          ```json
          {
            "email": "teacher@example.com",
            "password": "SecurePass123!",
            "role": "user"
          }
          ```
        - **Response** (201 Created):
          ```json
          {
            "id": "<teacher_id>",
            "email": "teacher@example.com",
            "role": "user",
            "is_active": true,
            "access": "<teacher_token>",
            "refresh": "<refresh_token>"
          }
          ```
        - **Action**: Store `<teacher_id>` and `<teacher_token>` for invitation and enrollment.

        #### 10. Invite Teacher to Institution
        - **Purpose**: Invite the teacher to join the institution.
        - **Endpoint**: `POST /auth/invitations/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **Request Body**:
          ```json
          {
            "email": "teacher@example.com",
            "role": "teacher"
          }
          ```
        - **Response** (201 Created):
          ```json
          {
            "id": "<invitation_id>",
            "email": "teacher@example.com",
            "role": "teacher",
            "token": "<invitation_token>",
            "status": "pending"
          }
          ```
        - **Action**: Store `<invitation_token>` for acceptance.

        #### 11. Accept Teacher Invitation
        - **Purpose**: Teacher joins the institution.
        - **Endpoint**: `POST /auth/invitations/accept/`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Request Body**:
          ```json
          {
            "token": "<invitation_token>"
          }
          ```
        - **Response** (200 OK):
          ```json
          {
            "id": "<invitation_id>",
            "status": "accepted",
            "role": "teacher",
            "institution": "<institution_id>"
          }
          ```
        - **Action**: Teacher is now `is_teacher=true` and can be enrolled in subjects.

        #### 12. Register and Invite Students
        - **Purpose**: Create and invite students to the institution.
        - **Endpoints**: `POST /auth/register/`, `POST /auth/invitations/`, `POST /auth/invitations/accept/`
        - **Example (Register)**:
          ```json
          {
            "email": "student@example.com",
            "password": "SecurePass123!",
            "role": "user"
          }
          ```
        - **Response** (201 Created):
          ```json
          {
            "id": "<student_id>",
            "email": "student@example.com",
            "role": "user",
            "is_active": true,
            "access": "<student_token>",
            "refresh": "<refresh_token>"
          }
          ```
        - **Action**: Store `<student_id>` and `<student_token>`. Invite and accept as in steps 10-11, setting `role: "student"`. Student is now `is_student=true` and can be enrolled in micro-lessons.
        - **Frontend Note**: Prompt admin to enroll students in `MicroLesson` after invitation acceptance.

        #### 13. Enroll a Teacher in a Subject
        - **Purpose**: Assign a teacher to a specific `Subject` to allow them to manage quizzes and content.
        - **Prerequisite**: Use `<teacher_id>` from step 9 and `<subject_id>` from step 8. Teacher must have `is_teacher=true` and be part of the institution.
        - **Endpoint**: `POST /institution/teacher-enrollments/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **Request Body**:
          ```json
          {
  
            "user": "b50c9476-5cbd-45e3-b779-1b4b777df60f",
            "curriculum_track":["8017b8b9-42bd-4605-ba34-9cbb4e68e8e7"],
            "subjects": ["00268557-6e03-4233-95a8-3e82f54d7883"],
            "section":["647ffc8c-3177-46ec-ac41-005b223f2f37"]
          }
          ```
        
        - **Response** (201 Created):
          ```json
          {
              "id": "6f0a0356-20b5-4e15-9c46-8bd49861e5e3",
              "user": "b50c9476-5cbd-45e3-b779-1b4b777df60f",
              "curriculum_track": [
                  "8017b8b9-42bd-4605-ba34-9cbb4e68e8e7"
              ],
              "section": [
                  "647ffc8c-3177-46ec-ac41-005b223f2f37"
              ],
              "subjects": [
                  "00268557-6e03-4233-95a8-3e82f54d7883"
              ],
              "is_active": true
          }
          ```
        
        #### Update the Teacher Enrollment
        - **Purpose**: Update a teacher to a specific `Subject` or `Curriculum Track` to allow them to manage quizzes and content.
        - **Prerequisite**: Use and `<subject_id>` from step 8. Teacher must have `is_teacher=true` and be part of the institution.
        - **Endpoint**: `PATCH /institution/teacher-enrollments/<teacher_enrollment_id>/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **Request Body**:
          ```json
          {
            "curriculum_track": "[<new_curriculum_track_id>]",
            "subjects": "[<new_subject_id>]",
            "section:" "[<new_section_id>]",
          }
        #### 14. Enroll a Student in a Curriculum Track, Section
        - **Purpose**: Enroll a student in a specific `Curriculum Track` to grant access to associated things.
        - **Prerequisite**: Use `<student_id>` from step 12 and `curriculum id` from step 5. Student must have `is_student=true` and be part of the institution.
        - **Endpoint**: `POST /institution/student-enrollments/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **Request Body**:
          ```json
          {
              "user": "20279304-b387-44e9-81de-561e411c3d9d",
              "curriculum_track":"8017b8b9-42bd-4605-ba34-9cbb4e68e8e7",
              "section":"647ffc8c-3177-46ec-ac41-005b223f2f37"
          }
          ```
        - **Response** (201 Created):
          ```json
          {
              "id": "3b0401b6-f691-4dfa-b914-5b49551797b9",
              "user": "20279304-b387-44e9-81de-561e411c3d9d",
              "curriculum_track": "8017b8b9-42bd-4605-ba34-9cbb4e68e8e7",
              "section": "647ffc8c-3177-46ec-ac41-005b223f2f37",
              "is_active": true
          }
          ```
        - **GET ALL THE ENROLLED STUDENTS IN A SECTION**
        
        - **Endpoint**: `GET /institution/student-enrollments/by-section/?section_id=<section_id>`
        
        
        #### Update the Student Enrollment
        - **Purpose**: Update a student to a specific `Curriculum Track` to allow them to attend quizzes and content.
        - **Prerequisite**: Use `<student_id>` from step 12 and `curriculum id` from step 5. Student must have `is_student=true` and be part of the institution.
        - **Endpoint**: `PATCH /institution/student-enrollments/<student_enrollment_id>/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **Request Body**:
          ```json
          {
            "curriculum_track": "<new_curriculum_track_id>"
          }
          
          
          
        ### Attendance API Workflow
        The attendance API manages student attendance records for the educational_management Attendance System, aligned with the provided models, serializers, views, and URLs.
        
        #### GET Request REQUIREMENTS:
        - **GET THE ENROLLED CURRICULUM TRACKS OF THE TEACHER**
        
        - **Endpoint**: `GET  /institution/my-curriculum-tracks/`
        
        - **GET THE ENROLLED SECTIONS  OF THE TEACHER**
        
        - **Endpoint**: `GET  /institution/my-sections/`
        
        - **GET THE ENROLLED SUBJECTS OF THE TEACHER BY INSTITUTION ID**
        
        - **Endpoint**: `GET  /institution/my-subjects/by-institution/?institution_id=1915f7ee-43bc-4eb1-b4d2-a7afaf6de25f`
        
        - **GET THE ENROLLED SUBJECTS OF THE TEACHER
        
        - **Endpoint**: `GET  /institution/my-subjects/`
        
        - **GET ALL THE ENROLLED STUDENTS IN A SECTION**
        
        - **Endpoint**: `GET /institution/student-enrollments/by-section/?section_id=<section_id>`
        
        #### 14. Bulk Student Attendance
        - **Purpose**: Record attendance for a student in a specific `Section and Subject`.
        - **Prerequisite**: Use `section id, student id and subject id` 
        - **Endpoint**: `POST /attendance/bulk/`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **status**: `present` or `absent` or `late` or `excused`
        
        - **Request Body**:
          ```json
          {
            "institution": "0bee8131-77a6-4937-8d90-da4bd51c6ac4",
            "attendances": [
              {"student_id": "b7a08fbd-cbc5-4a17-8bf2-91e28bd73167", "status": "present"},
              {"student_id": "20279304-b387-44e9-81de-561e411c3d9d", "status": "absent"}
            ],
            "section": "647ffc8c-3177-46ec-ac41-005b223f2f37",
            "subject": "00268557-6e03-4233-95a8-3e82f54d7883",
            "date": "2025-05-26"  YYYY-MM-DD format
          }
          ```
        
        ### GET The attendance data as a Teacher
        
        - **Endpoint**: `GET /attendance/?date=2025-07-05&section_id=<uuid>`
        
        ### GET The attendance statistics as a Teacher to see the Present and Absent days
        - **Endpoint**: `GET /attendance/statistics/?section_id=647ffc8c-3177-46ec-ac41-005b223f2f37&subject_id=00268557-6e03-4233-95a8-3e82f54d7883`
        - **Response** (200 OK):
          ```json
          [
              {
                  "student_id": "b7a08fbd-cbc5-4a17-8bf2-91e28bd73167",
                  "student_name": Murney,
                  "section_name": "Section A",
                  "subject_name": "96f47a8f-fde5-4b90-ab27-59676d732844",
                  "present_count": 1,
                  "absent_count": 0,
                  "late_count": 0,
                  "excused_count": 0
              },
              {
                  "student_id": "20279304-b387-44e9-81de-561e411c3d9d",
                  "student_name": "Miso",
                  "section_name": "Section A",
                  "subject_name": "96f47a8f-fde5-4b90-ab27-59676d732844",
                  "present_count": 1,
                  "absent_count": 1,
                  "late_count": 0,
                  "excused_count": 0
              }
          ]
          ```
        
        
        ### GET The attendance data as a Student  
        - **Endpoint**: `GET /attendance/`
        
        ### GET The attendance statistics as a Student to see the Present and Absent days
        
        - **Endpoint**: `GET /attendance/statistics/`
        - **Response** (200 OK):
          ```json
          [
              {
                  "student_id": "20279304-b387-44e9-81de-561e411c3d9d",
                  "student_name": "Walid Robi",
                  "section_name": "Section A",
                  "subject_name": "96f47a8f-fde5-4b90-ab27-59676d732844",
                  "present_count": 1,
                  "absent_count": 1,
                  "late_count": 0,
                  "excused_count": 0
              }
          ]
          ```

        
        ### Single Student Attendance Creation(Not Recommended)
        - **Purpose**: Record attendance for a single student in a specific `Section and Subject`.
        - **Prerequisite**: Use `section id, student id and subject id` 
        - **Endpoint**: `POST /attendance/`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Request Body**:
          ```json

          {
            "institution": "<uuid>",
            "student": "<uuid>",
            "section": "<uuid>",
            "subject": "<uuid>",
            "date": "2025-07-05",
            "status": "present"
          }
          ```
          
        
        ### Quiz API Workflow

        The quiz API manages global questions, quiz containers, attempts, and grading for the educational_management Quiz System, aligned with the provided models, serializers, views, and URLs.

        #### 15. Create a Global Quiz Question (MCQ)
        - **Purpose**: Add an MCQ question to the global question pool.
        - **Prerequisite**: Use **global curriculum IDs** from steps 4, 6, 8 (e.g., `<global_curriculum_track_id>`, `<global_stream_id>`, `<global_subject_id>`, `<global_module_id>`, `<global_unit_id>`, `<global_lesson_id>`, `<global_micro_lesson_id>`). Teacher must be enrolled in the relevant subject (step 13).
        - **Endpoint**: `POST /quiz/questions/`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Request Body**:
          ```json
          {
            "curriculum_track": "<global_curriculum_track_id>",
            "stream": "<global_stream_id>",
            "subject": "<global_subject_id>",
            "module": "<global_module_id>",
            "unit": "<global_unit_id>",
            "lesson": "<global_lesson_id>",
            "micro_lesson": "<global_micro_lesson_id>",
            "question_type": "mcq",
            "text": "What is the derivative of x^2?",
            "image_url": "https://example.com/derivative.jpg",
            "marks": 2.0,
            "status": "draft",
            "options": [
              {"label": "a", "text": "2x", "is_correct": true},
              {"label": "b", "text": "x", "is_correct": false},
              {"label": "c", "text": "x^3", "is_correct": false},
              {"label": "d", "text": "2", "is_correct": false}
            ]
          }
          ```
        - **Response** (201 Created):
          ```json
          {
            "id": "<question_id_1>",
            "curriculum_track": "<global_curriculum_track_id>",
            "stream": "<global_stream_id>",
            "subject": "<global_subject_id>",
            "module": "<global_module_id>",
            "unit": "<global_unit_id>",
            "lesson": "<global_lesson_id>",
            "micro_lesson": "<global_micro_lesson_id>",
            "question_type": "mcq",
            "text": "What is the derivative of x^2?",
            "image_url": "https://example.com/derivative.jpg",
            "marks": 2.0,
            "status": "draft",
            "options": [
              {"id": "<option_id_1>", "label": "a", "text": "2x"},
              {"id": "<option_id_2>", "label": "b", "text": "x"},
              {"id": "<option_id_3>", "label": "c", "text": "x^3"},
              {"id": "<option_id_4>", "label": "d", "text": "2"}
            ],
            "created_at": "2025-05-26T22:07:00+06:00",
            "updated_at": "2025-05-26T22:07:00+06:00"
          }
          ```
        - **Action**: Store `<question_id_1>` for quiz creation. Update `status` to `published` via `PUT /quiz/questions/<question_id_1>/` when ready.

        #### 16. Create a Global Quiz Question (Short Answer)
        - **Purpose**: Add a short answer question to the global question pool.
        - **Endpoint**: `POST /quiz/questions/`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Request Body**:
          ```json
          {
            "curriculum_track": "<global_curriculum_track_id>",
            "stream": "<global_stream_id>",
            "subject": "<global_subject_id>",
            "module": "<global_module_id>",
            "unit": "<global_unit_id>",
            "lesson": "<global_lesson_id>",
            "micro_lesson": "<global_micro_lesson_id>",
            "question_type": "short",
            "text": "Explain the concept of a limit in calculus.",
            "marks": 5.0,
            "status": "draft"
          }
          ```
        - **Response** (201 Created):
          ```json
          {
            "id": "<question_id_2>",
            "curriculum_track": "<global_curriculum_track_id>",
            "stream": "<global_stream_id>",
            "subject": "<global_subject_id>",
            "module": "<global_module_id>",
            "unit": "<global_unit_id>",
            "lesson": "<global_lesson_id>",
            "micro_lesson": "<global_micro_lesson_id>",
            "question_type": "short",
            "text": "Explain the concept of a limit in calculus.",
            "image_url": null,
            "marks": 5.0,
            "status": "draft",
            "options": [],
            "created_at": "2025-05-26T22:07:00+06:00",
            "updated_at": "2025-05-26T22:07:00+06:00"
          }
          ```
        - **Action**: Store `<question_id_2>` for quiz creation. Update `status` to `published` when finalized.

        #### 17. Filter Questions by Global Micro-Lesson
        - **Purpose**: Retrieve questions for a global micro-lesson.
        - **Endpoint**: `GET /quiz/questions/?global_micro_lesson_id=<global_micro_lesson_id>`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Response** (200 OK):
          ```json
          [
            {
              "id": "<question_id_1>",
              "question_type": "mcq",
              "text": "What is the derivative of x^2?",
              "marks": 2.0,
              "options": [
                {"id": "<option_id_1>", "label": "A", "text": "2x"},
                {"id": "<option_id_2>", "label": "B", "text": "x"},
                {"id": "<option_id_3>", "label": "C", "text": "x^3"},
                {"id": "<option_id>", "label": "4", "text": "D"}
              ],
              "created_at": "2025-05-26T22:22:00+06:00",
              "updated_at": "2025-05-26T22:22:00+06:00"
            },
            {
              "id": "<question_id_2>",
              "question_type": "short",
              "text": "Explain the concept of a limit in calculus.",
              "marks": 5.0,
              "options": [],
              "created_at": "2025-05-26T22:22:00+06:00",
              "updated_at": "2025-05-26T22:22:00+06:00"
            }
          ]
          ```
        - **Action**: Confirm `<question_id_1>` and `<question_id_2>` for quiz creation.

        #### 18. Create a Quiz Container
        - **Purpose**: Create a quiz with selected questions.
        - **Prerequisite**: Use **local curriculum IDs** from steps 5, 7, 8 (e.g., `<curriculum_track_id>`, `<stream_id>`, `<subject_id>`, `<module_id>`, `<unit_id>`, `<lesson_id>`, `<micro_lesson_id>`) and `<question_id_1>`, `<question_id_2>` from steps 15-16. Teacher must be enrolled in the subject (step 13).
        - **Endpoint**: `POST /quiz/`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Request Body**:
        
        - **NOTE:** You can put even the lesson, micro lesson, unit, module or you can opt out of it by not giving anything. These are not mandatory.
          ```json
          {
            "title": "Math Quiz 1",
            "curriculum_track_id": "8017b8b9-42bd-4605-ba34-9cbb4e68e8e7",
            "section_id": "647ffc8c-3177-46ec-ac41-005b223f2f37",
            "stream_id": "02ca80f8-6be9-412f-9792-71adf929b3c4",
            "subject_id": "00268557-6e03-4233-95a8-3e82f54d7883",
            "start_time": "2025-05-27T10:00:00Z",
            "end_time": "2025-05-27T12:00:00Z",
            "timer_per_question": 60,
            "enable_negative_marking": true,
            "negative_marks": 0.25,
            "status": "published",
            "is_free": true,
            "is_active": true,
            "order": 1,
            "question_ids": [
              "945fe7ee-f7a9-4f68-95ed-d40c9f774f95",
              "265da0bc-4f71-49d1-9a7b-e78f672e293e"
            ]
          }
          ```
          
        - **Response** (201 Created):
          ```json
          {
              "id": "0d4e6dc1-b676-49cc-9e58-07a6306517cf",
              "title": "Math Quiz 1",
              "curriculum_track_id": "8017b8b9-42bd-4605-ba34-9cbb4e68e8e7",
              "section_id": "647ffc8c-3177-46ec-ac41-005b223f2f37",
              "stream_id": "02ca80f8-6be9-412f-9792-71adf929b3c4",
              "subject_id": "00268557-6e03-4233-95a8-3e82f54d7883",
              "module_id": null,
              "unit_id": null,
              "lesson_id": null,
              "micro_lesson_id": null,
              "start_time": "2025-05-27T10:00:00Z",
              "end_time": "2025-05-27T12:00:00Z",
              "timer_per_question": 60,
              "enable_negative_marking": true,
              "negative_marks": 0.25,
              "status": "published",
              "is_free": true,
              "is_active": true,
              "order": 1,
              "question_ids": [
                  "265da0bc-4f71-49d1-9a7b-e78f672e293e",
                  "945fe7ee-f7a9-4f68-95ed-d40c9f774f95"
              ]
          }
          ```
        - **Action**: Store `<quiz_id>` for student attempts.

        #### 19. List Quizzes (Student)
        - **Purpose**: Display available quizzes for enrolled students.
        - **Prerequisite**: Student must be enrolled in the relevant `CurriculumTrack` (step 14).
        - **Endpoint**: `GET /quiz/`
        - **Authentication**: `Authorization: Token <student_token>`
        - **Response** (200 OK):
          ```json
          [
            {
              "id": "<quiz_id>",
              "title": "Calculus Quiz",
              "curriculum_track": {
                "id": "<curriculum_track_id>",
                "institution_info": "<institution_id>",
                "name": "<global_curriculum_track_id>",
                "name_detail": {"name": "Class 9"}
              },
              "stream": {
                "id": "<stream_id>",
                "name": "<global_stream_id>",
                "name_detail": {"name": "Science"}
              },
              "subject": {
                "id": "<subject_id>",
                "name": "<global_subject_id>",
                "name_detail": {"name": "Mathematics"}
              },
              "module": {
                "id": "<module_id>",
                "title": "<global_module_id>",
                "title_detail": {"title": "Differential Calculus"}
              },
              "unit": {
                "id": "<unit_id>",
                "title": "<global_unit_id>",
                "title_detail": {"title": "Limits"}
              },
              "lesson": {
                "id": "<lesson_id>",
                "title": "<global_lesson_id>",
                "title_detail": {"title": "Introduction to Limits"}
              },
              "micro_lesson": {
                "id": "<micro_lesson_id>",
                "title": "<global_micro_lesson_id>",
                "title_detail": {"title": "Limit Concepts"}
              },
              "start_time": "2025-06-01T15:00:00+06:00",
              "end_time": "2025-06-01T16:00:00+06:00",
              "is_active": true,
              "status": "published",
              "is_free": true
            }
          ]
          ```
        - **Action**: Use `<quiz_id>` to start the quiz attempt.
        #### 20. Start a Quiz
        - **Purpose**: Initiate a quiz start an enrolled student
        - **Prerequisite**: Student must be enrolled in the relevant `CurriculumTrack` (step 14).
        - **Endpoint**: `POST /quiz/<quiz_id>/start/`
        - **Authentication**: `Authorization: Token <student_token>`
        - **Request Body**:
          ```json
          { 
            
          }
          
      
        #### 21.Get Quiz Attempt
        - **Purpose**: Initiate a quiz attempt for an enrolled student.
        - **Endpoint**: `GET /quiz/attempts/
        - **Authentication**: `Authorization: Token <student_token>`
        - **Action**: Store `<attempt_id>` for answer submission.
        
        #### 22. Submit Quiz Attempt
        - **Purpose**: Submit the quiz attempt for grading.
        - **Endpoint**: `POST /quiz/<quiz_attempt_id>/submit/`
        - **Authentication**: `Authorization: Token <student_token>`
        - **Request Body**:
          ```json
          {
            "attempt_id": "62afdac0-d5fe-4944-9e7f-346248327608",
            "answers": [
              {
                "question_id": "945fe7ee-f7a9-4f68-95ed-d40c9f774f95",
                "selected_option": "a"
              },
              {
                "question_id": "265da0bc-4f71-49d1-9a7b-e78f672e293e",
                "short_answer": "Paris is the capital due to its historical and cultural significance."
              }
            ]
          }
          ```
          
        #### 23 Get Quiz Questions
        - **Purpose**: Fetch questions for the quiz attempt.
        - **Endpoint**: `GET /quiz/<quiz_id>/questions/`
        - **Authentication**: `Authorization: Token <student_token>`
        - **Response** (200 OK):
          ```json
          [
            {
                "id": "265da0bc-4f71-49d1-9a7b-e78f672e293e",
                "curriculum_track": "f5aefe6d-eea2-4765-b98b-e578a3b6ad66",
                "stream": "4d0ea95c-6c1e-4881-b207-2a3e017dd0aa",
                "subject": "96f47a8f-fde5-4b90-ab27-59676d732844",
                "module": "f58ab497-a0fe-4bec-bd60-40f0435647a1",
                "unit": "57014168-dcf6-484a-8856-a7bef20bae9e",
                "lesson": null,
                "micro_lesson": null,
                "question_type": "short",
                "text": "Explain why Paris is the capital of France.",
                "image_url": null,
                "marks": 2.0,
                "status": "published",
                "options": []
            },
            {
                "id": "945fe7ee-f7a9-4f68-95ed-d40c9f774f95",
                "curriculum_track": "f5aefe6d-eea2-4765-b98b-e578a3b6ad66",
                "stream": "4d0ea95c-6c1e-4881-b207-2a3e017dd0aa",
                "subject": "96f47a8f-fde5-4b90-ab27-59676d732844",
                "module": "f58ab497-a0fe-4bec-bd60-40f0435647a1",
                "unit": "57014168-dcf6-484a-8856-a7bef20bae9e",
                "lesson": null,
                "micro_lesson": null,
                "question_type": "mcq",
                "text": "What is the capital of France?",
                "image_url": null,
                "marks": 1.0,
                "status": "published",
                "options": [
                    {
                        "id": "830b797f-20e3-4235-b072-294e6b220028",
                        "label": "a",
                        "text": "Paris"
                    },
                    {
                        "id": "cc13529b-1346-413e-bb7a-f7491b87780b",
                        "label": "b",
                        "text": "London"
                    },
                    {
                        "id": "5d32984f-1856-488a-9e01-3a723b9c015c",
                        "label": "c",
                        "text": "Berlin"
                    },
                    {
                        "id": "56d83f6c-a6d0-4eb6-b591-d6322c327936",
                        "label": "d",
                        "text": "Madrid"
                    }
                ]
            }
        ]
          ```
        

        #### 24 List Quiz Attempts (Teacher)
        - **Purpose**: Retrieve attempts for review by an enrolled teacher.
        - **Endpoint**: `GET /quiz/attempts/`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Response** (200 OK):
          ```json
          [
              {
                  "id": "62afdac0-d5fe-4944-9e7f-346248327608",
                  "quiz": "0d4e6dc1-b676-49cc-9e58-07a6306517cf",
                  "user": "20279304-b387-44e9-81de-561e411c3d9d",
                  "score": 1.0,
                  "started_at": "2025-05-27T07:58:17.640030Z",
                  "ended_at": "2025-05-27T08:06:00.114838Z",
                  "status": "completed"
              }
          ]
          ```
        - **Action**: Use `<attempt_id>` to fetch responses for grading.

        #### 25. GET a single Quiz Attempt (Teacher)
        - **Purpose**: Retrieve a specific quiz attempt for review by an enrolled teacher.
        - **Endpoint**: `GET /quiz/attempts/<attempt_id>/`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Response** (200 OK):
        
          ```json
          {
              "id": "62afdac0-d5fe-4944-9e7f-346248327608",
              "quiz": "0d4e6dc1-b676-49cc-9e58-07a6306517cf",
              "user": "20279304-b387-44e9-81de-561e411c3d9d",
              "score": 1.0,
              "started_at": "2025-05-27T07:58:17.640030Z",
              "ended_at": "2025-05-27T08:06:00.114838Z",
              "status": "completed",
              "responses": [
                  {
                      "id": "d91acc3c-a213-4f58-a189-3bd086a70b04",
                      "attempt": "62afdac0-d5fe-4944-9e7f-346248327608",
                      "question": {
                          "id": "265da0bc-4f71-49d1-9a7b-e78f672e293e",
                          "curriculum_track": "f5aefe6d-eea2-4765-b98b-e578a3b6ad66",
                          "stream": "4d0ea95c-6c1e-4881-b207-2a3e017dd0aa",
                          "subject": "96f47a8f-fde5-4b90-ab27-59676d732844",
                          "module": "f58ab497-a0fe-4bec-bd60-40f0435647a1",
                          "unit": "57014168-dcf6-484a-8856-a7bef20bae9e",
                          "lesson": null,
                          "micro_lesson": null,
                          "question_type": "short",
                          "text": "Explain why Paris is the capital of France.",
                          "image_url": null,
                          "marks": 2.0,
                          "status": "published",
                          "options": []
                      },
                      "selected_option": null,
                      "short_answer": "Paris is the capital due to its historical and cultural significance.",
                      "is_correct": null,
                      "manual_score": null
                  },
                  {
                      "id": "8c80e8e4-d42c-4d7f-bd29-a547a4bef196",
                      "attempt": "62afdac0-d5fe-4944-9e7f-346248327608",
                      "question": {
                          "id": "945fe7ee-f7a9-4f68-95ed-d40c9f774f95",
                          "curriculum_track": "f5aefe6d-eea2-4765-b98b-e578a3b6ad66",
                          "stream": "4d0ea95c-6c1e-4881-b207-2a3e017dd0aa",
                          "subject": "96f47a8f-fde5-4b90-ab27-59676d732844",
                          "module": "f58ab497-a0fe-4bec-bd60-40f0435647a1",
                          "unit": "57014168-dcf6-484a-8856-a7bef20bae9e",
                          "lesson": null,
                          "micro_lesson": null,
                          "question_type": "mcq",
                          "text": "What is the capital of France?",
                          "image_url": null,
                          "marks": 1.0,
                          "status": "published",
                          "options": [
                              {
                                  "id": "830b797f-20e3-4235-b072-294e6b220028",
                                  "label": "a",
                                  "text": "Paris"
                              },
                              {
                                  "id": "cc13529b-1346-413e-bb7a-f7491b87780b",
                                  "label": "b",
                                  "text": "London"
                              },
                              {
                                  "id": "5d32984f-1856-488a-9e01-3a723b9c015c",
                                  "label": "c",
                                  "text": "Berlin"
                              },
                              {
                                  "id": "56d83f6c-a6d0-4eb6-b591-d6322c327936",
                                  "label": "d",
                                  "text": "Madrid"
                              }
                          ]
                      },
                      "selected_option": {
                          "id": "830b797f-20e3-4235-b072-294e6b220028",
                          "label": "a",
                          "text": "Paris"
                      },
                      "short_answer": null,
                      "is_correct": true,
                      "manual_score": null
                  }
              ]
          }     
          ```

        #### 26 Grade a Short Answer
        - **Purpose**: Manually grade a short answer response by an enrolled teacher.
        - **Endpoint**: `POST /quiz/<quiz_id>/grade/`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Request Body**:
          ```json
          {
            "response_id": "<response_id_2>",  The ID field from STEP 25. The id is above the attempt id. 
            "manual_score": 4.5
          }
          ```
        - **Response** (201 Created):
          ```json
          {
              "response_id": "d91acc3c-a213-4f58-a189-3bd086a70b04",
              "manual_score": 1.5
          }
          ```
        - **Action**: Update student score display in the frontend.
        
        ### Notice Workflow
        
        #### Creating Notice
        - **Endpoint**: `POST /notice/`
        - **Authentication**: `Authorization: Token <institution_token>`
        - **NOTE**: Only institution admins can create notices. Rest of them can see the notices using the same endpoint.
        - **Request Body**:
          ```json
          {
            "title": "Important Notice",
            "content": "School will be closed on Friday.",
            "image":,
            "target_audience":"students", [Target audience can be students, teachers, parents or all]
            "notice_type":"announcement"  [Notice Type type can be general, urgent, announcement, event, alert]
          }
          ```        
        - **Response** (201 Created):
          ```json
          {
              "id": "a83e9942-7e5a-4e2d-8273-55565ebb867a",
              "institution": "e4cdf94a-2dd9-41c9-8aa4-cbcaaf400b0d",
              "title": "Important Notice",
              "content": "School will be closed on Friday.",
              "target_audience": "students",
              "notice_type": "announcement",
              "image": null,
              "created_at": "2025-05-29T04:36:53.366947Z",
              "updated_at": "2025-05-29T04:36:53.366961Z",
              "is_active": true
          }
          ```
        
        ### Syllabus Workflow
        
        #### Creating Syllabus
        - **Endpoint**: `POST http://127.0.0.1:8000/syllabus/syllabus/?institution_id=33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Request Body**:
          ```json
          {
              "curriculum_track": "8017b8b9-42bd-4605-ba34-9cbb4e68e8e7",
              "section": "647ffc8c-3177-46ec-ac41-005b223f2f37",
              "subject": "00268557-6e03-4233-95a8-3e82f54d7883",
              "title": "Math Yearly Exam Syllabus",
              "purpose": "yearly_exam",
              "modules": ["bdaa09d1-3e78-43d9-8eaa-03f2b4dfbd58"],
              "units": ["530c76ff-1821-4bcf-8a9a-d0fa91e23144"],
              "lessons":[],
              "micro_lessons": [],
          }
          ```
        ##### GET SYLLABUS FOR A SUBJECT <teacher_token>
        - **Endpoint**: `GET syllabus/syllabus/by-subject/3f9f6a18-bc0d-41a8-8354-c9e752b88e5d/?institution_id=33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67`
        
        
        ### Homework Workflow
        
        #### Creating Homework As a Teacher
        - **Endpoint**: `POST /homework/homeworks/?institution_id=33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Request Body**:
          ```json
          {
              "curriculum_track": "7983545f-70f8-4cb5-a2f7-4741331f2c29",
              "section": "f7a12204-7348-410c-9d08-dfeb403514ec",
              "subject": "3f9f6a18-bc0d-41a8-8354-c9e752b88e5d",
              "title": "Math Homework",
              "image": null,  
              "description": "Read Chapter 1 and answer questions.",
              "due_date": "2025-07-30T23:59:00Z"
          }
          ```
        - **Response** (201 Created):
          ```json
          {
              "id": "8fefa3e5-bf96-433b-9214-dbe9546c9f68",
              "institution": "0bee8131-77a6-4937-8d90-da4bd51c6ac4",
              "curriculum_track": "8017b8b9-42bd-4605-ba34-9cbb4e68e8e7",
              "section": "647ffc8c-3177-46ec-ac41-005b223f2f37",
              "subject": "00268557-6e03-4233-95a8-3e82f54d7883",
              "title": "English Homework 1",
              "description": "Read Chapter 1 and answer questions.",
              "image": null,
              "due_date": "2025-06-01T23:59:00Z",
              "created_at": "2025-05-28T06:21:00.211710Z",
              "updated_at": "2025-05-28T06:21:00.211719Z",
              "is_active": true
          }
          ```
        #### GET HOMEWORKS FOR A SECTION AND A SUBJECT
        - **Endpoint**: `GET /homework/homeworks/assigned/<section_id>/<subject_id>/?institution_id=<institution_uuid>`
        
        
        #### PATCH THE HOMEWORK
        - **Endpoint**: `PATCH /homework/homeworks/<id>/?institution_id=<institution_uuid>`
        - **Authentication**: `Authorization: Token <teacher_token>`
        
        
        #### Submitting Homework As a Teacher. Teacher will just mark whether a student has submitted the homework or not.
        - **Endpoint**: `POST /homework/submissions/?institution_id=33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Request Body**:
          ```json
          {
              "homework_id": "8fefa3e5-bf96-433b-9214-dbe9546c9f68",
              "student_id": "20279304-b387-44e9-81de-561e411c3d9d",
              "submitted": true
          }
          ```
        - **Response** (201 Created):
          ```json
          {
              "id": "89bc1516-1cca-4c20-9ba6-246dcbbf6870",
              "homework": "8fefa3e5-bf96-433b-9214-dbe9546c9f68",
              "student": "20279304-b387-44e9-81de-561e411c3d9d",
              "submitted": true,
              "submission_date": "2025-05-28T06:24:58.838017Z",
              "updated_at": "2025-05-28T06:24:58.838234Z"
          }
          ```
        #### Number of Homework Submissions For a Section and a Subject
        - **Endpoint**: `/homework/homeworks/submissions/<homework_id>/?institution_id=33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67`
        - **Authentication**: `Authorization: Token <teacher_token>`
        - **Response** (200 OK):
          ```json
          {
              "homework_id": "9eff4e74-2105-41bb-ac50-fb9897093de8",
              "total_submissions": 1,
              "submissions": [
                  {
                      "id": "729382eb-d56f-4998-baa2-cad54ac5d8dd",
                      "homework": "9eff4e74-2105-41bb-ac50-fb9897093de8",
                      "student": "91140d9e-6fc6-42db-b7e7-c7e61b129bda",
                      "submitted": true,
                      "submission_date": "2025-08-03T07:37:31.004623Z",
                      "updated_at": "2025-08-03T07:37:31.005650Z"
                  }
              ]
          }
          ```
        #### Homework Submission Statistics For Teacher
        - **Endpoint**: `GET /homework/submissions/statistics/<section_id>/<subject_id>/?institution_id=<institution_uuid>`
        - **Authentication**: `Authorization: Token <teacher_token>`  
        - **NOTE**: This endpoint is used to see the number of homeworks submitted and not submitted by each student in a section for a subject.
        - **Response** (200 OK):
          ```json
          [
              {
                  "student": {
                      "id": "20279304-b387-44e9-81de-561e411c3d9d",
                      "email": null,
                      "phone_number": "01886134904",
                      "first_name": "Walid ",
                      "last_name": null,
                      "gender": "male",
                      "birth_date": "2025-05-20",
                      "profile_image": null,
                      "is_institution": false,
                      "is_teacher": false,
                      "is_student": true,
                      "is_parents": false,
                      "is_admission_seeker": false
                  },
                  "total_homeworks": 2,
                  "submitted": 1,
                  "not_submitted": 1
              },
              {
                  "student": {
                      "id": "b7a08fbd-cbc5-4a17-8bf2-91e28bd73167",
                      "email": null,
                      "phone_number": "01846024684",
                      "first_name": null,
                      "last_name": null,
                      "gender": null,
                      "birth_date": null,
                      "profile_image": null,
                      "is_institution": false,
                      "is_teacher": false,
                      "is_student": true,
                      "is_parents": false,
                      "is_admission_seeker": false
                  },
                  "total_homeworks": 2,
                  "submitted": 0,
                  "not_submitted": 2
              }
          ]
          ```
          
          
          ### Exam Workflow
          
          #### Creating Exam
          - **Endpoint**: `POST /exam/`
          - **Authentication**: `Authorization: Token <teacher_token>`
          - **Request Body**:
          ```json
          {
              "curriculum_track_id": "b8be52b6-6b6b-4495-a875-bdd462d08dfa",
              "section_id": "d3bfa8dd-4e0f-4879-ba26-d6922c15c3b6",
              "subject_id": "715fe38f-c8b5-4e44-a59b-1ee3f4f1ba68",
              "title": "Final Exam",
              "exam_type": "final",  [Exam type can be midterm, final, class_test, other]
              "exam_date": "2025-05-01",
              "total_marks": 100,
              "is_active": true
          }
          ```
          
          #### Assign Exam Marks to Students
          - **Endpoint**: `POST /exam/marks/`
          - **Authentication**: `Authorization: Token <teacher_token>`
          - **Request Body**:
          ```json
          {
              "exam_id": "<uuid>",
              "student_id": "<uuid>",
              "marks_obtained": 95,
              "remarks": "Excellent performance"
          }
          ```
          
          #### Get Exams for a Section and a Subject
          
          - **Endpoint**: `GET /exam/?section_id=<section_id>&subject_id=<subject_id>`
          
          #### Get Exams  for a Section
          
          - **Endpoint**: `GET /exam/?section_id=<section_id>`
          
          #### Get Exam Marks of all the students in a Section for a Subject
          - **Endpoint**: `GET exam/marks/?section_id=<section_id>&subject_id=<subject_id>`
        
        
          ### Result Workflow
          
          #### GET Result as a Student
          - **Endpoint**: `GET result/student/<student_id>`
          - **Authentication**: `Authorization: Token <student_token>`
          - **Response** (200 OK):
          ```json
          {
              "student_id": "7052486f-e17f-4394-ad47-fa8a65e7e4cc",
              "quiz_results": [
                  {
                      "id": "dab15d18-eb2b-41e1-b516-a6e06bb6a50f",
                      "quiz_title": "Quiz 1",
                      "subject": "MATH",
                      "curriculum_track": "Class 9",
                      "section": "A",
                      "score": 5.0,
                      "started_at": "2025-05-29T05:10:52.719727Z",
                      "ended_at": null,
                      "status": "completed"
                  }
              ],
              "exam_results": [
                  {
                      "id": "d1f36276-3125-48ba-9db0-a8b01ddb8eb4",
                      "exam_title": "Final Exam",
                      "subject": "MATH",
                      "curriculum_track": "Class 9",
                      "section": "A",
                      "exam_type": "final",
                      "exam_date": "2025-05-01",
                      "marks_obtained": 95.0,
                      "remarks": "Excellent performance"
                  }
              ]
          }
          ```
          #### GET Result as a Teacher
          
          - **Endpoint**: `GET /result/section/?section_id=<uuid>` To get the report of all the students in a section.
          - **Endpoint**: `GET /result/section/?section_id=<uuid>&subject_id=<uuid>&student_id=<uuid>` To get the report of a section for a subject for a student.
          - **Authentication**: `Authorization: Token <teacher_token>`
          - **Response** (200 OK):
          ```json
          {
              "section_id": "d3bfa8dd-4e0f-4879-ba26-d6922c15c3b6",
              "subject_id": "715fe38f-c8b5-4e44-a59b-1ee3f4f1ba68",
              "student_id": "7052486f-e17f-4394-ad47-fa8a65e7e4cc",
              "students": [
                  {
                      "student_id": "7052486f-e17f-4394-ad47-fa8a65e7e4cc",
                      "student_name": "None None",
                      "quiz_results": [
                          {
                              "id": "dab15d18-eb2b-41e1-b516-a6e06bb6a50f",
                              "quiz_title": "Quiz 1",
                              "subject": "MATH",
                              "curriculum_track": "Class 9",
                              "section": "A",
                              "score": 5.0,
                              "started_at": "2025-05-29T05:10:52.719727Z",
                              "ended_at": null,
                              "status": "completed"
                          }
                      ],
                      "exam_results": [
                          {
                              "id": "d1f36276-3125-48ba-9db0-a8b01ddb8eb4",
                              "exam_title": "Final Exam",
                              "subject": "MATH",
                              "curriculum_track": "Class 9",
                              "section": "A",
                              "exam_type": "final",
                              "exam_date": "2025-05-01",
                              "marks_obtained": 95.0,
                              "remarks": "Excellent performance"
                          }
                      ]
                  }
              ]
          }
          ```
          
          ### PAYMENT AND SCHOLARSHIP WORKFLOW
          
          #### CREATE DEFAULT FEES FOR EVERY STUDENTS (INSTITUTION ADMIN)
          
          - **Endpoint**: `POST /institution/fees/institution/`
          - **Authentication**: `Authorization: Token <institution_token>`
          - **Request Body**:
          
          ```json
          {
            "default_fee": 800.00
          }
          ```
          - **Response** (201 Created):
          ```json
          {
              "id": 2,
              "institution": "33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67",
              "default_fee": "800.00",
              "created_at": "2025-06-01T10:29:29.870566Z",
              "updated_at": "2025-06-01T10:29:29.870580Z"
          }
          ```
          
          #### CREATE FEES FOR A SPECIFIC CURRICULUM TRACK (INSTITUTION ADMIN)
          - **Endpoint**: `POST /institution/fees/curriculum-tracks/`
          - **Authentication**: `Authorization: Token <institution_token>`
          
          - **Request Body**:
          
          ```json
          {
            "curriculum_track": "<curriculum_track_id>",
            "fee": 1000.00
          }
          ```
          
          - **Response** (201 Created):
          
          ```json
          {
              "id": 2,
              "curriculum_track": "7983545f-70f8-4cb5-a2f7-4741331f2c29",
              "curriculum_track_name": "Class 9",
              "fee": "1000.00",
              "created_at": "2025-06-01T15:06:08.720663Z",
              "updated_at": "2025-06-01T15:06:08.720675Z"
          }
          ```
          
          - **NOTE**: GET the fees of curriculum track using the following endpoint 
          
          - **Endpoint**: `GET /institution/fees/curriculum-tracks/``
          
          #### CREATE FEES FOR A SPECIFIC STUDENT (INSTITUTION ADMIN)
          - **Endpoint**: `POST /institution/fees/students/`
          - **Authentication**: `Authorization: Token <institution_token>`
          - **Request Body**:
          ```json
          {
            "student_enrollment": "<student_enrollment_id>",  [GET the enrollment ID from /institution/my-sections/ endpoint]
            "fee": 20.00
          }
          ```
          
          - **Response** (201 Created):
          ```json
          {
              "id": 2,
              "student_enrollment": "c9516859-a5d7-4cce-9d8e-17ab7efb491e",
              "fee": "20.00",
              "created_at": "2025-06-01T15:10:31.351630Z",
              "updated_at": "2025-06-01T15:10:31.351644Z"
          }
          ```
          
          - **NOTE**: GET the fees of students  using the following endpoint 
          
          - **Endpoint**: `GET /institution/fees/students/``
          
          #### SCHOLARSHIP ASSIGNMENT (INSTITUTION ADMIN) [OPTIONAL]
          
          - **Endpoint**: `POST /scholarship/scholarships/`
          - **Authentication**: `Authorization: Token <institution_token>`
          - **Request Body**:
          ```json
          {
            "student_enrollment_id": "c9516859-a5d7-4cce-9d8e-17ab7efb491e",  [GET the enrollment ID from /institution/my-sections/ endpoint]
            "percentage": 50.00,
            "is_active": true
          }
          ```
          - **Response** (201 Created):
          
          ```json
          {
              "id": "06c47f09-ebd0-41df-9a9f-1d31b2e5270d",
              "institution": "33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67",
              "student_enrollment": {
                  "id": "c9516859-a5d7-4cce-9d8e-17ab7efb491e",
                  "user": "91140d9e-6fc6-42db-b7e7-c7e61b129bda",
                  "curriculum_track": "7983545f-70f8-4cb5-a2f7-4741331f2c29",
                  "section": "f7a12204-7348-410c-9d08-dfeb403514ec",
                  "is_active": true
              },
              "percentage": "50.00",
              "is_active": true
          }
          ```
          
          #### CREATE PAYMENT FOR BKASH (STUDENT)
          
          - **Endpoint**: `POST /bkash/fees/fee-payments/`
          - **Authentication**: `Authorization: Token <student_token>`
          
          - **Request Body**:
          
          ```json
          {
            "student_enrollment_id": "c9516859-a5d7-4cce-9d8e-17ab7efb491e",  [GET the enrollment ID from /institution/my-sections/ endpoint]
            "month": "2025-05"
          }
          ```
          - **Response** (201 Created):
          
          ```json
          {
              "payment_id": "TR0011rF0KjqE1748781110661",
              "bkash_url": "https://payment.bkash.com/?paymentId=TR0011rF0KjqE1748781110661&hash=4SySgxZCaI5NB7BoP0eGQOrd)e(LY9Rvrj)FZjzgCyP!VH!zQTqOzEo0GrBb7pUbZn)!pwNksop8N16RO3K6bm7h4B.ZR3K.BfEq1748781110661&mode=0011&apiVersion=v1.2.0-beta/",
              "fee_payment_id": "a65eeb6c-aa6d-4063-ad5d-0b3647664d58"
          }
          ```
          #### STORE THE PAYMENT ID AND REDIRECT THE USER TO THE BKASH URL
          
          #### EXECUTE THE PAYMENT (STUDENT)
          
          -**Endpoint**: `POST /bkash/execute/`
          - **Authentication**: `Authorization: Token <student_token>`
          - **Request Body**:
          
          ```json
          {
            "paymentID": "TR0011XXXXXXXX"
          }
          ```
          
          - **Response** (200 OK):
          ```json
          {
            "statusCode": "0000",
            "statusMessage": "Successful",
            "transactionStatus": "Completed",
            "transactionID": "<transaction_id>",
            "amount": "400.00",
            "currency": "BDT"
          }
          ```
          
          #### VERIFY PAYMENT STATUS (OPTIONAL)
          - **Endpoint**: `POST /bkash/query/`
          
          - **Request Body**:
          
          ```json
          {
            "paymentID": "TR0011XXXXXXXX"
          }
          ```
          
          - **Response** (200 OK):
          ```json
          {
            "statusCode": "0000",
            "statusMessage": "Successful",
            "transactionStatus": "Completed",
            "amount": "400.00",
            "currency": "BDT"
          }
          ```
          #### TRACK PAYMENT  (INSTITUTION ADMIN)
          
          - **Endpoint**: `GET /bkash/fees/payment-trackers/`
          - **Authentication**: `Authorization: Token <institution_token>`
          
          - **Response** (200 OK):
          
          ```json
          [
              {
                  "id": "8bc39e62-d0a3-411b-8059-32b2bf60fea5",
                  "institution": "33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67",
                  "institution_name": "Brac University",
                  "amount": "10.00",
                  "is_disbursed": false,
                  "disbursed_at": null,
                  "created_at": "2025-06-01T12:31:48.607617Z",
                  "updated_at": "2025-06-01T12:31:48.607628Z"
              }
          ]
          ```
          
          - **NOTE**: Here "is_disbursed": false means the payment is yet to be disbursed to the institution. 
          
          #### DISBURSE PAYMENT (INSTITUTION ADMIN)
          
          - **Endpoint**: `PATCH /bkash/fees/payment-trackers/<tracker_id>/`
          - **Authentication**: `Authorization: Token <institution_token>`
          
          - **Request Body**:
          
          ```json
          {
            "is_disbursed": true
          }
          ```
          
          - **Response** (200 OK):
          
          ```json
          {
              "id": "8bc39e62-d0a3-411b-8059-32b2bf60fea5",
              "institution": "33dcaa97-9d1d-4e64-a9ab-f6e9f7b05c67",
              "institution_name": "Brac University",
              "amount": "10.00",
              "is_disbursed": true,
              "disbursed_at": "2025-06-01T12:49:22.101747Z",
              "created_at": "2025-06-01T12:31:48.607617Z",
              "updated_at": "2025-06-01T12:49:22.101824Z"
          }
          ```
          

          
           
          

        """,
        terms_of_service="https://www.educational_management.com/terms/",
        contact=openapi.Contact(email="support@educational_management.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)
