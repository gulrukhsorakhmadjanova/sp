import sys
import os
import subprocess
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QVBoxLayout, 
                            QWidget, QPushButton, QFileDialog, QHBoxLayout, 
                            QLabel, QMessageBox, QInputDialog, QPlainTextEdit,
                            QTabWidget, QComboBox, QCheckBox, QCalendarWidget,
                            QTimeEdit, QGroupBox, QFormLayout)
from PyQt5.Qsci import QsciScintilla, QsciLexerBash
from PyQt5.QtCore import QProcess, QTimer, QDateTime
from PyQt5.QtGui import QColor, QFont

class ShellScriptEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.process = None
        self.scheduled_tasks = []
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Shell Script Editor & System Maintenance')
        self.setGeometry(100, 100, 1000, 800)
        
        # Main widget with tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Tab 1: Shell Script Editor
        self.init_editor_tab()
        
        # Tab 2: System Maintenance
        self.init_maintenance_tab()
        
        # Status Bar
        self.statusBar().showMessage('Ready')
        
    def init_editor_tab(self):
        """Initialize the shell script editor tab"""
        editor_tab = QWidget()
        layout = QVBoxLayout()
        
        # File label
        self.file_label = QLabel("File: New File")
        layout.addWidget(self.file_label)
        
        # Editor with syntax highlighting
        self.editor = QsciScintilla()
        self.editor.setUtf8(True)
        lexer = QsciLexerBash()
        self.editor.setLexer(lexer)
        self.editor.setMarginLineNumbers(1, True)
        self.editor.setMarginWidth(1, "0000")
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QColor(240, 240, 240))
        
        # Output display
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("font-family: monospace; font-size: 12px;")
        
        # Input field and Send Input button
        input_group = QWidget()
        input_layout = QHBoxLayout()
        
        self.input_field = QPlainTextEdit()
        self.input_field.setMaximumHeight(80)
        self.input_field.setPlaceholderText("Enter input for the script here...")
        
        self.send_input_btn = QPushButton("Send Input")
        self.send_input_btn.clicked.connect(self.send_input)
        self.send_input_btn.setToolTip("Send input to the running script")
        self.send_input_btn.setEnabled(False)  # Disabled by default
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_input_btn)
        input_group.setLayout(input_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        editor_buttons = [
            ("New", self.new_file, "Create a new script"),
            ("Open", self.open_file, "Open an existing script"),
            ("Save", self.save_file, "Save current script"),
            ("Save As", self.save_file_as, "Save script with new name"),
            ("Run", self.run_script, "Execute the script"),
            ("Stop", self.stop_script, "Stop running script"),
            ("Clear", self.clear_output, "Clear output window")
        ]
        
        for text, handler, tooltip in editor_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            btn.setToolTip(tooltip)
            btn_layout.addWidget(btn)
        
        layout.addWidget(self.editor)
        layout.addWidget(QLabel("Output:"))
        layout.addWidget(self.output)
        layout.addWidget(QLabel("Input:"))
        layout.addWidget(input_group)
        layout.addLayout(btn_layout)
        
        editor_tab.setLayout(layout)
        self.tabs.addTab(editor_tab, "Shell Script Editor")
    
    def init_maintenance_tab(self):
        """Initialize the system maintenance tab"""
        maintenance_tab = QWidget()
        layout = QVBoxLayout()
        
        # Maintenance Tasks Group
        tasks_group = QGroupBox("Maintenance Tasks")
        tasks_layout = QFormLayout()
        
        self.maintenance_tasks = [
            ("Clear System Logs", "sudo rm -f /var/log/*.log", False),
            ("Clear Temp Files", "sudo rm -rf /tmp/*", False),
            ("Update Package List", "sudo apt update", False),
            ("Upgrade Packages", "sudo apt upgrade -y", False),
            ("Clean Package Cache", "sudo apt clean", False),
            ("Check Disk Space", "df -h", False)
        ]
        
        self.task_checkboxes = []
        for name, cmd, default in self.maintenance_tasks:
            cb = QCheckBox(name)
            cb.setChecked(default)
            cb.command = cmd  # Store the command with the checkbox
            tasks_layout.addRow(cb)
            self.task_checkboxes.append(cb)
        
        tasks_group.setLayout(tasks_layout)
        
        # Scheduling Group
        schedule_group = QGroupBox("Scheduling")
        schedule_layout = QFormLayout()
        
        # Date picker
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDateTime.currentDateTime().date())
        
        # Time picker
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QDateTime.currentDateTime().time())
        
        # Frequency selector
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Once", "Daily", "Weekly", "Monthly"])
        
        schedule_layout.addRow("Date:", self.calendar)
        schedule_layout.addRow("Time:", self.time_edit)
        schedule_layout.addRow("Frequency:", self.frequency_combo)
        
        schedule_group.setLayout(schedule_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        run_now_btn = QPushButton("Run Selected Tasks Now")
        run_now_btn.clicked.connect(self.run_maintenance_tasks)
        
        schedule_btn = QPushButton("Schedule Selected Tasks")
        schedule_btn.clicked.connect(self.schedule_tasks)
        
        view_schedule_btn = QPushButton("View Scheduled Tasks")
        view_schedule_btn.clicked.connect(self.view_scheduled_tasks)
        
        btn_layout.addWidget(run_now_btn)
        btn_layout.addWidget(schedule_btn)
        btn_layout.addWidget(view_schedule_btn)
        
        # Maintenance Output
        self.maintenance_output = QPlainTextEdit()
        self.maintenance_output.setReadOnly(True)
        self.maintenance_output.setStyleSheet("font-family: monospace; font-size: 12px;")
        
        layout.addWidget(tasks_group)
        layout.addWidget(schedule_group)
        layout.addLayout(btn_layout)
        layout.addWidget(QLabel("Maintenance Output:"))
        layout.addWidget(self.maintenance_output)
        
        maintenance_tab.setLayout(layout)
        self.tabs.addTab(maintenance_tab, "System Maintenance")
        
        # Timer for scheduled tasks
        self.task_timer = QTimer()
        self.task_timer.timeout.connect(self.check_scheduled_tasks)
        self.task_timer.start(60000)  # Check every minute
    
    # Shell Editor Functions
    def new_file(self):
        self.editor.clear()
        self.current_file = None
        self.file_label.setText("File: New File")
        self.output.clear()
        self.statusBar().showMessage("New file created")
    
    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Shell Scripts (*.sh);;All Files (*)")
        if filename:
            try:
                with open(filename, 'r') as f:
                    self.editor.setText(f.read())
                self.current_file = filename
                self.file_label.setText(f"File: {filename}")
                self.output.clear()
                self.statusBar().showMessage(f"Opened: {filename}")
            except Exception as e:
                self.show_error(f"Cannot open file: {str(e)}")
    
    def save_file(self):
        if self.current_file:
            try:
                with open(self.current_file, 'w') as f:
                    f.write(self.editor.text())
                self.show_info("File saved successfully")
                self.statusBar().showMessage(f"Saved: {self.current_file}")
            except Exception as e:
                self.show_error(f"Cannot save file: {str(e)}")
        else:
            self.save_file_as()
    
    def save_file_as(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Shell Scripts (*.sh);;All Files (*)")
        if filename:
            if not filename.endswith('.sh'):
                filename += '.sh'
            try:
                with open(filename, 'w') as f:
                    f.write(self.editor.text())
                self.current_file = filename
                self.file_label.setText(f"File: {filename}")
                self.show_info("File saved successfully")
                self.statusBar().showMessage(f"Saved as: {filename}")
            except Exception as e:
                self.show_error(f"Cannot save file: {str(e)}")
    
    def run_script(self):
        if not self.editor.text():
            self.show_warning("Editor is empty!")
            return
            
        script = self.editor.text()
        temp_file = "/tmp/temp_script.sh"
        
        try:
            with open(temp_file, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write(script)
            
            os.chmod(temp_file, 0o755)
            
            self.process = QProcess()
            self.process.setProcessChannelMode(QProcess.MergedChannels)
            self.process.readyReadStandardOutput.connect(self.handle_output)
            self.process.readyReadStandardError.connect(self.handle_error)
            self.process.finished.connect(self.script_finished)
            self.process.start("/bin/bash", [temp_file])
            
            self.output.clear()
            self.output.appendPlainText(f"Running script: {temp_file}\n{'='*40}\n")
            self.statusBar().showMessage("Script is running...")
            
            # Enable the Send Input button when script starts
            self.send_input_btn.setEnabled(True)
            
        except Exception as e:
            self.show_error(f"Cannot run script: {str(e)}")
    
    def stop_script(self):
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            self.output.appendPlainText("\nScript stopped by user")
            self.statusBar().showMessage("Script stopped")
            
            # Disable the Send Input button when script stops
            self.send_input_btn.setEnabled(False)
    
    def clear_output(self):
        self.output.clear()
        self.statusBar().showMessage("Output cleared")
    
    def send_input(self):
        if not self.process or self.process.state() != QProcess.Running:
            self.show_warning("No running process to send input to!")
            return
            
        input_text = self.input_field.toPlainText()
        if not input_text:
            self.show_warning("Input field is empty!")
            return
            
        # Add a newline if not already present
        if not input_text.endswith('\n'):
            input_text += '\n'
            
        self.process.write(input_text.encode())
        self.input_field.clear()
        self.output.appendPlainText(f"[INPUT SENT]: {input_text.strip()}\n")
        self.statusBar().showMessage("Input sent to script")
    
    def handle_output(self):
        if self.process:
            data = self.process.readAllStandardOutput().data().decode()
            self.output.appendPlainText(data)
    
    def handle_error(self):
        if self.process:
            data = self.process.readAllStandardError().data().decode()
            self.output.appendPlainText(f"[ERROR]: {data}")
    
    def script_finished(self):
        self.output.appendPlainText("\n" + "="*40 + "\nScript finished")
        self.statusBar().showMessage("Script finished")
        self.process = None
        
        # Disable the Send Input button when script finishes
        self.send_input_btn.setEnabled(False)
    
    # Maintenance Functions
    def run_maintenance_tasks(self):
        selected_tasks = [cb.command for cb in self.task_checkboxes if cb.isChecked()]
        
        if not selected_tasks:
            self.show_warning("No tasks selected!")
            return
            
        self.maintenance_output.clear()
        self.maintenance_output.appendPlainText("Starting maintenance tasks...\n" + "="*50)
        
        for task in selected_tasks:
            self.maintenance_output.appendPlainText(f"\nExecuting: {task}\n{'='*30}")
            
            try:
                process = subprocess.Popen(task, shell=True, 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE,
                                          text=True)
                
                stdout, stderr = process.communicate()
                
                if stdout:
                    self.maintenance_output.appendPlainText(stdout)
                if stderr:
                    self.maintenance_output.appendPlainText(f"[ERROR]: {stderr}")
                
                self.maintenance_output.appendPlainText(f"\nTask completed with exit code: {process.returncode}")
            
            except Exception as e:
                self.maintenance_output.appendPlainText(f"Failed to execute task: {str(e)}")
        
        self.maintenance_output.appendPlainText("\n" + "="*50 + "\nAll tasks completed")
        self.statusBar().showMessage("Maintenance tasks completed")
    
    def schedule_tasks(self):
        selected_tasks = [cb.command for cb in self.task_checkboxes if cb.isChecked()]
        
        if not selected_tasks:
            self.show_warning("No tasks selected for scheduling!")
            return
            
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        time = self.time_edit.time().toString("HH:mm")
        frequency = self.frequency_combo.currentText()
        
        task_id = len(self.scheduled_tasks) + 1
        scheduled_time = f"{date} {time}"
        
        task_info = {
            'id': task_id,
            'commands': selected_tasks,
            'scheduled_time': scheduled_time,
            'frequency': frequency,
            'executed': False
        }
        
        self.scheduled_tasks.append(task_info)
        
        message = f"Scheduled {len(selected_tasks)} task(s) for {scheduled_time} ({frequency})"
        self.show_info(message)
        self.statusBar().showMessage(message)
    
    def check_scheduled_tasks(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        for task in self.scheduled_tasks:
            if not task['executed'] and task['scheduled_time'] <= now:
                self.execute_scheduled_task(task)
                
                # Handle recurring tasks
                if task['frequency'] != "Once":
                    self.reschedule_task(task)
                else:
                    task['executed'] = True
    
    def execute_scheduled_task(self, task):
        self.maintenance_output.appendPlainText(f"\nExecuting scheduled task #{task['id']}...\n{'='*50}")
        
        for cmd in task['commands']:
            self.maintenance_output.appendPlainText(f"\nExecuting: {cmd}\n{'-'*30}")
            
            try:
                process = subprocess.Popen(cmd, shell=True, 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE,
                                          text=True)
                
                stdout, stderr = process.communicate()
                
                if stdout:
                    self.maintenance_output.appendPlainText(stdout)
                if stderr:
                    self.maintenance_output.appendPlainText(f"[ERROR]: {stderr}")
                
                self.maintenance_output.appendPlainText(f"\nTask completed with exit code: {process.returncode}")
            
            except Exception as e:
                self.maintenance_output.appendPlainText(f"Failed to execute task: {str(e)}")
        
        self.maintenance_output.appendPlainText("\n" + "="*50 + "\nScheduled task completed")
        self.statusBar().showMessage(f"Completed scheduled task #{task['id']}")
    
    def reschedule_task(self, task):
        current_time = datetime.strptime(task['scheduled_time'], "%Y-%m-%d %H:%M")
        
        if task['frequency'] == "Daily":
            new_time = current_time + timedelta(days=1)
        elif task['frequency'] == "Weekly":
            new_time = current_time + timedelta(weeks=1)
        elif task['frequency'] == "Monthly":
            # Approximate month as 30 days
            new_time = current_time + timedelta(days=30)
        
        task['scheduled_time'] = new_time.strftime("%Y-%m-%d %H:%M")
        task['executed'] = False
    
    def view_scheduled_tasks(self):
        if not self.scheduled_tasks:
            self.show_info("No tasks scheduled")
            return
            
        message = "Scheduled Tasks:\n\n"
        for task in self.scheduled_tasks:
            status = "Executed" if task['executed'] else "Pending"
            message += (f"Task #{task['id']} ({task['frequency']}):\n"
                       f"Time: {task['scheduled_time']}\n"
                       f"Status: {status}\n"
                       f"Commands: {len(task['commands'])}\n\n")
        
        self.show_info(message)
    
    # Utility Functions
    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
    
    def show_warning(self, message):
        QMessageBox.warning(self, "Warning", message)
    
    def show_info(self, message):
        QMessageBox.information(self, "Information", message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application font for better readability
    font = QFont()
    font.setFamily("Arial")
    font.setPointSize(10)
    app.setFont(font)
    
    editor = ShellScriptEditor()
    editor.show()
    sys.exit(app.exec_())
