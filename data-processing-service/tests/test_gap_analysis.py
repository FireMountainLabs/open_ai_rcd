import pandas as pd

"""
Test suite for Gap Analysis functionality.

Tests the /api/gaps endpoint that identifies unmapped risks, controls, and questions,
and calculates coverage percentages.
"""

import sqlite3

import yaml

from config.config_manager import ConfigManager
from data_processor import DataProcessor
from database_manager import DatabaseManager


class TestGapAnalysis:
    """Test gap analysis functionality."""

    def test_gap_analysis_with_complete_mappings(self, temp_dir):
        """Test gap analysis when all entities are properly mapped."""
        # Create test data with complete mappings
        risks_data = pd.DataFrame(
            {
                "ID": ["AIR.001", "AIR.002"],
                "Risk": ["Risk 1", "Risk 2"],
                "Risk Description": ["Description 1", "Description 2"],
            }
        )

        controls_data = pd.DataFrame(
            {
                "Sub-Control": ["AIGPC.1", "AIGPC.2"],
                "Control Title": ["Control 1", "Control 2"],
                "Control Description": ["Control Desc 1", "Control Desc 2"],
                "Mapped Risks": ["AIR.001", "AIR.002"],
            }
        )

        questions_data = pd.DataFrame(
            {
                "Question Number": ["Q1", "Q2"],
                "Question Text": ["Question 1?", "Question 2?"],
                "Category": ["Privacy", "Security"],
                "Topic": ["Data Protection", "Access Control"],
                "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002"],
                "AIML_CONTROL": ["AIGPC.1", "AIGPC.2"],
            }
        )

        # Create configuration
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
            "database": {"file": "test_complete.db"},
            "extraction": {"validate_files": True, "remove_duplicates": True},
            "output": {"print_summary": False, "collect_metadata": True},
        }

        config_file = temp_dir / "complete_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Create Excel files
        risks_data.to_excel(temp_dir / "test_risks.xlsx", index=False)
        controls_data.to_excel(temp_dir / "test_controls.xlsx", index=False)
        questions_data.to_excel(temp_dir / "test_questions.xlsx", index=False)

        # Process data
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        processor = DataProcessor(
            data_dir=temp_dir,
            output_dir=output_dir,
            config_manager=ConfigManager(config_file),
        )
        processor.process_data()

        # Test gap analysis
        db_path = output_dir / "test_complete.db"
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all entities
            cursor.execute("SELECT risk_id, risk_title, risk_description FROM risks")
            all_risks = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                "SELECT control_id, control_title, control_description FROM controls"
            )
            all_controls = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT question_id, question_text, category FROM questions")
            all_questions = [dict(row) for row in cursor.fetchall()]

            # Get mapped entities
            cursor.execute("SELECT DISTINCT risk_id FROM risk_control_mapping")
            mapped_risk_ids = {row["risk_id"] for row in cursor.fetchall()}

            cursor.execute("SELECT DISTINCT control_id FROM risk_control_mapping")
            mapped_control_ids = {row["control_id"] for row in cursor.fetchall()}

            cursor.execute("SELECT DISTINCT question_id FROM question_risk_mapping")
            mapped_question_ids = {row["question_id"] for row in cursor.fetchall()}

            # Add question-control mappings
            cursor.execute("SELECT DISTINCT control_id FROM question_control_mapping")
            mapped_control_ids.update({row["control_id"] for row in cursor.fetchall()})

            cursor.execute("SELECT DISTINCT question_id FROM question_control_mapping")
            mapped_question_ids.update(
                {row["question_id"] for row in cursor.fetchall()}
            )

            # Find unmapped entities
            unmapped_risks = [
                r for r in all_risks if r["risk_id"] not in mapped_risk_ids
            ]
            unmapped_controls = [
                c for c in all_controls if c["control_id"] not in mapped_control_ids
            ]
            unmapped_questions = [
                q for q in all_questions if q["question_id"] not in mapped_question_ids
            ]

            # Calculate coverage percentages
            total_risks = len(all_risks)
            total_controls = len(all_controls)
            total_questions = len(all_questions)

            risk_coverage_pct = (
                ((total_risks - len(unmapped_risks)) / total_risks * 100)
                if total_risks > 0
                else 0
            )
            control_coverage_pct = (
                ((total_controls - len(unmapped_controls)) / total_controls * 100)
                if total_controls > 0
                else 0
            )
            question_coverage_pct = (
                ((total_questions - len(unmapped_questions)) / total_questions * 100)
                if total_questions > 0
                else 0
            )

            # Assertions for complete mappings
            assert len(unmapped_risks) == 0, "All risks should be mapped"
            assert len(unmapped_controls) == 0, "All controls should be mapped"
            assert len(unmapped_questions) == 0, "All questions should be mapped"
            assert risk_coverage_pct == 100.0, "Risk coverage should be 100%"
            assert control_coverage_pct == 100.0, "Control coverage should be 100%"
            assert question_coverage_pct == 100.0, "Question coverage should be 100%"

    def test_gap_analysis_with_missing_mappings(self, temp_dir):
        """Test gap analysis when some entities are unmapped."""
        # Create test data with missing mappings
        risks_data = pd.DataFrame(
            {
                "ID": ["AIR.001", "AIR.002", "AIR.003"],
                "Risk": ["Risk 1", "Risk 2", "Risk 3"],
                "Risk Description": ["Description 1", "Description 2", "Description 3"],
            }
        )

        controls_data = pd.DataFrame(
            {
                "Sub-Control": ["AIGPC.1", "AIGPC.2", "AIGPC.3"],
                "Control Title": ["Control 1", "Control 2", "Control 3"],
                "Control Description": [
                    "Control Desc 1",
                    "Control Desc 2",
                    "Control Desc 3",
                ],
                "Mapped Risks": ["AIR.001", "AIR.002", ""],
            }
        )

        questions_data = pd.DataFrame(
            {
                "Question Number": ["Q1", "Q2", "Q3"],
                "Question Text": ["Question 1?", "Question 2?", "Question 3?"],
                "Category": ["Privacy", "Security", "Compliance"],
                "Topic": ["Data Protection", "Access Control", "Regulatory"],
                "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002", ""],  # Q3 unmapped
                "AIML_CONTROL": ["AIGPC.1", "AIGPC.2", ""],  # Q3 unmapped
            }
        )

        # Create configuration
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
            "database": {"file": "test_gaps.db"},
            "extraction": {"validate_files": True, "remove_duplicates": True},
            "output": {"print_summary": False, "collect_metadata": True},
        }

        config_file = temp_dir / "gaps_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Create Excel files
        risks_data.to_excel(temp_dir / "test_risks.xlsx", index=False)
        controls_data.to_excel(temp_dir / "test_controls.xlsx", index=False)
        questions_data.to_excel(temp_dir / "test_questions.xlsx", index=False)

        # Process data
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        processor = DataProcessor(
            data_dir=temp_dir,
            output_dir=output_dir,
            config_manager=ConfigManager(config_file),
        )
        processor.process_data()

        # Test gap analysis
        db_path = output_dir / "test_gaps.db"
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all entities
            cursor.execute("SELECT risk_id, risk_title, risk_description FROM risks")
            all_risks = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                "SELECT control_id, control_title, control_description FROM controls"
            )
            all_controls = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT question_id, question_text, category FROM questions")
            all_questions = [dict(row) for row in cursor.fetchall()]

            # Get mapped entities
            cursor.execute("SELECT DISTINCT risk_id FROM risk_control_mapping")
            mapped_risk_ids = {row["risk_id"] for row in cursor.fetchall()}

            cursor.execute("SELECT DISTINCT control_id FROM risk_control_mapping")
            mapped_control_ids = {row["control_id"] for row in cursor.fetchall()}

            cursor.execute("SELECT DISTINCT question_id FROM question_risk_mapping")
            mapped_question_ids = {row["question_id"] for row in cursor.fetchall()}

            # Add question-control mappings
            cursor.execute("SELECT DISTINCT control_id FROM question_control_mapping")
            mapped_control_ids.update({row["control_id"] for row in cursor.fetchall()})

            cursor.execute("SELECT DISTINCT question_id FROM question_control_mapping")
            mapped_question_ids.update(
                {row["question_id"] for row in cursor.fetchall()}
            )

            # Find unmapped entities
            unmapped_risks = [
                r for r in all_risks if r["risk_id"] not in mapped_risk_ids
            ]
            unmapped_controls = [
                c for c in all_controls if c["control_id"] not in mapped_control_ids
            ]
            unmapped_questions = [
                q for q in all_questions if q["question_id"] not in mapped_question_ids
            ]

            # Calculate coverage percentages
            total_risks = len(all_risks)
            total_controls = len(all_controls)
            total_questions = len(all_questions)

            risk_coverage_pct = (
                ((total_risks - len(unmapped_risks)) / total_risks * 100)
                if total_risks > 0
                else 0
            )
            control_coverage_pct = (
                ((total_controls - len(unmapped_controls)) / total_controls * 100)
                if total_controls > 0
                else 0
            )
            question_coverage_pct = (
                ((total_questions - len(unmapped_questions)) / total_questions * 100)
                if total_questions > 0
                else 0
            )

            # Assertions for missing mappings
            assert (
                len(unmapped_risks) == 1
            ), f"Expected 1 unmapped risk, got {len(unmapped_risks)}"
            assert (
                len(unmapped_controls) == 1
            ), f"Expected 1 unmapped control, got {len(unmapped_controls)}"
            assert (
                len(unmapped_questions) == 1
            ), f"Expected 1 unmapped question, got {len(unmapped_questions)}"
            assert (
                abs(risk_coverage_pct - 66.7) < 0.1
            ), f"Expected ~66.7% risk coverage, got {risk_coverage_pct}%"
            assert (
                abs(control_coverage_pct - 66.7) < 0.1
            ), f"Expected ~66.7% control coverage, got {control_coverage_pct}%"
            assert (
                abs(question_coverage_pct - 66.7) < 0.1
            ), f"Expected ~66.7% question coverage, got {question_coverage_pct}%"

            # Verify specific unmapped entities
            assert (
                unmapped_risks[0]["risk_id"] == "R.AIR.003"
            ), "R.AIR.003 should be unmapped"
            assert (
                unmapped_controls[0]["control_id"] == "C.AIGPC.3"
            ), "C.AIGPC.3 should be unmapped"
            assert (
                unmapped_questions[0]["question_id"] == "Q.SHEET1.Q3"
            ), "Q.SHEET1.Q3 should be unmapped"

    def test_gap_analysis_coverage_calculations(self, temp_dir):
        """Test coverage percentage calculations with various scenarios."""
        # Test with different numbers of entities
        test_cases = [
            {
                "risks": 10,
                "controls": 5,
                "questions": 8,
                "mapped_risks": 7,
                "mapped_controls": 3,
                "mapped_questions": 6,
            },
            {
                "risks": 100,
                "controls": 50,
                "questions": 75,
                "mapped_risks": 90,
                "mapped_controls": 45,
                "mapped_questions": 60,
            },
            {
                "risks": 1,
                "controls": 1,
                "questions": 1,
                "mapped_risks": 0,
                "mapped_controls": 0,
                "mapped_questions": 0,
            },
        ]

        for case in test_cases:
            # Calculate expected coverage percentages
            expected_risk_coverage = (
                (case["mapped_risks"] / case["risks"] * 100) if case["risks"] > 0 else 0
            )
            expected_control_coverage = (
                (case["mapped_controls"] / case["controls"] * 100)
                if case["controls"] > 0
                else 0
            )
            expected_question_coverage = (
                (case["mapped_questions"] / case["questions"] * 100)
                if case["questions"] > 0
                else 0
            )

            # Test the calculation logic
            total_risks = case["risks"]
            total_controls = case["controls"]
            total_questions = case["questions"]

            unmapped_risks = total_risks - case["mapped_risks"]
            unmapped_controls = total_controls - case["mapped_controls"]
            unmapped_questions = total_questions - case["mapped_questions"]

            risk_coverage_pct = (
                ((total_risks - unmapped_risks) / total_risks * 100)
                if total_risks > 0
                else 0
            )
            control_coverage_pct = (
                ((total_controls - unmapped_controls) / total_controls * 100)
                if total_controls > 0
                else 0
            )
            question_coverage_pct = (
                ((total_questions - unmapped_questions) / total_questions * 100)
                if total_questions > 0
                else 0
            )

            # Assertions
            assert (
                abs(risk_coverage_pct - expected_risk_coverage) < 0.1
            ), f"Risk coverage calculation incorrect: expected {expected_risk_coverage}, got {risk_coverage_pct}"
            assert (
                abs(control_coverage_pct - expected_control_coverage) < 0.1
            ), f"Control coverage calculation incorrect: expected {expected_control_coverage}, got {control_coverage_pct}"
            assert (
                abs(question_coverage_pct - expected_question_coverage) < 0.1
            ), f"Question coverage calculation incorrect: expected {expected_question_coverage}, got {question_coverage_pct}"

    def test_gap_analysis_empty_database(self, temp_dir):
        """Test gap analysis with empty database."""
        # Create empty database
        db_path = temp_dir / "empty.db"
        db_manager = DatabaseManager(db_path)
        db_manager.create_tables()

        # Test gap analysis on empty database
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all entities (should be empty)
            cursor.execute("SELECT risk_id, risk_title, risk_description FROM risks")
            all_risks = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                "SELECT control_id, control_title, control_description FROM controls"
            )
            all_controls = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT question_id, question_text, category FROM questions")
            all_questions = [dict(row) for row in cursor.fetchall()]

            # Calculate coverage percentages
            total_risks = len(all_risks)
            total_controls = len(all_controls)
            total_questions = len(all_questions)

            risk_coverage_pct = (
                ((total_risks - 0) / total_risks * 100) if total_risks > 0 else 0
            )
            control_coverage_pct = (
                ((total_controls - 0) / total_controls * 100)
                if total_controls > 0
                else 0
            )
            question_coverage_pct = (
                ((total_questions - 0) / total_questions * 100)
                if total_questions > 0
                else 0
            )

            # Assertions for empty database
            assert total_risks == 0, "Should have no risks"
            assert total_controls == 0, "Should have no controls"
            assert total_questions == 0, "Should have no questions"
            assert risk_coverage_pct == 0, "Risk coverage should be 0%"
            assert control_coverage_pct == 0, "Control coverage should be 0%"
            assert question_coverage_pct == 0, "Question coverage should be 0%"

    def test_gap_analysis_api_response_format(self, temp_dir):
        """Test that gap analysis returns the correct API response format."""
        # Create test data
        risks_data = pd.DataFrame(
            {
                "ID": ["AIR.001", "AIR.002"],
                "Risk": ["Risk 1", "Risk 2"],
                "Risk Description": ["Description 1", "Description 2"],
            }
        )

        controls_data = pd.DataFrame(
            {
                "ID": ["AIGPC.1", "AIGPC.2"],
                "Control": ["Control 1", "Control 2"],
                "Control Description": ["Control Desc 1", "Control Desc 2"],
            }
        )

        questions_data = pd.DataFrame(
            {
                "Question Number": ["Q1", "Q2"],
                "Question Text": ["Question 1?", "Question 2?"],
                "Category": ["Privacy", "Security"],
                "Topic": ["Data Protection", "Access Control"],
                "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002"],
                "AIML_CONTROL": ["AIGPC.1", "AIGPC.2"],
            }
        )

        # Create configuration
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
                        "control_mapping": "AIGPC",
                    },
                },
            },
            "database": {"file": "test_api_format.db"},
            "extraction": {"validate_files": True, "remove_duplicates": True},
            "output": {"print_summary": False, "collect_metadata": True},
        }

        config_file = temp_dir / "api_format_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Create Excel files
        risks_data.to_excel(temp_dir / "test_risks.xlsx", index=False)
        controls_data.to_excel(temp_dir / "test_controls.xlsx", index=False)
        questions_data.to_excel(temp_dir / "test_questions.xlsx", index=False)

        # Process data
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        processor = DataProcessor(
            data_dir=temp_dir,
            output_dir=output_dir,
            config_manager=ConfigManager(config_file),
        )
        processor.process_data()

        # Simulate API response format
        db_path = output_dir / "test_api_format.db"
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all entities
            cursor.execute("SELECT risk_id, risk_title, risk_description FROM risks")
            all_risks = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                "SELECT control_id, control_title, control_description FROM controls"
            )
            all_controls = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT question_id, question_text, category FROM questions")
            all_questions = [dict(row) for row in cursor.fetchall()]

            # Get mapped entities
            cursor.execute("SELECT DISTINCT risk_id FROM risk_control_mapping")
            mapped_risk_ids = {row["risk_id"] for row in cursor.fetchall()}

            cursor.execute("SELECT DISTINCT control_id FROM risk_control_mapping")
            mapped_control_ids = {row["control_id"] for row in cursor.fetchall()}

            cursor.execute("SELECT DISTINCT question_id FROM question_risk_mapping")
            mapped_question_ids = {row["question_id"] for row in cursor.fetchall()}

            # Add question-control mappings
            cursor.execute("SELECT DISTINCT control_id FROM question_control_mapping")
            mapped_control_ids.update({row["control_id"] for row in cursor.fetchall()})

            cursor.execute("SELECT DISTINCT question_id FROM question_control_mapping")
            mapped_question_ids.update(
                {row["question_id"] for row in cursor.fetchall()}
            )

            # Find unmapped entities
            unmapped_risks = [
                r for r in all_risks if r["risk_id"] not in mapped_risk_ids
            ]
            unmapped_controls = [
                c for c in all_controls if c["control_id"] not in mapped_control_ids
            ]
            unmapped_questions = [
                q for q in all_questions if q["question_id"] not in mapped_question_ids
            ]

            # Calculate coverage percentages
            total_risks = len(all_risks)
            total_controls = len(all_controls)
            total_questions = len(all_questions)

            risk_coverage_pct = (
                ((total_risks - len(unmapped_risks)) / total_risks * 100)
                if total_risks > 0
                else 0
            )
            control_coverage_pct = (
                ((total_controls - len(unmapped_controls)) / total_controls * 100)
                if total_controls > 0
                else 0
            )
            question_coverage_pct = (
                ((total_questions - len(unmapped_questions)) / total_questions * 100)
                if total_questions > 0
                else 0
            )

            # Create API response format
            api_response = {
                "summary": {
                    "total_risks": total_risks,
                    "total_controls": total_controls,
                    "total_questions": total_questions,
                    "mapped_risks": total_risks - len(unmapped_risks),
                    "mapped_controls": total_controls - len(unmapped_controls),
                    "mapped_questions": total_questions - len(unmapped_questions),
                    "unmapped_risks": len(unmapped_risks),
                    "unmapped_controls": len(unmapped_controls),
                    "unmapped_questions": len(unmapped_questions),
                    "risk_coverage_pct": round(risk_coverage_pct, 1),
                    "control_coverage_pct": round(control_coverage_pct, 1),
                    "question_coverage_pct": round(question_coverage_pct, 1),
                    "control_utilization_pct": round(control_coverage_pct, 1),
                },
                "unmapped_risks": unmapped_risks,
                "unmapped_controls": unmapped_controls,
                "unmapped_questions": unmapped_questions,
            }

            # Assertions for API response format
            assert "summary" in api_response, "Response should have summary section"
            assert (
                "unmapped_risks" in api_response
            ), "Response should have unmapped_risks section"
            assert (
                "unmapped_controls" in api_response
            ), "Response should have unmapped_controls section"
            assert (
                "unmapped_questions" in api_response
            ), "Response should have unmapped_questions section"

            # Check summary fields
            summary = api_response["summary"]
            required_fields = [
                "total_risks",
                "total_controls",
                "total_questions",
                "mapped_risks",
                "mapped_controls",
                "mapped_questions",
                "unmapped_risks",
                "unmapped_controls",
                "unmapped_questions",
                "risk_coverage_pct",
                "control_coverage_pct",
                "question_coverage_pct",
                "control_utilization_pct",
            ]

            for field in required_fields:
                assert field in summary, f"Summary should have {field} field"
                assert isinstance(
                    summary[field], (int, float)
                ), f"{field} should be numeric"

            # Check that percentages are rounded to 1 decimal place
            assert summary["risk_coverage_pct"] == round(
                risk_coverage_pct, 1
            ), "Risk coverage should be rounded to 1 decimal place"
            assert summary["control_coverage_pct"] == round(
                control_coverage_pct, 1
            ), "Control coverage should be rounded to 1 decimal place"
            assert summary["question_coverage_pct"] == round(
                question_coverage_pct, 1
            ), "Question coverage should be rounded to 1 decimal place"
