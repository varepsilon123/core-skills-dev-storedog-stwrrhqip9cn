"""
Unit tests for the words utility module.
"""
import pytest
from words import get_random, load_words, WordsException


@pytest.mark.unit
class TestGetRandom:
    """Tests for get_random() function"""

    def test_returns_single_word_by_default(self):
        """get_random() with no arguments returns a single word"""
        result = get_random()
        parts = result.split(" ")
        assert len(parts) == 1

    def test_returns_multiple_words_when_requested(self):
        """get_random(n) returns n space-separated words"""
        result = get_random(3)
        parts = result.split(" ")
        assert len(parts) == 3

    def test_returns_reasonably_random_selection(self):
        """get_random() returns varied words, not the same word repeatedly"""
        result = get_random(10)
        parts = result.split(" ")
        unique_words = set(parts)
        assert len(unique_words) > 3


@pytest.mark.unit
class TestLoadWords:
    """Tests for load_words() function"""

    def test_loads_words_from_valid_json_file(self, tmp_path):
        """load_words() successfully loads words from a valid JSON file"""
        # Use pytest's tmp_path fixture for automatic cleanup
        test_file = tmp_path / "testwords.json"
        test_file.write_text('["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]')

        result = load_words(str(test_file))
        assert len(result) == 10

    def test_raises_exception_for_missing_file(self):
        """load_words() raises WordsException when file doesn't exist"""
        with pytest.raises(WordsException):
            load_words("I_d0_NOT_ex157.fudge")
