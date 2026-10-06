import time as sleep
from playwright.sync_api import sync_playwright
import os
from datetime import date, timedelta
import shutil
import subprocess

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.0.0 Safari/537.36"
)


def get_target_date(day_of_week):
    today = date.today()
    day_of_week_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    target_day = day_of_week_map.get(day_of_week)
    if target_day is None:
        raise ValueError("Invalid day of the week")
    days_ahead = (target_day - today.weekday() + 7) % 7
    target_date = today + timedelta(days=days_ahead)
    return target_date.strftime("%m%%2F%d%%2F%Y")


def get_target_filename(day_of_week, file_prefix="muni"):
    readable_date = get_target_date(day_of_week).replace("%2F", "-")
    return f"{file_prefix}_tee_times_{readable_date}.txt"


def read_saved_tee_times_with_slots(file_path):
    """Read saved tee times and return a dict mapping keys to max slot counts seen"""
    saved_data = {}
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if line and ", Open Slots:" in line:
                    parts = line.split(", Open Slots: ")
                    if len(parts) == 2:
                        key = parts[0]
                        try:
                            slot_count = int(parts[1])
                            if key not in saved_data or slot_count > saved_data[key]:
                                saved_data[key] = slot_count
                        except ValueError:
                            if key not in saved_data:
                                saved_data[key] = 0
    return saved_data


def save_tee_times(file_path, tee_times):
    with open(file_path, "w") as file:
        for tee_time in tee_times:
            file.write(f"{tee_time}\n")


def aggressive_cleanup():
    """Aggressively clean up Chrome/Chromium temporary files and processes"""
    try:
        subprocess.run(['pkill', '-9', 'chrome'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-9', 'chromedriver'], stderr=subprocess.DEVNULL)
        sleep.sleep(1)
    except Exception:
        pass

    cleaned_count = 0
    for temp_dir in ['/tmp', '/var/tmp']:
        try:
            if not os.path.exists(temp_dir):
                continue
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                if any(x in item.lower() for x in ['chrome', 'tmp', 'scoped', '.org.chromium']):
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                            cleaned_count += 1
                        elif os.path.isfile(item_path):
                            os.remove(item_path)
                            cleaned_count += 1
                    except Exception:
                        pass
        except Exception:
            pass

    if cleaned_count > 0:
        print(f"[CLEANUP] Removed {cleaned_count} temp items")


def build_url(cityConfig, day_of_week):
    """Build the search URL from a city config dict."""
    return (
        f"https://{cityConfig['domain']}/webtrac/web/search.html?"
        f"Action=Start&SubAction=&_csrf_token={cityConfig['csrf_token']}"
        f"&numberofplayers={cityConfig['number_of_players']}"
        f"&secondarycode=&begindate={get_target_date(day_of_week)}"
        f"&begintime={cityConfig['begin_time']}"
        f"&numberofholes={cityConfig['number_of_holes']}"
        f"&display=Detail&module=GR&multiselectlist_value="
        f"&grwebsearch_buttonsearch=yes"
    )


CHROMIUM_ARGS = [
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--disable-software-rasterizer",
    "--disable-extensions",
    "--js-flags=--max-old-space-size=64",
    "--renderer-process-limit=1",
]


class Driver:
    """
    A headless Chromium page launched by Playwright, reused across all of a
    city's scrape days.

    Playwright downloads its own Chromium build (not the system snap) and
    talks to it over a pipe rather than chromedriver's localhost HTTP port,
    which started resetting every connection in Oct 2026 on the Pi.
    Playwright also creates and deletes the browser's temp profile itself.
    """

    def __init__(self, playwright, browser, page):
        self._playwright = playwright
        self._browser = browser
        self.page = page

    def quit(self):
        for close in (self._browser.close, self._playwright.stop):
            try:
                close()
            except Exception:
                pass


def create_driver(max_attempts=3):
    """
    Launch a single headless Chromium to be reused across multiple
    scrape_tee_times() calls for the same city.

    Browser startup occasionally fails on a resource constrained Pi -- retried
    with a cleanup pass in between, since a retry resolves the vast majority
    of these transient failures. On failure of every attempt the last error
    is re-raised, so callers never have to handle a partially-created driver.
    """
    last_error = None
    for attempt in range(1, max_attempts + 1):
        playwright = None
        try:
            playwright = sync_playwright().start()
            # channel="chromium" runs the full browser in new headless mode
            # (same as the old --headless=new) rather than the stripped-down
            # headless shell, which Cloudflare is quicker to flag.
            browser = playwright.chromium.launch(channel="chromium", headless=True, args=CHROMIUM_ARGS)
            context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1920, "height": 1080})
            page = context.new_page()
            page.set_default_timeout(30000)
        except Exception as e:
            last_error = e
            if playwright is not None:
                try:
                    playwright.stop()
                except Exception:
                    pass
            if attempt < max_attempts:
                print(f"[WARN] Browser failed to start (attempt {attempt}/{max_attempts}): {e}. Retrying...")
                aggressive_cleanup()
                sleep.sleep(3)
            continue

        print(f"Browser started successfully (attempt {attempt}/{max_attempts})")
        return Driver(playwright, browser, page)

    raise last_error


