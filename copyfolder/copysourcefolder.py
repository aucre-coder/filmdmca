import shutil
import os


def copy_and_empty_files(source_folder, destination_folder):
    """
    Copy a folder structure and empty files in specific subdirectories.

    Args:
        source_folder: Path to the source folder (e.g., 'filmpalast')
        destination_folder: Path where to copy the folder
    """

    # Step 1: Copy the entire folder structure
    print(f"Copying {source_folder} to {destination_folder}...")
    shutil.copytree(source_folder, destination_folder)
    print("Copy completed!")

    # Step 2: Find and empty files in 'extractor' and 'scanner' folders
    print("\nEmptying files in extractor and scanner folders...")

    for root, dirs, files in os.walk(destination_folder):
        # Check if current directory is named 'extractor' or 'scanner'
        if os.path.basename(root) in ['extractor', 'scanner']:
            for file in files:
                if file.endswith('.py'):  # Only empty Python files
                    file_path = os.path.join(root, file)
                    # Empty the file by opening in write mode
                    with open(file_path, 'w') as f:
                        pass  # Writing nothing empties the file
                    print(f"Emptied: {file_path}")

    print("\nDone!")