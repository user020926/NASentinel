# NASentinel

## Overview

**NASentinel** is a log querying and management tool specifically designed for **Synology NAS**. It provides a powerful graphical user interface (GUI) that helps administrators securely and efficiently query, analyze, and export various types of logs and user activity rankings, improving auditing and administrative efficiency.

---

## Key Features

* **Synology NAS API Integration**
  Built-in `NASClient` provides direct interaction with the Synology NAS API, including authentication, log queries, and user information retrieval.

* **Two-Factor Authentication Support**
  Supports OTP-based two-factor authentication during the login process to enhance security.

* **Log Query and Export**
  Supports system logs, FileStation logs, and user activity rankings, with one-click export to formatted Excel files.

* **Automated Activity Ranking**
  Automatically calculates the number of upload, download, and delete operations performed by users and generates activity rankings.

* **Date Range Filtering**
  Provides an intuitive date picker that allows administrators to specify custom query periods.

* **Batch Processing and Operation Logging**
  Supports batch queries and exports while recording operation results for auditing and troubleshooting.

* **Modern GUI**
  Built with PyQt5, providing an intuitive and user-friendly interface.

---

## System Requirements

* Python 3.8 or later
* Required packages:

  * `requests`
  * `tenacity`
  * `PyQt5`
  * `pandas`
  * `openpyxl`

---

## Installation and Execution

1. Download and extract the project files.
2. Navigate to the `/dist/NASentinel` directory.
3. Locate and copy the path of `NASentinel.exe`.
4. It is recommended to create a desktop shortcut for convenient access.
5. Double-click `NASentinel.exe` to launch the application.

---

## Usage

### 1. Log in to the NAS

Enter the following information on the login screen:

* NAS IP address (e.g., `10.57.78.62`)
* Port (e.g., `5000`)
* Administrator username
* Password
* Two-factor authentication code (OTP), if enabled

Click **Login** to enter the main interface.

### 2. Query and Export Logs

1. Select the desired query type:

   * System Log
   * FileStation Log
   * User Activity Ranking
2. Specify the start and end dates.
3. Click **Query** to retrieve the corresponding records.
4. Review the results in the table.
5. Click **Export** to save the results to the desktop.

### 3. User Activity Ranking

The ranking feature automatically aggregates the number of upload, download, and delete operations performed by each user and generates corresponding rankings. The results can also be exported to Excel.

### 4. Date Picker

The date picker supports mouse, keyboard, and scroll-wheel input, allowing administrators to flexibly select the desired date range for log queries.

---

## Excel Export Format

### System Log

* **File Name:** `NAS_System_Log_YYYY-MM-DD-HH_MM_SS.xlsx`
* **Columns:** Priority | Log | Time | User | Event

### FileStation Log

* **File Name:** `NAS_Filestation_Log_YYYY-MM-DD-HH_MM_SS.xlsx`
* **Columns:** Log | Time | IP Address | User | Event | File/Folder | File Size | File Name

### Ranking Log

* **File Name:** `NAS_Ranking_Log_YYYY-MM-DD-HH_MM_SS.xlsx`
* **Worksheets:**

  * Upload Ranking
  * Download Ranking
  * Delete Ranking
* **Columns:** Rank | User | Count | File Size | Name | Email

---

## Project Structure

| Module               | Description                                                      |
| -------------------- | ---------------------------------------------------------------- |
| `main.py`            | Main application entry point, GUI, and workflow control          |
| `api.py`             | Synology NAS API communication and error handling                |
| `system_log.py`      | System log processing and Excel export                           |
| `filestation_log.py` | FileStation log processing and Excel export                      |
| `ranking_log.py`     | User activity statistics and ranking export                      |
| `date_picker.py`     | Custom date picker component                                     |
| `utils.py`           | Utility functions such as date formatting and window positioning |

---

## Error Handling

NASentinel provides built-in error handling for common operational issues:

* **Login failures:** Displays clear error messages for incorrect credentials, invalid OTP codes, insufficient permissions, and other authentication issues.
* **API connection failures:** Automatically retries failed API requests and notifies the user when a connection problem occurs.
* **Export errors:** Displays a notification when exported data is incomplete or contains formatting issues.

---

## Contact

**Author:** Hao-Wei Yu
**Email:** [haoweiyu0926@gmail.com](mailto:haoweiyu0926@gmail.com)

For questions, suggestions, or feedback, feel free to contact me.
