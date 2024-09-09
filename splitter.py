import os


def split_rdf_file(file_path, max_size_mb):
    max_size = max_size_mb * 1024 * 1024  # Convert MB to bytes
    part_number = 1
    current_part_size = 0
    current_part_lines = []

    with open(file_path, 'r') as f:
        for line in f:
            line_size = len(line.encode('utf-8'))
            if current_part_size + line_size > max_size:
                part_filename = f"{file_path}.part{part_number}"
                with open(part_filename, 'w') as part_file:
                    part_file.writelines(current_part_lines)
                print(f"Created part file: {part_filename}")
                part_number += 1
                current_part_lines = []
                current_part_size = 0

            current_part_lines.append(line)
            current_part_size += line_size

        # Write the remaining lines
        if current_part_lines:
            part_filename = f"{file_path}.part{part_number}"
            with open(part_filename, 'w') as part_file:
                part_file.writelines(current_part_lines)
            print(f"Created part file: {part_filename}")


# Usage
split_rdf_file('/Dataset Big/big-output.rdf', max_size_mb=500)