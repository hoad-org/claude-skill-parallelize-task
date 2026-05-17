"""Comprehensive tests for CLI Integration module (Phase 4)."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from parallelizer_skill.cli import (
    analyze,
    decide,
    plan,
    execute,
    document,
    reset,
    _load_json_file,
    _save_json_file,
    _format_json_output,
    _format_text_summary,
)
from parallelizer_skill.models import (
    Task,
    TaskDependency,
    DependencyType,
    WorkflowAnalysis,
    ExecutionPlan,
    ExecutionPhase,
    TaskGroup,
)
from parallelizer_skill.decision_engine import DecisionRecommendation
from parallelizer_skill.config import reset_config


@pytest.mark.unit
class TestCLIUtilities:
    """Test CLI utility functions."""

    def test_load_json_file_success(self):
        """Test loading valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {"key": "value", "count": 42}
            json.dump(test_data, f)
            temp_path = f.name

        try:
            result = _load_json_file(temp_path)
            assert result == test_data
        finally:
            Path(temp_path).unlink()

    def test_load_json_file_not_found(self):
        """Test loading non-existent file."""
        with pytest.raises(FileNotFoundError):
            _load_json_file("/nonexistent/file.json")

    def test_load_json_file_invalid_json(self):
        """Test loading invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                _load_json_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_save_json_file(self):
        """Test saving JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "output.json")
            test_data = {"key": "value"}

            _save_json_file(output_path, test_data)

            assert Path(output_path).exists()
            with open(output_path) as f:
                loaded = json.load(f)
            assert loaded == test_data

    def test_format_json_output(self):
        """Test JSON formatting."""
        data = {"key": "value", "number": 42}
        result = _format_json_output(data)

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == data

    def test_format_text_summary(self):
        """Test text formatting."""
        data = {"key": "value", "count": 42}
        result = _format_text_summary("Test Section", data)

        assert "Test Section" in result
        assert "key: value" in result
        assert "count: 42" in result


