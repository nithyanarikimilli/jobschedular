from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.models import User, Organization, Project, Queue, RetryPolicy, BackoffType
from app.schemas.schemas import UserCreate, Token, UserResponse, UserLogin
from app.api.deps import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger("smartqueue.auth")

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    
    if existing_user:
        # User already exists. Verify if password is correct.
        if not verify_password(user_in.password, existing_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists."
            )
        user = existing_user
        org_id = user.organization_id
    else:
        user = None
        org_id = None

    try:
        # If user does not exist, we create Org and User transactional
        if not user:
            # 1. Create Organization
            org = Organization(name=user_in.organization_name)
            db.add(org)
            db.flush()
            org_id = org.id

            # 2. Create User
            user = User(
                email=user_in.email,
                hashed_password=get_password_hash(user_in.password),
                full_name=user_in.full_name,
                organization_id=org_id
            )
            db.add(user)
            db.flush()

        # 3. Create Default Project
        project = db.query(Project).filter(
            Project.organization_id == org_id,
            Project.name == "Main Project"
        ).first()
        if not project:
            project = Project(
                name="Main Project",
                organization_id=org_id
            )
            db.add(project)
            db.flush()

        # 4. Create required default queues only if they do not already exist
        default_queue = db.query(Queue).filter(Queue.project_id == project.id, Queue.name == "default").first()
        if not default_queue:
            default_queue = Queue(
                project_id=project.id,
                name="default",
                description="Default processing queue",
                priority=1,
                max_concurrency=10
            )
            db.add(default_queue)

        high_queue = db.query(Queue).filter(Queue.project_id == project.id, Queue.name == "high-priority").first()
        if not high_queue:
            high_queue = Queue(
                project_id=project.id,
                name="high-priority",
                description="High-priority processing queue",
                priority=3,
                max_concurrency=15
            )
            db.add(high_queue)

        low_queue = db.query(Queue).filter(Queue.project_id == project.id, Queue.name == "low-priority").first()
        if not low_queue:
            low_queue = Queue(
                project_id=project.id,
                name="low-priority",
                description="Low-priority processing queue",
                priority=0,
                max_concurrency=5
            )
            db.add(low_queue)

        # 5. Create default retry policy
        policy = db.query(RetryPolicy).filter(RetryPolicy.name == "Default Policy").first()
        if not policy:
            policy = RetryPolicy(
                name="Default Policy",
                backoff_type=BackoffType.EXPONENTIAL,
                base_delay=5,
                max_retries=3
            )
            db.add(policy)

        db.commit()

        # Generate Token
        access_token = create_access_token(subject=user.id)
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Internal database error."
        )

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

# Alternative JSON body login endpoint for UI flexibility
@router.post("/login/json", response_model=Token)
def login_json(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
