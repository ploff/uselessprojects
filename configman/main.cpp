#include <QApplication>
#include <QWidget>
#include <QPushButton>
#include <QFileDialog>
#include <QMessageBox>
#include <QProcess>
#include <QVBoxLayout>
#include <QListWidget>
#include <QStandardPaths>
#include <QTextStream>
#include <QSettings>
#include <QDebug>

class AutoRunApp : public QWidget {
public:
    AutoRunApp(QWidget *parent = nullptr) : QWidget(parent) {
        QVBoxLayout *layout = new QVBoxLayout(this);

        autorunButton = new QPushButton("Add to Autorun", this);
        layout->addWidget(autorunButton);

        autorunList = new QListWidget(this);
        layout->addWidget(autorunList);

        removeButton = new QPushButton("Remove from Autorun", this);
        layout->addWidget(removeButton);

        connect(autorunButton, &QPushButton::clicked, this, &AutoRunApp::setForAutorun);
        connect(removeButton, &QPushButton::clicked, this, &AutoRunApp::removeAutorun);

        loadAutorunApps();
    }

private slots:
    void setForAutorun() {

        QString filePath = QFileDialog::getOpenFileName(this, "Select Program");
        if (!filePath.isEmpty()) {
            selectedProgram = filePath;
        }

        if (selectedProgram.isEmpty()) {
            QMessageBox::warning(this, "Error", "Please select a program first.");
            return;
        }

        QString desktopFilePath = QDir::homePath() + "/.config/autostart/" + QFileInfo(selectedProgram).fileName() + ".desktop";

        QFile desktopFile(desktopFilePath);
        if (desktopFile.open(QIODevice::WriteOnly | QIODevice::Text)) {
            QTextStream out(&desktopFile);
            QString desktopFileContent = "[Desktop Entry]\n"
                                         "Name=" + QFileInfo(selectedProgram).fileName() + "\n"
                                         "Exec=" + selectedProgram + "\n"
                                         "TryExec=" + selectedProgram + "\n"
                                         "Terminal=false\n"
                                         "Type=Application\n"
                                         "Version=1.0\n"
                                         "X-GNOME-Autostart-enabled=true\n"
                                         "X-GNOME-Autostart-Delay=2\n"
                                         "X-KDE-autostart-after=panel\n"
                                         "X-LXQt-Need-Tray=true\n";
            out << desktopFileContent;
            desktopFile.close();
            QMessageBox::information(this, "Success", "Program set for autorun successfully.");
            loadAutorunApps();
        } else {
            QMessageBox::critical(this, "Error", "Failed to set program for autorun.");
        }
    }

    void loadAutorunApps() {
        autorunList->clear();
        QDir autostartDir(QDir::homePath() + "/.config/autostart/");
        QStringList filters;
        filters << "*.desktop";
        autostartDir.setNameFilters(filters);
        autostartDir.setFilter(QDir::Files | QDir::NoSymLinks);

        foreach(const QFileInfo &fileInfo, autostartDir.entryInfoList()) {
            autorunList->addItem(fileInfo.fileName());
        }
    }

    void removeAutorun() {
        QListWidgetItem *item = autorunList->currentItem();
        if (!item) {
            QMessageBox::warning(this, "Error", "Please select an item to remove.");
            return;
        }

        QString filePath = QDir::homePath() + "/.config/autostart/" + item->text();
        QFile file(filePath);
        if (file.remove()) {
            delete item;
            QMessageBox::information(this, "Success", "Item removed successfully.");
        } else {
            QMessageBox::critical(this, "Error", "Failed to remove item.");
        }
    }

private:
    QPushButton *selectButton;
    QPushButton *autorunButton;
    QPushButton *removeButton;
    QListWidget *autorunList;
    QString selectedProgram;
};

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    AutoRunApp window;
    window.setWindowTitle("Autorun Manager");
    window.show();
    return app.exec();
}
