import argparse
import json
import openai
import threading
import sys
import re


def connect_to_openai(api_key):
    openai.api_key = api_key
    print("Connected to OpenAI\n")


def estimate_tokens(words, extra_tokens=0):
    return sum(len(word) for word in words) + len(words) + extra_tokens


def split_text(text, max_words, max_word_length=50):
    max_chars = int(4096 * (max_words / 5))  # Estimate based on an average of 5 tokens per word
    sections = text.split('\n\n\n')
    chunks = []

    current_chunk = []
    current_word_count = 0

    for section in sections:
        words = section.split()
        filtered_words = [word for word in words if len(word) <= max_word_length]  # Filter words based on length

        # Check if adding the current section will exceed the max_words limit
        if current_word_count + len(filtered_words) > max_words:
            # If yes, go back one section and add the current chunk to the list of chunks
            chunk = ' '.join(current_chunk)
            chunks.append(chunk)

            # Reset the current chunk and word count
            current_chunk = filtered_words
            current_word_count = len(filtered_words)
        else:
            # If no, add the current section to the current chunk
            if current_chunk:
                current_chunk.append('\n\n\n')  # Add the separator between sections
            current_chunk.extend(filtered_words)
            current_word_count += len(filtered_words)

    # Add the last chunk to the list of chunks
    if current_chunk:
        chunk = ' '.join(current_chunk)
        chunks.append(chunk)

    return chunks





def parse_qa(content):
    qa_pairs = []

    # Find the questions and answers using regular expressions for Q: and A: format
    q_a_qa = re.findall(r'(Q:|A:)(.*?)(?=(?:\nQ:|\nA:|$))', content, re.DOTALL)

    questions = []
    answers = []

    # Extract questions and answers from the Q:/A: format
    for i, item in enumerate(q_a_qa):
        if item[0] == 'Q:':
            questions.append(item[1].strip())
        elif item[0] == 'A:':
            answers.append(item[1].strip())

    # Pair the questions and answers and create the final list of dictionaries
    for question, answer in zip(questions, answers):
        if question and answer:
            qa_pairs.append({
                'instruction': question,
                'input': '',
                'output': answer
            })

    return qa_pairs





def process_sections(sections, model, output_file, stop_event):
    def save_to_file(qa_pairs, close=False):
        with open(output_file, 'a') as f:
            for idx, pair in enumerate(qa_pairs):
                json.dump(pair, f, indent=2)
                if idx < len(qa_pairs) - 1:
                    f.write(",\n")
                elif not close:
                    f.write(",\n")
            if close:
                f.write("\n]")

    dataset = []

    # Clear the output file before processing sections
    with open(output_file, 'w') as f:
        f.write("[\n")

    total_sections = len(sections)
    for index, section in enumerate(sections, 1):
        if stop_event.is_set():
            break

        prompt = f"Please generate questions and answers from the following text in the format 'Q:' for questions and 'A:' for answers:\n\n{section}"

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]

        response = openai.ChatCompletion.create(
            model=model,
            messages=messages
        )

        content = response['choices'][0]['message']['content']
        print(f"\n{content}\n")

        qa_pairs = parse_qa(content)
        dataset.extend(qa_pairs)

        # Save the dataset after every 5 sections
        if index % 5 == 0:
            save_to_file(dataset)
            dataset = []

        print(f"Section {index} of {total_sections} processed")

    # Save the remaining dataset and close the JSON array
    save_to_file(dataset, close=True)

    print(f"Processing completed. Results saved to {output_file}")





def main(api_key, model, input_file, split_length, output_file):
    connect_to_openai(api_key)

    with open(input_file, 'r') as f:
        raw_text = f.read()

    sections = split_text(raw_text, split_length, max_word_length=50)


    for section in sections:
        print(f"\n\n\n{section}")

    stop_event = threading.Event()
    t = threading.Thread(target=process_sections, args=(sections, model, output_file, stop_event))
    t.start()

    while t.is_alive():
        try:
            if input() == "stop":
                stop_event.set()
                t.join()
                break
        except KeyboardInterrupt:
            break

    print("Processing stopped by the user.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apikey", default="you_open_ai_api_key")
    parser.add_argument("--model", default="gpt-3.5-turbo")
    parser.add_argument("--input", default="input.txt")
    parser.add_argument("--max_words", default=700, type=int)  # Change this to the desired word count
    parser.add_argument("--output", default="output.json")

    args = parser.parse_args()
    main(args.apikey, args.model, args.input, args.max_words, args.output)
