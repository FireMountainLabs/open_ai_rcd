import pandas as pd

"""
Integration tests for the complete data processing workflow with acronyms.

Tests that the entire data processing pipeline correctly handles service acronyms
from extraction through to database population.
"""

from pathlib import Path

import pytest

from config.config_manager import ConfigManager
from extractors.mapping_extractor import MappingExtractor
from extractors.question_extractor import QuestionExtractor
from utils.service_acronyms import normalize_service_name_for_id


class TestIntegrationAcronyms:
    """Integration tests for acronym functionality."""

    @pytest.fixture
    def config_manager(self):
        """Create a ConfigManager instance for testing."""
        config_path = Path(__file__).parent.parent / "config" / "default_config.yaml"
        return ConfigManager(config_path)

    def test_complete_workflow_with_acronyms(self, config_manager, temp_dir):
        """Test complete data processing workflow with acronyms."""
        # Create test Excel files
        questions_file = temp_dir / "test_questions_acronyms.xlsx"

        # Create questions file with multiple services
        with pd.ExcelWriter(questions_file) as writer:
            services_data = [
                ("Cyber Risk Architecture", "CRA", ["6.1", "6.2"]),
                ("Operational Assurance", "OA", ["1.1", "1.2"]),
                ("CREM Platform & Automation", "CPA", ["2.1", "2.2"]),
            ]

            for service_name, expected_acronym, question_nums in services_data:
                pd.DataFrame(
                    {
                        "Question Number": question_nums,
                        "Question Text": [
                            f"{expected_acronym} Question {num}?"
                            for num in question_nums
                        ],
                        "Category": ["Test"] * len(question_nums),
                        "Topic": ["Test"] * len(question_nums),
                        "AIML_RISK_TAXONOMY": ["AIR.001"] * len(question_nums),
                        "AIML_CONTROL": ["AIGPC.1"] * len(question_nums),
                    }
                ).to_excel(writer, sheet_name=service_name, index=False)

        # Initialize extractors
        question_extractor = QuestionExtractor(config_manager)
        mapping_extractor = MappingExtractor(config_manager)

        # Extract questions
        questions_df = question_extractor.extract(questions_file)

        # Verify questions were extracted with acronyms
        assert len(questions_df) == 6  # 2 questions per service

        question_ids = questions_df["question_id"].tolist()

        # Verify acronyms are used
        cra_ids = [qid for qid in question_ids if qid.startswith("Q.CRA.")]
        oa_ids = [qid for qid in question_ids if qid.startswith("Q.OA.")]
        cpa_ids = [qid for qid in question_ids if qid.startswith("Q.CPA.")]

        assert len(cra_ids) == 2, f"Expected 2 CRA IDs, got {cra_ids}"
        assert len(oa_ids) == 2, f"Expected 2 OA IDs, got {oa_ids}"
        assert len(cpa_ids) == 2, f"Expected 2 CPA IDs, got {cpa_ids}"

        # Verify specific IDs
        expected_ids = [
            "Q.CRA.6.1",
            "Q.CRA.6.2",
            "Q.OA.1.1",
            "Q.OA.1.2",
            "Q.CPA.2.1",
            "Q.CPA.2.2",
        ]
        for expected_id in expected_ids:
            assert expected_id in question_ids, f"Expected {expected_id} not found"

        # Create sample risks and controls data
        risks_df = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001"],
                "risk_title": ["Risk 1"],
                "risk_description": ["Desc 1"],
            }
        )

        controls_df = pd.DataFrame(
            {
                "control_id": ["C.AIGPC.1"],
                "control_title": ["Control 1"],
                "control_description": ["Desc 1"],
            }
        )

        # Extract mappings
        question_risk_mappings, question_control_mappings = (
            mapping_extractor.extract_question_mappings(
                questions_file, risks_df, controls_df
            )
        )

        # Verify mappings were created with acronyms
        assert len(question_risk_mappings) == 6
        assert len(question_control_mappings) == 6

        mapping_question_ids = question_risk_mappings["question_id"].tolist()
        control_mapping_question_ids = question_control_mappings["question_id"].tolist()

        # Verify mapping question IDs match question IDs
        for expected_id in expected_ids:
            assert (
                expected_id in mapping_question_ids
            ), f"Risk mapping missing for {expected_id}"
            assert (
                expected_id in control_mapping_question_ids
            ), f"Control mapping missing for {expected_id}"

    def test_database_population_with_acronyms(self, config_manager, temp_dir):
        """Test database population with acronym-based question IDs."""
        # Create test data
        questions_file = temp_dir / "test_questions_db.xlsx"

        with pd.ExcelWriter(questions_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "1.2"],
                    "Question Text": ["CRA Question 1.1?", "CRA Question 1.2?"],
                    "Category": ["Test", "Test"],
                    "Topic": ["Test", "Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002"],
                    "AIML_CONTROL": ["AIGPC.1", "AIGPC.2"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        # Initialize extractor
        question_extractor = QuestionExtractor(config_manager)

        # Extract questions
        questions_df = question_extractor.extract(questions_file)

        # Verify questions were extracted with CRA acronym
        assert len(questions_df) == 2

        question_ids = questions_df["question_id"].tolist()
        assert "Q.CRA.1.1" in question_ids
        assert "Q.CRA.1.2" in question_ids

        # Verify managing role is preserved
        managing_roles = questions_df["managing_role"].tolist()
        assert all(role == "Cyber Risk Architecture" for role in managing_roles)

    def test_acronym_consistency_across_extractors(self, config_manager, temp_dir):
        """Test that all extractors use consistent acronyms."""
        # Create test data
        questions_file = temp_dir / "test_consistency.xlsx"

        with pd.ExcelWriter(questions_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1"],
                    "Question Text": ["Test Question 1.1?"],
                    "Category": ["Test"],
                    "Topic": ["Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.001"],
                    "AIML_CONTROL": ["AIGPC.1"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        # Initialize extractors
        question_extractor = QuestionExtractor(config_manager)
        mapping_extractor = MappingExtractor(config_manager)

        # Extract questions
        questions_df = question_extractor.extract(questions_file)

        # Verify question extractor uses CRA acronym
        assert len(questions_df) == 1
        question_id = questions_df.iloc[0]["question_id"]
        assert (
            question_id == "Q.CRA.1.1"
        ), f"Question extractor should use CRA acronym, got {question_id}"

        # Create sample data for mapping extractor
        risks_df = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001"],
                "risk_title": ["Risk 1"],
                "risk_description": ["Desc 1"],
            }
        )

        # Extract mappings
        question_risk_mappings, _ = mapping_extractor.extract_question_mappings(
            questions_file, risks_df, None
        )

        # Verify mapping extractor uses same CRA acronym
        assert len(question_risk_mappings) == 1
        mapping_question_id = question_risk_mappings.iloc[0]["question_id"]
        assert (
            mapping_question_id == "Q.CRA.1.1"
        ), f"Mapping extractor should use CRA acronym, got {mapping_question_id}"

        # Verify IDs match
        assert (
            question_id == mapping_question_id
        ), "Question IDs should match between extractors"

    def test_acronym_handling_with_special_characters(self, config_manager, temp_dir):
        """Test acronym handling with special characters in service names."""
        # Create test data with service containing ampersand
        questions_file = temp_dir / "test_special_chars.xlsx"

        with pd.ExcelWriter(questions_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1"],
                    "Question Text": ["CPA Question 1.1?"],
                    "Category": ["Test"],
                    "Topic": ["Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.001"],
                    "AIML_CONTROL": ["AIGPC.1"],
                }
            ).to_excel(writer, sheet_name="CREM Platform & Automation", index=False)

        # Initialize extractor
        question_extractor = QuestionExtractor(config_manager)

        # Extract questions
        questions_df = question_extractor.extract(questions_file)

        # Verify CPA acronym is used
        assert len(questions_df) == 1
        question_id = questions_df.iloc[0]["question_id"]
        assert question_id == "Q.CPA.1.1", f"Expected Q.CPA.1.1, got {question_id}"

    def test_acronym_validation_in_workflow(self, config_manager, temp_dir):
        """Test that acronym validation works in the complete workflow."""
        # Create test data with all services
        questions_file = temp_dir / "test_all_services.xlsx"

        services = [
            "Operational Assurance",
            "Cyber Risk Architecture",
            "CREM Platform & Automation",
            "IAM Engineering",
            "Security Threat Testing",
            "Technical Security Solutions",
            "Risk Engineering",
            "CREM Incident Response",
            "Security Risk Management",
            "IAM Operations",
        ]

        with pd.ExcelWriter(questions_file) as writer:
            for i, service in enumerate(services):
                pd.DataFrame(
                    {
                        "Question Number": [f"{i + 1}.1"],
                        "Question Text": [f"Question for {service}?"],
                        "Category": ["Test"],
                        "Topic": ["Test"],
                        "AIML_RISK_TAXONOMY": ["AIR.001"],
                        "AIML_CONTROL": ["AIGPC.1"],
                    }
                ).to_excel(writer, sheet_name=service, index=False)

        # Initialize extractor
        question_extractor = QuestionExtractor(config_manager)

        # Extract questions
        questions_df = question_extractor.extract(questions_file)

        # Verify all services are processed with correct acronyms
        assert len(questions_df) == len(services)

        # Check that each service uses its correct acronym
        for service in services:
            expected_acronym = normalize_service_name_for_id(service)
            service_questions = questions_df[questions_df["managing_role"] == service]

            assert len(service_questions) == 1, f"Expected 1 question for {service}"

            question_id = service_questions.iloc[0]["question_id"]
            assert question_id.startswith(
                f"Q.{expected_acronym}."
            ), f"Question ID {question_id} should start with Q.{expected_acronym}."

    def test_acronym_performance_with_large_dataset(self, config_manager, temp_dir):
        """Test acronym performance with a larger dataset."""
        # Create test data with multiple questions per service
        questions_file = temp_dir / "test_large_dataset.xlsx"

        with pd.ExcelWriter(questions_file) as writer:
            # Create 10 questions per service for 3 services
            services_data = [
                ("Cyber Risk Architecture", "CRA", 10),
                ("Operational Assurance", "OA", 10),
                ("CREM Platform & Automation", "CPA", 10),
            ]

            for service_name, expected_acronym, num_questions in services_data:
                question_nums = [f"{i + 1}.1" for i in range(num_questions)]
                pd.DataFrame(
                    {
                        "Question Number": question_nums,
                        "Question Text": [
                            f"{expected_acronym} Question {num}?"
                            for num in question_nums
                        ],
                        "Category": ["Test"] * num_questions,
                        "Topic": ["Test"] * num_questions,
                        "AIML_RISK_TAXONOMY": ["AIR.001"] * num_questions,
                        "AIML_CONTROL": ["AIGPC.1"] * num_questions,
                    }
                ).to_excel(writer, sheet_name=service_name, index=False)

        # Initialize extractor
        question_extractor = QuestionExtractor(config_manager)

        # Extract questions
        questions_df = question_extractor.extract(questions_file)

        # Verify all questions were processed with correct acronyms
        assert len(questions_df) == 30  # 10 questions per service

        # Verify acronym distribution
        question_ids = questions_df["question_id"].tolist()

        cra_ids = [qid for qid in question_ids if qid.startswith("Q.CRA.")]
        oa_ids = [qid for qid in question_ids if qid.startswith("Q.OA.")]
        cpa_ids = [qid for qid in question_ids if qid.startswith("Q.CPA.")]

        assert len(cra_ids) == 10, f"Expected 10 CRA IDs, got {len(cra_ids)}"
        assert len(oa_ids) == 10, f"Expected 10 OA IDs, got {len(oa_ids)}"
        assert len(cpa_ids) == 10, f"Expected 10 CPA IDs, got {len(cpa_ids)}"
