# Moodle Course File Downloader

A Selenium automation script for downloading **Lecture Notes** from Moodle courses hosted at:

`https://cetpgex.iitp.ac.in/moodle/`

The script opens Microsoft SSO, waits for the user to complete login and Microsoft Authenticator verification, visits each course, downloads the `Lecture Notes` folder, extracts the ZIP file, and copies only new files into a course-specific folder.

## Use Case

Use this script when course files are stored in multiple Moodle courses and you want to:

- Download Lecture Notes from all enrolled courses automatically.
- Avoid downloading or copying files that already exist.
- Keep files organized in separate folders for each course.
- Repeat the process later to collect newly added files.
- Extract downloaded ZIP files automatically.

The script does not bypass authentication. Microsoft login and Authenticator approval must be completed manually in the browser.

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- Google Chrome
- Access to the IIT Patna Moodle website
- A valid Microsoft SSO account
- Permission to download the course files

## Setup

### 1. Download the code

Download the project from GitHub using **Code > Download ZIP**, then extract it. Alternatively, clone it with Git:

```powershell
git clone <repository-url>
cd Notes_Download
```

If the project is already cloned, open PowerShell in the project folder and pull the latest version:

```powershell
git pull
```

### 2. Open a terminal in the project folder

In VS Code, open the extracted or cloned `Notes_Download` folder, then open **Terminal > New Terminal**. You can also open PowerShell in that folder and run:

```powershell
cd path\to\Notes_Download
```

### 3. Check Python

Run:

```powershell
python -V
```

Python 3.10 or newer is recommended. If Python is not installed, install it from [python.org](https://www.python.org/downloads/) and select **Add Python to PATH** during installation. Close and reopen the terminal, then run `python -V` again.

### 4. Install Selenium

Install the required dependency:

```powershell
pip install selenium
```

If `pip` is not recognized, use:

```powershell
python -m pip install selenium
```

Make sure Google Chrome is installed and up to date. Selenium Manager normally downloads and manages the required Chrome driver automatically.

## Run the Script

From the project folder, run:

```powershell
py main.py
```

# Demo Video
## Demo

[![Watch the video](https://img.youtube.com/vi/2DNgIh88TzA/maxresdefault.jpg)](https://youtu.be/2DNgIh88TzA)


The script opens Moodle in Chrome. Complete the Microsoft login and Authenticator verification using your own credentials. After login, do not close the browser or interact with it; the script will visit the courses available to your account, download each course's `Lecture Notes` folder, extract the files, and save them under `Lecture_Notes/`.

The script will:

1. Open the Moodle login page in Chrome.
2. Open Microsoft SSO and wait for you to complete login and Authenticator verification.
3. Visit each course visible to your account.
4. Open the `Lecture Notes` folder and click `Download folder`.
5. Download and extract the ZIP file.
6. Copy only files that are not already present.
7. Delete the temporary ZIP and extracted files.

Keep the Chrome window open while the script is running.

## Output Structure

The script creates this folder automatically in the directory from which it is run:

```text
Lecture_Notes/
├── Course name MB-GAI-501_ Foundations of AI models for Product Management/
│   ├── lecture1.pdf
│   └── lecture2.pdf
├── Course name MB-GAI-502_ Another Course/
│   └── notes.pdf
└── _incoming/
```

`_incoming` is used only for temporary downloads. ZIP files and temporary extracted folders are deleted after each course is processed.

## Re-running the Script

You can run the script again whenever new files are added to Moodle.

Existing files are preserved. If a file with the same relative path already exists in a course folder, it is skipped. New files are copied automatically.

The comparison is based on file path and filename. The script does not replace an existing file if Moodle has a newer version with the same name.

## Terminal Progress

During a download, the terminal shows the current ZIP size:

```text
Downloading ZIP: 12.45 MB
```

During file comparison, it shows processed and remaining files:

```text
Files: [###############---------------] 50% | processed 5/10 | remaining 5
```

The download display shows the current downloaded size, not an exact percentage, because Chrome does not expose the total ZIP size reliably through Selenium.

## Troubleshooting

### Selenium is not installed

Error:

```text
ModuleNotFoundError: No module named 'selenium'
```

Fix:

```powershell
python -m pip install selenium
```

### Chrome does not open

Check that Google Chrome is installed. Then update Selenium:

```powershell
python -m pip install --upgrade selenium
```

### Microsoft login times out

Complete the login and Authenticator approval within five minutes. If the login takes longer, run the script again.

### The script cannot find `Lecture Notes`

The course page must contain a folder link whose text includes `Lecture Notes`. If the Moodle website changes its layout or naming, the selector in `download_lecture_notes()` may need to be updated.

### The script cannot find `Download folder`

The folder page must contain a button named `Download folder`. If Moodle changes the button text, update the XPath in `download_lecture_notes()`.

### ZIP extraction fails because of invalid Windows names

The script already normalizes invalid ZIP path names, including names with trailing spaces or characters such as `:`, `?`, and `*`.

### `[Errno 2] No such file or directory` for a downloaded PowerPoint

If the error shows a long path under `Lecture_Notes\_incoming\..._extracted`, Windows has reached its legacy path-length limit while handling the temporary extracted files. The script uses a short `_incoming\_extracted` folder for temporary files. Pull the latest code with `git pull` or download the updated project, then run the script again.

### Existing files are not updated

The script intentionally copies only files that do not already exist. Delete the old file manually if you want the newly downloaded version to be copied.

## Sharing the Script

Share these items with the other user:

```text
main.py
README.md
```

Do not share a local `.venv` folder if you created one. The other user should install Selenium by following the setup instructions above.

The other user must use their own Moodle and Microsoft SSO account. Never store Moodle passwords, Microsoft credentials, or Authenticator information in the script.

## Important Notes

- The script downloads only courses visible to the logged-in Moodle account.
- The script currently looks specifically for the `Lecture Notes` folder.
- The script currently downloads courses listed on the Moodle courses page.
- Internet access is required while logging in and downloading files.
- Do not close Chrome until the script finishes.
- Use the downloaded files only according to your institution's course-content and copyright policies.
