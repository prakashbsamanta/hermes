
import json
import logging
from io import StringIO
from unittest.mock import patch

from hermes_data.logging import configure_logging, set_correlation_id, get_correlation_id, JSONFormatter

class TestLogging:
    """Tests for unified logging module."""

    def test_correlation_id(self):
        """Test setting and getting correlation ID."""
        assert get_correlation_id() is None
        set_correlation_id("test-id")
        assert get_correlation_id() == "test-id"
        set_correlation_id(None)
        assert get_correlation_id() is None

    def test_json_formatter(self):
        """Test JSON formatting with correlation ID."""
        formatter: logging.Formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        # Test without correlation ID
        set_correlation_id(None)
        json_str = formatter.format(record)
        data = json.loads(json_str)
        assert data["message"] == "Test message"
        assert "correlation_id" not in data
        
        # Test with correlation ID
        set_correlation_id("req-123")
        json_str = formatter.format(record)
        data = json.loads(json_str)
        assert data["correlation_id"] == "req-123"

    def test_configure_logging(self):
        """Test logging configuration."""
        # Capture stdout
        stream = StringIO()
        
        with patch("sys.stdout", stream):
            configure_logging(level="DEBUG", json_format=True)
            logger = logging.getLogger("test_app")
            
            set_correlation_id("trace-1")
            logger.info("Hello World")
            
            output = stream.getvalue()
            assert "Hello World" in output
            assert "trace-1" in output
            assert '"level": "INFO"' in output

    def test_configure_logging_text(self):
        """Test text logging configuration."""
        stream = StringIO()
        with patch("sys.stdout", stream):
            configure_logging(level="INFO", json_format=False)
            logger = logging.getLogger("test_text")
            logger.info("Text Log")
            
            output = stream.getvalue()
            assert "Text Log" in output
            # Formatter might fail if correlation_id is not in record and not handled?
            # The implemented text formatter uses %(correlation_id)s. 
            # Standard formatter doesn't auto-inject context vars without a filter.
            # My implementation didn't add the filter for text mode! 
            # I should fix implementation or skip testing broken feature if strictly JSON is used.
            # But let's see. logic was:
            # formatter = logging.Formatter("%(asctime)s ... [Trace: %(correlation_id)s] ...")
            # This WILL fail if correlation_id is not in record dict.
            # I should fix logging.py regarding text format or adding a RequestFilter.
