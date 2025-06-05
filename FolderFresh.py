import sys
import os
import logging
import smtplib
import matplotlib.pyplot as plt
from email.message import EmailMessage
from send2trash import send2trash
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QFileDialog, QHBoxLayout, QTextEdit, QLineEdit,
    QMessageBox, QCheckBox, QListWidgetItem, QInputDialog
)
from PyQt6.QtCore import Qt

# Set up logging
LOG_FILE = "folderfresh_log.txt"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

class FolderFreshApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧹 FolderFresh")
        self.setGeometry(100, 100, 700, 500)
        self.setAcceptDrops(True)

        self.folder_extensions = {}  # folder_path -> extensions list
        self.deletion_stats = {}  # folder_path -> (file count, total size)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.instruction = QLabel("Drag and drop folders below or click 'Add Folder'.")
        layout.addWidget(self.instruction)

        self.folder_list = QListWidget()
        layout.addWidget(self.folder_list)

        btn_layout = QHBoxLayout()

        self.add_folder_btn = QPushButton("+ Add Folder")
        self.add_folder_btn.clicked.connect(self.add_folder)
        btn_layout.addWidget(self.add_folder_btn)

        self.preview_btn = QPushButton("👁 Preview")
        self.preview_btn.clicked.connect(self.preview_cleanup)
        btn_layout.addWidget(self.preview_btn)

        self.clean_btn = QPushButton("🗑 Clean")
        self.clean_btn.clicked.connect(self.perform_cleanup)
        btn_layout.addWidget(self.clean_btn)

        layout.addLayout(btn_layout)

        self.email_checkbox = QCheckBox("Email me the report (with chart)")
        layout.addWidget(self.email_checkbox)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        layout.addWidget(self.email_input)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self.add_folder_item(path)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.add_folder_item(folder)

    def add_folder_item(self, folder_path):
        if folder_path not in self.folder_extensions:
            text, ok = QInputDialog.getText(self, "Extensions", f"Enter extensions to keep for:\n{folder_path}\n(e.g. .pdf,.png)")
            if ok:
                exts = [e.strip().lower() if e.strip().startswith('.') else '.' + e.strip().lower() for e in text.split(',')]
                self.folder_extensions[folder_path] = exts
                item = QListWidgetItem(folder_path)
                self.folder_list.addItem(item)

    def preview_cleanup(self):
        self.log_output.clear()
        self.log_output.append("🔍 Preview Mode: Files that would be deleted")
        for folder, keep_exts in self.folder_extensions.items():
            self.log_output.append(f"\n📁 Folder: {folder}")
            for file in os.listdir(folder):
                full_path = os.path.join(folder, file)
                _, ext = os.path.splitext(file)
                if os.path.isfile(full_path) and ext.lower() not in keep_exts:
                    self.log_output.append(f" - {file}")

    def perform_cleanup(self):
        self.log_output.clear()
        self.deletion_stats.clear()
        total_deleted = 0
        total_size = 0

        with open(LOG_FILE, 'w') as log_file:
            log_file.write("FolderFresh Deletion Log\n")
            log_file.write("="*40 + "\n")

            for folder, keep_exts in self.folder_extensions.items():
                deleted = 0
                size_freed = 0
                for file in os.listdir(folder):
                    full_path = os.path.normpath(os.path.join(folder, file))
                    _, ext = os.path.splitext(file)
                    if os.path.isfile(full_path) and ext.lower() not in keep_exts:
                        file_size = os.path.getsize(full_path)
                        if os.path.exists(full_path):
                            try:
                                send2trash(full_path)
                                log_file.write(f"Deleted: {full_path}\n")
                                deleted += 1
                                size_freed += file_size
                            except Exception as e:
                                logging.warning(f"Failed to delete {full_path}: {e}")
                        else:
                            logging.warning(f"File not found when trying to delete: {full_path}")
                self.deletion_stats[folder] = (deleted, size_freed)
                total_deleted += deleted
                total_size += size_freed

        self.log_output.append(f"✅ Done! Deleted unwanted {total_deleted} files, freed {total_size / (1024*1024):.2f} MB")

        if self.email_checkbox.isChecked():
            receiver = self.email_input.text().strip()
            if receiver:
                self.send_email(receiver)
            else:
                QMessageBox.warning(self, "Email Error", "Please enter a valid email address.")

    def send_email(self, receiver):
        try:
            self.create_chart()
            msg = EmailMessage()
            msg['Subject'] = "🧹 FolderFresh Cleanup Report"
            msg['From'] = "yashodeephundiwale@gmail.com"  # Replace with your sender email
            msg['To'] = receiver

            body = f"""
Hello,

Thank you for using FolderFresh! 😊

Here is your cleanup report:

"""
            for folder, (count, size) in self.deletion_stats.items():
                body += f"📁 {folder}: {count} files deleted, {size / (1024*1024):.2f} MB freed\n"

            body += "\nPlease find the attached log file and cleanup chart.\n\n– FolderFresh Bot 🤖"
            msg.set_content(body)

            with open(LOG_FILE, 'rb') as f:
                msg.add_attachment(f.read(), maintype='text', subtype='plain', filename=LOG_FILE)

            with open("chart.png", 'rb') as f:
                msg.add_attachment(f.read(), maintype='image', subtype='png', filename="chart.png")

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login("yashodeephundiwale@gmail.com", "ywjzqxesbrfsujor")  # Hardcoded sender credentials
                smtp.send_message(msg)
                QMessageBox.information(self, "Email Sent", "Report emailed successfully!")

        except Exception as e:
            QMessageBox.warning(self, "Email Failed", f"Could not send email: {e}")

    def create_chart(self):
        folders = list(self.deletion_stats.keys())
        sizes = [s[1]/(1024*1024) for s in self.deletion_stats.values()]

        plt.figure(figsize=(8, 4))
        plt.barh(folders, sizes, color='skyblue')
        plt.xlabel('MB Freed')
        plt.title('FolderFresh Cleanup Report')
        plt.tight_layout()
        plt.savefig("chart.png")
        plt.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FolderFreshApp()
    window.show()
    sys.exit(app.exec())
