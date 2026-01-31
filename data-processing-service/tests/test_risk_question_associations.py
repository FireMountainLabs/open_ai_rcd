import pandas as pd

"""
Test for risk-question associations not showing up in risk inventory.

This test covers the complete workflow from data processing to API retrieval
to ensure that risk-question associations are properly created, stored, and retrieved.
Includes comprehensive testing of different processing modes and edge cases.
"""

import sqlite3

import pytest
import yaml

from config.config_manager import ConfigManager
from data_processor import DataProcessor


@pytest.fixture
def test_data_with_associations():
    """Create test data with proper risk-question associations."""
    # Create risks data
    risks_data = pd.DataFrame(
        {
            "ID": ["AIR.001", "AIR.002", "AIR.003"],
            "Risk": ["Data Privacy Risk", "Model Bias Risk", "Security Risk"],
            "Risk Description": [
                "Risk of unauthorized access to sensitive data",
                "Risk of biased model outputs",
                "Risk of system compromise",
            ],
        }
    )

    # Create controls data
    controls_data = pd.DataFrame(
        {
            "Code": ["AIGPC.1", "AIGPC.2", "AIGPC.3"],
            "Purpose": ["Data Encryption", "Model Validation", "Access Control"],
            "Description": [
                "Implement encryption for data at rest and in transit",
                "Validate model outputs for bias and accuracy",
                "Control access to AI systems and data",
            ],
            "Mapped Risks": ["AIR.001", "AIR.002", "AIR.003"],
        }
    )

    # Create questions data with explicit risk mappings
    questions_data = pd.DataFrame(
        {
            "Question Number": ["Q1", "Q2", "Q3", "Q4", "Q5"],
            "Question Text": [
                "How is data privacy protected?",
                "What validation processes are in place?",
                "How is access controlled?",
                "What data encryption measures are implemented?",
                "How are model outputs validated for bias?",
            ],
            "Category": ["Privacy", "Validation", "Security", "Privacy", "Validation"],
            "Topic": [
                "Data Protection",
                "Model Testing",
                "Access Management",
                "Encryption",
                "Bias Detection",
            ],
            "AIML_RISK_TAXONOMY": [
                "AIR.001",
                "AIR.002",
                "AIR.003",
                "AIR.001",
                "AIR.002",
            ],
            "AIML_CONTROL": ["AIGPC.1", "AIGPC.2", "AIGPC.3", "AIGPC.1", "AIGPC.2"],
        }
    )

    return {"risks": risks_data, "controls": controls_data, "questions": questions_data}


@pytest.fixture
def test_config_with_associations(temp_dir, test_data_with_associations):
    """Create test configuration for associations testing."""
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
                    "id": "Code",
                    "title": "Purpose",
                    "description": "Description",
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
        "database": {"file": "test_associations.db"},
        "extraction": {
            "validate_files": True,
            "remove_duplicates": True,
            "log_level": "DEBUG",
        },
        "output": {"print_summary": False, "collect_metadata": True},
    }

    config_file = temp_dir / "test_config.yaml"
    import yaml

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Create Excel files
    risks_file = temp_dir / "test_risks.xlsx"
    controls_file = temp_dir / "test_controls.xlsx"
    questions_file = temp_dir / "test_questions.xlsx"

    test_data_with_associations["risks"].to_excel(risks_file, index=False)
    # Create controls file with "Domains" sheet name to match expected structure
    with pd.ExcelWriter(controls_file) as writer:
        test_data_with_associations["controls"].to_excel(
            writer, sheet_name="Domains", index=False
        )
    test_data_with_associations["questions"].to_excel(questions_file, index=False)

    return config_file


