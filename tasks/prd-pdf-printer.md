# Product Requirements Document: PDF Printer Web App

## 1. Introduction/Overview

This feature introduces a web-based PDF printing service for the Raspberry Pi server. Users on the local area network can access a simple web interface to upload PDF files and send them to the network printer via the CUPS print server. This eliminates the need for users to install printer drivers on their devices and provides a centralized printing solution accessible from any device with a web browser.

**Problem it solves:** Provides easy printing access for employees and guests on the local network without requiring printer driver installation or complex configuration on individual devices.

**Goal:** Create a user-friendly web interface at `http://printerpi.local/print` that allows anyone on the local network to upload and print PDF files with basic print options.

## 2. Goals

1. Enable easy PDF printing from any device on the local network
2. Provide visibility into print queue status (pending, completed, failed)
3. Allow users to manage print jobs (cancel pending jobs)
4. Support multiple file uploads with configurable print options
5. Maintain a 7-day history of printed files for reference
6. Ensure reliable file handling with appropriate size limits (20 MB)

## 3. User Stories

1. **As an employee**, I want to upload a PDF from my phone and print it to the office printer, so that I don't need to email files to myself or use a computer.

2. **As a guest**, I want to print a document without installing printer drivers, so that I can quickly print what I need without technical assistance.

3. **As a user**, I want to see the status of my print job (queued, printing, completed), so that I know when to collect my document from the printer.

4. **As a user**, I want to print multiple copies of a document and use duplex printing, so that I can save paper when printing multi-page documents.

5. **As a user**, I want to cancel a print job I submitted by mistake, so that I don't waste paper and ink.

6. **As a user**, I want to see what documents were recently printed, so that I can verify my print job was successful or reprint if needed.

## 4. Functional Requirements

### 4.1 File Upload
1. The system must provide a web interface accessible at `http://printerpi.local/print`
2. The system must allow users to select and upload multiple PDF files simultaneously
3. The system must enforce a maximum file size limit of 20 MB per file
4. The system must only accept PDF file types (reject other formats with clear error message)
5. The system must store all uploaded files in `/home/aoi/print` directory
6. The system must display upload progress for each file
7. The system must validate files are not corrupted before accepting them

### 4.2 Print Options
8. The system must allow users to specify the number of copies (1-10) for each print job
9. The system must provide a duplex/double-sided printing option
10. The system must set reasonable defaults (1 copy, simplex) if options are not specified
11. The system must pass these options to the `lp` command correctly

### 4.3 Print Job Management
12. The system must submit print jobs to CUPS using the `lp filename.pdf` command
13. The system must capture and display the job ID returned by CUPS
14. The system must query CUPS to determine print job status (pending, processing, completed, failed)
15. The system must display real-time status updates for submitted jobs
16. The system must allow users to cancel pending print jobs
17. The system must handle CUPS errors gracefully and display user-friendly error messages

### 4.4 Queue Viewing
18. The system must display a list of all pending print jobs with: filename, job ID, copies, duplex setting, status
19. The system must refresh the queue status automatically (every 5-10 seconds)
20. The system must display the current user's jobs prominently
21. The system must show all users' jobs in the queue (since there's no authentication)

### 4.5 Print History
22. The system must maintain a history of printed documents for 7 days
23. The system must display print history with: filename, print date/time, status (success/failed), job ID
24. The system must automatically delete files and records older than 7 days
25. The system must allow users to reprint documents from history

### 4.6 User Interface
26. The system must have a clean, responsive interface that works on mobile and desktop browsers
27. The system must display clear success/error messages for all user actions
28. The system must show the server hostname (printerpi.local) in the interface
29. The system must have sections for: Upload, Current Queue, and History

### 4.7 Error Handling
30. The system must handle cases where CUPS is unavailable or printer is offline
31. The system must handle disk space issues when storing uploaded files
32. The system must handle invalid or corrupted PDF files gracefully
33. The system must log errors for debugging purposes

## 5. Non-Goals (Out of Scope)

1. **Authentication/Authorization**: No user accounts or login system (open access on local network)
2. **Non-PDF file types**: Only PDF files are supported; no Word, images, or other formats
3. **Advanced print settings**: Color vs B&W, page range selection, paper size/tray selection
4. **Remote access**: Not accessible from outside the local network
5. **Mobile apps**: Web interface only, no native mobile applications
6. **Printer management**: No ability to add/remove/configure printers through the interface
7. **File preview**: No PDF preview before printing
8. **File editing**: No ability to modify PDF content
9. **Cloud integration**: No integration with Google Drive, Dropbox, etc.
10. **Email notifications**: No email alerts when print jobs complete

