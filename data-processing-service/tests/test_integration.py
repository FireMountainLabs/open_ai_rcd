import pandas as pd

"""
Integration tests for Data Processing Microservice.

Tests the complete data processing workflow from Excel files to database.
"""

import pytest

from config.config_manager import ConfigManager
from data_processor import DataProcessor
from database_manager import DatabaseManager


class TestDataProcessingIntegration:
    """Integration tests for complete data processing workflow."""

    def test_complete_processing_workflow(
        self, temp_dir, sample_config, mock_excel_files
    ):
        """Test complete data processing workflow."""
        # Create output directory
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Initialize processor
        processor = DataProcessor(
            data_dir=temp_dir,
            output_dir=output_dir,
            config_manager=ConfigManager(sample_config),
        )

        # Run complete workflow
        processor.process_data()

        # Verify database was created
        db_path = output_dir / "test_data.db"
        assert db_path.exists()

        # Verify data was inserted
        db_manager = DatabaseManager(db_path)
        conn = db_manager._get_connection()
        cursor = conn.cursor()

        # Check risks table
        cursor.execute("SELECT COUNT(*) FROM risks")
        risks_count = cursor.fetchone()[0]
        assert risks_count > 0

        # Check controls table
        cursor.execute("SELECT COUNT(*) FROM controls")
        controls_count = cursor.fetchone()[0]
        assert controls_count > 0

        # Check questions table
        cursor.execute("SELECT COUNT(*) FROM questions")
        questions_count = cursor.fetchone()[0]
        assert questions_count > 0

    def test_file_validation_success(self, data_processor, mock_excel_files):
        """Test successful file validation."""
        # Should not raise any errors
        result = data_processor.validate_input_files()
        assert result is True

    def test_file_validation_missing_files(self, data_processor, temp_dir):
        """Test file validation with missing files."""
        # Remove files to simulate missing files
        for file_path in temp_dir.glob("*.xlsx"):
            file_path.unlink()

        with pytest.raises(FileNotFoundError):
            data_processor.validate_input_files()

    def test_data_extraction_workflow(self, data_processor, mock_excel_files):
        """Test data extraction workflow."""
        # Validate files first
        data_processor.validate_input_files()

        # Extract data
        data_processor.extract_data()

        # Verify data was extracted
        assert data_processor.risks_df is not None
        assert data_processor.controls_df is not None
        assert data_processor.questions_df is not None

        # Verify data has expected structure
        assert "risk_id" in data_processor.risks_df.columns
        assert "risk_title" in data_processor.risks_df.columns
        assert "control_id" in data_processor.controls_df.columns
        assert "control_title" in data_processor.controls_df.columns
        assert "question_id" in data_processor.questions_df.columns
        assert "question_text" in data_processor.questions_df.columns

    def test_database_population_workflow(self, data_processor, mock_excel_files):
        """Test database population workflow."""
        # Run extraction first
        data_processor.extract_data()

        # Populate database
        data_processor.populate_database()

        # Verify database was created and populated
        db_path = data_processor.database_manager.db_path
        assert db_path.exists()

        # Verify data was inserted
        conn = data_processor.database_manager._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM risks")
        risks_count = cursor.fetchone()[0]
        assert risks_count == len(data_processor.risks_df)

        cursor.execute("SELECT COUNT(*) FROM controls")
        controls_count = cursor.fetchone()[0]
        assert controls_count == len(data_processor.controls_df)

        cursor.execute("SELECT COUNT(*) FROM questions")
        questions_count = cursor.fetchone()[0]
        assert questions_count == len(data_processor.questions_df)

    def test_mapping_creation(self, data_processor, mock_excel_files):
        """Test relationship mapping creation."""
        # Run extraction
        data_processor.extract_data()

        # Verify mappings were created
        assert data_processor.risk_control_mapping_df is not None
        assert data_processor.question_risk_mapping_df is not None
        assert data_processor.question_control_mapping_df is not None

        # Verify mapping structure
        if not data_processor.risk_control_mapping_df.empty:
            assert "risk_id" in data_processor.risk_control_mapping_df.columns
            assert "control_id" in data_processor.risk_control_mapping_df.columns

        if not data_processor.question_risk_mapping_df.empty:
            assert "question_id" in data_processor.question_risk_mapping_df.columns
            assert "risk_id" in data_processor.question_risk_mapping_df.columns

    def test_metadata_collection(self, data_processor, mock_excel_files):
        """Test file metadata collection."""
        # Run complete workflow
        data_processor.process_data()

        # Verify metadata was collected
        conn = data_processor.database_manager._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM file_metadata")
        metadata_count = cursor.fetchone()[0]
        assert metadata_count > 0

        # Verify metadata content
        cursor.execute("SELECT * FROM file_metadata LIMIT 1")
        metadata = cursor.fetchone()
        assert metadata is not None
        assert metadata[1] in ["risks", "controls", "questions"]  # data_type

    def test_error_handling_in_extraction(self, data_processor, temp_dir):
        """Test error handling during extraction."""
        # Create invalid Excel file
        invalid_file = temp_dir / "test_risks.xlsx"
        with open(invalid_file, "w") as f:
            f.write("This is not a valid Excel file")

        # Should handle error gracefully
        with pytest.raises(Exception):
            data_processor.extract_data()

    def test_duplicate_removal(self, data_processor, temp_dir, sample_config):
        """Test duplicate removal functionality."""
        # Create data with duplicates
        duplicate_risks = pd.DataFrame(
            {
                "ID": ["AIR.001", "AIR.001", "AIR.002"],
                "Risk": ["Risk 1", "Risk 1 Duplicate", "Risk 2"],
                "Risk Description": ["Desc 1", "Desc 1 Duplicate", "Desc 2"],
            }
        )

        # Create minimal control and question data to satisfy the processor
        duplicate_controls = pd.DataFrame(
            {
                "Code": ["AIGPC.1"],
                "Purpose": ["Test Control"],
                "Description": ["Test Description"],
                "Mapped Risks": ["AIR.001"],
            }
        )

        duplicate_questions = pd.DataFrame(
            {
                "Question Number": ["Q1"],
                "Question Text": ["Test Question"],
                "Category": ["Test"],
                "Topic": ["Test Topic"],
                "AIML_RISK_TAXONOMY": ["AIR.001"],
                "AIML_CONTROL": ["AIGPC.1"],
            }
        )

        # Save all files
        duplicate_risks.to_excel(temp_dir / "test_risks.xlsx", index=False)
        duplicate_controls.to_excel(temp_dir / "test_controls.xlsx", index=False)
        duplicate_questions.to_excel(temp_dir / "test_questions.xlsx", index=False)

        # Process data
        processor = DataProcessor(
            data_dir=temp_dir,
            output_dir=temp_dir / "output",
            config_manager=ConfigManager(sample_config),
        )

        processor.extract_data()

        # Verify duplicates were removed
        assert len(processor.risks_df) == 2  # Should have 2 unique records
        assert (
            len(processor.risks_df[processor.risks_df["risk_id"] == "R.AIR.001"]) == 1
        )

    def test_large_dataset_processing(
        self, temp_dir, sample_config, test_data_generator
    ):
        """Test processing of large datasets."""
        # Create large datasets
        large_risks = test_data_generator.create_risk_data(1000)
        large_controls = test_data_generator.create_control_data(500)
        large_questions = test_data_generator.create_question_data(2000)

        # Save to Excel files
        large_risks.to_excel(temp_dir / "test_risks.xlsx", index=False)
        large_controls.to_excel(temp_dir / "test_controls.xlsx", index=False)
        large_questions.to_excel(temp_dir / "test_questions.xlsx", index=False)

        # Process data
        processor = DataProcessor(
            data_dir=temp_dir,
            output_dir=temp_dir / "output",
            config_manager=ConfigManager(sample_config),
        )

        processor.process_data()

        # Verify all data was processed
        conn = processor.database_manager._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM risks")
        assert cursor.fetchone()[0] == 1000

        cursor.execute("SELECT COUNT(*) FROM controls")
        assert cursor.fetchone()[0] == 500

        cursor.execute("SELECT COUNT(*) FROM questions")
        assert cursor.fetchone()[0] == 2000

    def test_configuration_override(self, temp_dir, mock_excel_files):
        """Test configuration override functionality."""
        # Create custom config
        custom_config = temp_dir / "custom_config.yaml"
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
                        "description": "Purpose",
                    },
                },
                "questions": {
                    "file": "test_questions.xlsx",
                    "columns": {
                        "id": "Question Number",
                        "text": "Question Text",
                        "category": "Category",
                        "topic": "Topic",
                    },
                },
            },
            "database": {"file": "custom_data.db"},
            "extraction": {"validate_files": True, "remove_duplicates": True},
            "output": {"print_summary": False, "collect_metadata": True},
        }

        import yaml

        with open(custom_config, "w") as f:
            yaml.dump(config_data, f)

        # Process with custom config
        processor = DataProcessor(
            data_dir=temp_dir,
            output_dir=temp_dir / "output",
            config_manager=ConfigManager(custom_config),
        )

        processor.process_data()

        # Verify custom database was created
        custom_db = temp_dir / "output" / "custom_data.db"
        assert custom_db.exists()

    def test_processing_summary(self, data_processor, mock_excel_files, capsys):
        """Test processing summary output."""
        # Run processing
        data_processor.process_data()

        # Print summary
        data_processor._print_summary()

        # Capture output
        captured = capsys.readouterr()
        output = captured.out

        # Verify summary contains expected information
        assert "DATA PROCESSING SUMMARY" in output
        assert "Risks extracted:" in output
        assert "Controls extracted:" in output
        assert "Questions extracted:" in output
        assert "Database created at:" in output
