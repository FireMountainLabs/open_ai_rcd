import pandas as pd

"""
Comprehensive tests for all extractor classes.

Tests the functionality of ControlExtractor, MappingExtractor, QuestionExtractor,
and RiskExtractor to ensure they properly extract and validate data from Excel files.
"""

from pathlib import Path

import pytest

from extractors.control_extractor import ControlExtractor
from extractors.mapping_extractor import MappingExtractor
from extractors.question_extractor import QuestionExtractor
from extractors.risk_extractor import RiskExtractor


class TestControlExtractor:
    """Test cases for ControlExtractor class."""

    @pytest.fixture
    def control_extractor(self, config_manager):
        """Create a ControlExtractor instance for testing."""
        return ControlExtractor(config_manager)

    @pytest.fixture
    def sample_control_data_domains(self):
        """Sample data for Domains sheet."""
        return pd.DataFrame(
            {
                "Code": ["AIIM.1", "AIIM.2", "AIIM.3"],
                "Purpose": ["Data Management", "Model Governance", "Security Controls"],
                "Mapped Risks": ["AIR.001", "AIR.002", "AIR.003"],
                "Asset Type": ["Data", "Model", "System"],
                "Control Type": ["Preventive", "Detective", "Corrective"],
                "Security Function": ["Protect", "Detect", "Respond"],
                "Maturity": ["Basic", "Intermediate", "Advanced"],
            }
        )

    @pytest.fixture
    def sample_control_data_individual(self):
        """Sample data for individual control sheet."""
        return pd.DataFrame(
            {
                "Sub-Control": ["AIIM.1.1", "AIIM.1.2", "AIIM.2.1"],
                "Control Title": [
                    "Data Classification",
                    "Access Control",
                    "Model Validation",
                ],
                "Control Description": [
                    "Classify data by sensitivity",
                    "Control access to systems",
                    "Validate model outputs",
                ],
                "Mapped Risks": ["AIR.001", "AIR.002", "AIR.003"],
                "Asset Type": ["Data", "System", "Model"],
                "Control Type": ["Preventive", "Preventive", "Detective"],
                "Security Function": ["Protect", "Protect", "Detect"],
                "Maturity": ["Basic", "Intermediate", "Advanced"],
            }
        )

    def test_control_extractor_initialization(self, config_manager):
        """Test ControlExtractor initialization."""
        extractor = ControlExtractor(config_manager)
        assert extractor.config_manager == config_manager

    def test_extract_domains_sheet(
        self, control_extractor, temp_dir, sample_control_data_domains
    ):
        """Test extraction from Domains sheet."""
        # Create Excel file with Domains sheet
        excel_file = temp_dir / "test_controls.xlsx"
        with pd.ExcelWriter(excel_file) as writer:
            sample_control_data_domains.to_excel(
                writer, sheet_name="Domains", index=False
            )

        # Extract data
        result_df = control_extractor.extract(excel_file)

        # Verify results
        assert not result_df.empty
        assert len(result_df) == 3
        assert "control_id" in result_df.columns
        assert "control_title" in result_df.columns
        assert "control_description" in result_df.columns

        # Check ID formatting
        assert all(result_df["control_id"].str.startswith("C."))
        assert "C.AIIM.1" in result_df["control_id"].values
        assert "C.AIIM.2" in result_df["control_id"].values
        assert "C.AIIM.3" in result_df["control_id"].values

    def test_extract_individual_sheet(
        self, control_extractor, temp_dir, sample_control_data_individual
    ):
        """Test extraction from individual control sheet."""
        # Create Excel file with individual sheet
        excel_file = temp_dir / "test_controls.xlsx"
        with pd.ExcelWriter(excel_file) as writer:
            sample_control_data_individual.to_excel(
                writer, sheet_name="Individual Controls", index=False
            )

        # Extract data
        result_df = control_extractor.extract(excel_file)

        # Verify results
        assert not result_df.empty
        assert len(result_df) == 3
        assert "C.AIIM.1.1" in result_df["control_id"].values
        assert "C.AIIM.1.2" in result_df["control_id"].values
        assert "C.AIIM.2.1" in result_df["control_id"].values

    def test_extract_multiple_sheets(
        self,
        control_extractor,
        temp_dir,
        sample_control_data_domains,
        sample_control_data_individual,
    ):
        """Test extraction from multiple sheets."""
        # Create Excel file with multiple sheets
        excel_file = temp_dir / "test_controls.xlsx"
        with pd.ExcelWriter(excel_file) as writer:
            sample_control_data_domains.to_excel(
                writer, sheet_name="Domains", index=False
            )
            sample_control_data_individual.to_excel(
                writer, sheet_name="Individual Controls", index=False
            )

        # Extract data
        result_df = control_extractor.extract(excel_file)

        # Verify results - should have data from both sheets
        assert not result_df.empty
        assert len(result_df) == 6  # 3 from each sheet
        assert "C.AIIM.1" in result_df["control_id"].values  # From Domains
        assert "C.AIIM.1.1" in result_df["control_id"].values  # From Individual

    def test_extract_missing_mapped_risks_column(self, control_extractor, temp_dir):
        """Test extraction when Mapped Risks column is missing."""
        # Create Excel file without Mapped Risks column
        data = pd.DataFrame({"Code": ["AIIM.1"], "Purpose": ["Test Control"]})
        excel_file = temp_dir / "test_controls.xlsx"
        data.to_excel(excel_file, index=False)

        # Extract data - should return empty DataFrame
        result_df = control_extractor.extract(excel_file)
        assert result_df.empty

    def test_extract_file_not_found(self, control_extractor):
        """Test extraction with non-existent file."""
        with pytest.raises(FileNotFoundError):
            control_extractor.extract(Path("nonexistent.xlsx"))

    def test_extract_invalid_data(self, control_extractor, temp_dir):
        """Test extraction with invalid data."""
        # Create Excel file with missing required fields
        data = pd.DataFrame(
            {
                "Code": ["", "AIIM.1"],  # Empty ID
                "Purpose": ["Test Control", ""],  # Empty title
                "Mapped Risks": ["AIR.001", "AIR.002"],
            }
        )
        excel_file = temp_dir / "test_controls.xlsx"
        data.to_excel(excel_file, index=False)

        # Extract data - should skip invalid rows
        result_df = control_extractor.extract(excel_file)
        assert result_df.empty  # Both rows should be skipped

    def test_clean_value(self, control_extractor):
        """Test value cleaning functionality."""
        # Test various input types
        assert control_extractor._clean_value(None) == ""
        assert control_extractor._clean_value("") == ""
        assert control_extractor._clean_value("  test  ") == "test"
        assert (
            control_extractor._clean_value("test   with   spaces") == "test with spaces"
        )
        assert control_extractor._clean_value(123) == "123"

    def test_validate_data_success(self, control_extractor):
        """Test successful data validation."""
        valid_data = pd.DataFrame(
            {
                "control_id": ["C.AIIM.1", "C.AIIM.2"],
                "control_title": ["Control 1", "Control 2"],
                "control_description": ["Description 1", "Description 2"],
            }
        )

        assert control_extractor.validate_data(valid_data) is True

    def test_validate_data_empty(self, control_extractor):
        """Test validation with empty data."""
        empty_data = pd.DataFrame()
        with pytest.raises(ValueError, match="No control data found"):
            control_extractor.validate_data(empty_data)

    def test_validate_data_missing_columns(self, control_extractor):
        """Test validation with missing required columns."""
        invalid_data = pd.DataFrame(
            {
                "control_id": ["C.AIIM.1"]
                # Missing control_title
            }
        )
        with pytest.raises(ValueError, match="Missing required columns"):
            control_extractor.validate_data(invalid_data)

    def test_validate_data_empty_fields(self, control_extractor):
        """Test validation with empty required fields."""
        invalid_data = pd.DataFrame(
            {"control_id": ["", "C.AIIM.2"], "control_title": ["Control 1", ""]}
        )
        with pytest.raises(ValueError):
            control_extractor.validate_data(invalid_data)

    def test_validate_data_duplicates(self, control_extractor):
        """Test validation with duplicate IDs."""
        invalid_data = pd.DataFrame(
            {
                "control_id": ["C.AIIM.1", "C.AIIM.1"],
                "control_title": ["Control 1", "Control 2"],
            }
        )
        with pytest.raises(ValueError, match="duplicate control_id"):
            control_extractor.validate_data(invalid_data)