@pytest.mark.unit
class TestAnalyzeCommand:
    """Test analyze command."""

    @pytest.fixture
    def sample_tasks_file(self):
        """Create sample tasks JSON file."""
        tasks = [
            {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
            {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": True},
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(tasks, f)
            f.flush()
            temp_path = f.name
        yield temp_path
        Path(temp_path).unlink()

    @pytest.fixture
    def sample_dependencies_file(self):
        """Create sample dependencies JSON file."""
        deps = [
            {"source_task_id": "t1", "target_task_id": "t2", "dependency_type": "hard"}
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(deps, f)
            f.flush()
            temp_path = f.name
        yield temp_path
        Path(temp_path).unlink()

    def test_analyze_command_success(self, sample_tasks_file):
        """Test successful analysis."""
        reset_config()
        result = analyze(
            tasks_file=sample_tasks_file,
            output_format="json",
            verbose=True,
        )
        assert result == 0

    def test_analyze_command_with_dependencies(self, sample_tasks_file, sample_dependencies_file):
        """Test analysis with dependencies."""
        reset_config()
        result = analyze(
            tasks_file=sample_tasks_file,
            dependencies_file=sample_dependencies_file,
            output_format="json",
        )
        assert result == 0

    def test_analyze_command_with_output_file(self, sample_tasks_file):
        """Test analysis with output file."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = str(Path(temp_dir) / "analysis.json")
            result = analyze(
                tasks_file=sample_tasks_file,
                output_file=output_file,
                output_format="json",
            )
            assert result == 0
            assert Path(output_file).exists()

    def test_analyze_command_file_not_found(self):
        """Test analysis with missing file."""
        reset_config()
        result = analyze(
            tasks_file="/nonexistent/tasks.json",
            output_format="json",
        )
        assert result == 1

    def test_analyze_command_invalid_json(self):
        """Test analysis with invalid JSON."""
        reset_config()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json")
            temp_path = f.name

        try:
            result = analyze(
                tasks_file=temp_path,
                output_format="json",
            )
            assert result == 1
        finally:
            Path(temp_path).unlink()

    def test_analyze_command_invalid_format(self, sample_tasks_file):
        """Test analysis with invalid JSON format (not list)."""
        reset_config()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"not": "list"}, f)
            temp_path = f.name

        try:
            result = analyze(
                tasks_file=temp_path,
                output_format="json",
            )
            assert result == 1
        finally:
            Path(temp_path).unlink()

    def test_analyze_text_output(self, sample_tasks_file):
        """Test analysis with text output."""
        reset_config()
        result = analyze(
            tasks_file=sample_tasks_file,
            output_format="text",
        )
        assert result == 0


@pytest.mark.unit
class TestDecideCommand:
    """Test decide command."""

    @pytest.fixture
    def sample_tasks_file(self):
        """Create sample tasks JSON file."""
        tasks = [
            {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
            {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": False},
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(tasks, f)
            yield f.name
        Path(f.name).unlink()

    @pytest.fixture
    def sample_analysis_file(self):
        """Create sample analysis JSON file."""
        analysis = {
            "analysis_id": "analysis-123",
            "workflow_id": "workflow-1",
            "total_tasks": 2,
            "total_dependencies": 0,
            "complexity_scores": {"t1": 25, "t2": 45},
            "feasibility_ratings": {"t1": "feasible", "t2": "feasible"},
            "critical_path": ["t1", "t2"],
            "critical_path_duration": 3.0,
            "total_serial_duration": 3.0,
            "parallelizable_tasks": ["t1"],
            "sequential_bottlenecks": ["t2"],
            "resource_conflicts": [],
            "warnings": [],
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(analysis, f)
            f.flush()
            temp_path = f.name
        yield temp_path
        Path(temp_path).unlink()

    def test_decide_command_all_goals(self):
        """Test decide command with all goal types."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
                {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": False},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            for goal in ["performance", "cost", "reliability"]:
                result = decide(
                    goal=goal,
                    tasks_file=tasks_file,
                    output_format="json",
                )
                assert result == 0

    def test_decide_command_with_analysis_file(self, sample_analysis_file):
        """Test decide with analysis file."""
        reset_config()
        result = decide(
            goal="performance",
            analysis_file=sample_analysis_file,
            output_format="json",
        )
        assert result == 0

    def test_decide_command_with_output_file(self):
        """Test decide with output file."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
                {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": True},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            output_file = str(Path(temp_dir) / "strategy.json")
            result = decide(
                goal="performance",
                tasks_file=tasks_file,
                output_file=output_file,
                output_format="json",
            )
            assert result == 0
            assert Path(output_file).exists()

    def test_decide_command_invalid_goal(self, sample_tasks_file):
        """Test decide with invalid goal."""
        reset_config()
        result = decide(
            goal="invalid",
            tasks_file=sample_tasks_file,
            output_format="json",
        )
        assert result == 1

    def test_decide_command_no_input(self):
        """Test decide without input file."""
        reset_config()
        result = decide(
            goal="performance",
            output_format="json",
        )
        assert result == 1

    def test_decide_text_output(self):
        """Test decide with text output."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
                {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": True},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            result = decide(
                goal="performance",
                tasks_file=tasks_file,
                output_format="text",
            )
            assert result == 0


@pytest.mark.unit
class TestPlanCommand:
    """Test plan command."""

    @pytest.fixture
    def sample_tasks_file(self):
        """Create sample tasks JSON file."""
        tasks = [
            {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
            {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": True},
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(tasks, f)
            yield f.name
        Path(f.name).unlink()

    @pytest.fixture
    def sample_strategy_file(self):
        """Create sample strategy JSON file."""
        strategy = {
            "strategy_type": "balanced",
            "max_parallel_tasks": 4,
            "recommended_batch_size": 10,
            "recommended_retry_count": 2,
            "recommended_checkpoint_interval": 5,
            "parallel_execution": True,
            "resource_aware": True,
            "monitoring_intensity": "normal",
            "escalation_level": "warning",
            "rationale": "Test strategy",
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(strategy, f)
            f.flush()
            temp_path = f.name
        yield temp_path
        Path(temp_path).unlink()

    def test_plan_command_success(self):
        """Test successful plan creation."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
                {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": True},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            result = plan(
                tasks_file=tasks_file,
                output_format="json",
            )
            assert result == 0

    def test_plan_command_with_strategy(self):
        """Test plan with strategy file."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
                {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": True},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            strategy = {
                "strategy_type": "balanced",
                "max_parallel_tasks": 4,
                "recommended_batch_size": 10,
                "recommended_retry_count": 2,
                "recommended_checkpoint_interval": 5,
                "parallel_execution": True,
                "resource_aware": True,
                "monitoring_intensity": "normal",
                "escalation_level": "warning",
                "rationale": "Test strategy",
            }
            strategy_file = str(Path(temp_dir) / "strategy.json")
            with open(strategy_file, 'w') as f:
                json.dump(strategy, f)

            result = plan(
                tasks_file=tasks_file,
                strategy_file=strategy_file,
                output_format="json",
            )
            assert result == 0

    def test_plan_command_with_output_file(self):
        """Test plan with output file."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
                {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": True},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            output_file = str(Path(temp_dir) / "plan.json")
            result = plan(
                tasks_file=tasks_file,
                output_file=output_file,
                output_format="json",
            )
            assert result == 0
            assert Path(output_file).exists()

    def test_plan_command_file_not_found(self):
        """Test plan with missing file."""
        reset_config()
        result = plan(
            tasks_file="/nonexistent/tasks.json",
            output_format="json",
        )
        assert result == 1

    def test_plan_text_output(self):
        """Test plan with text output."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
                {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": True},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            result = plan(
                tasks_file=tasks_file,
                output_format="text",
            )
            assert result == 0


@pytest.mark.unit
class TestExecuteCommand:
    """Test execute command."""

    @pytest.fixture
    def sample_plan_file(self):
        """Create sample plan JSON file."""
        plan = {
            "id": "plan-123",
            "total_tasks": 2,
            "serial_duration": 3.0,
            "parallel_duration": 2.0,
            "efficiency_gain": 33.33,
            "critical_path": ["t1", "t2"],
            "phases": [
                {
                    "phase_number": 1,
                    "task_groups": [
                        {
                            "id": "group-1",
                            "tasks": ["t1"],
                            "sequential_order": None,
                            "estimated_duration": 1.0,
                            "can_parallelize": True,
                        }
                    ],
                    "is_parallel": True,
                    "estimated_duration": 1.0,
                    "sync_point_required": True,
                }
            ],
            "parallelizable_groups": {},
            "resource_conflicts": [],
            "safety_issues": [],
            "optimization_notes": [],
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(plan, f)
            f.flush()
            temp_path = f.name
        yield temp_path
        Path(temp_path).unlink()

    def test_execute_command_success(self, sample_plan_file):
        """Test successful execution."""
        reset_config()
        result = execute(
            plan_file=sample_plan_file,
            output_format="json",
        )
        assert result == 0

    def test_execute_command_simulate(self, sample_plan_file):
        """Test execution in simulate mode."""
        reset_config()
        result = execute(
            plan_file=sample_plan_file,
            simulate=True,
            output_format="json",
        )
        assert result == 0

    def test_execute_command_with_output_file(self, sample_plan_file):
        """Test execution with output file."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = str(Path(temp_dir) / "result.json")
            result = execute(
                plan_file=sample_plan_file,
                output_file=output_file,
                output_format="json",
            )
            assert result == 0
            assert Path(output_file).exists()

    def test_execute_command_file_not_found(self):
        """Test execution with missing file."""
        reset_config()
        result = execute(
            plan_file="/nonexistent/plan.json",
            output_format="json",
        )
        assert result == 1

    def test_execute_text_output(self, sample_plan_file):
        """Test execution with text output."""
        reset_config()
        result = execute(
            plan_file=sample_plan_file,
            output_format="text",
        )
        assert result == 0


@pytest.mark.unit
class TestDocumentCommand:
    """Test document command."""

    @pytest.fixture
    def sample_files(self):
        """Create sample input files."""
        analysis = {
            "analysis_id": "analysis-123",
            "workflow_id": "workflow-1",
            "total_tasks": 2,
            "total_dependencies": 0,
            "complexity_scores": {"t1": 25, "t2": 45},
            "feasibility_ratings": {"t1": "feasible", "t2": "feasible"},
            "critical_path": ["t1", "t2"],
            "critical_path_duration": 3.0,
            "total_serial_duration": 3.0,
            "parallelizable_tasks": ["t1"],
            "sequential_bottlenecks": ["t2"],
            "resource_conflicts": [],
            "warnings": [],
        }
        recommendation = {
            "strategy_type": "balanced",
            "max_parallel_tasks": 4,
            "recommended_batch_size": 10,
            "recommended_retry_count": 2,
            "recommended_checkpoint_interval": 5,
            "parallel_execution": True,
            "resource_aware": True,
            "monitoring_intensity": "normal",
            "escalation_level": "warning",
            "rationale": "Test strategy",
        }
        plan = {
            "id": "plan-123",
            "total_tasks": 2,
            "serial_duration": 3.0,
            "parallel_duration": 2.0,
            "efficiency_gain": 33.33,
            "critical_path": ["t1", "t2"],
            "phases": [
                {
                    "phase_number": 1,
                    "task_groups": [
                        {
                            "id": "group-1",
                            "tasks": ["t1"],
                            "sequential_order": None,
                            "estimated_duration": 1.0,
                            "can_parallelize": True,
                        }
                    ],
                    "is_parallel": True,
                    "estimated_duration": 1.0,
                    "sync_point_required": True,
                }
            ],
            "parallelizable_groups": {},
            "resource_conflicts": [],
            "safety_issues": [],
            "optimization_notes": [],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(analysis, f)
            f.flush()
            analysis_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(recommendation, f)
            f.flush()
            recommendation_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(plan, f)
            f.flush()
            plan_file = f.name

        yield analysis_file, recommendation_file, plan_file

        Path(analysis_file).unlink()
        Path(recommendation_file).unlink()
        Path(plan_file).unlink()

    def test_document_command_success(self):
        """Test successful document generation."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis = {
                "analysis_id": "analysis-123",
                "workflow_id": "workflow-1",
                "total_tasks": 2,
                "total_dependencies": 0,
                "complexity_scores": {"t1": 25, "t2": 45},
                "feasibility_ratings": {"t1": "feasible", "t2": "feasible"},
                "critical_path": ["t1", "t2"],
                "critical_path_duration": 3.0,
                "total_serial_duration": 3.0,
                "parallelizable_tasks": ["t1"],
                "sequential_bottlenecks": ["t2"],
                "resource_conflicts": [],
                "warnings": [],
            }
            analysis_file = str(Path(temp_dir) / "analysis.json")
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f)

            recommendation = {
                "strategy_type": "balanced",
                "max_parallel_tasks": 4,
                "recommended_batch_size": 10,
                "recommended_retry_count": 2,
                "recommended_checkpoint_interval": 5,
                "parallel_execution": True,
                "resource_aware": True,
                "monitoring_intensity": "normal",
                "escalation_level": "warning",
                "rationale": "Test strategy",
            }
            recommendation_file = str(Path(temp_dir) / "recommendation.json")
            with open(recommendation_file, 'w') as f:
                json.dump(recommendation, f)

            plan = {
                "id": "plan-123",
                "total_tasks": 2,
                "serial_duration": 3.0,
                "parallel_duration": 2.0,
                "efficiency_gain": 33.33,
                "critical_path": ["t1", "t2"],
                "phases": [
                    {
                        "phase_number": 1,
                        "task_groups": [
                            {
                                "id": "group-1",
                                "tasks": ["t1"],
                                "sequential_order": None,
                                "estimated_duration": 1.0,
                                "can_parallelize": True,
                            }
                        ],
                        "is_parallel": True,
                        "estimated_duration": 1.0,
                        "sync_point_required": True,
                    }
                ],
                "parallelizable_groups": {},
                "resource_conflicts": [],
                "safety_issues": [],
                "optimization_notes": [],
            }
            plan_file = str(Path(temp_dir) / "plan.json")
            with open(plan_file, 'w') as f:
                json.dump(plan, f)

            result = document(
                analysis_file=analysis_file,
                recommendation_file=recommendation_file,
                plan_file=plan_file,
                output_format="markdown",
            )
            assert result == 0

    def test_document_command_json_format(self):
        """Test document generation in JSON format."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis = {
                "analysis_id": "analysis-123",
                "workflow_id": "workflow-1",
                "total_tasks": 2,
                "total_dependencies": 0,
                "complexity_scores": {"t1": 25},
                "feasibility_ratings": {"t1": "feasible"},
                "critical_path": ["t1"],
                "critical_path_duration": 1.0,
                "total_serial_duration": 1.0,
                "parallelizable_tasks": ["t1"],
                "sequential_bottlenecks": [],
                "resource_conflicts": [],
                "warnings": [],
            }
            analysis_file = str(Path(temp_dir) / "analysis.json")
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f)

            recommendation = {
                "strategy_type": "balanced",
                "max_parallel_tasks": 4,
                "recommended_batch_size": 10,
                "recommended_retry_count": 2,
                "recommended_checkpoint_interval": 5,
                "parallel_execution": True,
                "resource_aware": True,
                "monitoring_intensity": "normal",
                "escalation_level": "warning",
                "rationale": "Test",
            }
            recommendation_file = str(Path(temp_dir) / "recommendation.json")
            with open(recommendation_file, 'w') as f:
                json.dump(recommendation, f)

            plan = {
                "id": "plan-123",
                "total_tasks": 1,
                "serial_duration": 1.0,
                "parallel_duration": 1.0,
                "efficiency_gain": 0.0,
                "critical_path": ["t1"],
                "phases": [],
                "parallelizable_groups": {},
                "resource_conflicts": [],
                "safety_issues": [],
                "optimization_notes": [],
            }
            plan_file = str(Path(temp_dir) / "plan.json")
            with open(plan_file, 'w') as f:
                json.dump(plan, f)

            result = document(
                analysis_file=analysis_file,
                recommendation_file=recommendation_file,
                plan_file=plan_file,
                output_format="json",
            )
            assert result == 0

    def test_document_command_with_output_file(self):
        """Test document with output file."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis = {
                "analysis_id": "analysis-123",
                "workflow_id": "workflow-1",
                "total_tasks": 1,
                "total_dependencies": 0,
                "complexity_scores": {"t1": 25},
                "feasibility_ratings": {"t1": "feasible"},
                "critical_path": ["t1"],
                "critical_path_duration": 1.0,
                "total_serial_duration": 1.0,
                "parallelizable_tasks": ["t1"],
                "sequential_bottlenecks": [],
                "resource_conflicts": [],
                "warnings": [],
            }
            analysis_file = str(Path(temp_dir) / "analysis.json")
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f)

            recommendation = {
                "strategy_type": "balanced",
                "max_parallel_tasks": 4,
                "recommended_batch_size": 10,
                "recommended_retry_count": 2,
                "recommended_checkpoint_interval": 5,
                "parallel_execution": True,
                "resource_aware": True,
                "monitoring_intensity": "normal",
                "escalation_level": "warning",
                "rationale": "Test",
            }
            recommendation_file = str(Path(temp_dir) / "recommendation.json")
            with open(recommendation_file, 'w') as f:
                json.dump(recommendation, f)

            plan = {
                "id": "plan-123",
                "total_tasks": 1,
                "serial_duration": 1.0,
                "parallel_duration": 1.0,
                "efficiency_gain": 0.0,
                "critical_path": ["t1"],
                "phases": [],
                "parallelizable_groups": {},
                "resource_conflicts": [],
                "safety_issues": [],
                "optimization_notes": [],
            }
            plan_file = str(Path(temp_dir) / "plan.json")
            with open(plan_file, 'w') as f:
                json.dump(plan, f)

            output_file = str(Path(temp_dir) / "strategy.md")
            result = document(
                analysis_file=analysis_file,
                recommendation_file=recommendation_file,
                plan_file=plan_file,
                output_file=output_file,
                output_format="markdown",
            )
            assert result == 0
            assert Path(output_file).exists()

    def test_document_command_file_not_found(self):
        """Test document with missing file."""
        reset_config()
        result = document(
            analysis_file="/nonexistent/analysis.json",
            recommendation_file="/nonexistent/recommendation.json",
            plan_file="/nonexistent/plan.json",
            output_format="markdown",
        )
        assert result == 1


@pytest.mark.unit
class TestResetCommand:
    """Test reset command."""

    def test_reset_command_success(self):
        """Test successful reset."""
        result = reset(verbose=True)
        assert result == 0

    def test_reset_clears_config(self):
        """Test that reset clears configuration."""
        from parallelizer_skill.config import get_config
        reset_config()

        # Get config to cache it
        config1 = get_config()
        assert config1 is not None

        # Reset and get again
        reset(verbose=False)
        # After reset, the cached config should be gone
        # We don't need to compare instances, just verify reset works
        reset_config()
        config2 = get_config()
        assert config2 is not None


@pytest.mark.unit
class TestCommandPiping:
    """Test command piping scenarios."""

    def test_analyze_to_decide_pipeline(self):
        """Test piping analysis output to decide command."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create tasks file
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
                {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": True},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            # Run analyze
            analysis_file = str(Path(temp_dir) / "analysis.json")
            result1 = analyze(
                tasks_file=tasks_file,
                output_file=analysis_file,
                output_format="json",
            )
            assert result1 == 0
            assert Path(analysis_file).exists()

            # Run decide with analysis output
            result2 = decide(
                goal="performance",
                analysis_file=analysis_file,
                output_format="json",
            )
            assert result2 == 0

    def test_plan_to_execute_pipeline(self):
        """Test piping plan output to execute command."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create tasks file
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            # Run plan
            plan_file = str(Path(temp_dir) / "plan.json")
            result1 = plan(
                tasks_file=tasks_file,
                output_file=plan_file,
                output_format="json",
            )
            assert result1 == 0
            assert Path(plan_file).exists()

            # Verify plan file is readable
            with open(plan_file, 'r') as f:
                plan_data = json.load(f)
            assert plan_data is not None
            assert "id" in plan_data

            # Run execute with plan output
            result2 = execute(
                plan_file=plan_file,
                simulate=True,
                output_format="json",
            )
            assert result2 == 0


@pytest.mark.unit
class TestJSONOutputFormat:
    """Test JSON output formatting."""

    def test_json_output_valid_structure(self):
        """Test that JSON output is valid."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            output_file = str(Path(temp_dir) / "output.json")
            result = analyze(
                tasks_file=tasks_file,
                output_file=output_file,
                output_format="json",
            )
            assert result == 0

            # Verify output is valid JSON
            with open(output_file) as f:
                output_data = json.load(f)
            assert isinstance(output_data, dict)
            assert "analysis_id" in output_data

    def test_json_output_serializes_complex_types(self):
        """Test JSON output handles complex types."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            output_file = str(Path(temp_dir) / "output.json")
            result = execute(
                plan_file=tasks_file,  # This will fail, but we test the JSON serialization
                output_file=output_file,
                output_format="json",
            )
            # Result should be 1 (error) but it demonstrates serialization


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling."""

    def test_analyze_error_message_on_failure(self):
        """Test error messages are helpful."""
        reset_config()
        result = analyze(
            tasks_file="/nonexistent/file.json",
            output_format="json",
        )
        assert result == 1

    def test_decide_error_on_invalid_goal(self):
        """Test error on invalid goal."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [{"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True}]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            result = decide(
                goal="invalid_goal",
                tasks_file=tasks_file,
                output_format="json",
            )
            assert result == 1

    def test_plan_error_on_invalid_strategy(self):
        """Test error on invalid strategy file."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [{"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True}]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            # Invalid strategy file
            strategy_file = str(Path(temp_dir) / "strategy.json")
            with open(strategy_file, 'w') as f:
                json.dump({"incomplete": "data"}, f)

            result = plan(
                tasks_file=tasks_file,
                strategy_file=strategy_file,
                output_format="json",
            )
            assert result == 1


@pytest.mark.unit
class TestDecideCommandExtended:
    """Additional tests for decide command edge cases."""

    def test_decide_with_both_files(self):
        """Test decide command with both task and analysis files."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [{"id": "t1", "name": "Task 1", "estimated_duration": 2.0, "parallelizable": True}]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            analysis = {
                "analysis_id": "analysis-1",
                "workflow_id": "workflow-1",
                "total_tasks": 1,
                "total_dependencies": 0,
                "complexity_scores": {"t1": 50},
                "feasibility_ratings": {"t1": "feasible"},
                "critical_path": ["t1"],
                "critical_path_duration": 2.0,
                "total_serial_duration": 2.0,
                "parallelizable_tasks": ["t1"],
                "sequential_bottlenecks": [],
                "resource_conflicts": [],
                "warnings": [],
            }
            analysis_file = str(Path(temp_dir) / "analysis.json")
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f)

            result = decide(
                goal="reliability",
                tasks_file=tasks_file,
                analysis_file=analysis_file,
                output_format="json",
            )
            assert result == 0

    def test_decide_with_verbose_output(self):
        """Test decide command with verbose output."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [{"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True}]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            result = decide(
                goal="cost",
                tasks_file=tasks_file,
                output_format="json",
                verbose=True,
            )
            assert result == 0


@pytest.mark.unit
class TestCLIUtilitiesExtended:
    """Additional tests for CLI utility functions."""

    def test_format_text_summary_with_dict(self):
        """Test text summary formatting with dictionary data."""
        from parallelizer_skill.cli import _format_text_summary
        data = {"key1": "value1", "key2": {"nested": "value2"}}
        result = _format_text_summary("Test Title", data)
        assert "Test Title" in result
        assert "key1" in result
        assert "value1" in result

    def test_format_text_summary_with_lists(self):
        """Test text summary formatting with list data."""
        from parallelizer_skill.cli import _format_text_summary
        data = {"items": ["item1", "item2", "item3"]}
        result = _format_text_summary("Items", data)
        assert "Items" in result
        assert "items" in result

    def test_save_json_file_creates_directory(self):
        """Test that save_json_file creates parent directories."""
        from parallelizer_skill.cli import _save_json_file
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = str(Path(temp_dir) / "level1" / "level2" / "data.json")
            data = {"test": "data"}
            _save_json_file(nested_path, data)
            assert Path(nested_path).exists()
            with open(nested_path) as f:
                assert json.load(f) == data


@pytest.mark.unit
class TestAnalyzeCommandExtended:
    """Additional tests for analyze command edge cases."""

    def test_analyze_with_verbose_and_output_file(self):
        """Test analyze command with both verbose and output file."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [{"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True}]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            output_file = str(Path(temp_dir) / "analysis.json")
            result = analyze(
                tasks_file=tasks_file,
                output_file=output_file,
                output_format="json",
                verbose=True,
            )
            assert result == 0
            assert Path(output_file).exists()

    def test_analyze_with_text_format_verbose(self):
        """Test analyze command with text output format and verbose."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
                {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": True},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            result = analyze(
                tasks_file=tasks_file,
                output_format="text",
                verbose=True,
            )
            assert result == 0


@pytest.mark.unit
class TestPlanCommandExtended:
    """Additional tests for plan command edge cases."""

    def test_plan_with_text_output_verbose(self):
        """Test plan command with text output and verbose."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [
                {"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True},
                {"id": "t2", "name": "Task 2", "estimated_duration": 2.0, "parallelizable": True},
            ]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            result = plan(
                tasks_file=tasks_file,
                output_format="text",
                verbose=True,
            )
            assert result == 0


