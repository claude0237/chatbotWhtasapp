"""ML Training Service for model training and evaluation"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.bot.models import MLModel, MLModelType
from app.bot.repositories import MLModelRepository


class MLTrainingService:
    """Service for ML model training and evaluation"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_repository = MLModelRepository(db)
    
    async def train_intent_classifier(
        self,
        company_id: UUID,
        training_data: List[Dict[str, Any]],
        model_name: str = "intent_classifier",
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> MLModel:
        """Train an intent classifier model"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import Pipeline
            import joblib
            import io
            import base64
            
            # Extract texts and labels
            texts = [item["text"] for item in training_data]
            labels = [item["intent"] for item in training_data]
            
            # Create pipeline
            pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000)),
                ('classifier', LogisticRegression(max_iter=1000))
            ])
            
            # Train model
            pipeline.fit(texts, labels)
            
            # Save model to bytes
            model_bytes = io.BytesIO()
            joblib.dump(pipeline, model_bytes)
            model_bytes.seek(0)
            model_data = base64.b64encode(model_bytes.read()).decode('utf-8')
            
            # Create MLModel record
            ml_model = MLModel(
                id=UUID(),
                company_id=company_id,
                name=model_name,
                model_type=MLModelType.CLASSIFIER,
                provider="SKLEARN",
                model_name="logistic_regression",
                version="1.0.0",
                configuration={
                    "hyperparameters": hyperparameters or {},
                    "training_samples": len(training_data),
                    "classes": list(set(labels)),
                    "model_data": model_data
                },
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            return await self.model_repository.create(ml_model)
        except ImportError:
            raise ImportError("scikit-learn not installed")
        except Exception as e:
            raise RuntimeError(f"Intent classifier training failed: {str(e)}")
    
    async def fine_tune_llm(
        self,
        company_id: UUID,
        training_data: List[Dict[str, str]],
        base_model: str = "gpt-3.5-turbo",
        model_name: str = "fine_tuned_llm",
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> MLModel:
        """Fine-tune an LLM model (placeholder for OpenAI fine-tuning API)"""
        try:
            # Placeholder for OpenAI fine-tuning API
            # In production, this would call OpenAI's fine-tuning API
            
            configuration = {
                "base_model": base_model,
                "hyperparameters": hyperparameters or {},
                "training_samples": len(training_data),
                "status": "pending_fine_tuning"
            }
            
            # Create MLModel record
            ml_model = MLModel(
                id=UUID(),
                company_id=company_id,
                name=model_name,
                model_type=MLModelType.RAG,
                provider="OPENAI",
                model_name=base_model,
                version="1.0.0",
                configuration=configuration,
                is_active=False,  # Not active until fine-tuning completes
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            return await self.model_repository.create(ml_model)
        except Exception as e:
            raise RuntimeError(f"LLM fine-tuning failed: {str(e)}")
    
    async def evaluate_model(
        self,
        model_id: UUID,
        test_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate a trained model"""
        try:
            from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
            import joblib
            import base64
            import io
            
            # Get model
            model = await self.model_repository.get_by_id(model_id)
            if not model:
                raise ValueError("Model not found")
            
            # Load model from configuration
            if model.model_type == MLModelType.CLASSIFIER:
                model_data = model.configuration.get("model_data")
                if not model_data:
                    raise ValueError("Model data not found")
                
                model_bytes = base64.b64decode(model_data)
                pipeline = joblib.load(io.BytesIO(model_bytes))
                
                # Extract texts and labels
                texts = [item["text"] for item in test_data]
                true_labels = [item["intent"] for item in test_data]
                
                # Predict
                predicted_labels = pipeline.predict(texts)
                
                # Calculate metrics
                accuracy = accuracy_score(true_labels, predicted_labels)
                precision, recall, f1, _ = precision_recall_fscore_support(
                    true_labels, predicted_labels, average='weighted'
                )
                
                return {
                    "model_id": str(model_id),
                    "model_name": model.name,
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1,
                    "classification_report": classification_report(true_labels, predicted_labels),
                    "test_samples": len(test_data)
                }
            else:
                return {
                    "model_id": str(model_id),
                    "model_name": model.name,
                    "message": "Evaluation not implemented for this model type",
                    "test_samples": len(test_data)
                }
        except ImportError:
            raise ImportError("scikit-learn not installed")
        except Exception as e:
            raise RuntimeError(f"Model evaluation failed: {str(e)}")
    
    async def get_training_jobs(self, company_id: UUID) -> List[MLModel]:
        """Get all training jobs for a company"""
        return await self.model_repository.get_by_company_id(company_id)
    
    async def deploy_model(self, model_id: UUID) -> MLModel:
        """Deploy a trained model"""
        model = await self.model_repository.get_by_id(model_id)
        if not model:
            raise ValueError("Model not found")
        
        # Deactivate other models of the same type for this company
        other_models = await self.model_repository.get_by_type(
            model.company_id, model.model_type.value
        )
        for other_model in other_models:
            other_model.is_active = False
            await self.model_repository.update(other_model)
        
        # Activate this model
        model.is_active = True
        model.updated_at = datetime.utcnow()
        return await self.model_repository.update(model)