class TestRiskExtractor:
    """Test cases for RiskExtractor class."""

    @pytest.fixture
    def risk_extractor(self, config_manager):
        """Create a RiskExtractor instance for testing."""
        return RiskExtractor(config_manager)

    @pytest.fixture
    def sample_risk_data(self):
        """Sample risk data for testing."""
        return pd.DataFrame(
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

    def test_risk_extractor_initialization(self, config_manager):
        """Test RiskExtractor initialization."""
        extractor = RiskExtractor(config_manager)
        assert extractor.config_manager == config_manager

    def test_extract_success(self, risk_extractor, temp_dir, sample_risk_data):
        """Test successful risk extraction."""
        excel_file = temp_dir / "test_risks.xlsx"
        sample_risk_data.to_excel(excel_file, index=False)

        result_df = risk_extractor.extract(excel_file)

        # Verify results
        assert not result_df.empty
        assert len(result_df) == 3
        assert "risk_id" in result_df.columns
        assert "risk_title" in result_df.columns
        assert "risk_description" in result_df.columns

        # Check ID formatting
        assert all(result_df["risk_id"].str.startswith("R."))
        assert "R.AIR.001" in result_df["risk_id"].values
        assert "R.AIR.002" in result_df["risk_id"].values
        assert "R.AIR.003" in result_df["risk_id"].values

    def test_extract_file_not_found(self, risk_extractor):
        """Test extraction with non-existent file."""
        with pytest.raises(FileNotFoundError):
            risk_extractor.extract(Path("nonexistent.xlsx"))

    def test_extract_missing_columns(self, risk_extractor, temp_dir):
        """Test extraction with missing required columns."""
        # Create Excel file with missing required columns
        data = pd.DataFrame(
            {
                "ID": ["AIR.001"]
                # Missing Risk column
            }
        )
        excel_file = temp_dir / "test_risks.xlsx"
        data.to_excel(excel_file, index=False)

        with pytest.raises(ValueError, match="Missing required columns"):
            risk_extractor.extract(excel_file)

    def test_extract_invalid_data(self, risk_extractor, temp_dir):
        """Test extraction with invalid data."""
        # Create Excel file with missing required fields
        data = pd.DataFrame(
            {
                "ID": ["", "AIR.002"],  # Empty ID
                "Risk": ["Risk 1", ""],  # Empty title
                "Risk Description": ["Description 1", "Description 2"],
            }
        )
        excel_file = temp_dir / "test_risks.xlsx"
        data.to_excel(excel_file, index=False)

        # Extract data - should skip invalid rows
        result_df = risk_extractor.extract(excel_file)
        assert result_df.empty  # Both rows should be skipped

    def test_clean_value(self, risk_extractor):
        """Test value cleaning functionality."""
        # Test various input types
        assert risk_extractor._clean_value(None) == ""
        assert risk_extractor._clean_value("") == ""
        assert risk_extractor._clean_value("  test  ") == "test"
        assert risk_extractor._clean_value("test   with   spaces") == "test with spaces"
        assert risk_extractor._clean_value(123) == "123"

    def test_validate_data_success(self, risk_extractor):
        """Test successful data validation."""
        valid_data = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001", "R.AIR.002"],
                "risk_title": ["Risk 1", "Risk 2"],
                "risk_description": ["Description 1", "Description 2"],
            }
        )

        assert risk_extractor.validate_data(valid_data) is True

    def test_validate_data_empty(self, risk_extractor):
        """Test validation with empty data."""
        empty_data = pd.DataFrame()
        with pytest.raises(ValueError, match="No risk data found"):
            risk_extractor.validate_data(empty_data)

    def test_validate_data_missing_columns(self, risk_extractor):
        """Test validation with missing required columns."""
        invalid_data = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001"]
                # Missing risk_title
            }
        )
        with pytest.raises(ValueError, match="Missing required columns"):
            risk_extractor.validate_data(invalid_data)

    def test_validate_data_empty_fields(self, risk_extractor):
        """Test validation with empty required fields."""
        invalid_data = pd.DataFrame(
            {"risk_id": ["", "R.AIR.002"], "risk_title": ["Risk 1", ""]}
        )
        with pytest.raises(ValueError):
            risk_extractor.validate_data(invalid_data)

    def test_validate_data_duplicates(self, risk_extractor):
        """Test validation with duplicate IDs."""
        invalid_data = pd.DataFrame(
            {"risk_id": ["R.AIR.001", "R.AIR.001"], "risk_title": ["Risk 1", "Risk 2"]}
        )
        with pytest.raises(ValueError, match="duplicate risk_id"):
            risk_extractor.validate_data(invalid_data)