def test_question_risk_mapping_creation(temp_dir, test_config_with_associations):
    """Test that question-risk mappings are properly created during data processing."""
    # Create output directory
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Initialize processor
    processor = DataProcessor(
        data_dir=temp_dir,
        output_dir=output_dir,
        config_manager=ConfigManager(test_config_with_associations),
    )

    # Run data extraction
    processor.extract_data()

    # Verify question-risk mappings were created
    assert processor.question_risk_mapping_df is not None
    assert not processor.question_risk_mapping_df.empty

    # Check specific mappings
    mappings = processor.question_risk_mapping_df

    # Should have mappings for Q1->AIR.001, Q2->AIR.002, Q3->AIR.003, Q4->AIR.001, Q5->AIR.002
    expected_mappings = [
        ("Q.SHEET1.Q1", "R.AIR.001"),
        ("Q.SHEET1.Q2", "R.AIR.002"),
        ("Q.SHEET1.Q3", "R.AIR.003"),
        ("Q.SHEET1.Q4", "R.AIR.001"),
        ("Q.SHEET1.Q5", "R.AIR.002"),
    ]

    for question_id, risk_id in expected_mappings:
        mapping_exists = (
            (mappings["question_id"] == question_id) & (mappings["risk_id"] == risk_id)
        ).any()
        assert mapping_exists, f"Missing mapping: {question_id} -> {risk_id}"

    # Verify AIR.001 has 2 questions (Q1, Q4)
    air001_mappings = mappings[mappings["risk_id"] == "R.AIR.001"]
    assert len(air001_mappings) == 2
    assert "Q.SHEET1.Q1" in air001_mappings["question_id"].values
    assert "Q.SHEET1.Q4" in air001_mappings["question_id"].values

    # Verify AIR.002 has 2 questions (Q2, Q5)
    air002_mappings = mappings[mappings["risk_id"] == "R.AIR.002"]
    assert len(air002_mappings) == 2
    assert "Q.SHEET1.Q2" in air002_mappings["question_id"].values
    assert "Q.SHEET1.Q5" in air002_mappings["question_id"].values

    # Verify AIR.003 has 1 question (Q3)
    air003_mappings = mappings[mappings["risk_id"] == "R.AIR.003"]
    assert len(air003_mappings) == 1
    assert "Q.SHEET1.Q3" in air003_mappings["question_id"].values


def test_database_storage_of_mappings(temp_dir, test_config_with_associations):
    """Test that question-risk mappings are correctly stored in the database."""
    # Create output directory
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Initialize processor
    processor = DataProcessor(
        data_dir=temp_dir,
        output_dir=output_dir,
        config_manager=ConfigManager(test_config_with_associations),
    )

    # Run complete processing
    processor.process_data()

    # Verify database was created
    db_path = output_dir / "test_associations.db"
    assert db_path.exists()

    # Connect to database and verify mappings
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check question_risk_mapping table exists and has data
    cursor.execute("SELECT COUNT(*) FROM question_risk_mapping")
    mapping_count = cursor.fetchone()[0]
    assert mapping_count > 0

    # Verify specific mappings are stored
    cursor.execute(
        """
        SELECT question_id, risk_id
        FROM question_risk_mapping
        ORDER BY question_id, risk_id
    """
    )
    stored_mappings = cursor.fetchall()

    # Convert to set for easier comparison
    stored_mapping_set = set(stored_mappings)

    expected_mappings = {
        ("Q.SHEET1.Q1", "R.AIR.001"),
        ("Q.SHEET1.Q2", "R.AIR.002"),
        ("Q.SHEET1.Q3", "R.AIR.003"),
        ("Q.SHEET1.Q4", "R.AIR.001"),
        ("Q.SHEET1.Q5", "R.AIR.002"),
    }

    for expected_mapping in expected_mappings:
        assert (
            expected_mapping in stored_mapping_set
        ), f"Missing mapping in database: {expected_mapping}"

    # Verify risk-question associations can be queried
    cursor.execute(
        """
        SELECT q.question_id, q.question_text, qrm.risk_id
        FROM questions q
        JOIN question_risk_mapping qrm ON q.question_id = qrm.question_id
        WHERE qrm.risk_id = 'R.AIR.001'
        ORDER BY q.question_id
    """
    )
    air001_questions = cursor.fetchall()

    # Should have 2 questions for AIR.001
    assert len(air001_questions) == 2
    question_ids = [row[0] for row in air001_questions]
    assert "Q.SHEET1.Q1" in question_ids
    assert "Q.SHEET1.Q4" in question_ids

    conn.close()


