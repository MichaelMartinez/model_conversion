import os
import glob
import re
import PyPDF2
import click
import ebooklib
from ebooklib import epub
from rich.progress import Progress


@click.command()
@click.option(
    "--input",
    "-i",
    prompt="Enter a file or directory path",
    help="Path to a file or directory to process",
    type=click.Path(exists=True, resolve_path=True),
)
@click.option(
    "--output-dir",
    "-o",
    prompt="Enter full output directory path",
    help="Directory where output file will be saved",
    type=click.Path(exists=True, resolve_path=True),
)
@click.option(
    "--output-file",
    "-f",
    prompt="Enter output file name",
    help="Name of the output file",
    type=str,
)
@click.option(
    "--concatenate/--strip",
    default=True,
    help="Concatenate files or just strip formatting",
)
@click.option(
    "--strip-epub/--no-strip-epub",
    default=False,
    help="Strip formatting from EPUB files",
)
def process_files(input, output_dir, output_file, concatenate, strip_epub):
    """Process Markdown, PDF, and EPUB files"""
    output_path = os.path.join(output_dir, output_file)

    # Check if input is a file or directory
    if os.path.isfile(input):
        # If input is a file, process it directly
        if input.endswith(".pdf"):
            process_pdf_file(input, output_path)
        elif input.endswith(".md"):
            process_md_file(input, output_path, concatenate)
        elif input.endswith(".epub"):
            process_epub_file(input, output_path, strip_epub)
        else:
            print(f"Unsupported file format: {input}")
    elif os.path.isdir(input):
        # If input is a directory, process all files inside it
        md_files = []
        pdf_files = []
        epub_files = []
        for root, dirs, files in os.walk(input):
            for name in files:
                if name.endswith(".md"):
                    md_files.append(os.path.abspath(os.path.join(root, name)))
                elif name.endswith(".pdf"):
                    pdf_files.append(os.path.abspath(os.path.join(root, name)))
                elif name.endswith(".epub"):
                    epub_files.append(os.path.abspath(os.path.join(root, name)))
        for md_file in md_files:
            process_md_file(md_file, output_path, concatenate)
        for pdf_file in pdf_files:
            process_pdf_file(pdf_file, output_path)
        for epub_file in epub_files:
            process_epub_file(epub_file, output_path, strip_epub)
    else:
        print(f"Invalid path: {input}")


def process_md_file(input_file, output_file, concatenate):
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
            with open(output_file, "a", encoding="utf-8") as f:
                # Write the stripped content to the output file
                f.write(content)
                if concatenate:
                    f.write("\n")  # Add a newline between files
        # Update the progress bar
        progress.update(task, advance=1)


def process_pdf_file(input_file, output_file):
    """Process a PDF file"""
    # Use PyPDF2 to extract text from PDF file
    with open(input_file, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(pdf_file)
        with Progress() as progress:
            task = progress.add_task(
                f"Processing {input_file}", total=pdf_reader.numPages
            )
            for page_num in range(pdf_reader.numPages):
                page = pdf_reader.getPage(page_num)
                text = page.extractText()
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(text)
                progress.update(task, advance=1)


def process_epub_file(input_file, output_file, strip_epub):
    """Process an EPUB file"""
    # Use ebooklib to extract text from EPUB file
    book = epub.read_epub(input_file)
    text = ""
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            # Extract text from document item
            content = item.get_content()
            if strip_epub:
                # Strip HTML tags and newlines from content
                content = re.sub(r"<[^>]+>", "", content)
                content = re.sub(r"\n", "", content)
                text += content
                # Use Rich to display a progress bar during the file operations
                with Progress() as progress:
                    task = progress.add_task(f"Processing {input_file}", total=1)
                    # Open the output file for writing
                    with open(output_file, "a", encoding="utf-8") as f:
                        # Write the extracted text to the output file
                        f.write(text)
                        f.write("\n")  # Add a newline between files
                        # Update the progress bar
                        progress.update(task, advance=1)


if __name__ == "main":
    process_files()