class TestQuestionExtractor:
    """Test cases for QuestionExtractor class."""

    @pytest.fixture
    def question_extractor(self, config_manager):
        """Create a QuestionExtractor instance for testing."""
        return QuestionExtractor(config_manager)

    @pytest.fixture
    def sample_question_data(self):
        """Sample question data for testing."""
        return pd.DataFrame(
            {
                "Question Number": ["Q1", "Q2", "Q3"],
                "Question Text": [
                    "How is data privacy protected?",
                    "What validation processes are in place?",
                    "How is access controlled?",
                ],
                "Category": ["Privacy", "Validation", "Security"],
                "Topic": ["Data Protection", "Model Testing", "Access Management"],
            }
        )

    def test_question_extractor_initialization(self, config_manager):
        """Test QuestionExtractor initialization."""
        extractor = QuestionExtractor(config_manager)
        assert extractor.config_manager == config_manager

    def test_extract_success(self, question_extractor, temp_dir, sample_question_data):
        """Test successful question extraction."""
        excel_file = temp_dir / "test_questions.xlsx"
        sample_question_data.to_excel(
            excel_file, sheet_name="Cyber Risk Architecture", index=False
        )

        result_df = question_extractor.extract(excel_file)

        # Verify results
        assert not result_df.empty
        assert len(result_df) == 3
        assert "question_id" in result_df.columns
        assert "question_text" in result_df.columns
        assert "category" in result_df.columns
        assert "topic" in result_df.columns
        assert "managing_role" in result_df.columns

        # Check ID formatting
        assert all(result_df["question_id"].str.startswith("Q."))
        assert "Q.CRA.Q1" in result_df["question_id"].values
        assert "Q.CRA.Q2" in result_df["question_id"].values
        assert "Q.CRA.Q3" in result_df["question_id"].values

    def test_extract_multiple_sheets(self, question_extractor, temp_dir):
        """Test extraction from multiple sheets."""
        # Create Excel file with multiple sheets
        excel_file = temp_dir / "test_questions.xlsx"
        with pd.ExcelWriter(excel_file) as writer:
            # Sheet 1
            pd.DataFrame(
                {
                    "Question Number": ["Q1"],
                    "Question Text": ["Question 1?"],
                    "Category": ["Category 1"],
                    "Topic": ["Topic 1"],
                }
            ).to_excel(writer, sheet_name="Sheet1", index=False)

            # Sheet 2
            pd.DataFrame(
                {
                    "Question Number": ["Q2"],
                    "Question Text": ["Question 2?"],
                    "Category": ["Category 2"],
                    "Topic": ["Topic 2"],
                }
            ).to_excel(writer, sheet_name="Sheet2", index=False)

        result_df = question_extractor.extract(excel_file)

        # Verify results - should have data from both sheets
        assert not result_df.empty
        assert len(result_df) == 2
        assert "Q.SHEET1.Q1" in result_df["question_id"].values
        assert "Q.SHEET2.Q2" in result_df["question_id"].values

        # Check managing_role is set to sheet name
        assert "Sheet1" in result_df["managing_role"].values
        assert "Sheet2" in result_df["managing_role"].values

    def test_extract_file_not_found(self, question_extractor):
        """Test extraction with non-existent file."""
        with pytest.raises(FileNotFoundError):
            question_extractor.extract(Path("nonexistent.xlsx"))

    def test_extract_invalid_data(self, question_extractor, temp_dir):
        """Test extraction with invalid data."""
        # Create Excel file with missing required fields
        data = pd.DataFrame(
            {
                "Question Number": ["", "Q2"],  # Empty ID
                "Question Text": ["Question 1?", ""],  # Empty text
                "Category": ["Category 1", "Category 2"],
                "Topic": ["Topic 1", "Topic 2"],
            }
        )
        excel_file = temp_dir / "test_questions.xlsx"
        data.to_excel(excel_file, index=False)

        # Extract data - should skip invalid rows
        result_df = question_extractor.extract(excel_file)
        assert result_df.empty  # Both rows should be skipped

    def test_clean_value(self, question_extractor):
        """Test value cleaning functionality."""
        # Test various input types
        assert question_extractor._clean_value(None) == ""
        assert question_extractor._clean_value("") == ""
        assert question_extractor._clean_value("  test  ") == "test"
        assert (
            question_extractor._clean_value("test   with   spaces")
            == "test with spaces"
        )
        assert question_extractor._clean_value(123) == "123"

    def test_validate_data_success(self, question_extractor):
        """Test successful data validation."""
        valid_data = pd.DataFrame(
            {
                "question_id": ["Q.Q1", "Q.Q2"],
                "question_text": ["Question 1?", "Question 2?"],
                "category": ["Category 1", "Category 2"],
                "topic": ["Topic 1", "Topic 2"],
            }
        )

        assert question_extractor.validate_data(valid_data) is True

    def test_validate_data_empty(self, question_extractor):
        """Test validation with empty data."""
        empty_data = pd.DataFrame()
        with pytest.raises(ValueError, match="No question data found"):
            question_extractor.validate_data(empty_data)

    def test_validate_data_missing_columns(self, question_extractor):
        """Test validation with missing required columns."""
        invalid_data = pd.DataFrame(
            {
                "question_id": ["Q.Q1"]
                # Missing question_text
            }
        )
        with pytest.raises(ValueError, match="Missing required columns"):
            question_extractor.validate_data(invalid_data)

    def test_validate_data_empty_fields(self, question_extractor):
        """Test validation with empty required fields."""
        invalid_data = pd.DataFrame(
            {"question_id": ["", "Q.Q2"], "question_text": ["Question 1?", ""]}
        )
        with pytest.raises(ValueError):
            question_extractor.validate_data(invalid_data)

    def test_validate_data_duplicates(self, question_extractor):
        """Test validation with duplicate IDs."""
        invalid_data = pd.DataFrame(
            {
                "question_id": ["Q.Q1", "Q.Q1"],
                "question_text": ["Question 1?", "Question 2?"],
            }
        )
        with pytest.raises(ValueError, match="duplicate question_id"):
            question_extractor.validate_data(invalid_data)


