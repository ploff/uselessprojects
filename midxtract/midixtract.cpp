#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cstdint>

#define BINFILE "r1"

size_t findSubstring(const std::vector<char>& data, const std::string& pattern, size_t start = 0) {
    for (size_t i = start; i <= data.size() - pattern.size(); ++i) {
        bool found = true;
        for (size_t j = 0; j < pattern.size(); ++j) {
            if (data[i + j] != pattern[j]) {
                found = false;
                break;
            }
        }
        if (found) {
            return i;
        }
    }
    return std::string::npos;
}

uint32_t bytesToUint32(const std::vector<char>& data, size_t start) {
    return (static_cast<uint8_t>(data[start]) << 24) |
    (static_cast<uint8_t>(data[start + 1]) << 16) |
    (static_cast<uint8_t>(data[start + 2]) << 8) |
    static_cast<uint8_t>(data[start + 3]);
}

int main() {

    std::string inputFilename = BINFILE;
    std::ifstream inputFile(inputFilename, std::ios::binary);

    if (!inputFile) {
        std::cerr << "Error opening input file: " << inputFilename << std::endl;
        return 1;
    }

    std::vector<char> fileData((std::istreambuf_iterator<char>(inputFile)), std::istreambuf_iterator<char>());
    inputFile.close();

    std::string midiHeader = "MThd";
    size_t startIndex = 0;
    size_t fileCount = 0;

    while ((startIndex = findSubstring(fileData, midiHeader, startIndex)) != std::string::npos) {
        // Get the length of the MIDI file header chunk
        uint32_t headerLength = bytesToUint32(fileData, startIndex + 4);

        // MIDI file chunk size includes header and all subsequent chunks
        size_t midiFileSize = startIndex + 8 + headerLength;

        // Search for the end of the MIDI file by finding the next header or end of file
        size_t nextHeaderIndex = findSubstring(fileData, midiHeader, midiFileSize);
        if (nextHeaderIndex == std::string::npos) {
            nextHeaderIndex = fileData.size();
        }

        // Extract the MIDI file data
        std::vector<char> midiFileData(fileData.begin() + startIndex, fileData.begin() + nextHeaderIndex);

        // Output filename for the extracted MIDI file
        std::string outputFilename = "output_" + std::to_string(fileCount++) + ".mid";
        std::ofstream outputFile(outputFilename, std::ios::binary);
        if (!outputFile) {
            std::cerr << "Error creating output file: " << outputFilename << std::endl;
            return 1;
        }

        // Write the extracted MIDI file data to the output file
        outputFile.write(midiFileData.data(), midiFileData.size());
        outputFile.close();

        // Move to the next position in the binary file
        startIndex = nextHeaderIndex;
    }

    std::cout << "Extraction completed. " << fileCount << " MIDI files extracted." << std::endl;
    return 0;
}