## 6. Design Considerations

### 6.1 User Interface Layout
- **Header**: Display "Acres of ice- Network Printer" with current printer status indicator
- **Upload Section**: Drag-and-drop zone with file selector button, print options (copies, duplex), and submit button
- **Current Queue Section**: Live-updating table of pending/active jobs with cancel buttons
- **History Section**: Collapsible table of recent print jobs (last 7 days) with reprint buttons

### 6.2 Visual Feedback
- Use color coding for status: Green (completed), Yellow (pending), Blue (processing), Red (failed)
- Show spinning indicator during file upload and job submission
- Display toast notifications for success/error messages
- Use icons for actions (upload, cancel, reprint, delete)

### 6.3 Responsive Design
- Mobile-first approach with touch-friendly buttons
- Single-column layout on mobile, multi-column on desktop
- Ensure upload button is large and easily tappable on mobile devices

## 7. Technical Considerations

### 7.1 Technology Stack
- **Backend**: Python with Flask framework
- **Frontend**: HTML5, CSS3, JavaScript (vanilla or lightweight framework)
- **Print Server**: CUPS (Common Unix Printing System)
- **File Storage**: Local filesystem at `/home/aoi/print`

### 7.2 Backend Implementation
- Use Flask for web server and routing
- Use subprocess module to execute `lp` command and query CUPS
- Use `lpstat` or `lpq` commands to query job status
- Implement file cleanup as a background task or cron job
- Use Flask's file upload handling with size validation

### 7.3 CUPS Integration
- Command to print: `lp -n <copies> -o sides=<one-sided|two-sided-long-edge> <filename>`
- Command to check status: `lpstat -o` or `lpstat -W completed` for history
- Command to cancel job: `cancel <job-id>`
- Parse CUPS command output to extract job IDs and status

### 7.4 File Management
- Create `/home/aoi/print` directory with appropriate permissions
- Implement daily cleanup job to remove files older than 7 days
- Store metadata (upload time, print status, options) in a simple database (SQLite) or JSON file

### 7.5 Network Configuration
- Application must listen on all interfaces (0.0.0.0) to be accessible via `printerpi.local`
- Use port 80 (requires root/sudo) or configure reverse proxy (nginx/apache)
- If using port 80, URL will be `http://printerpi.local/print`
- If using another port (e.g., 5000), URL will be `http://printerpi.local:5000/print`

### 7.6 Security Considerations (Even Without Auth)
- Validate all uploaded files are valid PDFs
- Sanitize filenames to prevent path traversal attacks
- Rate limit uploads to prevent abuse
- Consider IP-based access restrictions if needed
- Set appropriate file permissions on upload directory

## 8. Success Metrics

1. **Adoption Rate**: 80% of local network users successfully print at least one document within first month
2. **Reliability**: 95% of submitted print jobs complete successfully
3. **User Experience**: Average time from file upload to print completion under 30 seconds
4. **Error Rate**: Less than 5% of uploads result in errors
5. **System Uptime**: Web service available 99% of the time

## 9. Open Questions

1. **Printer Selection**: If multiple printers are configured in CUPS, should users be able to select which printer to use, or always use the default?

2. **File Naming**: Should uploaded files be renamed to avoid conflicts (e.g., append timestamp), or keep original names?

3. **Session Management**: Without authentication, how do we track "my jobs" vs "all jobs"? Use browser cookies/sessions?

4. **Deployment**: Should the app run as a systemd service? What user should it run as?

5. **Reverse Proxy**: Should we use nginx/apache as a reverse proxy for production, or run Flask directly?

6. **HTTPS**: Should we set up HTTPS even for local network access?

7. **Backup**: Should print history and metadata be backed up? Where?

8. **Logging**: What level of logging is needed? Where should logs be stored?

---

## Appendix: Example User Flow

1. User opens `http://printerpi.local/print` in their browser
2. User clicks "Select Files" or drags PDFs into the upload zone
3. User selects 2 PDF files (3 MB and 5 MB)
4. User sets copies to "2" and enables "Duplex"
5. User clicks "Print"
6. System uploads files, shows progress bar
7. System submits jobs to CUPS and displays "Print jobs submitted: #101, #102"
8. Queue section shows both jobs as "Pending"
9. Status updates to "Printing" then "Completed"
10. User collects printouts from printer
11. Files remain in history for 7 days for potential reprint