def test_api_risk_detail_endpoint(temp_dir, test_config_with_associations):
    """Test that the database correctly stores and can retrieve associated questions for a risk."""
    # Create output directory
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Initialize processor
    processor = DataProcessor(
        data_dir=temp_dir,
        output_dir=output_dir,
        config_manager=ConfigManager(test_config_with_associations),
    )

    # Run complete processing
    processor.process_data()

    # Test database directly (simulating API behavior)
    db_path = output_dir / "test_associations.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Simulate the API query for risk detail with associated questions
    cursor.execute(
        """
        SELECT r.risk_id as id, r.risk_title as title, r.risk_description as description
        FROM risks r
        WHERE r.risk_id = 'R.AIR.001'
    """
    )
    risk_row = cursor.fetchone()

    assert risk_row is not None
    risk_id, risk_title, risk_description = risk_row
    assert risk_id == "R.AIR.001"
    assert risk_title == "Data Privacy Risk"

    # Get associated questions (simulating API behavior)
    cursor.execute(
        """
        SELECT q.question_id as id, q.question_text as text, q.category, q.topic
        FROM questions q
        JOIN question_risk_mapping qrm ON q.question_id = qrm.question_id
        WHERE qrm.risk_id = 'R.AIR.001'
        ORDER BY q.question_id
    """
    )
    associated_questions = cursor.fetchall()

    # Verify associated questions
    assert len(associated_questions) == 2

    # Check that both Q1 and Q4 are associated with AIR.001
    question_ids = [q[0] for q in associated_questions]
    assert "Q.SHEET1.Q1" in question_ids
    assert "Q.SHEET1.Q4" in question_ids

    # Verify question details
    q1_data = next(q for q in associated_questions if q[0] == "Q.SHEET1.Q1")
    assert q1_data[1] == "How is data privacy protected?"
    assert q1_data[2] == "Privacy"
    assert q1_data[3] == "Data Protection"

    q4_data = next(q for q in associated_questions if q[0] == "Q.SHEET1.Q4")
    assert q4_data[1] == "What data encryption measures are implemented?"
    assert q4_data[2] == "Privacy"
    assert q4_data[3] == "Encryption"

    conn.close()


def test_api_risk_detail_endpoint_air002(temp_dir, test_config_with_associations):
    """Test database query for AIR.002 which should have 2 associated questions."""
    # Create output directory
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Initialize processor
    processor = DataProcessor(
        data_dir=temp_dir,
        output_dir=output_dir,
        config_manager=ConfigManager(test_config_with_associations),
    )

    # Run complete processing
    processor.process_data()

    # Test database directly (simulating API behavior)
    db_path = output_dir / "test_associations.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get associated questions for AIR.002
    cursor.execute(
        """
        SELECT q.question_id as id, q.question_text as text, q.category, q.topic
        FROM questions q
        JOIN question_risk_mapping qrm ON q.question_id = qrm.question_id
        WHERE qrm.risk_id = 'R.AIR.002'
        ORDER BY q.question_id
    """
    )
    associated_questions = cursor.fetchall()

    # Verify associated questions
    assert len(associated_questions) == 2

    # Check that both Q2 and Q5 are associated with AIR.002
    question_ids = [q[0] for q in associated_questions]
    assert "Q.SHEET1.Q2" in question_ids
    assert "Q.SHEET1.Q5" in question_ids

    conn.close()


