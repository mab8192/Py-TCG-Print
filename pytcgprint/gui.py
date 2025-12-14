import sys
from pathlib import Path
from math import ceil
from io import BytesIO
from PIL import Image
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QSpinBox, QDoubleSpinBox,
    QMessageBox, QProgressBar, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QPixmap, QIcon, QImage, QDesktopServices
from PyQt6.QtCore import QThread, pyqtSignal, QSize, QUrl

from pytcgprint.core import Settings, get_image_files, calculate_layout, create_page

class GenerateThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        try:
            image_files = get_image_files(self.settings)
            layout = calculate_layout(self.settings)
            total_images = len(image_files)
            cpp = layout['cards_per_page']
            total_pages = ceil(total_images / cpp)
            pages = []

            for i in range(total_pages):
                start = i * cpp
                end = start + cpp
                batch = image_files[start:end]
                page_img = create_page(batch, layout)
                pages.append(page_img)
                self.progress.emit(int((i + 1) / total_pages * 100))

            self.finished.emit(pages)
        except Exception as e:
            self.error.emit(str(e))

class PreviewThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, input_dir):
        super().__init__()
        self.input_dir = input_dir

    def run(self):
        try:
            temp_settings = Settings(
                input_dir=self.input_dir,
                output_file="",
                page_width=8.5,
                page_height=11.0,
                card_width=2.5,
                card_height=3.5,
                margin=0.5,
                scale=1.0,
                rows=0,
                cols=0,
                dpi=300
            )

            image_files = get_image_files(temp_settings)
            thumbnails = []

            for img_path in image_files:
                try:
                    with Image.open(img_path) as img:
                        img = img.convert("RGB")
                        img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                        thumbnails.append(img.copy())  # copy to keep after close
                except Exception as e:
                    print(f"Warning: Could not load thumbnail for {img_path.name}: {e}")

            self.finished.emit(thumbnails)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.preview_thread = None
        self.generate_thread = None
        self.setWindowTitle("PyTCG Print")
        self.setGeometry(100, 100, 500, 600)

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # Input directory
        self.input_edit = QLineEdit("cards")
        self.input_edit.textChanged.connect(self.load_preview)
        self.input_btn = QPushButton("Browse...")
        self.input_btn.clicked.connect(self.browse_input)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.input_btn)
        form_layout.addRow("Input Directory:", input_layout)

        # Output file
        self.output_edit = QLineEdit("output_deck.pdf")
        self.output_btn = QPushButton("Browse...")
        self.output_btn.clicked.connect(self.browse_output)
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.output_btn)
        form_layout.addRow("Output File:", output_layout)

        # Page dimensions
        self.page_width_edit = QDoubleSpinBox()
        self.page_width_edit.setRange(1, 50)
        self.page_width_edit.setValue(8.5)
        self.page_height_edit = QDoubleSpinBox()
        self.page_height_edit.setRange(1, 50)
        self.page_height_edit.setValue(11.0)
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("Width:"))
        page_layout.addWidget(self.page_width_edit)
        page_layout.addWidget(QLabel("Height:"))
        page_layout.addWidget(self.page_height_edit)
        form_layout.addRow("Page Size (inches):", page_layout)

        # Card dimensions
        self.card_width_edit = QDoubleSpinBox()
        self.card_width_edit.setRange(0.1, 10)
        self.card_width_edit.setValue(2.5)
        self.card_height_edit = QDoubleSpinBox()
        self.card_height_edit.setRange(0.1, 10)
        self.card_height_edit.setValue(3.5)
        card_layout = QHBoxLayout()
        card_layout.addWidget(QLabel("Width:"))
        card_layout.addWidget(self.card_width_edit)
        card_layout.addWidget(QLabel("Height:"))
        card_layout.addWidget(self.card_height_edit)
        form_layout.addRow("Card Size (inches):", card_layout)

        # Margin
        self.margin_edit = QDoubleSpinBox()
        self.margin_edit.setRange(0, 5)
        self.margin_edit.setValue(0.5)
        form_layout.addRow("Margin (inches):", self.margin_edit)

        # Scale
        self.scale_edit = QDoubleSpinBox()
        self.scale_edit.setRange(0.1, 2.0)
        self.scale_edit.setValue(0.98)
        self.scale_edit.setSingleStep(0.01)
        form_layout.addRow("Scale:", self.scale_edit)

        # Rows and Cols
        self.rows_edit = QSpinBox()
        self.rows_edit.setRange(0, 100)
        self.rows_edit.setValue(0)
        self.cols_edit = QSpinBox()
        self.cols_edit.setRange(0, 100)
        self.cols_edit.setValue(0)
        grid_layout = QHBoxLayout()
        grid_layout.addWidget(QLabel("Rows:"))
        grid_layout.addWidget(self.rows_edit)
        grid_layout.addWidget(QLabel("Cols:"))
        grid_layout.addWidget(self.cols_edit)
        form_layout.addRow("Grid (0=auto):", grid_layout)

        # DPI
        self.dpi_edit = QSpinBox()
        self.dpi_edit.setRange(72, 1200)
        self.dpi_edit.setValue(300)
        form_layout.addRow("DPI:", self.dpi_edit)

        layout.addLayout(form_layout)

        # Preview section
        preview_header = QHBoxLayout()
        preview_header.addWidget(QLabel("Card Preview:"))
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_preview)
        preview_header.addWidget(self.refresh_btn)
        preview_header.addStretch()
        layout.addLayout(preview_header)
        self.loading_label = QLabel("")
        layout.addWidget(self.loading_label)
        self.preview_list = QListWidget()
        self.preview_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.preview_list.setIconSize(QSize(150, 150))
        self.preview_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.preview_list.setDragEnabled(False)
        layout.addWidget(self.preview_list)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Generate button
        self.generate_btn = QPushButton("Generate PDF")
        self.generate_btn.clicked.connect(self.generate_pdf)
        layout.addWidget(self.generate_btn)

        self.setLayout(layout)

        self.load_preview()

        self.load_preview()

    def browse_input(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if folder:
            self.input_edit.setText(folder)

    def browse_output(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if file:
            self.output_edit.setText(file)

    def generate_pdf(self):
        try:
            settings = Settings(
                input_dir=self.input_edit.text(),
                output_file=self.output_edit.text(),
                page_width=self.page_width_edit.value(),
                page_height=self.page_height_edit.value(),
                card_width=self.card_width_edit.value(),
                card_height=self.card_height_edit.value(),
                margin=self.margin_edit.value(),
                scale=self.scale_edit.value(),
                rows=self.rows_edit.value(),
                cols=self.cols_edit.value(),
                dpi=self.dpi_edit.value()
            )

            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.generate_btn.setEnabled(False)

            self.generate_thread = GenerateThread(settings)
            self.generate_thread.progress.connect(self.progress_bar.setValue)
            self.generate_thread.finished.connect(self.on_generation_finished)
            self.generate_thread.error.connect(self.on_generation_error)
            self.generate_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def on_generation_finished(self, pages):
        if pages:
            output_path = Path(self.generate_thread.settings.output_file)
            if output_path.exists():
                msg = QMessageBox(self)
                msg.setWindowTitle("Success")
                msg.setText(f"PDF saved to {output_path.absolute()}")
                open_btn = msg.addButton("Open PDF", QMessageBox.ButtonRole.ActionRole)
                msg.addButton(QMessageBox.StandardButton.Ok)
                msg.exec()
                if msg.clickedButton() == open_btn:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_path)))
            else:
                QMessageBox.warning(self, "Warning", "PDF generation completed but output file not found.")
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)

    def on_generation_error(self, error_msg):
        QMessageBox.critical(self, "Error", error_msg)
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)

    def on_preview_finished(self, thumbnails):
        for img in thumbnails:
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            image = QImage()
            image.loadFromData(buffer.read(), "PNG")
            pixmap = QPixmap.fromImage(image)

            item = QListWidgetItem()
            item.setIcon(QIcon(pixmap))
            self.preview_list.addItem(item)
        self.loading_label.setText("")

    def on_preview_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"Failed to load preview: {error_msg}")
        self.loading_label.setText("")

    def closeEvent(self, event):
        if self.preview_thread and self.preview_thread.isRunning():
            self.preview_thread.wait()
        if self.generate_thread and self.generate_thread.isRunning():
            self.generate_thread.wait()
        event.accept()

    def load_preview(self):
        input_dir = self.input_edit.text()
        if not input_dir:
            self.preview_list.clear()
            return

        if self.preview_thread and self.preview_thread.isRunning():
            return

        self.preview_list.clear()
        self.preview_thread = PreviewThread(input_dir)
        self.preview_thread.finished.connect(self.on_preview_finished)
        self.preview_thread.error.connect(self.on_preview_error)
        self.preview_thread.start()
        self.loading_label.setText("Loading preview...")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
