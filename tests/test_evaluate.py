"""Unit tests for ticket evaluation system."""

import csv
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from src.models import TicketEvaluated
from src.config import MODEL_CONFIGS, get_available_modes
from src.csv_handler import read_tickets, write_results
from src.parser import (
    clamp_score,
    parse_response,
    parse_response_json,
    parse_response_regex,
)
from src.clients import create_client, GroqClient, GrokClient, OpenAIClient


# =============================================================================
# Test: Configuration
# =============================================================================


class TestConfig:
    """Tests for configuration."""

    def test_model_configs_exist(self):
        """Test that all expected modes are configured."""
        expected_modes = [
            "groq-fast",
            "groq-balanced",
            "grok-deep",
            "openai-fast",
            "openai-balanced",
            "openai-deep",
        ]
        for mode in expected_modes:
            assert mode in MODEL_CONFIGS

    def test_get_available_modes(self):
        """Test get_available_modes returns all modes."""
        modes = get_available_modes()
        assert "groq-fast" in modes
        assert "openai-balanced" in modes


# =============================================================================
# Test: CSV Reading
# =============================================================================


class TestReadTickets:
    """Tests for read_tickets function."""

    def test_read_valid_csv(self, tmp_path):
        """Test reading a valid CSV file."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text('ticket,reply\n"Hello","Hi there"\n"Help me","Sure thing"')

        tickets = read_tickets(str(csv_file))

        assert len(tickets) == 2
        assert tickets[0].ticket == "Hello"
        assert tickets[0].reply == "Hi there"
        assert tickets[1].ticket == "Help me"
        assert tickets[1].reply == "Sure thing"

    def test_read_csv_missing_columns(self, tmp_path):
        """Test error when required columns are missing."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("ticket,wrong_column\nHello,World")

        with pytest.raises(ValueError, match="Missing required columns"):
            read_tickets(str(csv_file))

    def test_read_empty_csv(self, tmp_path):
        """Test error when CSV has no data rows."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("ticket,reply\n")

        with pytest.raises(ValueError, match="No valid tickets found"):
            read_tickets(str(csv_file))

    def test_read_csv_skips_empty_rows(self, tmp_path):
        """Test that empty rows are skipped with warning."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text('ticket,reply\n"Hello","Hi"\n"",""\n"Bye","Goodbye"')

        tickets = read_tickets(str(csv_file))

        assert len(tickets) == 2
        assert tickets[0].ticket == "Hello"
        assert tickets[1].ticket == "Bye"

    def test_read_csv_file_not_found(self):
        """Test error when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            read_tickets("nonexistent.csv")


# =============================================================================
# Test: CSV Writing
# =============================================================================


class TestWriteResults:
    """Tests for write_results function."""

    def test_write_results(self, tmp_path):
        """Test writing evaluation results to CSV."""
        output_file = tmp_path / "output.csv"
        results = [
            TicketEvaluated(
                ticket="Test ticket",
                reply="Test reply",
                content_score=4,
                content_explanation="Good content",
                format_score=5,
                format_explanation="Excellent format",
            )
        ]

        write_results(str(output_file), results)

        # Read and verify
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["ticket"] == "Test ticket"
        assert rows[0]["reply"] == "Test reply"
        assert rows[0]["content_score"] == "4"
        assert rows[0]["content_explanation"] == "Good content"
        assert rows[0]["format_score"] == "5"
        assert rows[0]["format_explanation"] == "Excellent format"

    def test_write_results_correct_columns(self, tmp_path):
        """Test that output has correct column order."""
        output_file = tmp_path / "output.csv"
        results = [
            TicketEvaluated(
                ticket="T",
                reply="R",
                content_score=3,
                content_explanation="CE",
                format_score=3,
                format_explanation="FE",
            )
        ]

        write_results(str(output_file), results)

        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == [
                "ticket",
                "reply",
                "content_score",
                "content_explanation",
                "format_score",
                "format_explanation",
            ]


# =============================================================================
# Test: Response Parsing
# =============================================================================


class TestParseResponse:
    """Tests for response parsing functions."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        response = json.dumps(
            {
                "content_score": 4,
                "content_explanation": "Good response",
                "format_score": 5,
                "format_explanation": "Well formatted",
            }
        )

        result = parse_response_json(response)

        assert result.content_score == 4
        assert result.content_explanation == "Good response"
        assert result.format_score == 5
        assert result.format_explanation == "Well formatted"

    def test_parse_json_clamps_high_score(self):
        """Test that scores above 5 are clamped."""
        response = json.dumps(
            {
                "content_score": 10,
                "content_explanation": "Test",
                "format_score": 5,
                "format_explanation": "Test",
            }
        )

        result = parse_response_json(response)

        assert result.content_score == 5

    def test_parse_json_clamps_low_score(self):
        """Test that scores below 1 are clamped."""
        response = json.dumps(
            {
                "content_score": 0,
                "content_explanation": "Test",
                "format_score": -1,
                "format_explanation": "Test",
            }
        )

        result = parse_response_json(response)

        assert result.content_score == 1
        assert result.format_score == 1

    def test_parse_regex_fallback(self):
        """Test regex fallback for malformed JSON."""
        # Malformed JSON-like response
        response = 'content_score: 4, content_explanation: "Good", format_score: 3, format_explanation: "OK"'

        result = parse_response_regex(response)

        assert result.content_score == 4
        assert result.format_score == 3

    def test_parse_response_uses_fallback(self):
        """Test that parse_response falls back to regex on invalid JSON."""
        response = "not valid json but content_score: 5"

        result = parse_response(response)

        assert result.content_score == 5

    def test_clamp_score_in_range(self):
        """Test clamp_score with value in range."""
        assert clamp_score(3) == 3

    def test_clamp_score_below_range(self):
        """Test clamp_score with value below range."""
        assert clamp_score(0) == 1
        assert clamp_score(-5) == 1

    def test_clamp_score_above_range(self):
        """Test clamp_score with value above range."""
        assert clamp_score(6) == 5
        assert clamp_score(100) == 5