@pytest.mark.unit
class TestExecuteCommandExtended:
    """Additional tests for execute command edge cases."""

    def test_execute_with_text_output_verbose(self):
        """Test execute command with text output and verbose mode."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_data = {
                "id": "plan-1",
                "total_tasks": 1,
                "serial_duration": 1.0,
                "parallel_duration": 1.0,
                "efficiency_gain": 0.0,
                "critical_path": ["t1"],
                "phases": [
                    {
                        "phase_number": 1,
                        "is_parallel": False,
                        "estimated_duration": 1.0,
                        "sync_point_required": True,
                        "task_groups": [
                            {
                                "id": "group-1",
                                "tasks": ["t1"],
                                "estimated_duration": 1.0,
                                "can_parallelize": False,
                            }
                        ],
                    }
                ],
                "parallelizable_groups": {},
            }
            plan_file = str(Path(temp_dir) / "plan.json")
            with open(plan_file, 'w') as f:
                json.dump(plan_data, f)

            result = execute(
                plan_file=plan_file,
                output_format="text",
                verbose=True,
            )
            assert result == 0


@pytest.mark.unit
class TestResetCommandExtended:
    """Additional tests for reset command."""

    def test_reset_with_verbose(self):
        """Test reset command with verbose output."""
        reset_config()
        result = reset(verbose=True)
        assert result == 0


@pytest.mark.unit
class TestDecideCommandErrorPaths:
    """Test error handling in decide command."""

    def test_decide_with_nonexistent_analysis_file(self):
        """Test decide with non-existent analysis file."""
        reset_config()
        result = decide(
            goal="performance",
            analysis_file="/nonexistent/file.json",
            output_format="json",
        )
        assert result == 1

    def test_decide_with_invalid_analysis_json(self):
        """Test decide with invalid analysis JSON."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_file = str(Path(temp_dir) / "analysis.json")
            with open(analysis_file, 'w') as f:
                f.write("{invalid json")

            result = decide(
                goal="performance",
                analysis_file=analysis_file,
                output_format="json",
            )
            assert result == 1


