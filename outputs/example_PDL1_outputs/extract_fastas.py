#!/usr/bin/env python3
"""
extract_sample1_fastas.py

Batch-extract the sequence that follows a header containing "sample=<N>" from .fa files
and write a cleaned FASTA file per input file.

Usage:
    python extract_sample1_fastas.py --infolder path/to/input --outfolder path/to/output
    python extract_sample1_fastas.py -i inputs -o clean_fastas -s 1 --overwrite

By default it looks for "sample=1" (case-insensitive). Change with --sample or -s.
"""

import argparse
from pathlib import Path
import re
import csv
import sys

# Allowed amino acids (20 standard) + X for unknown
ALLOWED_AA = set("ACDEFGHIKLMNPQRSTVWYX")

def clean_sequence(raw_seq: str) -> str:
    """Remove whitespace, take portion before '/', filter to allowed amino acids and upper-case."""
    # keep first part before slash if present
    part = raw_seq.split("/", 1)[0]
    # remove whitespace/newlines and uppercase
    part = re.sub(r"\s+", "", part).upper()
    # keep only allowed amino acid letters
    cleaned = "".join(ch for ch in part if ch in ALLOWED_AA)
    return cleaned

def extract_from_file(path: Path, sample_str: str) -> str:
    """
    Return the cleaned sequence found immediately after a header line that contains sample_str.
    If none found, return empty string.
    """
    seq_lines = []
    keep = False
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith(">"):
                # if we were already capturing and hit another header, stop
                if keep and seq_lines:
                    break
                # detect header containing sample string (case-insensitive)
                if sample_str.lower() in line.lower():
                    keep = True
                    seq_lines = []  # reset in case of multi-header files
                else:
                    keep = False
                continue

            if keep:
                # if blank line and we've already collected some sequence, we can stop
                if line.strip() == "" and seq_lines:
                    break
                # collect this line (stop if next header encountered handled above)
                seq_lines.append(line.strip())

    if not seq_lines:
        return ""

    # join (in case the sequence spans multiple lines)
    raw_seq = "".join(seq_lines)
    return clean_sequence(raw_seq)

def main():
    p = argparse.ArgumentParser(description="Extract sample=N sequences from .fa files and write cleaned FASTA files.")
    p.add_argument("-i", "--infolder", required=True, help="Input folder containing .fa files")
    p.add_argument("-o", "--outfolder", required=True, help="Output folder to write cleaned .fasta files")
    p.add_argument("-s", "--sample", default="1", help="Sample number to match (default: 1). Matches 'sample=1' header text.")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")
    p.add_argument("--min-len", type=int, default=10, help="Minimum sequence length to write (default 10). Shorter sequences will be written but warned about.")
    args = p.parse_args()

    infolder = Path(args.infolder)
    outfolder = Path(args.outfolder)
    sample_str = f"sample={args.sample}"

    if not infolder.is_dir():
        print(f"ERROR: input folder not found: {infolder}", file=sys.stderr)
        sys.exit(2)
    outfolder.mkdir(parents=True, exist_ok=True)

    rows = []
    files = list(infolder.glob("*.fa")) + list(infolder.glob("*.fasta"))
    if not files:
        print("No .fa or .fasta files found in input folder.", file=sys.stderr)
        sys.exit(1)

    for f in files:
        cleaned = extract_from_file(f, sample_str)
        outname = f"{f.stem}_sample_{args.sample}.fasta"
        outpath = outfolder / outname

        if not cleaned:
            status = "MISSING_SAMPLE_LINE_OR_NO_SEQUENCE"
            print(f"[WARN] {f.name}: did not find header with '{sample_str}' or sequence after it.")
        else:
            if outpath.exists() and not args.overwrite:
                status = "SKIPPED_EXISTS"
                print(f"[SKIP] {outpath.name} exists (use --overwrite to replace).")
            else:
                # write FASTA
                with outpath.open("w", encoding="utf-8") as of:
                    header = f">{f.stem}_sample_{args.sample}"
                    of.write(header + "\n")
                    # wrap sequence at 80 chars per FASTA convention
                    for i in range(0, len(cleaned), 80):
                        of.write(cleaned[i:i+80] + "\n")
                status = "WRITTEN"
                print(f"[OK] Wrote {outpath.name} ({len(cleaned)} aa)")

                if len(cleaned) < args.min_len:
                    print(f"[WARN] {outpath.name}: sequence length {len(cleaned)} < {args.min_len}")

        rows.append({
            "input_file": str(f),
            "output_file": str(outpath) if cleaned else "",
            "status": status,
            "length": len(cleaned) if cleaned else 0
        })

    # write summary CSV
    csv_path = outfolder / "extract_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csvf:
        fieldnames = ["input_file", "output_file", "status", "length"]
        writer = csv.DictWriter(csvf, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"\nDone. Summary written to {csv_path}")
    print("Statuses: WRITTEN, SKIPPED_EXISTS, MISSING_SAMPLE_LINE_OR_NO_SEQUENCE")

if __name__ == "__main__":
    main()