import pytest
from playwright.sync_api import sync_playwright
from src.main import main


def test_execution():
    main()

test_execution()