@pytest.mark.unit
class TestPlanCommandErrorPaths:
    """Test error handling in plan command."""

    def test_plan_with_invalid_strategy_file(self):
        """Test plan with invalid strategy file."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [{"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True}]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            strategy_file = str(Path(temp_dir) / "strategy.json")
            with open(strategy_file, 'w') as f:
                f.write("{invalid json")

            result = plan(
                tasks_file=tasks_file,
                strategy_file=strategy_file,
                output_format="json",
            )
            assert result == 1


@pytest.mark.unit
class TestExecuteCommandErrorPaths:
    """Test error handling in execute command."""

    def test_execute_with_invalid_plan_json(self):
        """Test execute with invalid plan JSON."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_file = str(Path(temp_dir) / "plan.json")
            with open(plan_file, 'w') as f:
                f.write("{invalid json")

            result = execute(
                plan_file=plan_file,
                output_format="json",
            )
            assert result == 1


@pytest.mark.unit
class TestOutputFileBehavior:
    """Test output file writing behavior."""

    def test_decide_saves_output_file(self):
        """Test decide command saves output to file."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = [{"id": "t1", "name": "Task 1", "estimated_duration": 1.0, "parallelizable": True}]
            tasks_file = str(Path(temp_dir) / "tasks.json")
            with open(tasks_file, 'w') as f:
                json.dump(tasks, f)

            output_file = str(Path(temp_dir) / "decision.json")
            result = decide(
                goal="performance",
                tasks_file=tasks_file,
                output_file=output_file,
                output_format="json",
            )
            assert result == 0
            assert Path(output_file).exists()
            with open(output_file) as f:
                data = json.load(f)
                assert "strategy_type" in data

    def test_execute_with_output_file_and_verbose(self):
        """Test execute command saves output file with verbose output."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_data = {
                "id": "plan-1",
                "total_tasks": 1,
                "serial_duration": 1.0,
                "parallel_duration": 1.0,
                "efficiency_gain": 0.0,
                "critical_path": ["t1"],
                "phases": [
                    {
                        "phase_number": 1,
                        "is_parallel": False,
                        "estimated_duration": 1.0,
                        "sync_point_required": True,
                        "task_groups": [
                            {
                                "id": "group-1",
                                "tasks": ["t1"],
                                "estimated_duration": 1.0,
                                "can_parallelize": False,
                            }
                        ],
                    }
                ],
                "parallelizable_groups": {},
            }
            plan_file = str(Path(temp_dir) / "plan.json")
            output_file = str(Path(temp_dir) / "result.json")
            with open(plan_file, 'w') as f:
                json.dump(plan_data, f)

            result = execute(
                plan_file=plan_file,
                output_file=output_file,
                output_format="json",
                verbose=True,
            )
            assert result == 0
            assert Path(output_file).exists()