# =============================================================================
# Test: LLM Clients
# =============================================================================


class TestCreateClient:
    """Tests for client creation."""

    @patch.dict(os.environ, {"GROQ_API_KEY": "test_key"})
    def test_create_groq_client_fast(self):
        """Test creating Groq client for fast mode."""
        client = create_client("groq-fast")

        assert isinstance(client, GroqClient)
        assert client.model == "llama-3.3-70b-versatile"
        assert client.temperature == 0.1

    @patch.dict(os.environ, {"GROQ_API_KEY": "test_key"})
    def test_create_groq_client_balanced(self):
        """Test creating Groq client for balanced mode."""
        client = create_client("groq-balanced")

        assert isinstance(client, GroqClient)
        assert client.temperature == 0.3

    @patch.dict(os.environ, {"XAI_API_KEY": "test_key"})
    def test_create_grok_client_deep(self):
        """Test creating Grok client for deep mode."""
        client = create_client("grok-deep")

        assert isinstance(client, GrokClient)
        assert client.model == "grok-3"
        assert client.temperature == 0.2

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_create_openai_client_balanced(self):
        """Test creating OpenAI client for balanced mode."""
        client = create_client("openai-balanced")

        assert isinstance(client, OpenAIClient)
        assert client.model == "gpt-4o"
        assert client.temperature == 0.2

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_create_openai_client_fast(self):
        """Test creating OpenAI client for fast mode."""
        client = create_client("openai-fast")

        assert isinstance(client, OpenAIClient)
        assert client.model == "gpt-4o-mini"
        assert client.temperature == 0.1