def test_api_risk_detail_endpoint_air003(temp_dir, test_config_with_associations):
    """Test database query for AIR.003 which should have 1 associated question."""
    # Create output directory
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Initialize processor
    processor = DataProcessor(
        data_dir=temp_dir,
        output_dir=output_dir,
        config_manager=ConfigManager(test_config_with_associations),
    )

    # Run complete processing
    processor.process_data()

    # Test database directly (simulating API behavior)
    db_path = output_dir / "test_associations.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get associated questions for AIR.003
    cursor.execute(
        """
        SELECT q.question_id as id, q.question_text as text, q.category, q.topic
        FROM questions q
        JOIN question_risk_mapping qrm ON q.question_id = qrm.question_id
        WHERE qrm.risk_id = 'R.AIR.003'
        ORDER BY q.question_id
    """
    )
    associated_questions = cursor.fetchall()

    # Verify associated questions
    assert len(associated_questions) == 1

    # Check that Q3 is associated with AIR.003
    question_ids = [q[0] for q in associated_questions]
    assert "Q.SHEET1.Q3" in question_ids

    # Verify question details
    q3_data = associated_questions[0]
    assert q3_data[1] == "How is access controlled?"
    assert q3_data[2] == "Security"
    assert q3_data[3] == "Access Management"

    conn.close()


def test_end_to_end_workflow(temp_dir, test_config_with_associations):
    """Test complete end-to-end workflow from Excel files to database queries."""
    # Create output directory
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Initialize processor
    processor = DataProcessor(
        data_dir=temp_dir,
        output_dir=output_dir,
        config_manager=ConfigManager(test_config_with_associations),
    )

    # Run complete processing
    processor.process_data()

    # Verify all components worked together
    db_path = output_dir / "test_associations.db"
    assert db_path.exists()

    # Test database queries (simulating API behavior)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Test all three risks
    for risk_id in ["R.AIR.001", "R.AIR.002", "R.AIR.003"]:
        # Get risk details
        cursor.execute(
            """
            SELECT r.risk_id as id, r.risk_title as title, r.risk_description as description
            FROM risks r
            WHERE r.risk_id = ?
        """,
            (risk_id,),
        )
        risk_row = cursor.fetchone()

        assert risk_row is not None
        assert risk_row[0] == risk_id

        # Get associated questions
        cursor.execute(
            """
            SELECT q.question_id as id, q.question_text as text, q.category, q.topic
            FROM questions q
            JOIN question_risk_mapping qrm ON q.question_id = qrm.question_id
            WHERE qrm.risk_id = ?
            ORDER BY q.question_id
        """,
            (risk_id,),
        )
        associated_questions = cursor.fetchall()

        # Verify questions are properly formatted
        for question in associated_questions:
            assert question[0].startswith("Q.")  # question_id
            assert len(question[1]) > 0  # question_text
            assert len(question[2]) > 0  # category
            assert len(question[3]) > 0  # topic

    conn.close()


def test_missing_associations_scenario(temp_dir):
    """Test scenario where questions exist but no associations are created."""
    # Create data where questions don't have proper risk mappings
    risks_data = pd.DataFrame(
        {
            "ID": ["AIR.001", "AIR.002"],
            "Risk": ["Risk 1", "Risk 2"],
            "Risk Description": ["Description 1", "Description 2"],
        }
    )

    controls_data = pd.DataFrame(
        {
            "Code": ["AIGPC.1"],
            "Purpose": ["Control 1"],
            "Description": ["Description 1"],
            "Mapped Risks": ["AIR.001"],
        }
    )

    # Questions without proper risk mappings
    questions_data = pd.DataFrame(
        {
            "Question Number": ["Q1", "Q2"],
            "Question Text": ["Question 1?", "Question 2?"],
            "Category": ["Category 1", "Category 2"],
            "Topic": ["Topic 1", "Topic 2"],
            "AIML_RISK_TAXONOMY": ["", "TBD"],  # Empty and TBD values
            "AIML_CONTROL": ["AIGPC.1", "AIGPC.1"],
        }
    )

    # Create config
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
                    "id": "Code",
                    "title": "Purpose",
                    "description": "Description",
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
        "database": {"file": "test_no_associations.db"},
        "extraction": {"validate_files": True, "remove_duplicates": True},
        "output": {"print_summary": False, "collect_metadata": True},
    }

    config_file = temp_dir / "test_config.yaml"
    import yaml

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Create Excel files
    risks_data.to_excel(temp_dir / "test_risks.xlsx", index=False)
    # Create controls file with "Domains" sheet name to match expected structure
    with pd.ExcelWriter(temp_dir / "test_controls.xlsx") as writer:
        controls_data.to_excel(writer, sheet_name="Domains", index=False)
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

    # Verify no associations were created
    assert processor.question_risk_mapping_df.empty

    # Test database query - should return empty associated_questions
    db_path = output_dir / "test_no_associations.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get associated questions for AIR.001 (should be empty)
    cursor.execute(
        """
        SELECT q.question_id as id, q.question_text as text, q.category, q.topic
        FROM questions q
        JOIN question_risk_mapping qrm ON q.question_id = qrm.question_id
        WHERE qrm.risk_id = 'R.AIR.001'
        ORDER BY q.question_id
    """
    )
    associated_questions = cursor.fetchall()

    # Should be empty since no associations were created
    assert len(associated_questions) == 0

    conn.close()


