import os

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.ui


def test_page_opens(page):
    page.goto(os.getenv("BASE_URL", "http://127.0.0.1:8000"), timeout=10000)
    expect(page).to_have_title("Task Manager — QA Training")
    expect(page.get_by_test_id("create-task-form")).to_be_visible()
