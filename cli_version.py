import os
from send2trash import send2trash
import logging
from datetime import datetime
import smtplib
from email.message import EmailMessage
import time

# Setup logging
log_file = 'activity.log'
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Hardcoded sender credentials
SENDER_EMAIL = 'yashodeephundiwale@gmail.com'
SENDER_PASSWORD = 'ywjzqxesbrfsujor'  # Use app password

def send_log_email(recipient_email, log_file_path, stats):
    msg = EmailMessage()
    msg['Subject'] = 'FolderFresh - Deleted Files Log & Report'
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    email_body = f'''
Hello,

Thank you for using FolderFresh! 😊

Here is your cleanup report:

- Total files deleted: {stats["files_deleted"]}
- Total size freed: {stats["size_freed"] / (1024*1024):.2f} MB

Please find attached the log file containing the list of deleted files.

Have a great day!
FolderFresh Bot 🤖
'''
    msg.set_content(email_body)

    with open(log_file_path, 'rb') as file:
        msg.add_attachment(file.read(), maintype='text', subtype='plain', filename='activity.log')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

    print("✅ Log file and report emailed successfully.")

def clean_folders_with_individual_ext():
    num_folders = int(input("How many folders do you want to clean? "))
    files_deleted = 0
    size_freed = 0
    start_time = time.time()

    for i in range(num_folders):
        folder_path = input(f"\nEnter path for folder #{i+1}: ").strip()
        if not os.path.isdir(folder_path):
            print(f"❌ Folder not found or invalid: {folder_path}")
            continue

        ext_input = input(f"Enter extensions to keep for folder #{i+1} (comma-separated, e.g. .pdf,.png): ")
        extensions_to_keep = [
            ext.strip().lower() if ext.strip().startswith('.') else '.' + ext.strip().lower()
            for ext in ext_input.split(',')
        ]

        print(f"🗂️ Cleaning folder: {folder_path} with keep extensions: {extensions_to_keep}")

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            _, ext = os.path.splitext(filename)
            if os.path.isfile(file_path) and ext.lower() not in extensions_to_keep:
                try:
                    file_size = os.path.getsize(file_path)
                    send2trash(file_path)
                    print(f"Sent to Trash: {filename}")
                    logging.info(f"Sent to Trash: {filename}")
                    files_deleted += 1
                    size_freed += file_size
                except Exception as e:
                    print(f"Failed to delete {filename}: {e}")

    time_taken = time.time() - start_time

    # After finishing all deletions
    print(f"\n✅ Done! Deleted unwanted {files_deleted} files, freed {size_freed / (1024*1024):.2f} MB.")

    print(" Deleted files are logged in 'activity.log'")

    send_email_choice = input("\nDo you want to receive the log file and report by email? (yes/no): ").strip().lower()

    if send_email_choice == 'yes':
        recipient_email = input("📧 Enter your email address to receive the log: ").strip()
        stats = {
            "files_deleted": files_deleted,
            "size_freed": size_freed,
            "time_taken": time_taken
        }
        try:
            send_log_email(recipient_email, log_file, stats)
        except Exception as e:
            print("❌ Failed to send email:", e)

if __name__ == "__main__":
    clean_folders_with_individual_ext()
