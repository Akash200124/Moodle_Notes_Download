import re
import shutil
import time
import zipfile
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

LOGIN_URL = "https://cetpgex.iitp.ac.in/moodle/login/index.php"
COURSES_URL = "https://cetpgex.iitp.ac.in/moodle/my/courses.php"
TEMP_DOWNLOAD = Path.cwd() / "Lecture_Notes"
INCOMING_DOWNLOAD = TEMP_DOWNLOAD / "_incoming"


def microsoft_login(driver, wait):
	"""Open Microsoft SSO and wait for the user to finish authentication."""
	driver.get(LOGIN_URL)

	# The visible Microsoft label may be on the link, its image alt text, or
	# an enclosing button, depending on the Moodle theme.
	microsoft_xpath = (
		"//a[.//img[contains(translate(@alt, 'MICROSOFT', 'microsoft'), "
		"'microsoft')] or contains(translate(., 'MICROSOFT', 'microsoft'), "
		"'microsoft')] | //button[contains(translate(., 'MICROSOFT', "
		"'microsoft'), 'microsoft')]"
	)

	button = wait.until(
		EC.element_to_be_clickable((By.XPATH, microsoft_xpath))
	)
	old_handles = set(driver.window_handles)
	button.click()

	print("Microsoft login opened. Complete SSO and Authenticator verification.")

	def login_finished(current_driver):
		new_handles = set(current_driver.window_handles) - old_handles
		if new_handles:
			current_driver.switch_to.window(new_handles.pop())

		return (
			current_driver.current_url != LOGIN_URL
			and "login.microsoftonline.com" not in current_driver.current_url
		)

	wait.until(login_finished)
	print("Login completed and Moodle is open.")


def safe_folder_name(course_name):
	"""Return a readable, Windows-safe, underscore-separated course name."""
	name = re.sub(r"^\s*course\s+name\s+", "", course_name, flags=re.IGNORECASE)
	name = re.sub(r"\s+", " ", name).strip()

	code_match = re.match(r"^([A-Za-z]+(?:-[A-Za-z0-9]+)*-\d+)\s+(.+)$", name)
	if code_match:
		course_code, title = code_match.groups()
		title_parts = re.findall(r"[A-Za-z0-9]+", title)
		title = "_".join(
			part if part.isupper() else part.lower() for part in title_parts
		)
		name = f"{course_code}_{title}"
	else:
		name = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()

	if name.upper() in {"CON", "PRN", "AUX", "NUL"}:
		name = f"_{name}"
	return name or "untitled_course"


def safe_archive_part(part):
	"""Return a ZIP file or folder name that is valid on Windows."""
	name = re.sub(r"[<>:\"/\\|?*]", "_", part).rstrip(" .")
	name_root = name.split(".", 1)[0].upper()
	if name_root in {"CON", "PRN", "AUX", "NUL"}:
		name = f"_{name}"
	return name or "untitled"


def wait_for_download(download_folder, old_files, wait):
	"""Wait for Chrome to finish a new ZIP download and show its size."""
	last_reported_size = -1

	def completed_download(_driver):
		nonlocal last_reported_size
		zip_files = {
			file_path for file_path in download_folder.glob("*.zip")
			if file_path not in old_files
		}
		partial_files = list(download_folder.glob("*.crdownload"))
		if partial_files:
			size = partial_files[0].stat().st_size
			if size != last_reported_size:
				print(f"\r  Downloading ZIP: {size / 1024 / 1024:.2f} MB", end="", flush=True)
				last_reported_size = size
		if zip_files and not partial_files:
			print("\r  Download complete.                         ")
			return next(iter(zip_files))
		return False

	return wait.until(completed_download)


def extract_zip(zip_path, destination):
	"""Extract a ZIP while making archive names valid on Windows."""
	if destination.exists():
		shutil.rmtree(destination)
	extract_folder = destination / zip_path.stem
	extract_folder.mkdir(parents=True, exist_ok=True)
	with zipfile.ZipFile(zip_path) as archive:
		for member in archive.infolist():
			archive_path = member.filename.replace("\\", "/")
			parts = [
				safe_archive_part(part)
				for part in archive_path.split("/")
				if part not in {"", ".", ".."}
			]
			if not parts:
				continue

			target_path = extract_folder.joinpath(*parts)
			if member.is_dir() or archive_path.endswith("/"):
				target_path.mkdir(parents=True, exist_ok=True)
				continue

			target_path.parent.mkdir(parents=True, exist_ok=True)
			with archive.open(member) as source, target_path.open("wb") as target:
				shutil.copyfileobj(source, target)
	return extract_folder


