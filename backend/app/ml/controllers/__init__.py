"""ML Controller - Documents, Ingestion, and Training"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import uuid

from app.database import get_db
from app.ml.services import KnowledgeIngestionService
from app.ml.training import MLTrainingService
from app.ml.repositories import DocumentRepository, IngestionJobRepository
from app.bot.repositories import MLModelRepository
from app.ml.models import FileType
from app.auth.dependencies import get_current_active_user, get_current_company_id
from app.users.models import User


router = APIRouter(prefix="/ml", tags=["ML"])


# Request/Response Schemas
class DocumentResponse(BaseModel):
    """Document response schema"""
    id: str
    company_id: str
    file_name: str
    file_type: str
    file_path: Optional[str]
    file_size: Optional[int]
    status: str
    chunk_count: int
    processed_at: Optional[str]
    extra_data: Optional[dict]
    created_at: str
    updated_at: str


class IngestionJobResponse(BaseModel):
    """Ingestion job response schema"""
    id: str
    company_id: str
    source_type: str
    source_config: Optional[dict]
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    total_documents: int
    processed_documents: int
    failed_documents: int
    created_at: str
    updated_at: str


# Documents endpoints
@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Upload and ingest a document"""
    # Determine file type
    file_extension = file.filename.split('.')[-1].lower() if file.filename else ""
    file_type_map = {
        'pdf': FileType.PDF,
        'docx': FileType.WORD,
        'doc': FileType.WORD,
        'xlsx': FileType.EXCEL,
        'xls': FileType.EXCEL,
        'md': FileType.MARKDOWN,
        'txt': FileType.TXT,
        'html': FileType.HTML
    }
    
    file_type = file_type_map.get(file_extension, FileType.TXT)
    
    # For now, save to a temporary path
    # In production, this would use S3/MinIO
    import os
    import tempfile
    
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    
    try:
        # Save uploaded file
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Ingest document
        ingestion_service = KnowledgeIngestionService(db)
        document = await ingestion_service.ingest_document(
            company_id=company_id,
            file_name=file.filename,
            file_type=file_type,
            file_path=file_path,
            file_size=len(content)
        )
        
        return {
            "id": str(document.id),
            "company_id": str(document.company_id),
            "file_name": document.file_name,
            "file_type": document.file_type.value,
            "file_path": document.file_path,
            "file_size": document.file_size,
            "status": document.status.value,
            "chunk_count": document.chunk_count,
            "processed_at": document.processed_at.isoformat() if document.processed_at else None,
            "extra_data": document.extra_data,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat()
        }
    except Exception as e:
        # Clean up temp file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )


