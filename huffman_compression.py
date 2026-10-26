import heapq
import os
import struct
from collections import Counter


# Node of the Huffman Tree
class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None


# Build the Huffman Tree
def build_huffman_tree(frequency):
    if not frequency:
        return None

    heap = []
    order = 0

    for char, freq in frequency.items():
        node = Node(char, freq)
        heapq.heappush(heap, (freq, order, node))
        order += 1

    while len(heap) > 1:
        freq1, _, left = heapq.heappop(heap)
        freq2, _, right = heapq.heappop(heap)

        merged = Node(None, freq1 + freq2)
        merged.left = left
        merged.right = right

        heapq.heappush(
            heap, (merged.freq, order, merged)
        )
        order += 1

    return heap[0][2]


# Generate Huffman Codes
def generate_codes(root):
    codes = {}

    def traverse(node, code):
        if node is None:
            return

        if node.char is not None:
            codes[node.char] = code or "0"
            return

        traverse(node.left, code + "0")
        traverse(node.right, code + "1")

    traverse(root, "")
    return codes


# Convert bits into bytes
def bits_to_bytes(bits):
    padding = (8 - len(bits) % 8) % 8
    bits += "0" * padding

    data = bytearray()

    for i in range(0, len(bits), 8):
        data.append(int(bits[i:i + 8], 2))

    return bytes(data)


# Compress the file
def compress_file(input_file, output_file):

    with open(input_file, "rb") as file:
        data = file.read()

    if not data:
        print("The input file is empty.")
        return

    # Calculate frequency of each byte
    frequency = Counter(data)

    # Build Huffman Tree
    root = build_huffman_tree(frequency)

    # Generate Huffman Codes
    codes = generate_codes(root)

    # Encode original data
    encoded_bits = "".join(codes[byte] for byte in data)

    # Convert bits into bytes
    encoded_data = bits_to_bytes(encoded_bits)

    # Compact binary header:
    # 4 bytes: Magic signature
    # 2 bytes: Number of unique symbols
    # 9 bytes per symbol: 1-byte symbol + 8-byte frequency

    header = bytearray(b"HUF1")

    header.extend(struct.pack(">H", len(frequency)))

    for byte, freq in frequency.items():
        header.extend(struct.pack(">BQ", byte, freq))

    compressed_data = bytes(header) + encoded_data

    # Write compressed file
    with open(output_file, "wb") as file:
        file.write(compressed_data)

    original_size = len(data)
    compressed_size = os.path.getsize(output_file)

    print("\nFile compressed successfully!")
    print("Original file size:", original_size, "bytes")
    print("Compressed file size:", compressed_size, "bytes")

    print("\nHuffman Codes:")

    for byte, code in sorted(codes.items()):
        print(repr(bytes([byte])), ":", code)

    ratio = compressed_size / original_size * 100
    saving = 100 - ratio

    print("\nCompressed size:", f"{ratio:.2f}% of original")
    print("Space saved:", f"{saving:.2f}%")

    if compressed_size >= original_size:
        print(
            "\nNote: This file cannot be compressed further "
            "with this format because metadata overhead "
            "and/or the encoded data are too large."
        )


# Decompress the file
def decompress_file(input_file, output_file):

    with open(input_file, "rb") as file:
        compressed_data = file.read()

    # Check file signature
    if len(compressed_data) < 6 or compressed_data[:4] != b"HUF1":
        raise ValueError("Invalid Huffman compressed file.")

    # Read number of unique symbols
    symbol_count = struct.unpack(">H", compressed_data[4:6])[0]

    if not 1 <= symbol_count <= 256:
        raise ValueError("Invalid symbol count.")

    # Read frequency table
    position = 6
    frequency = {}

    for _ in range(symbol_count):

        if position + 9 > len(compressed_data):
            raise ValueError("Incomplete frequency table.")

        byte, freq = struct.unpack(
            ">BQ", compressed_data[position:position + 9]
        )

        position += 9

        if byte in frequency or freq == 0:
            raise ValueError("Invalid frequency table.")

        frequency[byte] = freq

    # Remaining bytes contain encoded data
    encoded_data = compressed_data[position:]

    # Rebuild Huffman Tree
    root = build_huffman_tree(frequency)

    # Calculate expected original size
    original_size = sum(frequency.values())

    # Convert bytes into bits
    bit_string = "".join(
        format(byte, "08b") for byte in encoded_data
    )

    decoded_data = bytearray()

    # Handle a file containing only one unique byte
    if root.char is not None:
        if len(encoded_data) * 8 < original_size:
            raise ValueError("Compressed data is incomplete.")

        decoded_data.extend(
            bytes([root.char]) * original_size
        )

    else:
        current = root

        for bit in bit_string:

            if bit == "0":
                current = current.left
            else:
                current = current.right

            if current is None:
                raise ValueError("Invalid compressed bitstream.")

            if current.char is not None:
                decoded_data.append(current.char)
                current = root

                if len(decoded_data) == original_size:
                    break

        if len(decoded_data) != original_size:
            raise ValueError("Compressed data is incomplete.")

    # Write recovered original data
    with open(output_file, "wb") as file:
        file.write(decoded_data)

    print("\nFile decompressed successfully!")
    print("Recovered file:", output_file)
    print("Recovered size:", len(decoded_data), "bytes")


# Main Menu
def main():

    while True:

        print("\n===== HUFFMAN FILE COMPRESSION =====")
        print("1. Compress File")
        print("2. Decompress File")
        print("3. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":

            input_file = input(
                "Enter input text filename: "
            ).strip()

            output_file = input(
                "Enter compressed filename (e.g. data.huff): "
            ).strip()

            try:
                compress_file(input_file, output_file)

            except (OSError, ValueError, struct.error) as error:
                print("Compression error:", error)

        elif choice == "2":

            input_file = input(
                "Enter compressed filename: "
            ).strip()

            output_file = input(
                "Enter output text filename: "
            ).strip()

            try:
                decompress_file(input_file, output_file)

            except (OSError, ValueError, struct.error) as error:
                print("Decompression error:", error)

        elif choice == "3":

            print("Thank you for using Huffman Compression!")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()