class TestGroqClient:
    """Tests for GroqClient."""

    def test_groq_client_missing_api_key(self):
        """Test error when GROQ_API_KEY is not set."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GROQ_API_KEY", None)
            with pytest.raises(ValueError, match="GROQ_API_KEY"):
                GroqClient(model="test", temperature=0.1)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test_key"})
    @patch("src.clients.groq_client.Groq")
    def test_groq_client_evaluate(self, mock_groq_class):
        """Test Groq client evaluate method."""
        # Setup mock
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices[
            0
        ].message.content = '{"content_score": 4, "content_explanation": "Good", "format_score": 5, "format_explanation": "Great"}'
        mock_client.chat.completions.create.return_value = mock_response

        client = GroqClient(model="test-model", temperature=0.1)
        result = client.evaluate("ticket", "reply")

        assert (
            result
            == '{"content_score": 4, "content_explanation": "Good", "format_score": 5, "format_explanation": "Great"}'
        )
        mock_client.chat.completions.create.assert_called_once()


class TestGrokClient:
    """Tests for GrokClient."""

    def test_grok_client_missing_api_key(self):
        """Test error when XAI_API_KEY is not set."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("XAI_API_KEY", None)
            with pytest.raises(ValueError, match="XAI_API_KEY"):
                GrokClient(model="test", temperature=0.1)

    @patch.dict(os.environ, {"XAI_API_KEY": "test_key"})
    @patch("src.clients.grok_client.OpenAI")
    def test_grok_client_evaluate(self, mock_openai_class):
        """Test Grok client evaluate method."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices[
            0
        ].message.content = '{"content_score": 5, "content_explanation": "Excellent", "format_score": 4, "format_explanation": "Good"}'
        mock_client.chat.completions.create.return_value = mock_response

        client = GrokClient(model="test-model", temperature=0.2)
        result = client.evaluate("ticket", "reply")

        assert (
            result
            == '{"content_score": 5, "content_explanation": "Excellent", "format_score": 4, "format_explanation": "Good"}'
        )
        # Verify base_url was set
        mock_openai_class.assert_called_once_with(
            api_key="test_key",
            base_url="https://api.x.ai/v1",
        )


class TestOpenAIClient:
    """Tests for OpenAIClient."""

    def test_openai_client_missing_api_key(self):
        """Test error when OPENAI_API_KEY is not set."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                OpenAIClient(model="test", temperature=0.1)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch("src.clients.openai_client.OpenAI")
    def test_openai_client_evaluate(self, mock_openai_class):
        """Test OpenAI client evaluate method."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices[
            0
        ].message.content = '{"content_score": 4, "content_explanation": "Good", "format_score": 4, "format_explanation": "Good"}'
        mock_client.chat.completions.create.return_value = mock_response

        client = OpenAIClient(model="gpt-4o", temperature=0.2)
        result = client.evaluate("ticket", "reply")

        assert (
            result
            == '{"content_score": 4, "content_explanation": "Good", "format_score": 4, "format_explanation": "Good"}'
        )
        mock_client.chat.completions.create.assert_called_once()


# =============================================================================
# Test: Integration
# =============================================================================


class TestIntegration:
    """Integration tests with mocked LLM."""

    @patch.dict(os.environ, {"GROQ_API_KEY": "test_key"})
    @patch("src.clients.groq_client.Groq")
    def test_full_flow(self, mock_groq_class, tmp_path):
        """Test complete evaluation flow with mocked LLM."""
        from src.evaluator import evaluate_tickets

        # Create input file
        input_file = tmp_path / "input.csv"
        input_file.write_text('ticket,reply\n"Test ticket","Test reply"')

        # Setup mock
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(
            {
                "content_score": 4,
                "content_explanation": "Good content",
                "format_score": 5,
                "format_explanation": "Great format",
            }
        )
        mock_client.chat.completions.create.return_value = mock_response

        # Run evaluation
        tickets = read_tickets(str(input_file))
        client = create_client("groq-fast")
        results = evaluate_tickets(tickets, client)

        # Verify
        assert len(results) == 1
        assert results[0].content_score == 4
        assert results[0].format_score == 5
