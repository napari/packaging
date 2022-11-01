"""Constructor manager main interface."""

import sys

from qtpy.QtCore import (
    QEvent,
    QObject,
    QPoint,
    QProcess,
    QProcessEnvironment,
    QSize,
    Qt,
    Signal,
    Slot,
)
from qtpy.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTableWidget
)

from superqt import QCollapsible, QElidingLabel

class Dialog(QDialog):

    def __init__(self, parent=None):
        super().__init__()

        self.setup_ui()

        self.show()


    def setup_ui(self):
        self.resize(1080, 640)
        vlay_1 = QVBoxLayout(self)
        self.h_splitter = QSplitter(self)
        vlay_1.addWidget(self.h_splitter)
        self.h_splitter.setOrientation(Qt.Orientation.Horizontal)
        self.v_splitter = QSplitter(self.h_splitter)
        self.v_splitter.setOrientation(Qt.Orientation.Vertical)
        self.v_splitter.setMinimumWidth(500)

        installed = QWidget(self.v_splitter)
        lay = QVBoxLayout(installed)
        lay.setContentsMargins(0, 2, 0, 2)
        
        self.packages_filter = QLineEdit()
        self.packages_filter.setPlaceholderText(trans._("filter..."))
        self.packages_filter.setMaximumWidth(350)
        self.packages_filter.setClearButtonEnabled(True)
        top_lay = QHBoxLayout()
        top_lay.addWidget(self.packages_filter)
        install_napari_label = QLabel(trans._('Install napari version: '))
        self.napari_version_dropdown = QComboBox()
        self.install_btn = QPushButton('Install', self)
        top_lay.addWidget(install_napari_label)
        top_lay.addWidget(self.napari_version_dropdown)
        top_lay.addWidget(self.install_btn)

        lay.addLayout(top_lay)

        self.napari_list = QPNapariList(installed, self.installer)
        self.packages_filter.textChanged.connect(self.napari_list.filter)
        lay.addWidget(self.napari_list)

        buttonBox = QHBoxLayout()
        self.working_indicator = QLabel(trans._("loading ..."), self)
        sp = self.working_indicator.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.working_indicator.setSizePolicy(sp)
        self.process_error_indicator = QLabel(self)
        self.process_error_indicator.setObjectName("error_label")
        self.process_error_indicator.hide()
        load_gif = str(Path(napari.resources.__file__).parent / "loading.gif")
        mov = QMovie(load_gif)
        mov.setScaledSize(QSize(18, 18))
        self.working_indicator.setMovie(mov)
        mov.start()

       
        self.pref_button = QPushButton(trans._("Open Install Preferences"), self)
        self.pref_button.clicked.connect(self._open_preferences)

        self.show_status_btn = QPushButton(trans._("Show Status"), self)
        self.show_status_btn.setFixedWidth(100)


        self.close_btn = QPushButton(trans._("Close"), self)
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setObjectName("close_button")
        buttonBox.addWidget(self.show_status_btn)
        buttonBox.addWidget(self.pref_button)
        buttonBox.addSpacing(20)
        buttonBox.addSpacing(20)
        buttonBox.addWidget(self.close_btn)
        buttonBox.setContentsMargins(0, 0, 4, 0)
        vlay_1.addLayout(buttonBox)

        self.show_status_btn.setCheckable(True)
        self.show_status_btn.setChecked(False)
        self.show_status_btn.toggled.connect(self._toggle_status)

        self.v_splitter.setStretchFactor(1, 2)
        self.h_splitter.setStretchFactor(0, 2)

        self.packages_filter.setFocus()

    def _open_preferences(self):
        print('open preferences')

class QPNapariList(QListWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        # self.installer = installer
        

    # @Slot()
    # def addItem(
    #     self,
    #     project_info_versions: Tuple[PackageMetadata, list, list],
    #     installed=False,
    #     plugin_name=None,
    #     enabled=True,
    #     npe_version=1,
    # ):

        # pkg_name = project_info.name
        # # don't add duplicates
        # if (
        #     self.findItems(pkg_name, Qt.MatchFlag.MatchFixedString)
        #     and not plugin_name
        # ):
        #     return

        # # including summary here for sake of filtering below.
        # searchable_text = f"{pkg_name} {project_info.summary}"
        # item = QListWidgetItem(searchable_text, self)
        # # item.version = project_info.version
        # super().addItem(item)
        # widg = NapariListItem(
        #     version = '0.0'
        # )
        # item.widget = widg
        # action_name = 'uninstall' if installed else 'install'
        # item.setSizeHint(widg.sizeHint())
        # self.setItemWidget(item, widg)

        # if project_info.home_page:
        #     import webbrowser

        #     widg.help_button.clicked.connect(
        #         lambda: webbrowser.open(project_info.home_page)
        #     )
        # else:
        #     widg.help_button.setVisible(False)

        # widg.action_button.clicked.connect(
        #     lambda: self.handle_action(
        #         item,
        #         pkg_name,
        #         action_name,
        #         version=widg.version_choice_dropdown.currentText(),
        #         installer_choice=widg.source_choice_dropdown.currentText(),
        #     )
        # )

        # widg.update_btn.clicked.connect(
        #     lambda: self.handle_action(
        #         item,
        #         pkg_name,
        #         "install",
        #         update=True,
        #     )
        # )
        # widg.cancel_btn.clicked.connect(
        #     lambda: self.handle_action(item, pkg_name, "cancel")
        # )

        # item.setSizeHint(widg.sizeHint())
        # self.setItemWidget(item, widg)
        # widg.install_info_button.setDuration(0)
        # widg.install_info_button.toggled.connect(
        #     lambda: self._resize_pluginlistitem(item)
        # )

class NapariListItem(QFrame):
    def __init__(
        self,
        version: str = None,
    ):
        super().__init__(parent)

        star_icon = QLabel(self)
        icon = QColoredSVGIcon.from_resources('star')
        star_icon.setPixmap(
            icon.colored(color='#33F0FF', opacity=opacity).pixmap(20, 20)
        )
        star_icon.hide()
        layout = QHBoxLayout()
        layout.addWidget(star_icon)
        napari_version_text = QLabel('napari v?')
        layout.addWidget(napari_version_text)

        more_info_tab = QCollapsible("More information")
        layout.addWidget(more_info_tab)

        running_icon = QLabel(self)
        icon = QColoredSVGIcon.from_resources('running')
        running_icon.setPixmap(
            icon.colored(color='#33F0FF', opacity=opacity).pixmap(20, 20)
        )
        running_icon.hide()
        running_label = QLabel(trans._('Running'))
        action_btn = QPushButton('Open')

        layout.addWidget(running_icon)
        layout.addWidget(running_label)
        layout.addWidget(action_btn)
        running_icon.hide()
        running_label.hide()

        self.get_info_widget()

        self.more_info_tab.addWidget(self.info_widget)

    def get_info_widget(self):

        self._info_table = QTableWidget()
        self._info_table.setShowGrid(False)

        #fill out the table with the first column being "plugins, other packages, etc"
        # make 2 other tables for plugins



def main(package_name):
    """Run the main interface.

    Parameters
    ----------
    package_name : str
        Name of the package that the installation manager is handling.
    """
    app = QApplication([])
    dialog = Dialog()
    dialog.setWindowTitle(f"{package_name} installation manager")
    sys.exit(app.exec_())
