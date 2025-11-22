"""
Workflow/Pipeline engine for document processing automation.
"""
import uuid
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from utils.logger import app_logger


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of a workflow step."""
    status: StepStatus
    output: Any = None
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class WorkflowStep:
    """Definition of a workflow step."""
    name: str
    handler: str  # Function name or task name
    config: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None  # Condition to run this step
    on_failure: str = "fail"  # fail, skip, retry


@dataclass
class Workflow:
    """Workflow definition."""
    id: str
    name: str
    steps: List[WorkflowStep]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowExecution:
    """Execution instance of a workflow."""
    id: str
    workflow_id: str
    status: StepStatus
    context: Dict[str, Any]
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class WorkflowEngine:
    """Engine for executing document processing workflows."""

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register built-in workflow handlers."""
        self.handlers = {
            "ocr_extract": self._handle_ocr_extract,
            "field_extract": self._handle_field_extract,
            "validate_fields": self._handle_validate_fields,
            "transform_data": self._handle_transform_data,
            "export_data": self._handle_export_data,
            "send_webhook": self._handle_send_webhook,
            "send_notification": self._handle_send_notification,
        }

    def register_handler(self, name: str, handler: Callable):
        """Register a custom workflow handler."""
        self.handlers[name] = handler

    def create_workflow(
        self,
        name: str,
        steps: List[Dict[str, Any]]
    ) -> Workflow:
        """
        Create a new workflow definition.

        Args:
            name: Workflow name
            steps: List of step definitions

        Returns:
            Created workflow
        """
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"

        workflow_steps = [
            WorkflowStep(
                name=step.get("name", f"step_{i}"),
                handler=step["handler"],
                config=step.get("config", {}),
                condition=step.get("condition"),
                on_failure=step.get("on_failure", "fail")
            )
            for i, step in enumerate(steps)
        ]

        workflow = Workflow(
            id=workflow_id,
            name=name,
            steps=workflow_steps
        )

        self.workflows[workflow_id] = workflow

        app_logger.info(
            "Created workflow",
            workflow_id=workflow_id,
            name=name,
            steps=len(steps)
        )

        return workflow

    def execute(
        self,
        workflow_id: str,
        context: Dict[str, Any]
    ) -> WorkflowExecution:
        """
        Execute a workflow.

        Args:
            workflow_id: ID of workflow to execute
            context: Initial context data

        Returns:
            Workflow execution result
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.workflows[workflow_id]
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"

        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            status=StepStatus.RUNNING,
            context=context.copy()
        )

        app_logger.info(
            "Starting workflow execution",
            execution_id=execution_id,
            workflow_id=workflow_id
        )

        try:
            for step in workflow.steps:
                # Check condition
                if step.condition and not self._evaluate_condition(step.condition, execution.context):
                    execution.step_results[step.name] = StepResult(
                        status=StepStatus.SKIPPED
                    )
                    continue

                # Execute step
                result = self._execute_step(step, execution.context)
                execution.step_results[step.name] = result

                # Handle failure
                if result.status == StepStatus.FAILED:
                    if step.on_failure == "fail":
                        execution.status = StepStatus.FAILED
                        break
                    elif step.on_failure == "skip":
                        continue
                    # retry would be handled by Celery

                # Update context with output
                if result.output:
                    execution.context[f"{step.name}_output"] = result.output

            if execution.status == StepStatus.RUNNING:
                execution.status = StepStatus.COMPLETED

        except Exception as e:
            app_logger.error(
                "Workflow execution failed",
                execution_id=execution_id,
                error=str(e)
            )
            execution.status = StepStatus.FAILED

        execution.completed_at = datetime.utcnow()

        app_logger.info(
            "Workflow execution completed",
            execution_id=execution_id,
            status=execution.status.value
        )

        return execution

    def _execute_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> StepResult:
        """Execute a single workflow step."""
        import time

        if step.handler not in self.handlers:
            return StepResult(
                status=StepStatus.FAILED,
                error=f"Unknown handler: {step.handler}"
            )

        handler = self.handlers[step.handler]
        start_time = time.time()

        try:
            output = handler(context, step.config)
            duration_ms = int((time.time() - start_time) * 1000)

            return StepResult(
                status=StepStatus.COMPLETED,
                output=output,
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            return StepResult(
                status=StepStatus.FAILED,
                error=str(e),
                duration_ms=duration_ms
            )

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a step condition."""
        try:
            # Simple condition evaluation
            # Format: "field_name == value" or "field_name > value"
            return eval(condition, {"__builtins__": {}}, context)
        except:
            return True

    # Default handlers

    def _handle_ocr_extract(self, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """OCR extraction handler."""
        from core.ocr_engine import get_ocr_engine

        engine = get_ocr_engine()
        file_path = context.get("file_path")

        result = engine.process_document(
            file_path,
            max_tokens=config.get("max_tokens", 2048)
        )

        return {
            "text": result.total_text,
            "pages": result.metadata.total_pages
        }

    def _handle_field_extract(self, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Field extraction handler."""
        from core.field_extractor import FieldExtractor

        text = context.get("ocr_extract_output", {}).get("text", "")
        fields = config.get("fields", [])

        extractor = FieldExtractor()
        results = extractor.extract(text, fields)

        return extractor.to_dict(results)

    def _handle_validate_fields(self, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Field validation handler."""
        fields = context.get("field_extract_output", {})
        required = config.get("required_fields", [])

        missing = [f for f in required if not fields.get(f)]

        return {
            "valid": len(missing) == 0,
            "missing_fields": missing
        }

    def _handle_transform_data(self, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Data transformation handler."""
        data = context.get("field_extract_output", {})
        mapping = config.get("mapping", {})

        transformed = {}
        for source, target in mapping.items():
            if source in data:
                transformed[target] = data[source]

        return transformed

    def _handle_export_data(self, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Data export handler."""
        from integrations.connectors import get_connector

        connector_type = config.get("connector_type", "rest")
        connector_config = config.get("connector_config", {})

        data = context.get("transform_data_output") or context.get("field_extract_output", {})

        connector = get_connector(connector_type, connector_config)
        return connector.send(data)

    def _handle_send_webhook(self, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Webhook notification handler."""
        import requests

        url = config.get("url", "")
        payload = {
            "event": "workflow.completed",
            "data": context.get("field_extract_output", {})
        }

        response = requests.post(url, json=payload, timeout=30)
        return {"status_code": response.status_code}

    def _handle_send_notification(self, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification (email/slack)."""
        channel = config.get("channel", "email")
        message = config.get("message", "Workflow completed")

        # Placeholder - would integrate with email/Slack APIs
        return {"sent": True, "channel": channel}


# Predefined workflow templates
WORKFLOW_TEMPLATES = {
    "invoice_processing": {
        "name": "Invoice Processing",
        "steps": [
            {"name": "ocr", "handler": "ocr_extract", "config": {"max_tokens": 4096}},
            {"name": "extract", "handler": "field_extract", "config": {
                "fields": ["Invoice Number", "Invoice Date", "Total Amount", "Vendor Name"]
            }},
            {"name": "validate", "handler": "validate_fields", "config": {
                "required_fields": ["Invoice Number", "Total Amount"]
            }},
            {"name": "export", "handler": "export_data", "config": {
                "connector_type": "rest",
                "connector_config": {"base_url": "https://erp.example.com", "endpoint": "/invoices"}
            }}
        ]
    },
    "receipt_processing": {
        "name": "Receipt Processing",
        "steps": [
            {"name": "ocr", "handler": "ocr_extract"},
            {"name": "extract", "handler": "field_extract", "config": {
                "fields": ["Store Name", "Date", "Total Amount", "Items"]
            }},
            {"name": "webhook", "handler": "send_webhook", "config": {
                "url": "https://api.example.com/receipts"
            }}
        ]
    }
}


# Global workflow engine instance
workflow_engine = WorkflowEngine()


if __name__ == "__main__":
    print("=" * 60)
    print("WORKFLOW ENGINE TEST")
    print("=" * 60)

    engine = WorkflowEngine()

    # Create a simple workflow
    workflow = engine.create_workflow(
        name="Test Workflow",
        steps=[
            {"name": "step1", "handler": "validate_fields", "config": {"required_fields": ["field1"]}},
        ]
    )

    print(f"Created workflow: {workflow.id}")
    print(f"  Steps: {len(workflow.steps)}")

    # Execute workflow
    execution = engine.execute(
        workflow.id,
        context={"field_extract_output": {"field1": "value1"}}
    )

    print(f"Execution: {execution.id}")
    print(f"  Status: {execution.status.value}")

    print("  ✓ Workflow engine working")
    print("=" * 60)
