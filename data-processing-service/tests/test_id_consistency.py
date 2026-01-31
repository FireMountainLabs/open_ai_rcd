import pandas as pd

"""
Focused tests for ID consistency across the refactored architecture.

This test suite validates critical ID consistency requirements that were
previously tested in the deleted test_id_mapping_consistency.py file.
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest
import yaml

from config.config_manager import ConfigManager
from data_processor import DataProcessor
from extractors.mapping_extractor import MappingExtractor


class TestIDConsistency:
    """Test ID consistency across the refactored architecture."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        import shutil

        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def sample_data(self):
        """Create sample data with proper IDs."""
        return {
            "risks": pd.DataFrame(
                {
                    "ID": ["AIR.001", "AIR.002"],
                    "Risk": ["Test Risk 1", "Test Risk 2"],
                    "Risk Description": ["Description 1", "Description 2"],
                }
            ),
            "controls": pd.DataFrame(
                {
                    "Sub-Control": ["AIGPC.1", "AIGPC.2"],
                    "Control Title": ["Control 1", "Control 2"],
                    "Control Description": ["Control Desc 1", "Control Desc 2"],
                    "Mapped Risks": ["AIR.001", "AIR.002"],
                }
            ),
            "questions": pd.DataFrame(
                {
                    "Question Number": ["Q1", "Q2"],
                    "Question Text": ["Question 1?", "Question 2?"],
                    "Category": ["Privacy", "Security"],
                    "Topic": ["Data Protection", "Access Control"],
                    "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002"],
                    "AIML_CONTROL": ["AIGPC.1", "AIGPC.2"],
                }
            ),
        }

    @pytest.fixture
    def test_config(self, temp_dir):
        """Create test configuration."""
        config_data = {
            "data_sources": {
                "risks": {
                    "file": "test_risks.xlsx",
                    "columns": {
                        "id": "ID",
                        "title": "Risk",
                        "description": "Risk Description",
                    },
                },
                "controls": {
                    "file": "test_controls.xlsx",
                    "columns": {
                        "id": "Sub-Control",
                        "title": "Control Title",
                        "description": "Control Description",
                    },
                },
                "questions": {
                    "file": "test_questions.xlsx",
                    "columns": {
                        "id": "Question Number",
                        "text": "Question Text",
                        "category": "Category",
                        "topic": "Topic",
                        "risk_mapping": "AIML_RISK_TAXONOMY",
                        "control_mapping": "AIML_CONTROL",
                    },
                },
            },
            "database": {"file": "test_consistency.db"},
            "extraction": {"validate_files": True, "remove_duplicates": True},
            "output": {"print_summary": False, "collect_metadata": True},
        }

        config_file = temp_dir / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        return config_file

    def test_cross_processor_id_consistency(self, temp_dir, sample_data, test_config):
        """Test that different processors produce consistent ID formats."""
        # Create test files
        sample_data["risks"].to_excel(temp_dir / "test_risks.xlsx", index=False)
        sample_data["controls"].to_excel(temp_dir / "test_controls.xlsx", index=False)
        sample_data["questions"].to_excel(temp_dir / "test_questions.xlsx", index=False)

        # Test with DataProcessor (current architecture)
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        config_manager = ConfigManager(test_config)
        processor = DataProcessor(
            data_dir=temp_dir, output_dir=output_dir, config_manager=config_manager
        )
        processor.process_data()

        # Test with individual extractors
        mapping_extractor = MappingExtractor(config_manager)
        question_risk_mappings, question_control_mappings = (
            mapping_extractor.extract_question_mappings(
                temp_dir / "test_questions.xlsx"
            )
        )

        # Verify ID consistency between DataProcessor and individual extractors
        db_path = output_dir / "test_consistency.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Get IDs from database (processed by DataProcessor)
            cursor.execute("SELECT question_id FROM questions ORDER BY question_id")
            db_question_ids = {row[0] for row in cursor.fetchall()}

            cursor.execute("SELECT risk_id FROM risks ORDER BY risk_id")
            db_risk_ids = {row[0] for row in cursor.fetchall()}

            cursor.execute("SELECT control_id FROM controls ORDER BY control_id")
            db_control_ids = {row[0] for row in cursor.fetchall()}

        # Get IDs from individual extractors
        extractor_question_ids = set(question_risk_mappings["question_id"].tolist())
        extractor_risk_ids = set(question_risk_mappings["risk_id"].tolist())
        extractor_control_ids = set(question_control_mappings["control_id"].tolist())

        # Verify ID formats are consistent
        assert (
            db_question_ids == extractor_question_ids
        ), f"Question ID mismatch: DB={db_question_ids} vs Extractor={extractor_question_ids}"

        assert (
            db_risk_ids == extractor_risk_ids
        ), f"Risk ID mismatch: DB={db_risk_ids} vs Extractor={extractor_risk_ids}"

        assert (
            db_control_ids == extractor_control_ids
        ), f"Control ID mismatch: DB={db_control_ids} vs Extractor={extractor_control_ids}"

        # Verify all IDs have proper prefixes
        assert all(
            qid.startswith("Q.") for qid in db_question_ids
        ), "Question IDs missing Q. prefix"
        assert all(
            rid.startswith("R.") for rid in db_risk_ids
        ), "Risk IDs missing R. prefix"
        assert all(
            cid.startswith("C.") for cid in db_control_ids
        ), "Control IDs missing C. prefix"

    def test_database_referential_integrity(self, temp_dir, sample_data, test_config):
        """Test database referential integrity and ID consistency."""
        # Create test files
        sample_data["risks"].to_excel(temp_dir / "test_risks.xlsx", index=False)
        sample_data["controls"].to_excel(temp_dir / "test_controls.xlsx", index=False)
        sample_data["questions"].to_excel(temp_dir / "test_questions.xlsx", index=False)

        # Process data
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        config_manager = ConfigManager(test_config)
        processor = DataProcessor(
            data_dir=temp_dir, output_dir=output_dir, config_manager=config_manager
        )
        processor.process_data()

        # Test database integrity
        db_path = output_dir / "test_consistency.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Test that all foreign key references are valid
            cursor.execute(
                """
                SELECT q.question_id, qrm.risk_id
                FROM questions q
                JOIN question_risk_mapping qrm ON q.question_id = qrm.question_id
                LEFT JOIN risks r ON qrm.risk_id = r.risk_id
                WHERE r.risk_id IS NULL
            """
            )
            orphaned_risk_mappings = cursor.fetchall()
            assert (
                len(orphaned_risk_mappings) == 0
            ), f"Found orphaned risk mappings: {orphaned_risk_mappings}"

            cursor.execute(
                """
                SELECT q.question_id, qcm.control_id
                FROM questions q
                JOIN question_control_mapping qcm ON q.question_id = qcm.question_id
                LEFT JOIN controls c ON qcm.control_id = c.control_id
                WHERE c.control_id IS NULL
            """
            )
            orphaned_control_mappings = cursor.fetchall()
            assert (
                len(orphaned_control_mappings) == 0
            ), f"Found orphaned control mappings: {orphaned_control_mappings}"

            cursor.execute(
                """
                SELECT rcm.risk_id, rcm.control_id
                FROM risk_control_mapping rcm
                LEFT JOIN risks r ON rcm.risk_id = r.risk_id
                LEFT JOIN controls c ON rcm.control_id = c.control_id
                WHERE r.risk_id IS NULL OR c.control_id IS NULL
            """
            )
            orphaned_risk_control_mappings = cursor.fetchall()
            assert (
                len(orphaned_risk_control_mappings) == 0
            ), f"Found orphaned risk-control mappings: {orphaned_risk_control_mappings}"

    def test_id_normalization_consistency(self, temp_dir, sample_data, test_config):
        """Test that ID normalization is consistent across all processing steps."""
        # Create test files with various ID formats
        sample_data["risks"].to_excel(temp_dir / "test_risks.xlsx", index=False)
        sample_data["controls"].to_excel(temp_dir / "test_controls.xlsx", index=False)
        sample_data["questions"].to_excel(temp_dir / "test_questions.xlsx", index=False)

        # Process data
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        config_manager = ConfigManager(test_config)
        processor = DataProcessor(
            data_dir=temp_dir, output_dir=output_dir, config_manager=config_manager
        )
        processor.process_data()

        # Verify ID normalization consistency
        db_path = output_dir / "test_consistency.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check that all IDs follow the same normalization pattern
            cursor.execute("SELECT question_id FROM questions")
            question_ids = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT risk_id FROM risks")
            risk_ids = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT control_id FROM controls")
            control_ids = [row[0] for row in cursor.fetchall()]

            # Verify consistent formatting
            assert all(
                qid.startswith("Q.") and len(qid) > 2 for qid in question_ids
            ), f"Question IDs not properly normalized: {question_ids}"

            assert all(
                rid.startswith("R.") and len(rid) > 2 for rid in risk_ids
            ), f"Risk IDs not properly normalized: {risk_ids}"

            assert all(
                cid.startswith("C.") and len(cid) > 2 for cid in control_ids
            ), f"Control IDs not properly normalized: {control_ids}"

            # Verify no duplicates
            assert len(question_ids) == len(
                set(question_ids)
            ), "Duplicate question IDs found"
            assert len(risk_ids) == len(set(risk_ids)), "Duplicate risk IDs found"
            assert len(control_ids) == len(
                set(control_ids)
            ), "Duplicate control IDs found"