class TestMappingExtractor:
    """Test cases for MappingExtractor class."""

    @pytest.fixture
    def mapping_extractor(self, config_manager):
        """Create a MappingExtractor instance for testing."""
        return MappingExtractor(config_manager)

    @pytest.fixture
    def sample_mapping_data(self):
        """Sample mapping data for testing."""
        return pd.DataFrame(
            {
                "Question Number": ["Q1", "Q2", "Q3"],
                "Question Text": [
                    "How is data privacy protected?",
                    "What validation processes are in place?",
                    "How is access controlled?",
                ],
                "Category": ["Privacy", "Validation", "Security"],
                "Topic": ["Data Protection", "Model Testing", "Access Management"],
                "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002", "AIR.003"],
                "AIML_CONTROL": ["AIGPC.1", "AIGPC.2", "AIGPC.3"],
            }
        )

    @pytest.fixture
    def sample_risks_data(self):
        """Sample risks data for testing."""
        return pd.DataFrame(
            {
                "risk_id": ["R.AIR.001", "R.AIR.002", "R.AIR.003"],
                "risk_title": ["Risk 1", "Risk 2", "Risk 3"],
                "risk_description": ["Description 1", "Description 2", "Description 3"],
            }
        )

    @pytest.fixture
    def sample_controls_data(self):
        """Sample controls data for testing."""
        return pd.DataFrame(
            {
                "control_id": ["C.AIGPC.1", "C.AIGPC.2", "C.AIGPC.3"],
                "control_title": ["Control 1", "Control 2", "Control 3"],
                "mapped_risks": ["AIR.001", "AIR.002", "AIR.003"],
            }
        )

    def test_mapping_extractor_initialization(self, config_manager):
        """Test MappingExtractor initialization."""
        extractor = MappingExtractor(config_manager)
        assert extractor.config_manager == config_manager

    def test_extract_question_mappings_success(
        self, mapping_extractor, temp_dir, sample_mapping_data
    ):
        """Test successful question mapping extraction."""
        excel_file = temp_dir / "test_questions.xlsx"
        sample_mapping_data.to_excel(excel_file, index=False)

        risk_mappings, control_mappings = mapping_extractor.extract_question_mappings(
            excel_file
        )

        # Verify risk mappings
        assert not risk_mappings.empty
        assert len(risk_mappings) == 3
        assert "question_id" in risk_mappings.columns
        assert "risk_id" in risk_mappings.columns
        assert "Q.SHEET1.Q1" in risk_mappings["question_id"].values
        assert "R.AIR.001" in risk_mappings["risk_id"].values

        # Verify control mappings
        assert not control_mappings.empty
        assert len(control_mappings) == 3
        assert "question_id" in control_mappings.columns
        assert "control_id" in control_mappings.columns
        assert "Q.SHEET1.Q1" in control_mappings["question_id"].values
        assert "C.AIGPC.1" in control_mappings["control_id"].values

    def test_extract_question_mappings_multiple_sheets(
        self, mapping_extractor, temp_dir
    ):
        """Test extraction from multiple sheets."""
        # Create Excel file with multiple sheets
        excel_file = temp_dir / "test_questions.xlsx"
        with pd.ExcelWriter(excel_file) as writer:
            # Sheet 1
            pd.DataFrame(
                {
                    "Question Number": ["Q1"],
                    "Question Text": ["Question 1?"],
                    "Category": ["Category 1"],
                    "Topic": ["Topic 1"],
                    "AIML_RISK_TAXONOMY": ["AIR.001"],
                    "AIML_CONTROL": ["AIGPC.1"],
                }
            ).to_excel(writer, sheet_name="Sheet1", index=False)

            # Sheet 2
            pd.DataFrame(
                {
                    "Question Number": ["Q2"],
                    "Question Text": ["Question 2?"],
                    "Category": ["Category 2"],
                    "Topic": ["Topic 2"],
                    "AIML_RISK_TAXONOMY": ["AIR.002"],
                    "AIML_CONTROL": ["AIGPC.2"],
                }
            ).to_excel(writer, sheet_name="Sheet2", index=False)

        risk_mappings, control_mappings = mapping_extractor.extract_question_mappings(
            excel_file
        )

        # Verify results - should have data from both sheets
        assert len(risk_mappings) == 2
        assert len(control_mappings) == 2
        assert "Q.SHEET1.Q1" in risk_mappings["question_id"].values
        assert "Q.SHEET2.Q2" in risk_mappings["question_id"].values

    def test_extract_question_mappings_invalid_data(self, mapping_extractor, temp_dir):
        """Test extraction with invalid mapping data."""
        # Create Excel file with invalid mappings
        data = pd.DataFrame(
            {
                "Question Number": ["Q1", "Q2", "Q3"],
                "Question Text": ["Question 1?", "Question 2?", "Question 3?"],
                "Category": ["Category 1", "Category 2", "Category 3"],
                "Topic": ["Topic 1", "Topic 2", "Topic 3"],
                "AIML_RISK_TAXONOMY": ["", "AIR.002", "TBD"],  # Empty and TBD values
                "AIML_CONTROL": ["AIGPC.1", "", "TBD"],  # Empty and TBD values
            }
        )
        excel_file = temp_dir / "test_questions.xlsx"
        data.to_excel(excel_file, index=False)

        risk_mappings, control_mappings = mapping_extractor.extract_question_mappings(
            excel_file
        )

        # Should only have valid mappings (Q2 with AIR.002 and AIGPC.1)
        assert len(risk_mappings) == 1
        assert len(control_mappings) == 1
        assert "Q.SHEET1.Q2" in risk_mappings["question_id"].values
        assert "Q.SHEET1.Q1" in control_mappings["question_id"].values

    def test_create_risk_control_mappings_success(
        self, mapping_extractor, sample_risks_data, sample_controls_data
    ):
        """Test successful risk-control mapping creation."""
        result_df = mapping_extractor.create_risk_control_mappings(
            sample_risks_data, sample_controls_data
        )

        # Verify results
        assert not result_df.empty
        assert len(result_df) == 3
        assert "risk_id" in result_df.columns
        assert "control_id" in result_df.columns
        assert "R.AIR.001" in result_df["risk_id"].values
        assert "C.AIGPC.1" in result_df["control_id"].values

    def test_create_risk_control_mappings_no_controls(
        self, mapping_extractor, sample_risks_data
    ):
        """Test risk-control mapping creation with no controls data."""
        empty_controls = pd.DataFrame()
        result_df = mapping_extractor.create_risk_control_mappings(
            sample_risks_data, empty_controls
        )

        assert result_df.empty

    def test_create_risk_control_mappings_no_mapped_risks_column(
        self, mapping_extractor, sample_risks_data
    ):
        """Test risk-control mapping creation with no mapped_risks column."""
        controls_without_mapping = pd.DataFrame(
            {
                "control_id": ["C.AIGPC.1"],
                "control_title": ["Control 1"],
                # Missing mapped_risks column
            }
        )
        result_df = mapping_extractor.create_risk_control_mappings(
            sample_risks_data, controls_without_mapping
        )

        assert result_df.empty

    def test_create_risk_control_mappings_multiple_risks(
        self, mapping_extractor, sample_risks_data
    ):
        """Test risk-control mapping creation with multiple risks per control."""
        controls_with_multiple_risks = pd.DataFrame(
            {
                "control_id": ["C.AIGPC.1"],
                "control_title": ["Control 1"],
                "mapped_risks": ["AIR.001, AIR.002"],  # Multiple risks
            }
        )
        result_df = mapping_extractor.create_risk_control_mappings(
            sample_risks_data, controls_with_multiple_risks
        )

        # Should create two mappings for the single control
        assert len(result_df) == 2
        assert all(result_df["control_id"] == "C.AIGPC.1")
        assert "R.AIR.001" in result_df["risk_id"].values
        assert "R.AIR.002" in result_df["risk_id"].values

    def test_create_risk_control_mappings_nonexistent_risk(
        self, mapping_extractor, sample_risks_data
    ):
        """Test risk-control mapping creation with non-existent risk."""
        controls_with_nonexistent_risk = pd.DataFrame(
            {
                "control_id": ["C.AIGPC.1"],
                "control_title": ["Control 1"],
                "mapped_risks": ["AIR.999"],  # Non-existent risk
            }
        )

        # Should skip the mapping and log a warning (current behavior)
        result_df = mapping_extractor.create_risk_control_mappings(
            sample_risks_data, controls_with_nonexistent_risk
        )

        # Current implementation skips non-existent risks
        assert len(result_df) == 0

    def test_clean_value(self, mapping_extractor):
        """Test value cleaning functionality."""
        # Test various input types
        assert mapping_extractor._clean_value(None) == ""
        assert mapping_extractor._clean_value("") == ""
        assert mapping_extractor._clean_value("  test  ") == "test"
        assert (
            mapping_extractor._clean_value("test   with   spaces") == "test with spaces"
        )
        assert mapping_extractor._clean_value(123) == "123"

    def test_validate_mappings_risk_control_success(self, mapping_extractor):
        """Test successful risk-control mapping validation."""
        valid_mappings = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001", "R.AIR.002"],
                "control_id": ["C.AIGPC.1", "C.AIGPC.2"],
            }
        )

        assert (
            mapping_extractor.validate_mappings(valid_mappings, "risk_control") is True
        )

    def test_validate_mappings_question_risk_success(self, mapping_extractor):
        """Test successful question-risk mapping validation."""
        valid_mappings = pd.DataFrame(
            {"question_id": ["Q.Q1", "Q.Q2"], "risk_id": ["R.AIR.001", "R.AIR.002"]}
        )

        assert (
            mapping_extractor.validate_mappings(valid_mappings, "question_risk") is True
        )

    def test_validate_mappings_question_control_success(self, mapping_extractor):
        """Test successful question-control mapping validation."""
        valid_mappings = pd.DataFrame(
            {"question_id": ["Q.Q1", "Q.Q2"], "control_id": ["C.AIGPC.1", "C.AIGPC.2"]}
        )

        assert (
            mapping_extractor.validate_mappings(valid_mappings, "question_control")
            is True
        )

    def test_validate_mappings_empty(self, mapping_extractor):
        """Test validation with empty mappings."""
        empty_mappings = pd.DataFrame()
        assert (
            mapping_extractor.validate_mappings(empty_mappings, "risk_control") is True
        )

    def test_validate_mappings_unknown_type(self, mapping_extractor):
        """Test validation with unknown mapping type."""
        mappings = pd.DataFrame({"test": ["value"]})
        with pytest.raises(ValueError, match="Unknown mapping type"):
            mapping_extractor.validate_mappings(mappings, "unknown_type")

    def test_validate_mappings_missing_columns(self, mapping_extractor):
        """Test validation with missing required columns."""
        invalid_mappings = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001"]
                # Missing control_id
            }
        )
        with pytest.raises(ValueError, match="Missing required columns"):
            mapping_extractor.validate_mappings(invalid_mappings, "risk_control")

    def test_validate_mappings_empty_fields(self, mapping_extractor):
        """Test validation with empty required fields."""
        invalid_mappings = pd.DataFrame(
            {"risk_id": ["", "R.AIR.002"], "control_id": ["C.AIGPC.1", ""]}
        )
        with pytest.raises(ValueError):
            mapping_extractor.validate_mappings(invalid_mappings, "risk_control")

    def test_validate_mappings_duplicates(self, mapping_extractor):
        """Test validation with duplicate mappings."""
        invalid_mappings = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001", "R.AIR.001"],
                "control_id": ["C.AIGPC.1", "C.AIGPC.1"],
            }
        )
        with pytest.raises(ValueError, match="duplicate"):
            mapping_extractor.validate_mappings(invalid_mappings, "risk_control")


