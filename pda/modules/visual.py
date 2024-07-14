# visualization of directory space usage for ploff disk analyzer

import matplotlib.pyplot as plt

class visual():
    def visualizeDiskSpace(self):
        directory = self.pathInput.text()
        if not os.path.isdir(directory):
            self.showErrMsg(".wrong directory path.")
            return

        file_sizes = {}

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                file_extension = os.path.splitext(file_path)[1][1:]
                if file_extension in file_sizes:
                    file_sizes[file_extension] += file_size
                else:
                    file_sizes[file_extension] = file_size

        labels = list(file_sizes.keys())
        sizes = list(file_sizes.values())

        fig, ax = plt.subplots(figsize=(10, 7.68))
        ax.set_title('.disk_space_usage_at_directory()')

        colors = plt.cm.tab20.colors

        plt.pie(sizes, startangle=140, wedgeprops={'center': (0.6, 0.0)})

        legend_labels = [f"{label} - {self.convertSize(file_sizes[label])} ({sizes[i] / sum(sizes) * 100:.2f}%)" for i, label in enumerate(labels)]
        ax.legend(legend_labels, loc='center left', bbox_to_anchor=(-0.2, 0.5))

        plt.show()