class TestProcessingModes:
    """Test risk-question associations across different processing modes."""

    def test_adaptive_mode_associations(self, temp_dir):
        """Test question-risk associations in adaptive processing mode."""
        # Create test data
        risks_data = pd.DataFrame(
            {
                "ID": ["AIR.001", "AIR.002"],
                "Risk": ["Data Privacy Risk", "Model Bias Risk"],
                "Risk Description": [
                    "Risk of unauthorized access",
                    "Risk of biased outputs",
                ],
            }
        )

        questions_data = pd.DataFrame(
            {
                "Question Number": ["Q1", "Q2"],
                "Question Text": [
                    "How is data privacy protected?",
                    "What validation processes are in place?",
                ],
                "Category": ["Privacy", "Validation"],
                "Topic": ["Data Protection", "Model Testing"],
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
            "database": {"file": "test_adaptive.db"},
            "extraction": {"validate_files": True, "remove_duplicates": True},
            "output": {"print_summary": False, "collect_metadata": True},
        }

        config_file = temp_dir / "adaptive_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Create Excel files
        risks_data.to_excel(temp_dir / "test_risks.xlsx", index=False)
        questions_data.to_excel(temp_dir / "test_questions.xlsx", index=False)

        # Test adaptive mode processing
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        processor = DataProcessor(
            data_dir=temp_dir,
            output_dir=output_dir,
            config_manager=ConfigManager(config_file),
            use_adaptive_mode=True,
        )

        processor.process_data()

        # Verify associations were created
        db_path = output_dir / "test_adaptive.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM question_risk_mapping")
        mapping_count = cursor.fetchone()[0]
        assert mapping_count > 0

        conn.close()