def copy_missing_files(source_folder, destination_folder):
	"""Copy missing files and show processed and remaining file counts."""
	destination_folder.mkdir(parents=True, exist_ok=True)
	copied_count = 0
	skipped_count = 0
	source_files = [file_path for file_path in source_folder.rglob("*") if file_path.is_file()]
	total_files = len(source_files)
	processed_files = 0

	if total_files == 0:
		print("  No files found in the downloaded folder.")
		return

	for source_file in source_files:
		relative_path = source_file.relative_to(source_folder)
		destination_file = destination_folder / relative_path
		if destination_file.exists():
			skipped_count += 1
		else:
			destination_file.parent.mkdir(parents=True, exist_ok=True)
			shutil.copy2(source_file, destination_file)
			copied_count += 1

		processed_files += 1
		percent = processed_files * 100 // total_files
		remaining = total_files - processed_files
		bar_length = 30
		filled = percent * bar_length // 100
		bar = "#" * filled + "-" * (bar_length - filled)
		print(
			f"\r  Files: [{bar}] {percent:3d}% | "
			f"processed {processed_files}/{total_files} | remaining {remaining}",
			end="",
			flush=True,
		)

	print()

	print(f"  New files copied: {copied_count}")
	print(f"  Existing files skipped: {skipped_count}")


def download_lecture_notes(driver, wait, course_name, course_url):
	"""Download, merge, and clean up Lecture Notes for one course."""
	driver.get(course_url)

	lecture_notes_xpath = (
		"//a[contains(@href, '/mod/folder/view.php') and "
		"contains(translate(normalize-space(.), 'LECTURE NOTES', "
		"'lecture notes'), 'lecture notes')]"
	)
	lecture_link = wait.until(
		EC.element_to_be_clickable((By.XPATH, lecture_notes_xpath))
	)
	lecture_link.click()

	download_button = wait.until(
		EC.element_to_be_clickable(
			(By.XPATH, "//button[@type='submit' and contains(normalize-space(.), "
			"'Download folder')]")
		)
	)
	old_files = set(INCOMING_DOWNLOAD.glob("*.zip"))
	download_button.click()
	zip_path = wait_for_download(INCOMING_DOWNLOAD, old_files, wait)

	destination = TEMP_DOWNLOAD / safe_folder_name(course_name)
	extracted_root = INCOMING_DOWNLOAD / "_extracted"
	try:
		extracted_folder = extract_zip(zip_path, extracted_root)
		print(f"Comparing files for: {course_name}")
		copy_missing_files(extracted_folder, destination)
		print(f"Completed: {course_name}")
	finally:
		if zip_path.exists():
			zip_path.unlink()
		if extracted_root.exists():
			shutil.rmtree(extracted_root)
		print(f"Temporary ZIP and extracted files removed for: {course_name}")


def main():
	TEMP_DOWNLOAD.mkdir(parents=True, exist_ok=True)
	INCOMING_DOWNLOAD.mkdir(parents=True, exist_ok=True)
	for old_download in INCOMING_DOWNLOAD.glob("*"):
		if old_download.is_file():
			old_download.unlink()

	options = webdriver.ChromeOptions()
	options.add_experimental_option(
		"prefs",
		{
			"download.default_directory": str(INCOMING_DOWNLOAD.resolve()),
			"download.prompt_for_download": False,
			"download.directory_upgrade": True,
		}
	)
	driver = webdriver.Chrome(options=options)
	driver.maximize_window()
	wait = WebDriverWait(driver, 300)

	try:
		microsoft_login(driver, wait)

		driver.get(COURSES_URL)
		course_links = wait.until(
			EC.presence_of_all_elements_located(
				(By.CSS_SELECTOR, "a.aalink[href*='/course/view.php']")
			)
		)

		courses = [
			(link.text.strip(), link.get_attribute("href"))
			for link in course_links
			if link.get_attribute("href")
		]
		del courses[-1]  # Remove the last link, which is "View all courses"

        
		
		print(f"Found {len(courses)} courses:")
		for index, (title, url) in enumerate(courses, start=1):
			course_name = title or f"course_{index}"
			print(f"[{index}/{len(courses)}] Processing {course_name}")
			try:
				download_lecture_notes(driver, wait, course_name, url)
			except Exception as error:
				print(f"Skipped {course_name}: {error}")
	finally:
		driver.quit()


if __name__ == "__main__":
	main()