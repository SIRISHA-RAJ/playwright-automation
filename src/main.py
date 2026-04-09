import csv
import time
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import Page, sync_playwright, expect 
from src.server import apply_enb_config
import re

# ================== CONSTANTS ==================
INPUT_FILE_PATH = "data/testcases.csv"

USERNAME = "admin"
PASSWORD = "admin"


# ================== UTIL FUNCTIONS ==================
def read_testcases():
    testcases = []

    with open(INPUT_FILE_PATH, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        reader.fieldnames = [field.strip() for field in reader.fieldnames]

        for row in reader:
            testcases.append({
                "testcase_id": row["testcase_id"].strip(),
                "config_file": row["config_file"].strip()
            })

    return testcases


def get_testcase_status_from_url(page):
    url = page.url
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)
    status = params.get("testCaseStatus", ["Unknown"])[0]
    return status.replace("+", " ")


# ================== PAGE ACTIONS ==================
def login(page):
    page.goto("http://192.168.1.95:8080/")

    page.fill("#username", USERNAME)
    page.fill("#password", PASSWORD)
    #page.click('xpath=//*[@id="root"]/div/div[2]/div/form/button')
    page.get_by_role("button", name="Login").click()


    page.get_by_role("button", name="create Create Test Case").wait_for()
    print("Login successful")


def stop_testcase(page):
    stop_button = page.get_by_role("button", name="Stop")

    try:
        if stop_button.is_visible():
            print("A testcase is in progress, stopping  it.")
            stop_button.click()
            page.wait_for_timeout(10000)
            print("Testcase stopped.")
            return True

        print("No testcase is in progress, moving towards execution.")
        return False

    except Exception:
        print("A testcase is in progress, stopping  it.")

        enable_button = page.locator('xpath=/html/body/div/div/div/div[2]/button')
        enable_button.click()

        stop_button.wait_for(timeout=3000)
        stop_button.click()
        page.wait_for_timeout(5000)

        print("Testcase stopped.")
        return True


# ================== TESTCASE EXECUTION ==================
def navigate_to_testcases(page):
    page.get_by_text("My Tests").click()

def search_testcase(page, testcase):
    page.get_by_role("textbox", name="Search TestCase Name").fill(testcase)
    page.wait_for_timeout(2000)


def click_start(page, testcase):
    page.get_by_role("cell", name=testcase)
    page.get_by_role("button", name="Start Test Case").click()

    if page.get_by_text("Availability:").is_visible(): 
        page.get_by_role("cell", name="UE-Simulator").locator("p").click()
        page.get_by_role("row", name="Toggle Row Selected UE-").get_by_role("checkbox").check()
        page.locator(".w-\\[28px\\]").first.click()
        page.get_by_role("button", name="Next").click() 
        page.get_by_role("button", name="Execute Now").click() 
    elif page.get_by_role("heading", name="Execution Summary").is_visible(): 
        page.get_by_role("button", name="Execute Now").click() 
    else: 
        pass 

    print("Testcase execution initiated")
    page.wait_for_timeout(3000)


def start_testcase(page, testcase):
    print(f"Starting execution of {testcase}")

    navigate_to_testcases(page)
    search_testcase(page, testcase)

    table_check = page.get_by_text("Showing 1 of 1 items")

    if table_check.count() > 0 and table_check.is_visible():
        row = page.locator(
            'xpath=/html/body/div/div/div/main/div/div[2]/div/div[2]/div/div/div[2]/div[2]/table/tbody/tr/td[1]'
        )
        row.wait_for(state="visible")
        row.hover()

        click_start(page, testcase)

    else:
        row = page.locator("table tbody tr").filter(
            has=page.get_by_text(testcase, exact=True)
        )

        if row.count() > 0:
            row.hover()
            click_start(page, testcase)
            #print("Exact testcase clicked")
        else:
            print("No testcase found")


# ================== MONITORING ==================
def monitor_testcase_status(page, testcase):
    print("Waiting for testcase to start...")
    page.wait_for_timeout(36000)

    while True:
        status = get_testcase_status_from_url(page).lower()
        if page.get_by_text("Test Running").is_visible():
            print(f"{testcase} is in progress")
            page.wait_for_timeout(10000)

        elif status in ["stopped", "aborted"]:
            print(f"{testcase} is {status}")
            break

        else:
            print(f"Execution of {testcase} is completed.")
            break

# ================== LOGS and STATS download ==================
import os