class TestExtractorIntegration:
    """Integration tests for extractor classes working together."""

    def test_full_extraction_workflow(self, temp_dir, config_manager):
        """Test complete extraction workflow with all extractors."""
        # Create sample data files
        risks_data = pd.DataFrame(
            {
                "ID": ["AIR.001", "AIR.002"],
                "Risk": ["Risk 1", "Risk 2"],
                "Risk Description": ["Description 1", "Description 2"],
            }
        )

        controls_data = pd.DataFrame(
            {
                "Code": ["AIGPC.1", "AIGPC.2"],
                "Purpose": ["Control 1", "Control 2"],
                "Mapped Risks": ["AIR.001", "AIR.002"],
            }
        )

        questions_data = pd.DataFrame(
            {
                "Question Number": ["Q1", "Q2"],
                "Question Text": ["Question 1?", "Question 2?"],
                "Category": ["Category 1", "Category 2"],
                "Topic": ["Topic 1", "Topic 2"],
                "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002"],
                "AIML_CONTROL": ["AIGPC.1", "AIGPC.2"],
            }
        )

        # Create Excel files
        risks_file = temp_dir / "test_risks.xlsx"
        controls_file = temp_dir / "test_controls.xlsx"
        questions_file = temp_dir / "test_questions.xlsx"

        risks_data.to_excel(risks_file, index=False)
        # Create controls file with "Domains" sheet name to match expected structure
        with pd.ExcelWriter(controls_file) as writer:
            controls_data.to_excel(writer, sheet_name="Domains", index=False)
        questions_data.to_excel(questions_file, index=False)

        # Extract data using all extractors
        risk_extractor = RiskExtractor(config_manager)
        control_extractor = ControlExtractor(config_manager)
        question_extractor = QuestionExtractor(config_manager)
        mapping_extractor = MappingExtractor(config_manager)

        risks_df = risk_extractor.extract(risks_file)
        controls_df = control_extractor.extract(controls_file)
        questions_df = question_extractor.extract(questions_file)
        question_risk_mappings, question_control_mappings = (
            mapping_extractor.extract_question_mappings(questions_file)
        )
        risk_control_mappings = mapping_extractor.create_risk_control_mappings(
            risks_df, controls_df
        )

        # Verify all extractions succeeded
        assert not risks_df.empty
        assert not controls_df.empty
        assert not questions_df.empty
        assert not question_risk_mappings.empty
        assert not question_control_mappings.empty
        assert not risk_control_mappings.empty

        # Verify data consistency
        assert len(risks_df) == 2
        assert len(controls_df) == 2
        assert len(questions_df) == 2
        assert len(question_risk_mappings) == 2
        assert len(question_control_mappings) == 2
        assert len(risk_control_mappings) == 2

        # Verify ID formatting consistency
        assert all(risks_df["risk_id"].str.startswith("R."))
        assert all(controls_df["control_id"].str.startswith("C."))
        assert all(questions_df["question_id"].str.startswith("Q."))

        # Verify mappings reference correct IDs
        assert all(question_risk_mappings["risk_id"].str.startswith("R."))
        assert all(question_control_mappings["control_id"].str.startswith("C."))
        assert all(risk_control_mappings["risk_id"].str.startswith("R."))
        assert all(risk_control_mappings["control_id"].str.startswith("C."))