@router.get("/documents")
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get documents for the current user's company"""
    document_repository = DocumentRepository(db)
    
    if status_filter:
        from app.ml.models import DocumentStatus
        documents = await document_repository.get_by_status(
            company_id,
            DocumentStatus(status_filter),
            skip,
            limit
        )
    else:
        documents = await document_repository.get_by_company_id(company_id, skip, limit)
    
    return [
        {
            "id": str(d.id),
            "company_id": str(d.company_id),
            "file_name": d.file_name,
            "file_type": d.file_type.value,
            "file_path": d.file_path,
            "file_size": d.file_size,
            "status": d.status.value,
            "chunk_count": d.chunk_count,
            "processed_at": d.processed_at.isoformat() if d.processed_at else None,
            "extra_data": d.extra_data,
            "created_at": d.created_at.isoformat(),
            "updated_at": d.updated_at.isoformat()
        }
        for d in documents
    ]


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get document by ID"""
    document_repository = DocumentRepository(db)
    document = await document_repository.get_by_id(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if str(document.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": str(document.id),
        "company_id": str(document.company_id),
        "file_name": document.file_name,
        "file_type": document.file_type.value,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "status": document.status.value,
        "chunk_count": document.chunk_count,
        "processed_at": document.processed_at.isoformat() if document.processed_at else None,
        "extra_data": document.extra_data,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat()
    }


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Delete document by ID"""
    document_repository = DocumentRepository(db)
    document = await document_repository.get_by_id(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if str(document.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    ingestion_service = KnowledgeIngestionService(db)
    await ingestion_service.delete_document(document_id)
    
    return {"message": "Document deleted successfully"}


# Ingestion endpoints
@router.post("/ingestion/from-db", status_code=status.HTTP_201_CREATED)
async def ingest_from_database(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Ingest documents from knowledge base"""
    ingestion_service = KnowledgeIngestionService(db)
    
    job = await ingestion_service.ingest_from_database(
        company_id=company_id,
        source_config={}
    )
    
    return {
        "id": str(job.id),
        "company_id": str(job.company_id),
        "source_type": job.source_type,
        "source_config": job.source_config,
        "status": job.status.value,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_message": job.error_message,
        "total_documents": job.total_documents,
        "processed_documents": job.processed_documents,
        "failed_documents": job.failed_documents,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat()
    }


@router.post("/ingestion/reindex", status_code=status.HTTP_201_CREATED)
async def reindex_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Reindex all documents for a company"""
    ingestion_service = KnowledgeIngestionService(db)
    
    job = await ingestion_service.reindex_all(company_id)
    
    return {
        "id": str(job.id),
        "company_id": str(job.company_id),
        "source_type": job.source_type,
        "source_config": job.source_config,
        "status": job.status.value,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_message": job.error_message,
        "total_documents": job.total_documents,
        "processed_documents": job.processed_documents,
        "failed_documents": job.failed_documents,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat()
    }


@router.get("/ingestion/jobs/{job_id}")
async def get_ingestion_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get ingestion job by ID"""
    job_repository = IngestionJobRepository(db)
    job = await job_repository.get_by_id(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingestion job not found"
        )
    
    if str(job.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": str(job.id),
        "company_id": str(job.company_id),
        "source_type": job.source_type,
        "source_config": job.source_config,
        "status": job.status.value,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_message": job.error_message,
        "total_documents": job.total_documents,
        "processed_documents": job.processed_documents,
        "failed_documents": job.failed_documents,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat()
    }


# ML Training Schemas
class MLModelResponse(BaseModel):
    """ML model response schema"""
    id: str
    company_id: str
    name: str
    model_type: str
    provider: str
    model_name: str
    version: Optional[str]
    configuration: Optional[dict]
    is_active: bool
    created_at: str
    updated_at: str


class TrainingRequest(BaseModel):
    """Training request schema"""
    training_data: List[dict] = Field(..., min_items=1)
    model_name: str = Field(..., min_length=1, max_length=255)
    hyperparameters: Optional[dict] = None


class FineTuningRequest(BaseModel):
    """Fine-tuning request schema"""
    training_data: List[dict] = Field(..., min_items=1)
    base_model: str = Field(default="gpt-3.5-turbo", max_length=100)
    model_name: str = Field(..., min_length=1, max_length=255)
    hyperparameters: Optional[dict] = None


class EvaluationRequest(BaseModel):
    """Evaluation request schema"""
    test_data: List[dict] = Field(..., min_items=1)


class SimulateRequest(BaseModel):
    """Simulation request schema"""
    company_id: str
    message: str


# ML Training endpoints
@router.post("/train/intent-classifier", status_code=status.HTTP_201_CREATED)
async def train_intent_classifier(
    request: TrainingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Train an intent classifier model"""
    training_service = MLTrainingService(db)
    
    try:
        model = await training_service.train_intent_classifier(
            company_id=company_id,
            training_data=request.training_data,
            model_name=request.model_name,
            hyperparameters=request.hyperparameters
        )
        
        return {
            "id": str(model.id),
            "company_id": str(model.company_id),
            "name": model.name,
            "model_type": model.model_type.value,
            "provider": model.provider,
            "model_name": model.model_name,
            "version": model.version,
            "configuration": model.configuration,
            "is_active": model.is_active,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {str(e)}"
        )


@router.post("/train/fine-tune-llm", status_code=status.HTTP_201_CREATED)
async def fine_tune_llm(
    request: FineTuningRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Fine-tune an LLM model"""
    training_service = MLTrainingService(db)
    
    try:
        model = await training_service.fine_tune_llm(
            company_id=company_id,
            training_data=request.training_data,
            base_model=request.base_model,
            model_name=request.model_name,
            hyperparameters=request.hyperparameters
        )
        
        return {
            "id": str(model.id),
            "company_id": str(model.company_id),
            "name": model.name,
            "model_type": model.model_type.value,
            "provider": model.provider,
            "model_name": model.model_name,
            "version": model.version,
            "configuration": model.configuration,
            "is_active": model.is_active,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fine-tuning failed: {str(e)}"
        )


@router.post("/evaluate/{model_id}")
async def evaluate_model(
    model_id: str,
    request: EvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Evaluate a trained model"""
    training_service = MLTrainingService(db)
    
    try:
        # Check model ownership
        model_repository = MLModelRepository(db)
        model = await model_repository.get_by_id(model_id)
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        if str(model.company_id) != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        evaluation = await training_service.evaluate_model(model_id, request.test_data)
        return evaluation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.get("/models")
async def get_ml_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """Get all ML models for the company"""
    training_service = MLTrainingService(db)
    models = await training_service.get_training_jobs(company_id)
    
    return [
        {
            "id": str(model.id),
            "company_id": str(model.company_id),
            "name": model.name,
            "model_type": model.model_type.value,
            "provider": model.provider,
            "model_name": model.model_name,
            "version": model.version,
            "configuration": model.configuration,
            "is_active": model.is_active,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat()
        }
        for model in models[skip:skip + limit]
    ]


@router.post("/models/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Deploy a trained model"""
    training_service = MLTrainingService(db)
    
    try:
        # Check model ownership
        model_repository = MLModelRepository(db)
        model = await model_repository.get_by_id(model_id)
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        if str(model.company_id) != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        deployed_model = await training_service.deploy_model(model_id)
        
        return {
            "id": str(deployed_model.id),
            "company_id": str(deployed_model.company_id),
            "name": deployed_model.name,
            "model_type": deployed_model.model_type.value,
            "provider": deployed_model.provider,
            "model_name": deployed_model.model_name,
            "version": deployed_model.version,
            "configuration": deployed_model.configuration,
            "is_active": deployed_model.is_active,
            "created_at": deployed_model.created_at.isoformat(),
            "updated_at": deployed_model.updated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}"
        )


@router.post("/simulate")
async def simulate_bot(
    request: SimulateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Simulate bot response with ML support (no auth required for testing)"""
    from app.bot.engine import BotEngine
    from uuid import UUID
    
    bot_engine = BotEngine(db)
    
    response = await bot_engine.process(
        company_id=UUID(request.company_id),
        phone_number="SIMULATION",
        message_text=request.message
    )
    
    if response is None:
        return {
            "response": "Bot not configured",
            "source": "error",
            "confidence": 0.0
        }
    
    return {
        "response": response,
        "source": "bot",
        "confidence": 1.0
    }


# Create a separate router for public endpoints without auth
public_router = APIRouter()

@public_router.post("/simulate")
async def simulate_bot_public(
    request: SimulateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Simulate bot response with ML support (public endpoint - no auth)"""
    from app.bot.engine import BotEngine
    from uuid import UUID
    
    bot_engine = BotEngine(db)
    
    response = await bot_engine.process(
        company_id=UUID(request.company_id),
        phone_number="SIMULATION",
        message_text=request.message
    )
    
    if response is None:
        return {
            "response": "Bot not configured",
            "source": "error",
            "confidence": 0.0
        }
    
    return {
        "response": response,
        "source": "bot",
        "confidence": 1.0
    }
