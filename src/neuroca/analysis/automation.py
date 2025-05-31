"""
Automation Pipeline Integration for Codebase Summarization

This module provides CI/CD integration and automation capabilities for the
11-step codebase summarization pipeline, including scheduling, monitoring,
and alerting functionality.
"""

import asyncio
import json
import yaml
import logging
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from ..analysis.summarization_engine import CodebaseSummarizationEngine, ScopeConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for automation pipeline"""
    triggers: List[str]
    schedule: str
    quality_threshold: float
    alerting: Dict[str, List[str]]
    retention_days: int
    workspace_path: str
    output_path: str
    encryption_enabled: bool
    notification_webhook: Optional[str] = None


@dataclass
class PipelineRun:
    """Record of a pipeline execution"""
    run_id: str
    started_at: str
    completed_at: Optional[str]
    status: str  # 'running', 'completed', 'failed', 'cancelled'
    trigger: str
    quality_score: Optional[float]
    artifacts_path: str
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None


class AutomationEngine:
    """Engine for automating the summarization pipeline"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.workspace_path = Path(config.workspace_path)
        self.output_path = Path(config.output_path)
        self.runs_history: List[PipelineRun] = []
        
        # Create output directory
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Load previous runs history
        self._load_runs_history()
    
    async def setup_automation(self):
        """Setup automation infrastructure"""
        logger.info("Setting up automation infrastructure")
        
        # Create GitHub Actions workflow
        await self._create_github_actions_workflow()
        
        # Create GitLab CI configuration
        await self._create_gitlab_ci_config()
        
        # Create Jenkins pipeline
        await self._create_jenkins_pipeline()
        
        # Create monitoring configuration
        await self._create_monitoring_config()
        
        # Setup scheduling
        await self._setup_scheduling()
        
    async def _create_github_actions_workflow(self):
        """Create GitHub Actions workflow for automated summarization"""
        workflow_content = """name: Automated Codebase Summarization

on:
  push:
    tags:
      - 'v*'
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main
  schedule:
    # Run weekly on Sundays at 2 AM UTC
    - cron: '0 2 * * 0'
  workflow_dispatch:
    inputs:
      force_quality:
        description: 'Force execution even if quality gates fail'
        required: false
        default: false
        type: boolean
      context_window:
        description: 'Target LLM context window size'
        required: false
        default: '128000'
        type: string

env:
  PYTHON_VERSION: '3.9'
  POETRY_VERSION: '1.4.2'

jobs:
  summarize-codebase:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Full history for git analysis
        submodules: true
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
      with:
        version: ${{ env.POETRY_VERSION }}
        virtualenvs-create: true
        virtualenvs-in-project: true
    
    - name: Load cached dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pypoetry
        key: poetry-${{ runner.os }}-${{ hashFiles('**/pyproject.toml') }}
    
    - name: Install dependencies
      run: |
        poetry install
    
    - name: Run tests (for dynamic analysis)
      run: |
        poetry run python -m pytest tests/ --cov=src --cov-report=json
      continue-on-error: true
    
    - name: Generate codebase summary
      run: |
        poetry run python -m neuroca.scripts.summarize_codebase \\
          --workspace . \\
          --context-window ${{ github.event.inputs.context_window || '128000' }} \\
          --log-level INFO \\
          ${{ github.event.inputs.force_quality == 'true' && '--force-quality' || '' }}
      env:
        SUMMARY_ENCRYPTION_KEY: ${{ secrets.SUMMARY_ENCRYPTION_KEY }}
    
    - name: Upload summarization artifacts
      uses: actions/upload-artifact@v3
      with:
        name: codebase-summary-${{ github.sha }}
        path: analysis_artifacts/summarization/
        retention-days: 30
    
    - name: Generate summary report
      run: |
        echo "## Codebase Summarization Report" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        if [ -f "analysis_artifacts/summarization/summary_report.md" ]; then
          cat analysis_artifacts/summarization/summary_report.md >> $GITHUB_STEP_SUMMARY
        else
          echo "Summary report not generated - check logs for errors" >> $GITHUB_STEP_SUMMARY
        fi
    
    - name: Notify on failure
      if: failure()
      uses: 8398a7/action-slack@v3
      with:
        status: failure
        text: "Codebase summarization pipeline failed for ${{ github.repository }}"
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
    
    - name: Notify on success
      if: success()
      uses: 8398a7/action-slack@v3
      with:
        status: success
        text: "Codebase summarization completed successfully for ${{ github.repository }}"
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

  drift-detection:
    runs-on: ubuntu-latest
    needs: summarize-codebase
    if: github.event_name == 'schedule'
    
    steps:
    - name: Download current summary
      uses: actions/download-artifact@v3
      with:
        name: codebase-summary-${{ github.sha }}
        path: current-summary/
    
    - name: Download previous summary
      uses: dawidd6/action-download-artifact@v2
      with:
        name: codebase-summary-*
        path: previous-summary/
        if_no_artifact_found: warn
      continue-on-error: true
    
    - name: Compare summaries for drift
      run: |
        python - << 'EOF'
        import json
        import os
        from pathlib import Path
        
        def calculate_drift(current_path, previous_path):
            try:
                with open(current_path / "metadata_package.json") as f:
                    current_data = json.load(f)
                with open(previous_path / "metadata_package.json") as f:
                    previous_data = json.load(f)
                
                # Simple drift calculation
                current_files = len(current_data.get("files", {}))
                previous_files = len(previous_data.get("files", {}))
                
                drift_ratio = abs(current_files - previous_files) / max(previous_files, 1)
                return drift_ratio
            except Exception as e:
                print(f"Error calculating drift: {e}")
                return 0.0
        
        current_dir = Path("current-summary")
        previous_dir = Path("previous-summary")
        
        if previous_dir.exists():
            drift = calculate_drift(current_dir, previous_dir)
            print(f"Detected drift ratio: {drift:.2%}")
            
            if drift > 0.1:  # 10% threshold
                print("::warning::Significant codebase drift detected!")
                with open(os.environ["GITHUB_ENV"], "a") as f:
                    f.write(f"DRIFT_DETECTED=true\\n")
                    f.write(f"DRIFT_RATIO={drift:.2%}\\n")
        EOF
    
    - name: Alert on drift
      if: env.DRIFT_DETECTED == 'true'
      uses: 8398a7/action-slack@v3
      with:
        status: warning
        text: "Significant codebase drift detected: ${{ env.DRIFT_RATIO }}"
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
"""
        
        workflow_path = self.workspace_path / ".github" / "workflows" / "summarize-codebase.yml"
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(workflow_path, 'w') as f:
            f.write(workflow_content)
            
        logger.info(f"GitHub Actions workflow created: {workflow_path}")
    
    async def _create_gitlab_ci_config(self):
        """Create GitLab CI configuration"""
        gitlab_config = """stages:
  - prepare
  - analyze
  - summarize
  - notify

variables:
  PYTHON_VERSION: "3.9"
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - .venv/

before_script:
  - python -V
  - pip install poetry
  - poetry config virtualenvs.in-project true
  - poetry install

prepare:
  stage: prepare
  script:
    - echo "Preparing environment for codebase summarization"
    - poetry run python --version
    - poetry show
  artifacts:
    paths:
      - .venv/
    expire_in: 1 hour

analyze:
  stage: analyze
  needs: ["prepare"]
  script:
    - echo "Running static and dynamic analysis"
    - poetry run python -m pytest tests/ --cov=src --cov-report=json || true
  artifacts:
    paths:
      - coverage.json
      - htmlcov/
    expire_in: 1 week
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

summarize:
  stage: summarize
  needs: ["analyze"]
  script:
    - echo "Generating codebase summary"
    - poetry run python -m neuroca.scripts.summarize_codebase
        --workspace .
        --context-window 128000
        --log-level INFO
  artifacts:
    paths:
      - analysis_artifacts/
    expire_in: 1 month
  only:
    - main
    - develop
    - tags
    - schedules

notify_success:
  stage: notify
  needs: ["summarize"]
  script:
    - echo "Summarization completed successfully"
    - |
      curl -X POST "$SLACK_WEBHOOK_URL" \\
        -H 'Content-type: application/json' \\
        --data '{"text":"Codebase summarization completed for '$CI_PROJECT_NAME'"}'
  only:
    - main
    - develop
    - tags
    - schedules
  when: on_success

notify_failure:
  stage: notify
  script:
    - echo "Summarization failed"
    - |
      curl -X POST "$SLACK_WEBHOOK_URL" \\
        -H 'Content-type: application/json' \\
        --data '{"text":"Codebase summarization FAILED for '$CI_PROJECT_NAME'"}'
  when: on_failure

# Schedule: Run weekly on Sundays at 2 AM
schedule_weekly:
  extends: summarize
  only:
    - schedules
"""
        
        gitlab_path = self.workspace_path / ".gitlab-ci.yml"
        with open(gitlab_path, 'w') as f:
            f.write(gitlab_config)
            
        logger.info(f"GitLab CI configuration created: {gitlab_path}")
    
    async def _create_jenkins_pipeline(self):
        """Create Jenkins pipeline configuration"""
        jenkins_config = """pipeline {
    agent any
    
    parameters {
        choice(
            name: 'CONTEXT_WINDOW',
            choices: ['128000', '200000', '100000'],
            description: 'Target LLM context window size'
        )
        booleanParam(
            name: 'FORCE_QUALITY',
            defaultValue: false,
            description: 'Force execution even if quality gates fail'
        )
    }
    
    environment {
        PYTHON_VERSION = '3.9'
        POETRY_HOME = "${env.WORKSPACE}/.poetry"
        PATH = "${env.POETRY_HOME}/bin:${env.PATH}"
    }
    
    triggers {
        // Run weekly on Sundays at 2 AM
        cron('0 2 * * 0')
        
        // Run on pushes to main/develop
        pollSCM('H/5 * * * *')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                }
            }
        }
        
        stage('Setup Environment') {
            steps {
                sh '''
                    curl -sSL https://install.python-poetry.org | python3 -
                    poetry config virtualenvs.in-project true
                    poetry install
                '''
            }
        }
        
        stage('Run Tests') {
            steps {
                sh '''
                    poetry run python -m pytest tests/ \\
                        --cov=src \\
                        --cov-report=xml \\
                        --cov-report=html \\
                        --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    publishTestResults testResultsPattern: 'test-results.xml'
                    publishCoverage adapters: [
                        coberturaAdapter('coverage.xml')
                    ], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                }
            }
        }
        
        stage('Generate Summary') {
            steps {
                sh \"""
                    poetry run python -m neuroca.scripts.summarize_codebase \\
                        --workspace . \\
                        --context-window ${params.CONTEXT_WINDOW} \\
                        --log-level INFO \\
                        ${params.FORCE_QUALITY ? '--force-quality' : ''}
                \"""
            }
        }
        
        stage('Archive Artifacts') {
            steps {
                archiveArtifacts artifacts: 'analysis_artifacts/**/*', 
                                allowEmptyArchive: false
                
                script {
                    // Create summary for build description
                    if (fileExists('analysis_artifacts/summarization/summary_report.md')) {
                        def summary = readFile('analysis_artifacts/summarization/summary_report.md')
                        currentBuild.description = "Codebase Summary Generated"
                    }
                }
            }
        }
    }
    
    post {
        success {
            slackSend(
                channel: '#devops',
                color: 'good',
                message: "✅ Codebase summarization completed for ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            )
        }
        
        failure {
            slackSend(
                channel: '#devops',
                color: 'danger',
                message: "❌ Codebase summarization failed for ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            )
        }
        
        always {
            cleanWs()
        }
    }
}
"""
        
        jenkins_path = self.workspace_path / "Jenkinsfile"
        with open(jenkins_path, 'w') as f:
            f.write(jenkins_config)
            
        logger.info(f"Jenkins pipeline created: {jenkins_path}")
    
    async def _create_monitoring_config(self):
        """Create monitoring and alerting configuration"""
        
        # Prometheus monitoring configuration
        prometheus_config = """global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'codebase-summarization'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

rule_files:
  - "summarization_alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
"""
        
        # Alerting rules
        alert_rules = """groups:
- name: codebase_summarization
  rules:
  - alert: SummarizationPipelineFailed
    expr: summarization_pipeline_success == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Codebase summarization pipeline failed"
      description: "The codebase summarization pipeline has failed for {{ $labels.repository }}"

  - alert: QualityGatesFailure
    expr: summarization_quality_score < 0.8
    for: 0m
    labels:
      severity: warning
    annotations:
      summary: "Quality gates failing"
      description: "Summarization quality score is {{ $value }}, below threshold of 0.8"

  - alert: SignificantCodebaseDrift
    expr: summarization_drift_ratio > 0.1
    for: 0m
    labels:
      severity: warning
    annotations:
      summary: "Significant codebase drift detected"
      description: "Codebase drift ratio is {{ $value }}, indicating significant changes"
"""
        
        monitoring_dir = self.workspace_path / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)
        
        with open(monitoring_dir / "prometheus.yml", 'w') as f:
            f.write(prometheus_config)
            
        with open(monitoring_dir / "summarization_alerts.yml", 'w') as f:
            f.write(alert_rules)
            
        # Grafana dashboard configuration
        dashboard_config = {
            "dashboard": {
                "title": "Codebase Summarization Metrics",
                "panels": [
                    {
                        "title": "Pipeline Success Rate",
                        "type": "stat",
                        "targets": [{"expr": "rate(summarization_pipeline_success[24h])"}]
                    },
                    {
                        "title": "Quality Score Trend",
                        "type": "graph",
                        "targets": [{"expr": "summarization_quality_score"}]
                    },
                    {
                        "title": "Codebase Drift",
                        "type": "graph", 
                        "targets": [{"expr": "summarization_drift_ratio"}]
                    }
                ]
            }
        }
        
        with open(monitoring_dir / "grafana_dashboard.json", 'w') as f:
            json.dump(dashboard_config, f, indent=2)
            
        logger.info(f"Monitoring configuration created in: {monitoring_dir}")
    
    async def _setup_scheduling(self):
        """Setup scheduling for automated runs"""
        
        # Cron configuration for Unix systems
        cron_config = """# Codebase Summarization Automation
# Run weekly on Sundays at 2 AM
0 2 * * 0 cd {workspace} && python -m neuroca.scripts.summarize_codebase --workspace . --log-level INFO

# Run on the 1st of each month for comprehensive analysis
0 3 1 * * cd {workspace} && python -m neuroca.scripts.summarize_codebase --workspace . --context-window 200000 --log-level DEBUG
""".format(workspace=self.workspace_path)
        
        # Windows Task Scheduler XML
        task_scheduler_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2024-01-01T02:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByWeek>
        <DaysOfWeek>Sunday</DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>python</Command>
      <Arguments>-m neuroca.scripts.summarize_codebase --workspace {self.workspace_path}</Arguments>
      <WorkingDirectory>{self.workspace_path}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""
        
        scheduling_dir = self.workspace_path / "scheduling"
        scheduling_dir.mkdir(exist_ok=True)
        
        with open(scheduling_dir / "crontab", 'w') as f:
            f.write(cron_config)
            
        with open(scheduling_dir / "windows_task.xml", 'w') as f:
            f.write(task_scheduler_xml)
            
        # Docker Compose for scheduled execution
        docker_compose = """version: '3.8'

services:
  summarization-scheduler:
    build:
      context: .
      dockerfile: Dockerfile.summarization
    volumes:
      - .:/workspace
      - ./analysis_artifacts:/artifacts
    environment:
      - WORKSPACE_PATH=/workspace
      - OUTPUT_PATH=/artifacts
      - SUMMARY_ENCRYPTION_KEY=${SUMMARY_ENCRYPTION_KEY}
    command: >
      sh -c "
        echo '0 2 * * 0 cd /workspace && python -m neuroca.scripts.summarize_codebase' | crontab -
        crond -f
      "
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/summarization_alerts.yml:/etc/prometheus/summarization_alerts.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./monitoring/grafana_dashboard.json:/var/lib/grafana/dashboards/summarization.json
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
"""
        
        with open(scheduling_dir / "docker-compose.yml", 'w') as f:
            f.write(docker_compose)
            
        logger.info(f"Scheduling configuration created in: {scheduling_dir}")
    
    async def execute_scheduled_run(self, trigger: str = "scheduled") -> PipelineRun:
        """Execute a scheduled pipeline run"""
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        run = PipelineRun(
            run_id=run_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            completed_at=None,
            status="running",
            trigger=trigger,
            quality_score=None,
            artifacts_path=str(self.output_path / run_id)
        )
        
        self.runs_history.append(run)
        logger.info(f"Starting scheduled run: {run_id}")
        
        try:
            # Create scope configuration
            scope = ScopeConfig(
                repos=["main"],
                branches=["main"],
                target_llm_profile={
                    "context_window": 128000,
                    "input_limits": 100000
                }
            )
            
            # Execute summarization pipeline
            engine = CodebaseSummarizationEngine(scope, str(self.workspace_path))
            bundle = await engine.execute_full_pipeline()
            
            # Update run status
            run.completed_at = datetime.now(timezone.utc).isoformat()
            run.status = "completed"
            run.quality_score = bundle.quality_metrics.get('overall_passed', 0.0)
            run.metrics = {
                "total_files": len(engine.file_metadata),
                "total_chunks": len(bundle.chunk_manifest),
                "quality_passed": bundle.quality_metrics.get('overall_passed', False)
            }
            
            # Send success notification
            await self._send_notification("success", run)
            
            logger.info(f"Scheduled run completed successfully: {run_id}")
            
        except Exception as e:
            run.completed_at = datetime.now(timezone.utc).isoformat()
            run.status = "failed"
            run.error_message = str(e)
            
            # Send failure notification
            await self._send_notification("failure", run)
            
            logger.error(f"Scheduled run failed: {run_id} - {e}")
            
        finally:
            self._save_runs_history()
            
        return run
    
    async def _send_notification(self, status: str, run: PipelineRun):
        """Send notification about pipeline run"""
        if not self.config.notification_webhook:
            return
            
        message = {
            "text": f"Codebase Summarization {status.upper()}",
            "attachments": [
                {
                    "color": "good" if status == "success" else "danger",
                    "fields": [
                        {"title": "Run ID", "value": run.run_id, "short": True},
                        {"title": "Trigger", "value": run.trigger, "short": True},
                        {"title": "Status", "value": run.status, "short": True},
                        {"title": "Quality Score", "value": str(run.quality_score), "short": True}
                    ]
                }
            ]
        }
        
        if run.error_message:
            message["attachments"][0]["fields"].append({
                "title": "Error", "value": run.error_message, "short": False
            })
            
        try:
            import requests
            requests.post(self.config.notification_webhook, json=message)
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
    
    def _load_runs_history(self):
        """Load pipeline runs history"""
        history_file = self.output_path / "runs_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.runs_history = [PipelineRun(**run) for run in data]
            except Exception as e:
                logger.warning(f"Failed to load runs history: {e}")
                self.runs_history = []
    
    def _save_runs_history(self):
        """Save pipeline runs history"""
        history_file = self.output_path / "runs_history.json"
        try:
            with open(history_file, 'w') as f:
                json.dump([asdict(run) for run in self.runs_history], f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save runs history: {e}")
    
    async def cleanup_old_artifacts(self):
        """Clean up old artifacts based on retention policy"""
        logger.info("Cleaning up old artifacts")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.retention_days)
        
        for run in self.runs_history:
            run_date = datetime.fromisoformat(run.started_at.replace('Z', '+00:00'))
            if run_date < cutoff_date:
                artifacts_path = Path(run.artifacts_path)
                if artifacts_path.exists():
                    import shutil
                    shutil.rmtree(artifacts_path)
                    logger.info(f"Cleaned up artifacts for run: {run.run_id}")
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get pipeline performance metrics"""
        if not self.runs_history:
            return {"total_runs": 0}
            
        total_runs = len(self.runs_history)
        successful_runs = len([r for r in self.runs_history if r.status == "completed"])
        failed_runs = len([r for r in self.runs_history if r.status == "failed"])
        
        recent_runs = [r for r in self.runs_history 
                      if datetime.fromisoformat(r.started_at.replace('Z', '+00:00')) > 
                         datetime.now(timezone.utc) - timedelta(days=30)]
        
        avg_quality_score = 0.0
        if recent_runs:
            scores = [r.quality_score for r in recent_runs if r.quality_score is not None]
            if scores:
                avg_quality_score = sum(scores) / len(scores)
        
        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": successful_runs / total_runs if total_runs > 0 else 0.0,
            "recent_runs_30d": len(recent_runs),
            "avg_quality_score": avg_quality_score,
            "last_run": self.runs_history[-1].started_at if self.runs_history else None
        }


# Factory function for creating automation engine
def create_automation_engine(
    workspace_path: str,
    output_path: str = None,
    quality_threshold: float = 0.8,
    retention_days: int = 30
) -> AutomationEngine:
    """Factory function to create automation engine with default configuration"""
    
    if output_path is None:
        output_path = str(Path(workspace_path) / "analysis_artifacts" / "automation")
        
    config = PipelineConfig(
        triggers=["on_tag", "on_merge_to_main", "scheduled_weekly"],
        schedule="0 2 * * 0",  # Weekly on Sunday at 2 AM
        quality_threshold=quality_threshold,
        alerting={
            "on_failure": ["email", "slack"],
            "on_completion": ["email"],
            "on_drift_threshold": ["slack"]
        },
        retention_days=retention_days,
        workspace_path=workspace_path,
        output_path=output_path,
        encryption_enabled=True,
        notification_webhook=os.environ.get('SLACK_WEBHOOK_URL')
    )
    
    return AutomationEngine(config)