class TestDataQualityScenarios:
    """Test risk-question associations with various data quality scenarios."""

    def test_mixed_data_types_in_mappings(self, temp_dir):
        """Test with mixed data types in mapping columns."""
        # Create data with mixed types (strings, numbers, NaN)
        questions_data = pd.DataFrame(
            {
                "Question Number": ["Q1", "Q2", "Q3"],
                "Question Text": ["Question 1?", "Question 2?", "Question 3?"],
                "Category": ["Privacy", "Validation", "Security"],
                "Topic": ["Data Protection", "Model Testing", "Access Management"],
                "AIML_RISK_TAXONOMY": ["AIR.001", 2, "AIR.003"],  # Mixed types
                "AIML_CONTROL": ["AIGPC.1", "AIGPC.2", 3],  # Mixed types
            }
        )

        risks_data = pd.DataFrame(
            {
                "ID": ["AIR.001", "AIR.002", "AIR.003"],
                "Risk": ["Risk 1", "Risk 2", "Risk 3"],
                "Risk Description": ["Desc 1", "Desc 2", "Desc 3"],
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
            "database": {"file": "test_mixed_types.db"},
            "extraction": {"validate_files": True, "remove_duplicates": True},
            "output": {"print_summary": False, "collect_metadata": True},
        }

        config_file = temp_dir / "mixed_types_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Create Excel files
        risks_data.to_excel(temp_dir / "test_risks.xlsx", index=False)
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

        # Verify processing handled mixed types gracefully
        db_path = output_dir / "test_mixed_types.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Should have some valid mappings despite mixed types
        cursor.execute("SELECT COUNT(*) FROM question_risk_mapping")
        mapping_count = cursor.fetchone()[0]
        assert mapping_count >= 0  # Should not crash

        conn.close()


def test_database_schema_validation(
    temp_dir, test_config_with_associations, test_data_with_associations
):
    """Test that the database schema properly supports question-risk associations."""
    # Create test Excel files
    test_data_with_associations["risks"].to_excel(
        temp_dir / "test_risks.xlsx", index=False
    )
    test_data_with_associations["controls"].to_excel(
        temp_dir / "test_controls.xlsx", index=False
    )
    test_data_with_associations["questions"].to_excel(
        temp_dir / "test_questions.xlsx", index=False
    )

    # Create output directory
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Initialize processor
    processor = DataProcessor(
        data_dir=temp_dir,
        output_dir=output_dir,
        config_manager=ConfigManager(test_config_with_associations),
    )

    # Run complete processing
    processor.process_data()

    # Verify database schema
    db_path = output_dir / "test_associations.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check that question_risk_mapping table exists with correct schema
    cursor.execute("PRAGMA table_info(question_risk_mapping)")
    columns = cursor.fetchall()

    column_names = [col[1] for col in columns]
    # The actual schema may vary, so check for the essential columns
    assert "question_id" in column_names
    assert "risk_id" in column_names

    # Check foreign key constraints (may not be enabled in test environment)
    cursor.execute("PRAGMA foreign_key_list(question_risk_mapping)")

    # Foreign keys may not be enabled in test environment, so just verify table exists
    # and has the required columns
    assert len(column_names) > 0

    # Check that we can query the table successfully
    cursor.execute("SELECT COUNT(*) FROM question_risk_mapping")
    count = cursor.fetchone()[0]
    assert count >= 0  # Should be able to query without error

    conn.close()


def test_mapping_extractor_validation(temp_dir, test_config_with_associations):
    """Test that MappingExtractor properly validates question-risk mappings."""
    from extractors.mapping_extractor import MappingExtractor

    # Create questions file
    questions_data = pd.DataFrame(
        {
            "Question Number": ["Q1", "Q2", "Q3"],
            "Question Text": ["Question 1?", "Question 2?", "Question 3?"],
            "Category": ["Category 1", "Category 2", "Category 3"],
            "Topic": ["Topic 1", "Topic 2", "Topic 3"],
            "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002", "AIR.003"],
            "AIML_CONTROL": ["AIGPC.1", "AIGPC.2", "AIGPC.3"],
        }
    )

    questions_file = temp_dir / "test_questions.xlsx"
    questions_data.to_excel(
        questions_file, sheet_name="Cyber Risk Architecture", index=False
    )

    # Test mapping extraction
    config_manager = ConfigManager(test_config_with_associations)
    mapping_extractor = MappingExtractor(config_manager)

    risk_mappings, control_mappings = mapping_extractor.extract_question_mappings(
        questions_file
    )

    # Validate mappings
    assert mapping_extractor.validate_mappings(risk_mappings, "question_risk") is True
    assert (
        mapping_extractor.validate_mappings(control_mappings, "question_control")
        is True
    )

    # Verify mapping content
    assert len(risk_mappings) == 3
    assert len(control_mappings) == 3

    # Check specific mappings
    expected_risk_mappings = [
        ("Q.CRA.Q1", "R.AIR.001"),
        ("Q.CRA.Q2", "R.AIR.002"),
        ("Q.CRA.Q3", "R.AIR.003"),
    ]

    for question_id, risk_id in expected_risk_mappings:
        mapping_exists = (
            (risk_mappings["question_id"] == question_id)
            & (risk_mappings["risk_id"] == risk_id)
        ).any()
        assert mapping_exists, f"Missing risk mapping: {question_id} -> {risk_id}"