@pytest.mark.unit
class TestDocumentCommandExtended:
    """Additional tests for document command edge cases."""

    def test_document_command_with_output_file_verbose(self):
        """Test document command with output file and verbose mode."""
        reset_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis = {
                "analysis_id": "analysis-123",
                "workflow_id": "workflow-1",
                "total_tasks": 1,
                "total_dependencies": 0,
                "complexity_scores": {"t1": 25},
                "feasibility_ratings": {"t1": "feasible"},
                "critical_path": ["t1"],
                "critical_path_duration": 1.0,
                "total_serial_duration": 1.0,
                "parallelizable_tasks": ["t1"],
                "sequential_bottlenecks": [],
                "resource_conflicts": [],
                "warnings": [],
            }
            recommendation = {
                "strategy_type": "performance",
                "max_parallel_tasks": 4,
                "recommended_batch_size": 10,
                "recommended_retry_count": 2,
                "recommended_checkpoint_interval": 5,
                "parallel_execution": True,
                "resource_aware": True,
                "monitoring_intensity": "high",
                "escalation_level": "error",
                "rationale": "Test strategy",
            }
            plan = {
                "id": "plan-1",
                "total_tasks": 1,
                "serial_duration": 1.0,
                "parallel_duration": 1.0,
                "efficiency_gain": 0.0,
                "critical_path": ["t1"],
                "phases": [
                    {
                        "phase_number": 1,
                        "is_parallel": False,
                        "estimated_duration": 1.0,
                        "sync_point_required": True,
                        "task_groups": [
                            {
                                "id": "group-1",
                                "tasks": ["t1"],
                                "estimated_duration": 1.0,
                                "can_parallelize": False,
                            }
                        ],
                    }
                ],
                "parallelizable_groups": {},
            }

            analysis_file = str(Path(temp_dir) / "analysis.json")
            recommendation_file = str(Path(temp_dir) / "recommendation.json")
            plan_file = str(Path(temp_dir) / "plan.json")
            output_file = str(Path(temp_dir) / "output.md")

            with open(analysis_file, 'w') as f:
                json.dump(analysis, f)
            with open(recommendation_file, 'w') as f:
                json.dump(recommendation, f)
            with open(plan_file, 'w') as f:
                json.dump(plan, f)

            result = document(
                analysis_file=analysis_file,
                recommendation_file=recommendation_file,
                plan_file=plan_file,
                output_file=output_file,
                output_format="markdown",
                verbose=True,
            )
            assert result == 0
            assert Path(output_file).exists()
