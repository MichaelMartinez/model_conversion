#############################################
##
## python my_script.py -i "path/to/input" -o \
## "path/to/output_dir" -f "output.txt" --concatenate
##
## This would run the script with input set to
## "path/to/input", output-dir set to "path/to/output_dir",
## output-file set to "output.txt", and concatenate set to
## True. You can replace --concatenate with --strip if you
## want to strip formatting instead of concatenating.
##
## 1. Convert Markdown and PDF files to text
## 2. Concatenate text files
## 3. Strip Markdown formatting
## 4. Save output to a text file
#############################################

import os
import glob
import re
import PyPDF2
import click
from rich.progress import Progress


@click.command()
@click.option(
    "--input",
    "-i",
    prompt="Enter a file or directory path",
    help="Path to a file or directory to process",
    type=click.Path(exists=True, resolve_path=True),
    default=lambda: click.prompt(
        "Select a file or directory", type=click.Path(exists=True)
    ),
)
@click.option(
    "--output-dir",
    "-o",
    prompt="Enter full output directory path",
    help="Directory where output file will be saved",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    default=lambda: click.prompt(
        "Select a directory to save the output file",
        type=click.Path(file_okay=False, dir_okay=True, writable=True),
    ),
)
@click.option(
    "--output-file",
    "-f",
    prompt="Enter output file name",
    help="Name of the output file",
    type=str,
    default=lambda ctx: os.path.splitext(os.path.basename(ctx.params["input"]))[0],
    show_default=False,
)
@click.option(
    "--concatenate/--strip",
    default=True,
    help="Concatenate files or just strip formatting",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Run the script without making any modifications to the input data",
)
def process_files(input, output_dir, output_file, concatenate, dry_run):
    """Process Markdown and PDF files"""
    if dry_run:
        print("Running in dry run mode")
    output_path = os.path.join(output_dir, output_file)

    # Check if input is a file or directory
    if os.path.isfile(input):
        # If input is a file, process it directly
        if input.endswith(".pdf"):
            process_pdf_file(input, output_path, dry_run)
        elif input.endswith(".md"):
            process_md_file(input, output_path, concatenate, dry_run)
        else:
            print(f"Unsupported file format: {input}")
    elif os.path.isdir(input):
        # If input is a directory, process all files inside it
        md_files = []
        pdf_files = []
        for root, dirs, files in os.walk(input):
            for name in files:
                if name.endswith(".md"):
                    md_files.append(os.path.abspath(os.path.join(root, name)))
                elif name.endswith(".pdf"):
                    pdf_files.append(os.path.abspath(os.path.join(root, name)))
        for md_file in md_files:
            process_md_file(md_file, output_path, concatenate, dry_run)
        for pdf_file in pdf_files:
            process_pdf_file(pdf_file, output_path, dry_run)
    else:
        print(f"Invalid path: {input}")


def process_md_file(input_file, output_file, concatenate, dry_run):
    """Process a Markdown file"""
    # Define the regular expression for matching Markdown formatting
    md_formatting = re.compile(r"\W*([*_~`]{1,3})\w+\1\W*")
    # Use Rich to display a progress bar during the file operations
    with Progress() as progress:
        task = progress.add_task(f"Processing {input_file}", total=1)
        # Open the input file for reading
        with open(input_file, "r", encoding="utf-8") as md_file:
            # Read the content of the file and strip Markdown formatting if not concatenating
            content = md_file.read()
            if not concatenate:
                content = re.sub(md_formatting, "", content)
            # Open the output file for writing
            if not dry_run:
                with open(output_file, "a", encoding="utf-8") as f:
                    # Write the stripped content to the output file
                    f.write(content)
                    if concatenate:
                        f.write("\n")  # Add a newline between files
        # Update the progress bar
        progress.update(task, advance=1)


def process_pdf_file(input_file, output_file, dry_run):
    """Process a PDF file"""
    # Use PyPDF2 to extract text from PDF file
    with open(input_file, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(pdf_file, strict=False)
        with Progress() as progress:
            task = progress.add_task(
                f"Processing {input_file}", total=pdf_reader.numPages
            )
            for page_num in range(pdf_reader.numPages):
                page = pdf_reader.getPage(page_num)
                text = page.extractText()
                if not dry_run:
                    with open(output_file, "a", encoding="utf-8") as f:
                        f.write(text)
                progress.update(task, advance=1)


if __name__ == "__main__":
    process_files()