def export_stats_and_logs(page, testcase):
    try:
        # Create folder
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        download_path = os.path.join(BASE_DIR, "results", testcase)

        os.makedirs(download_path, exist_ok=True)
        print(f"Creating directory at: {download_path}")
        
        #download_path = f"./results/{testcase}"
        #os.makedirs(download_path, exist_ok=True)

        print("Exporting stats...")
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Export Export").click()
            page.wait_for_timeout(5000)

            download = download_info.value
            stats_file = os.path.join(download_path, download.suggested_filename)
            download.save_as(stats_file)

            print(f"Stats saved at: {stats_file}")

            #Navigate to My Tests
            print("Navigating to My Tests...")
            page.get_by_text("My Tests").click()
            page.wait_for_timeout(3000)
            navigate_to_testcases(page)
            search_testcase(page, testcase)
            table_check = page.get_by_text("Showing 1 of 1 items")

            if table_check.count() > 0 and table_check.is_visible():
                row = page.locator(
                    'xpath=/html/body/div/div/div/main/div/div[2]/div/div[2]/div/div/div[2]/div[2]/table/tbody/tr/td[1]'
                )
                row.wait_for(state="visible")
                row.hover()
                with page.expect_download() as download_info:
                    page.get_by_role("cell", name=testcase)
                    page.get_by_role("button", name="Download").click()
                    page.wait_for_timeout(5000)
                    download = download_info.value
                    test_file = os.path.join(download_path, download.suggested_filename)
                    download.save_as(test_file)
                    print(f"testcase saved at: {test_file}")

            else:
                row = page.locator("table tbody tr").filter(
                    has=page.get_by_text(testcase, exact=True)
                )

                if row.count() > 0:
                    row.hover()
                    with page.expect_download() as download_info:
                        page.get_by_role("cell", name=testcase)
                        page.get_by_role("button", name="Download").click()
                        download = download_info.value
                        test_file = os.path.join(download_path, download.suggested_filename)
                        download.save_as(test_file)
                        page.wait_for_timeout(5000)
                        print(f"testcase saved at: {test_file}")
                else:
                    print("No testcase found")
                    
                    

            # Navigate to Logs
            print("Navigating to Logs page...")
            page.locator("div").filter(has_text=re.compile(r"^Logs$")).nth(2).click()
            page.wait_for_timeout(10000)


            # Check logs disabled
            if page.get_by_text("No Testcase in Progress").count() > 0:
                print("Logs are disabled")
                return "Logs disabled"

            else:
                print("Exporting logs...")
                with page.expect_download() as download_info:
                    page.get_by_role("button", name="Export Logs Export").click()

                    download = download_info.value
                    logs_file = os.path.join(download_path, download.suggested_filename)
                    download.save_as(logs_file)

                    print(f"Logs saved at: {logs_file}")

                return "Success"

    except Exception as e:
        print(f"Error occurred: {e}")
        return "Failed"
    
def verdict(page, testcase):
    page.get_by_text("My Tests").click()
    page.wait_for_timeout(3000)
    navigate_to_testcases(page)
    search_testcase(page, testcase)
    table_check = page.get_by_text("Showing 1 of 1 items")

    if table_check.count() > 0 and table_check.is_visible():
        row = page.locator(
            'xpath=/html/body/div/div/div/main/div/div[2]/div/div[2]/div/div/div[2]/div[2]/table/tbody/tr/td[1]'
        )
        row.wait_for(state="visible")
        row.hover()
        
    else:
        row = page.locator("table tbody tr").filter(
            has=page.get_by_text(testcase, exact=True)
        )

        if row.count() > 0:
            row.hover()
            page.get_by_role("row", name=testcase).get_by_role("button").nth(4).click()
            expect(page.get_by_role("main")).to_match_aria_snapshot("- table:\n  - rowgroup:\n    - row \"BLER (PASSED)\":\n      - cell \"BLER (PASSED)\"\n    - row \"Metric Measured(%) Criteria Verdict\":\n      - cell \"Metric\"\n      - cell \"Measured(%)\"\n      - cell \"Criteria\"\n      - cell \"Verdict\"\n  - rowgroup:\n    - row \"Avg_DL_BLER 0 Avg_DL_BLER<=5% PASS\":\n      - cell \"Avg_DL_BLER\"\n      - cell \"0\"\n      - cell \"Avg_DL_BLER<=5%\"\n      - cell \"PASS\"")

           
        else:
            print("No testcase found")

    page.get_by_role("row", name=testcase).get_by_role("button").nth(4).click()
    expect(page.get_by_role("main")).to_match_aria_snapshot("- table:\n  - rowgroup:\n    - row \"BLER (PASSED)\":\n      - cell \"BLER (PASSED)\"\n    - row \"Metric Measured(%) Criteria Verdict\":\n      - cell \"Metric\"\n      - cell \"Measured(%)\"\n      - cell \"Criteria\"\n      - cell \"Verdict\"\n  - rowgroup:\n    - row \"Avg_DL_BLER 0 Avg_DL_BLER<=5% PASS\":\n      - cell \"Avg_DL_BLER\"\n      - cell \"0\"\n      - cell \"Avg_DL_BLER<=5%\"\n      - cell \"PASS\"")

    
# ================== MAIN ==================
def main():
    testcases = read_testcases()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Automated execution triggered")
        login(page)
        stop_testcase(page)

        for tc in testcases:
            testcase = tc["testcase_id"]
            config_path = tc["config_file"]

            print(f"Execution of {testcase} using config {config_path}")

            apply_enb_config(config_path)
            start_testcase(page, testcase)
            monitor_testcase_status(page, testcase)
            page.wait_for_timeout(3000)
            export_stats_and_logs(page, testcase)
           #verdict(page, testcase)

        browser.close()


if __name__ == "__main__":
    main()
