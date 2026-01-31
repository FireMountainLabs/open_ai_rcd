import pandas as pd

"""
Test for complete data extraction across all sheets.

This test would have caught the bug where only some sheets were being processed
due to question ID collisions, resulting in missing managing roles.
"""


from config.config_manager import ConfigManager
from data_processor import DataProcessor


class TestCompleteExtraction:
    """Test cases for complete data extraction."""

    def test_all_question_sheets_processed(self, temp_dir, sample_config):
        """Test that all sheets in the questions Excel file are processed."""
        # Create Excel file with multiple sheets representing different managing roles
        excel_file = temp_dir / "test_questions.xlsx"

        managing_roles = [
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

        with pd.ExcelWriter(excel_file) as writer:
            for i, role in enumerate(managing_roles):
                # Each sheet has different number of questions to simulate real data
                num_questions = 25 + (i % 5)  # 25-29 questions per sheet
                questions = []
                for j in range(num_questions):
                    questions.append(
                        {
                            "Question Number": f"{j + 1}.1",
                            "Question Text": f"Question {j + 1}.1 for {role}?",
                            "Category": f"Category {j + 1}",
                            "Topic": f"Topic {j + 1}",
                            "AIML_RISK_TAXONOMY": f"AIR.{j + 1:03d}",
                            "AIML_CONTROL": f"AIGPC.{j + 1}",
                        }
                    )

                pd.DataFrame(questions).to_excel(writer, sheet_name=role, index=False)

        # Create required risks and controls files
        risks_file = temp_dir / "test_risks.xlsx"
        risks_data = []
        for i in range(1, 11):  # Create 10 risks
            risks_data.append(
                {
                    "ID": f"AIR.{i:03d}",
                    "Risk": f"Test Risk {i}",
                    "Risk Description": f"Description for test risk {i}",
                }
            )
        pd.DataFrame(risks_data).to_excel(risks_file, index=False)

        controls_file = temp_dir / "test_controls.xlsx"
        controls_data = []
        for i in range(1, 11):  # Create 10 controls
            controls_data.append(
                {
                    "Code": f"AIGPC.{i}",
                    "Purpose": f"Test Control {i}",
                    "Description": f"Description for test control {i}",
                    "Mapped Risks": f"AIR.{i:03d}",
                }
            )
        pd.DataFrame(controls_data).to_excel(controls_file, index=False)

        # Process the data
        processor = DataProcessor(
            data_dir=temp_dir,
            output_dir=temp_dir / "output",
            config_manager=ConfigManager(sample_config),
        )

        # Override the questions file path for testing
        processor.data_dir = temp_dir
        processor.extract_data()

        # Verify all managing roles were processed
        assert processor.questions_df is not None
        assert len(processor.questions_df) > 0

        extracted_roles = set(processor.questions_df["managing_role"].unique())
        expected_roles = set(managing_roles)

        assert (
            extracted_roles == expected_roles
        ), f"Expected {expected_roles}, got {extracted_roles}"

        # Verify each role has questions
        for role in managing_roles:
            role_questions = processor.questions_df[
                processor.questions_df["managing_role"] == role
            ]
            assert len(role_questions) > 0, f"Role {role} should have questions"

            # Verify question IDs are unique and include role acronym
            for _, question in role_questions.iterrows():
                from utils.service_acronyms import normalize_service_name_for_id

                expected_acronym = normalize_service_name_for_id(role)
                assert question["question_id"].startswith(
                    f"Q.{expected_acronym}"
                ), f"Question ID {question['question_id']} should start with Q.{expected_acronym}"

    def test_question_extraction_counts_match_expected(self, temp_dir, sample_config):
        """Test that question extraction counts match expected totals."""
        # Create Excel file with known question counts
        excel_file = temp_dir / "test_questions.xlsx"

        expected_counts = {
            "Operational Assurance": 28,
            "Cyber Risk Architecture": 32,
            "CREM Platform & Automation": 34,
            "IAM Engineering": 25,
            "Security Threat Testing": 28,
            "Technical Security Solutions": 27,
            "Risk Engineering": 26,
            "CREM Incident Response": 47,
            "Security Risk Management": 24,
            "IAM Operations": 28,
        }

        with pd.ExcelWriter(excel_file) as writer:
            for role, count in expected_counts.items():
                questions = []
                for i in range(count):
                    questions.append(
                        {
                            "Question Number": f"{i + 1}.1",
                            "Question Text": f"Question {i + 1}.1 for {role}?",
                            "Category": f"Category {i + 1}",
                            "Topic": f"Topic {i + 1}",
                            "AIML_RISK_TAXONOMY": f"AIR.{i + 1:03d}",
                            "AIML_CONTROL": f"AIGPC.{i + 1}",
                        }
                    )

                pd.DataFrame(questions).to_excel(writer, sheet_name=role, index=False)

        # Create required risks and controls files
        risks_file = temp_dir / "test_risks.xlsx"
        risks_data = []
        for i in range(1, 11):  # Create 10 risks
            risks_data.append(
                {
                    "ID": f"AIR.{i:03d}",
                    "Risk": f"Test Risk {i}",
                    "Risk Description": f"Description for test risk {i}",
                }
            )
        pd.DataFrame(risks_data).to_excel(risks_file, index=False)

        controls_file = temp_dir / "test_controls.xlsx"
        controls_data = []
        for i in range(1, 11):  # Create 10 controls
            controls_data.append(
                {
                    "Code": f"AIGPC.{i}",
                    "Purpose": f"Test Control {i}",
                    "Description": f"Description for test control {i}",
                    "Mapped Risks": f"AIR.{i:03d}",
                }
            )
        pd.DataFrame(controls_data).to_excel(controls_file, index=False)

        # Process the data
        processor = DataProcessor(
            data_dir=temp_dir,
            output_dir=temp_dir / "output",
            config_manager=ConfigManager(sample_config),
        )

        processor.extract_data()

        # Verify counts match expected
        assert processor.questions_df is not None

        total_expected = sum(expected_counts.values())
        total_extracted = len(processor.questions_df)

        assert (
            total_extracted == total_expected
        ), f"Expected {total_expected} questions, got {total_extracted}"

        # Verify each role has the expected count
        for role, expected_count in expected_counts.items():
            role_questions = processor.questions_df[
                processor.questions_df["managing_role"] == role
            ]
            actual_count = len(role_questions)
            assert (
                actual_count == expected_count
            ), f"Role {role}: expected {expected_count}, got {actual_count}"

    def test_question_mappings_created_for_all_questions(self, temp_dir, sample_config):
        """Test that mappings are created for all questions."""
        # Create Excel file with questions and mappings
        excel_file = temp_dir / "test_questions.xlsx"

        managing_roles = [
            "Operational Assurance",
            "IAM Engineering",
            "Security Threat Testing",
        ]

        with pd.ExcelWriter(excel_file) as writer:
            for role in managing_roles:
                questions = []
                for i in range(5):  # 5 questions per role
                    questions.append(
                        {
                            "Question Number": f"{i + 1}.1",
                            "Question Text": f"Question {i + 1}.1 for {role}?",
                            "Category": f"Category {i + 1}",
                            "Topic": f"Topic {i + 1}",
                            "AIML_RISK_TAXONOMY": f"AIR.{i + 1:03d}",
                            "AIML_CONTROL": f"AIGPC.{i + 1}",
                        }
                    )

                pd.DataFrame(questions).to_excel(writer, sheet_name=role, index=False)

        # Create corresponding risks and controls data
        risks_file = temp_dir / "test_risks.xlsx"
        risks_data = []
        for i in range(5):
            risks_data.append(
                {
                    "ID": f"AIR.{i + 1:03d}",
                    "Risk": f"Risk {i + 1}",
                    "Risk Description": f"Description {i + 1}",
                }
            )
        pd.DataFrame(risks_data).to_excel(risks_file, index=False)

        controls_file = temp_dir / "test_controls.xlsx"
        controls_data = []
        for i in range(5):
            controls_data.append(
                {
                    "Code": f"AIGPC.{i + 1}",
                    "Purpose": f"Control {i + 1}",
                    "Description": f"Control Description {i + 1}",
                    "Mapped Risks": f"AIR.{i + 1:03d}",
                }
            )
        pd.DataFrame(controls_data).to_excel(controls_file, index=False)

        # Process the data
        processor = DataProcessor(
            data_dir=temp_dir,
            output_dir=temp_dir / "output",
            config_manager=ConfigManager(sample_config),
        )

        processor.extract_data()

        # Verify mappings were created
        assert processor.question_risk_mapping_df is not None
        assert processor.question_control_mapping_df is not None

        # Should have mappings for all questions (3 roles * 5 questions = 15)
        expected_mappings = 15
        assert len(processor.question_risk_mapping_df) == expected_mappings
        assert len(processor.question_control_mapping_df) == expected_mappings

        # Verify all question IDs in mappings are unique
        risk_question_ids = set(
            processor.question_risk_mapping_df["question_id"].unique()
        )
        control_question_ids = set(
            processor.question_control_mapping_df["question_id"].unique()
        )

        assert len(risk_question_ids) == expected_mappings
        assert len(control_question_ids) == expected_mappings

        # Verify mappings include all managing roles (using acronyms)
        from utils.service_acronyms import normalize_service_name_for_id

        risk_roles = set()
        control_roles = set()

        for question_id in risk_question_ids:
            acronym = question_id.split(".")[1]
            risk_roles.add(acronym)

        for question_id in control_question_ids:
            acronym = question_id.split(".")[1]
            control_roles.add(acronym)

        expected_acronyms = {
            normalize_service_name_for_id(role) for role in managing_roles
        }
        assert risk_roles == expected_acronyms
        assert control_roles == expected_acronyms

    def test_extraction_with_mixed_valid_invalid_sheets(self, temp_dir, sample_config):
        """Test extraction with mix of valid and invalid sheets."""
        excel_file = temp_dir / "test_questions.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Valid sheet
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "1.2"],
                    "Question Text": ["Valid question 1?", "Valid question 2?"],
                    "Category": ["Test", "Test"],
                    "Topic": ["Test", "Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002"],
                    "AIML_CONTROL": ["AIGPC.1", "AIGPC.2"],
                }
            ).to_excel(writer, sheet_name="Valid Sheet", index=False)

            # Empty sheet
            pd.DataFrame().to_excel(writer, sheet_name="Empty Sheet", index=False)

            # Sheet with missing columns
            pd.DataFrame({"Wrong Column": ["Value 1", "Value 2"]}).to_excel(
                writer, sheet_name="Wrong Columns Sheet", index=False
            )

            # Another valid sheet
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "1.2"],
                    "Question Text": [
                        "Another valid question 1?",
                        "Another valid question 2?",
                    ],
                    "Category": ["Test", "Test"],
                    "Topic": ["Test", "Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.003", "AIR.004"],
                    "AIML_CONTROL": ["AIGPC.3", "AIGPC.4"],
                }
            ).to_excel(writer, sheet_name="Another Valid Sheet", index=False)

        # Create required risks and controls files
        risks_file = temp_dir / "test_risks.xlsx"
        risks_data = []
        for i in range(1, 11):  # Create 10 risks
            risks_data.append(
                {
                    "ID": f"AIR.{i:03d}",
                    "Risk": f"Test Risk {i}",
                    "Risk Description": f"Description for test risk {i}",
                }
            )
        pd.DataFrame(risks_data).to_excel(risks_file, index=False)

        controls_file = temp_dir / "test_controls.xlsx"
        controls_data = []
        for i in range(1, 11):  # Create 10 controls
            controls_data.append(
                {
                    "Code": f"AIGPC.{i}",
                    "Purpose": f"Test Control {i}",
                    "Description": f"Description for test control {i}",
                    "Mapped Risks": f"AIR.{i:03d}",
                }
            )
        pd.DataFrame(controls_data).to_excel(controls_file, index=False)

        # Process the data
        processor = DataProcessor(
            data_dir=temp_dir,
            output_dir=temp_dir / "output",
            config_manager=ConfigManager(sample_config),
        )

        processor.extract_data()

        # Should only process valid sheets
        assert processor.questions_df is not None
        assert len(processor.questions_df) == 4  # 2 from each valid sheet

        # Verify only valid sheets are represented
        managing_roles = set(processor.questions_df["managing_role"].unique())
        expected_roles = {"Valid Sheet", "Another Valid Sheet"}
        assert managing_roles == expected_roles