def _get_column_value(parent_row, label):
    """
    Extract a labeled column's value from a results row.

    The table has no data-title attributes; each td instead holds a
    mobile-column-header span with the label text, followed by the value as a
    plain text sibling (the span is visually hidden at desktop widths).
    """
    td = parent_row.locator(f"xpath=.//td[.//span[normalize-space(text())='{label}']]").first
    # Short timeout so a missing column fails fast instead of waiting the
    # page's 30s default.
    text = td.inner_text(timeout=2000).strip()
    if text.startswith(label):
        text = text[len(label):].strip()
    return text


def scrape_tee_times(day_of_week, cityConfig, driver):
    """
    Scrape tee times for a given day using the provided city config and an
    already-running Driver (shared across all scrape_days for this city).

    cityConfig should be a dict with keys:
        domain, csrf_token, number_of_players, begin_time,
        number_of_holes, file_prefix, name
    """
    city_name = cityConfig.get("name", "Unknown")
    file_prefix = cityConfig.get("file_prefix", "muni")

    url = build_url(cityConfig, day_of_week)
    print(f"[{city_name}] Navigating to: {url}")

    new_tee_times_list = []

    try:
        page = driver.page
        page.goto(url)
        sleep.sleep(5)

        cart_buttons = page.locator(".button-cell--cart").all()
        print(f"[{city_name}] Found {len(cart_buttons)} tee time buttons on page")

        current_tee_times = []

        for button in cart_buttons:
            try:
                parent_row = button.locator("xpath=ancestor::tr").first
                parent_row.wait_for(state="attached", timeout=2000)
            except Exception as e:
                print(f"[{city_name}][WARN] Skipping tee time button with no ancestor row: {e}")
                continue

            try:
                time_val = _get_column_value(parent_row, "Time")
                date_val = _get_column_value(parent_row, "Date")
                holes = _get_column_value(parent_row, "Holes")
                course = _get_column_value(parent_row, "Course")
                open_slots = _get_column_value(parent_row, "Open Slots")
            except Exception as e:
                row_html = parent_row.evaluate("el => el.outerHTML")[:2000]
                print(f"[{city_name}][WARN] Skipping unparseable tee time row: {e}\nRow HTML: {row_html}")
                continue

            full_tee_time = f"Time: {time_val}, Date: {date_val}, Holes: {holes}, Course: {course}, Open Slots: {open_slots}"
            current_tee_times.append(full_tee_time)
            print(f"[{city_name}][FOUND] {full_tee_time}")

        file_path = get_target_filename(day_of_week, file_prefix)
        saved_tee_times_data = read_saved_tee_times_with_slots(file_path)
        print(f"[{city_name}] Loaded {len(saved_tee_times_data)} saved tee time keys from file")

        for tee_time in current_tee_times:
            if ", Open Slots: " in tee_time:
                parts = tee_time.split(", Open Slots: ")
                if len(parts) == 2:
                    tee_key = parts[0]
                    try:
                        current_slots = int(parts[1])
                        if tee_key not in saved_tee_times_data:
                            new_tee_times_list.append(tee_time)
                            print(f"[{city_name}][NEW TIME SLOT] {tee_time}")
                        elif current_slots > saved_tee_times_data[tee_key]:
                            new_tee_times_list.append(tee_time)
                            print(f"[{city_name}][MORE SLOTS] {tee_time} (was {saved_tee_times_data[tee_key]}, now {current_slots})")
                    except ValueError:
                        if tee_key not in saved_tee_times_data:
                            new_tee_times_list.append(tee_time)
                            print(f"[{city_name}][NEW TIME SLOT] {tee_time}")

        if new_tee_times_list:
            print(f"[{city_name}] Found {len(new_tee_times_list)} new/increased tee times!")
        else:
            print(f"[{city_name}] No new tee times or increased availability found.")

        save_tee_times(file_path, current_tee_times)

    except Exception as e:
        print(f"[{city_name}][ERROR] An error occurred: {e}")

    return new_tee_times_list