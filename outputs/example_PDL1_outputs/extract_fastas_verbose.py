# # #!/usr/bin/env python3
# # import argparse
# # from pathlib import Path
# # import re
# # import sys

# # ALLOWED_AA = set("ACDEFGHIKLMNPQRSTVWYX")

# # def clean_sequence(raw_seq):
# #     part = raw_seq.split("/", 1)[0]
# #     part = re.sub(r"\s+", "", part).upper()
# #     return "".join(c for c in part if c in ALLOWED_AA)

# # def extract_from_file(path, sample_str):
# #     seq_lines = []
# #     keep = False
# #     with open(path) as f:
# #         for line in f:
# #             line = line.strip()
# #             if line.startswith(">"):
# #                 if keep and seq_lines:
# #                     break
# #                 keep = sample_str.lower() in line.lower()
# #                 continue
# #             if keep:
# #                 seq_lines.append(line)
# #     if not seq_lines:
# #         return ""
# #     return clean_sequence("".join(seq_lines))

# # def main():
# #     p = argparse.ArgumentParser()
# #     p.add_argument("-i", "--infolder", required=True)
# #     p.add_argument("-o", "--outfolder", required=True)
# #     p.add_argument("-s", "--sample", default="1")
# #     p.add_argument("--overwrite", action="store_true")
# #     args = p.parse_args()

# #     infolder = Path(args.infolder)
# #     outfolder = Path(args.outfolder)
# #     outfolder.mkdir(parents=True, exist_ok=True)

# #     files = list(infolder.glob("*.fa")) + list(infolder.glob("*.fasta"))
# #     print(f"Found {len(files)} input files")

# #     for f in files:
# #         seq = extract_from_file(f, f"sample={args.sample}")
# #         if not seq:
# #             print(f"[WARN] {f.name}: sample not found")
# #             continue

# #         out = outfolder / f"{f.stem}.fasta"
# #         if out.exists() and not args.overwrite:
# #             print(f"[SKIP] {out.name} exists")
# #             continue

# #         with open(out, "w") as fo:
# #             # fo.write(f">{f.stem}\n")
# #             for i in range(0, len(seq), 80):
# #                 fo.write(seq[i:i+80] + "\n")

# #         print(f"[OK] wrote {out.name} ({len(seq)} aa)")

# # if __name__ == "__main__":
# #     main()

# #!/usr/bin/env python3
# """
# extract_with_headers.py

# For each .fa/.fasta file in --infolder:
#  - find the sequence after header containing "sample=<N>"
#  - clean sequence (strip after '/', remove non-AA, uppercase)
#  - write a FASTA with a guaranteed header of the form >PREFIX|ID

# Usage examples:
#   python extract_with_headers.py -i ./raw_fa -o ./clean_fa --prefix protein --start-id 101 --overwrite
#   python extract_with_headers.py -i ./raw_fa -o ./combined.fasta --combined --prefix PD-L1 --start-id 201 --overwrite
# """
# import argparse
# from pathlib import Path
# import re
# import sys

# ALLOWED_AA = set("ACDEFGHIKLMNPQRSTVWYX")

# def clean_sequence(raw_seq):
#     # keep before '/' then remove whitespace, uppercase and keep allowed chars
#     part = raw_seq.split("/", 1)[0]
#     part = re.sub(r"\s+", "", part).upper()
#     return "".join(c for c in part if c in ALLOWED_AA)

# def extract_from_file(path: Path, sample_str: str) -> str:
#     seq_lines = []
#     keep = False
#     try:
#         with path.open("r", encoding='utf-8', errors='replace') as fh:
#             for line in fh:
#                 line = line.rstrip("\n")
#                 if line.startswith(">"):
#                     if keep and seq_lines:
#                         break
#                     keep = sample_str.lower() in line.lower()
#                     continue
#                 if keep:
#                     if line.strip() == "" and seq_lines:
#                         break
#                     seq_lines.append(line.strip())
#     except Exception:
#         return ""
#     if not seq_lines:
#         return ""
#     return clean_sequence("".join(seq_lines))

# def write_fasta(path: Path, header: str, seq: str):
#     with path.open("w", encoding='utf-8') as fo:
#         fo.write(f">{header}\n")
#         for i in range(0, len(seq), 80):
#             fo.write(seq[i:i+80] + "\n")

# def main():
#     p = argparse.ArgumentParser()
#     p.add_argument("-i", "--infolder", required=True, help="Input folder with .fa/.fasta files")
#     p.add_argument("-o", "--out", required=True, help="Output folder (if --combined not used) or combined fasta path (if --combined used)")
#     p.add_argument("-s", "--sample", default="1", help="sample number to match (default 1)")
#     p.add_argument("--prefix", default="protein", help="Header prefix (default 'protein')")
#     p.add_argument("--start-id", type=int, default=101, help="Starting numeric ID (default 101)")
#     p.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
#     p.add_argument("--combined", action="store_true", help="Write a single combined FASTA instead of one file per input")
#     args = p.parse_args()

#     infolder = Path(args.infolder)
#     if not infolder.is_dir():
#         print("Input folder not found:", infolder, file=sys.stderr)
#         sys.exit(2)

#     files = sorted(list(infolder.glob("*.fa")) + list(infolder.glob("*.fasta")))
#     if not files:
#         print("No .fa/.fasta files found in", infolder, file=sys.stderr)
#         sys.exit(1)

#     sample_str = f"sample={args.sample}"
#     current_id = args.start_id
#     records = []  # for combined mode
#     outpath = Path(args.out)

#     if args.combined:
#         if outpath.exists() and not args.overwrite:
#             print(f"ERROR: {outpath} exists. Use --overwrite to replace.", file=sys.stderr)
#             sys.exit(3)

#     else:
#         outdir = outpath
#         outdir.mkdir(parents=True, exist_ok=True)

#     for f in files:
#         seq = extract_from_file(f, sample_str)
#         if not seq:
#             print(f"[WARN] {f.name}: no sample={args.sample} sequence found -> skipping")
#             current_id += 1
#             continue

#         header = f"{args.prefix}|{current_id}"
#         if args.combined:
#             records.append((header, seq, f.name))
#             print(f"[ADD] {f.name} -> header: >{header} (len {len(seq)})")
#         else:
#             out_file = outdir / f"{f.stem}.fasta"
#             if out_file.exists() and not args.overwrite:
#                 print(f"[SKIP] {out_file.name} exists (use --overwrite to replace)")
#             else:
#                 write_fasta(out_file, header, seq)
#                 print(f"[OK] Wrote {out_file.name} with header: >{header} (len {len(seq)})")

#         current_id += 1

#     if args.combined:
#         # write single combined fasta
#         write_fasta(outpath, "combined_index", "")  # create or clear file
#         with outpath.open("w", encoding='utf-8') as fh:
#             for header, seq, src in records:
#                 fh.write(f">{header}\n")
#                 for i in range(0, len(seq), 80):
#                     fh.write(seq[i:i+80] + "\n")
#         print(f"[OK] Wrote combined FASTA: {outpath} with {len(records)} records")

# if __name__ == "__main__":
#     main()



#### INCORRECT FORMAT!!!! - has covalent bonds (links target and binder together!!!)
# #!/usr/bin/env python3
# """
# extract_with_headers.py

# For each .fa/.fasta file in --infolder:
#  - find the sequence after header containing "sample=<N>"
#  - clean sequence (remove '/', remove non-AA, uppercase)
#  - write a FASTA with a guaranteed header of the form >PREFIX|ID

# Usage examples:
#   python extract_with_headers.py -i ./raw_fa -o ./clean_fa --prefix protein --start-id 101 --overwrite
#   python extract_with_headers.py -i ./raw_fa -o ./combined.fasta --combined --prefix PD-L1 --start-id 201 --overwrite
# """
# import argparse
# from pathlib import Path
# import re
# import sys

# ALLOWED_AA = set("ACDEFGHIKLMNPQRSTVWYX")

# def clean_sequence(raw_seq: str) -> str:
#     # Remove all '/' characters, remove whitespace, uppercase and keep allowed chars
#     no_slash = raw_seq.replace("/", "")
#     no_ws = re.sub(r"\s+", "", no_slash)
#     up = no_ws.upper()
#     return "".join(c for c in up if c in ALLOWED_AA)

# def extract_from_file(path: Path, sample_str: str) -> str:
#     seq_lines = []
#     keep = False
#     try:
#         with path.open("r", encoding='utf-8', errors='replace') as fh:
#             for line in fh:
#                 line = line.rstrip("\n")
#                 if line.startswith(">"):
#                     if keep and seq_lines:
#                         break
#                     keep = sample_str.lower() in line.lower()
#                     continue
#                 if keep:
#                     if line.strip() == "" and seq_lines:
#                         break
#                     seq_lines.append(line.strip())
#     except Exception:
#         return ""
#     if not seq_lines:
#         return ""
#     return clean_sequence("".join(seq_lines))

# def write_fasta(path: Path, header: str, seq: str):
#     with path.open("w", encoding='utf-8') as fo:
#         fo.write(f">{header}\n")
#         for i in range(0, len(seq), 80):
#             fo.write(seq[i:i+80] + "\n")

# def main():
#     p = argparse.ArgumentParser()
#     p.add_argument("-i", "--infolder", required=True, help="Input folder with .fa/.fasta files")
#     p.add_argument("-o", "--out", required=True, help="Output folder (if --combined not used) or combined fasta path (if --combined used)")
#     p.add_argument("-s", "--sample", default="1", help="sample number to match (default 1)")
#     p.add_argument("--prefix", default="protein", help="Header prefix (default 'protein')")
#     p.add_argument("--start-id", type=int, default=101, help="Starting numeric ID (default 101)")
#     p.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
#     p.add_argument("--combined", action="store_true", help="Write a single combined FASTA instead of one file per input")
#     args = p.parse_args()

#     infolder = Path(args.infolder)
#     if not infolder.is_dir():
#         print("Input folder not found:", infolder, file=sys.stderr)
#         sys.exit(2)

#     files = sorted(list(infolder.glob("*.fa")) + list(infolder.glob("*.fasta")))
#     if not files:
#         print("No .fa/.fasta files found in", infolder, file=sys.stderr)
#         sys.exit(1)

#     sample_str = f"sample={args.sample}"
#     current_id = args.start_id
#     records = []  # for combined mode
#     outpath = Path(args.out)

#     if args.combined:
#         if outpath.exists() and not args.overwrite:
#             print(f"ERROR: {outpath} exists. Use --overwrite to replace.", file=sys.stderr)
#             sys.exit(3)
#     else:
#         outdir = outpath
#         outdir.mkdir(parents=True, exist_ok=True)

#     for f in files:
#         seq = extract_from_file(f, sample_str)
#         if not seq:
#             print(f"[WARN] {f.name}: no sample={args.sample} sequence found -> skipping")
#             current_id += 1
#             continue

#         header = f"{args.prefix}|{current_id}"
#         if args.combined:
#             records.append((header, seq, f.name))
#             print(f"[ADD] {f.name} -> header: >{header} (len {len(seq)})")
#         else:
#             out_file = outdir / f"{f.stem}.fasta"
#             if out_file.exists() and not args.overwrite:
#                 print(f"[SKIP] {out_file.name} exists (use --overwrite to replace)")
#             else:
#                 write_fasta(out_file, header, seq)
#                 print(f"[OK] Wrote {out_file.name} with header: >{header} (len {len(seq)})")

#         current_id += 1

#     if args.combined:
#         # write single combined fasta
#         with outpath.open("w", encoding='utf-8') as fh:
#             for header, seq, src in records:
#                 fh.write(f">{header}\n")
#                 for i in range(0, len(seq), 80):
#                     fh.write(seq[i:i+80] + "\n")
#         print(f"[OK] Wrote combined FASTA: {outpath} with {len(records)} records")

# if __name__ == "__main__":
#     main()



# #!/usr/bin/env python3
# """
# extract_with_headers.py

# For each .fa/.fasta file in --infolder:
#  - find the sequence after header containing "sample=<N>"
#  - clean sequence (handle '/' chain marker according to --chain-mode)
#  - write a FASTA with a guaranteed header of the form >PREFIX|ID (with optional _A/_B suffix for split chains)

# Chain modes:
#   colon  -> replace '/' with ':' and return a single sequence (default)
#   split  -> split on '/' and return separate chains (multiple files or multiple records in combined mode)
#   remove -> remove '/' (legacy behavior)

# Usage examples:
#   python extract_with_headers.py -i ./raw_fa -o ./clean_fa --prefix protein --start-id 101 --overwrite
#   python extract_with_headers.py -i ./raw_fa -o ./combined.fasta --combined --prefix PD-L1 --start-id 201 --overwrite --chain-mode split
# """
# import argparse
# from pathlib import Path
# import re
# import sys
# from typing import List

# ALLOWED_AA = set("ACDEFGHIKLMNPQRSTVWYX")

# def clean_seq_fragment(fragment: str) -> str:
#     """Clean a single fragment (one chain): remove whitespace, uppercase, keep allowed chars."""
#     no_ws = re.sub(r"\s+", "", fragment)
#     up = no_ws.upper()
#     return "".join(c for c in up if c in ALLOWED_AA)

# def process_sequence(raw_seq: str, chain_mode: str) -> List[str]:
#     """
#     Process raw sequence containing zero or more '/' separators.

#     Returns a list of sequence strings (1 or more fragments) depending on chain_mode:
#       - 'colon'  => single sequence with ':' replacing '/' (returned as [single_seq])
#       - 'split'  => list of cleaned fragments (skip empty fragments)
#       - 'remove' => single sequence with all '/' removed
#     """
#     if chain_mode == "remove":
#         merged = raw_seq.replace("/", "")
#         cleaned = clean_seq_fragment(merged)
#         return [cleaned] if cleaned else []
#     # split into fragments around '/'
#     parts = [p for p in raw_seq.split("/") if p.strip() != ""]
#     cleaned_parts = [clean_seq_fragment(p) for p in parts]
#     cleaned_parts = [p for p in cleaned_parts if p]  # drop empty after cleaning
#     if not cleaned_parts:
#         return []
#     if chain_mode == "split":
#         return cleaned_parts
#     # chain_mode == 'colon'
#     # join cleaned parts with ':' to produce a single multimer-style sequence
#     return [":".join(cleaned_parts)]

# def extract_from_file(path: Path, sample_str: str, chain_mode: str) -> List[str]:
#     """
#     Extract and return list of sequence(s) from file for the matched sample_str.
#     Returns empty list on failure or if no match.
#     """
#     seq_lines = []
#     keep = False
#     try:
#         with path.open("r", encoding='utf-8', errors='replace') as fh:
#             for line in fh:
#                 line = line.rstrip("\n")
#                 if line.startswith(">"):
#                     if keep and seq_lines:
#                         break
#                     keep = sample_str.lower() in line.lower()
#                     continue
#                 if keep:
#                     if line.strip() == "" and seq_lines:
#                         break
#                     seq_lines.append(line.strip())
#     except Exception:
#         return []
#     if not seq_lines:
#         return []
#     raw = "".join(seq_lines)
#     return process_sequence(raw, chain_mode)

# def write_fasta(path: Path, header: str, seq: str):
#     with path.open("w", encoding='utf-8') as fo:
#         fo.write(f">{header}\n")
#         for i in range(0, len(seq), 80):
#             fo.write(seq[i:i+80] + "\n")

# def main():
#     p = argparse.ArgumentParser()
#     p.add_argument("-i", "--infolder", required=True, help="Input folder with .fa/.fasta files")
#     p.add_argument("-o", "--out", required=True, help="Output folder (if --combined not used) or combined fasta path (if --combined used)")
#     p.add_argument("-s", "--sample", default="1", help="sample number to match (default 1)")
#     p.add_argument("--prefix", default="protein_ligand", help="Header prefix (default 'protein:ligand')")
#     p.add_argument("--start-id", type=int, default=101, help="Starting numeric ID (default 101)")
#     p.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
#     p.add_argument("--combined", action="store_true", help="Write a single combined FASTA instead of one file per input")
#     p.add_argument("--chain-mode", choices=("colon", "split", "remove"), default="colon",
#                    help="How to handle '/' chain-breaks: colon (replace with ':'), split (separate chains), remove (strip). Default: colon")
#     args = p.parse_args()

#     infolder = Path(args.infolder)
#     if not infolder.is_dir():
#         print("Input folder not found:", infolder, file=sys.stderr)
#         sys.exit(2)

#     files = sorted(list(infolder.glob("*.fa")) + list(infolder.glob("*.fasta")))
#     if not files:
#         print("No .fa/.fasta files found in", infolder, file=sys.stderr)
#         sys.exit(1)

#     sample_str = f"sample={args.sample}"
#     current_id = args.start_id
#     records = []  # for combined mode: list of tuples (header, seq, src)
#     outpath = Path(args.out)

#     if args.combined:
#         if outpath.exists() and not args.overwrite:
#             print(f"ERROR: {outpath} exists. Use --overwrite to replace.", file=sys.stderr)
#             sys.exit(3)
#     else:
#         outdir = outpath
#         outdir.mkdir(parents=True, exist_ok=True)

#     for f in files:
#         seqs = extract_from_file(f, sample_str, args.chain_mode)
#         if not seqs:
#             print(f"[WARN] {f.name}: no sample={args.sample} sequence found or sequence empty after cleaning -> skipping")
#             current_id += 1
#             continue

#         # If split mode produced multiple fragments, we label them _A, _B, ...
#         if args.chain_mode == "split" and len(seqs) > 1:
#             suffixes = [chr(ord("A") + i) for i in range(len(seqs))]
#             if args.combined:
#                 for suf, seq in zip(suffixes, seqs):
#                     header = f"{args.prefix}|{current_id}_{suf}"
#                     records.append((header, seq, f.name))
#                     print(f"[ADD] {f.name} -> header: >{header} (len {len(seq)})")
#             else:
#                 # write separate files per chain
#                 for suf, seq in zip(suffixes, seqs):
#                     out_file = outdir / f"{f.stem}_{suf}.fasta"
#                     header = f"{args.prefix}|{current_id}_{suf}"
#                     if out_file.exists() and not args.overwrite:
#                         print(f"[SKIP] {out_file.name} exists (use --overwrite to replace)")
#                     else:
#                         write_fasta(out_file, header, seq)
#                         print(f"[OK] Wrote {out_file.name} with header: >{header} (len {len(seq)})")
#         else:
#             # single record result (either colon mode, remove mode, or split with only one fragment)
#             seq = seqs[0]
#             header = f"{args.prefix}|{current_id}"
#             if args.combined:
#                 records.append((header, seq, f.name))
#                 print(f"[ADD] {f.name} -> header: >{header} (len {len(seq)})")
#             else:
#                 out_file = outdir / f"{f.stem}.fasta"
#                 if out_file.exists() and not args.overwrite:
#                     print(f"[SKIP] {out_file.name} exists (use --overwrite to replace)")
#                 else:
#                     write_fasta(out_file, header, seq)
#                     print(f"[OK] Wrote {out_file.name} with header: >{header} (len {len(seq)})")

#         current_id += 1

#     if args.combined:
#         with outpath.open("w", encoding='utf-8') as fh:
#             for header, seq, src in records:
#                 fh.write(f">{header}\n")
#                 for i in range(0, len(seq), 80):
#                     fh.write(seq[i:i+80] + "\n")
#         print(f"[OK] Wrote combined FASTA: {outpath} with {len(records)} records")

# if __name__ == "__main__":
#     main()


######## FAILS - for the binder, it always gives GGGGGGG (i.e. it does not consider the correct input entry, i.e. the one containing the predicted sequence by MPNN)
#!/usr/bin/env python3
# """
# make_protein_binder_fastas.py

# For each input .fa/.fasta file (or a single file), read the first FASTA record,
# split the sequence at the first '/' into target / predicted, clean both sequences,
# and write an output file <orig_stem>_converted.fasta containing:

# >protein|<TARGET_ID>
# <TARGET_SEQUENCE>

# >protein|binder<INDEX>
# <PREDICTED_SEQUENCE>

# INDEX is the zero-based index of the file being processed (first file -> binder0).

# Usage:
#   # single file
#   python make_protein_binder_fastas.py -i example.fa -o outdir

#   # folder
#   python make_protein_binder_fastas.py -i raw_fa_folder -o outdir
# """
# import argparse
# from pathlib import Path
# import re
# import sys

# ALLOWED_AA = set("ACDEFGHIKLMNPQRSTVWYX")

# def clean_seq(s: str) -> str:
#     """Remove whitespace, uppercase, keep only standard AA letters (X allowed)."""
#     s2 = re.sub(r"\s+", "", s).upper()
#     return "".join(ch for ch in s2 if ch in ALLOWED_AA)

# def read_first_fasta_record(path: Path):
#     """Return (defline_without_gt, joined_sequence) for the first record, or (None, None)."""
#     defline = None
#     seq_lines = []
#     with path.open("r", encoding="utf-8", errors="replace") as fh:
#         for line in fh:
#             if line.startswith(">"):
#                 if defline is None:
#                     defline = line[1:].rstrip("\n")
#                     continue
#                 else:
#                     break
#             if defline is not None:
#                 seq_lines.append(line.strip())
#     if defline is None:
#         return None, None
#     return defline, "".join(seq_lines)

# def extract_target_id(defline: str, fallback_stem: str) -> str:
#     """
#     Best-effort extract a short target ID from the original defline.
#     Strategy:
#       - look for first token before whitespace or comma
#       - allow letters, digits, '-', '_' in token
#       - remove non-alphanum (keep letters+digits), remove leading/trailing punctuation
#       - uppercase result
#       - if empty, fall back to file stem
#     Example:
#       "PD-L1_0, score=..." -> finds "PD-L1_0" -> sanitize -> "PDL10" -> return
#       "SeqABCD [organism=...]" -> "SeqABCD" -> "SEQABCD"
#     """
#     if not defline:
#         return fallback_stem
#     # take substring before first space or comma
#     token = re.split(r"[,\s]", defline.strip(), maxsplit=1)[0]
#     # keep letters, digits, dash, underscore, period
#     token = re.sub(r"[^A-Za-z0-9\-_\.]", "", token)
#     # collapse dashes/underscores/dots, then keep alnum only (we want short seq id)
#     token_sanit = re.sub(r"[-_\.]+", "", token)
#     token_sanit = token_sanit.upper()
#     if token_sanit:
#         # limit length to 20 to be safe
#         return token_sanit[:20]
#     return fallback_stem.upper()[:20]

# def write_fasta_file(path: Path, records):
#     """
#     records: list of tuples (header_without_gt, seq)
#     Writes file, overwriting if exists.
#     """
#     with path.open("w", encoding="utf-8") as fh:
#         for header, seq in records:
#             fh.write(f">{header}\n")
#             for i in range(0, len(seq), 80):
#                 fh.write(seq[i:i+80] + "\n")

# def process_file(inpath: Path, outdir: Path, idx: int):
#     defline, rawseq = read_first_fasta_record(inpath)
#     if defline is None or rawseq is None:
#         print(f"[WARN] {inpath.name}: no FASTA record found -> skipping")
#         return

#     # split at first '/'
#     if "/" in rawseq:
#         left_raw, right_raw = rawseq.split("/", 1)
#     else:
#         left_raw, right_raw = rawseq, ""

#     left = clean_seq(left_raw)
#     right = clean_seq(right_raw) if right_raw else ""

#     # build headers
#     target_id = extract_target_id(defline, inpath.stem)
#     header_target = f"protein|{target_id}"
#     header_binder = f"protein|binder{idx}"

#     records = []
#     # always write target record if non-empty
#     if left:
#         records.append((header_target, left))
#     else:
#         print(f"[WARN] {inpath.name}: left (target) sequence is empty after cleaning -> skipping target record")

#     # write binder record only if predicted (right) sequence exists
#     if right:
#         records.append((header_binder, right))
#     else:
#         # if no slash or no right part, we skip binder record silently
#         pass

#     if not records:
#         print(f"[WARN] {inpath.name}: no valid sequences to write after cleaning -> skipping file")
#         return

#     out_file = outdir / f"{inpath.stem}_converted.fasta"
#     write_fasta_file(out_file, records)
#     print(f"[OK] Wrote {out_file.name} with {len(records)} record(s): {', '.join(h for h,_ in records)}")

# def main():
#     p = argparse.ArgumentParser(description="Split LEFT/RIGHT sequences into two protein FASTA records with standard headers.")
#     p.add_argument("-i", "--in", dest="inpath", required=True, help="Input FASTA file or folder")
#     p.add_argument("-o", "--out", dest="outdir", required=True, help="Output folder (will be created if missing)")
#     args = p.parse_args()

#     inp = Path(args.inpath)
#     outdir = Path(args.outdir)
#     outdir.mkdir(parents=True, exist_ok=True)

#     files = []
#     if inp.is_file():
#         files = [inp]
#     elif inp.is_dir():
#         files = sorted(list(inp.glob("*.fa")) + list(inp.glob("*.fasta")))
#     else:
#         print("Input not found:", inp, file=sys.stderr)
#         sys.exit(2)

#     if not files:
#         print("No .fa/.fasta files found in", inp, file=sys.stderr)
#         sys.exit(1)

#     for idx, f in enumerate(files):
#         process_file(f, outdir, idx)

# if __name__ == "__main__":
#     main()





#!/usr/bin/env python3
"""
make_protein_binder_fastas.py (use LAST record)

For each input .fa/.fasta file (or a single file), read the LAST FASTA record,
split the sequence at the first '/' into target / predicted, clean both sequences,
and write an output file <orig_stem>_converted.fasta containing:

>protein|<TARGET_ID>
<TARGET_SEQUENCE>

>protein|binder<INDEX>
<PREDICTED_SEQUENCE>

INDEX is the zero-based index of the file being processed (first file -> binder0).
"""
import argparse
from pathlib import Path
import re
import sys

ALLOWED_AA = set("ACDEFGHIKLMNPQRSTVWYX")

def clean_seq(s: str) -> str:
    """Remove whitespace, uppercase, keep only standard AA letters (X allowed)."""
    s2 = re.sub(r"\s+", "", s).upper()
    return "".join(ch for ch in s2 if ch in ALLOWED_AA)

def read_last_fasta_record(path: Path):
    """
    Read the LAST FASTA record from path.
    Returns (defline_without_gt, joined_sequence) for the last record, or (None, None).
    """
    last_defline = None
    last_seq_lines = []
    cur_defline = None
    cur_seq_lines = []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith(">"):
                # when a new header appears, push previous into last_*
                if cur_defline is not None:
                    last_defline, last_seq_lines = cur_defline, cur_seq_lines
                cur_defline = line[1:].rstrip("\n")
                cur_seq_lines = []
            else:
                if cur_defline is not None:
                    cur_seq_lines.append(line.strip())
        # at EOF, the current record is the last one; prefer cur if present
        if cur_defline is not None:
            return cur_defline, "".join(cur_seq_lines)
    return None, None

def extract_target_id(defline: str, fallback_stem: str) -> str:
    """
    Extract a tidy target id from the defline.
    Strategy:
      - take token before first whitespace or comma
      - strip trailing pattern _<digits> (e.g. _0)
      - remove non-alphanumeric characters (keep letters+digits)
      - uppercase, limit to 20 chars
    Examples:
      "PD-L1_0, score=..." -> token "PD-L1_0" -> strip "_0" -> "PD-L1" -> remove '-' -> "PDL1"
    """
    if not defline:
        return fallback_stem.upper()[:20]
    token = re.split(r"[,\s]", defline.strip(), maxsplit=1)[0]
    # strip trailing _digits
    token = re.sub(r"_[0-9]+$", "", token)
    # keep letters and digits only
    token = re.sub(r"[^A-Za-z0-9]", "", token)
    token = token.upper()
    return token[:20] if token else fallback_stem.upper()[:20]

def write_fasta_file(path: Path, records):
    """
    records: list of tuples (header_without_gt, seq)
    Writes file, overwriting if exists.
    """
    with path.open("w", encoding="utf-8") as fh:
        for header, seq in records:
            fh.write(f">{header}\n")
            for i in range(0, len(seq), 80):
                fh.write(seq[i:i+80] + "\n")

def process_file(inpath: Path, outdir: Path, idx: int):
    defline, rawseq = read_last_fasta_record(inpath)
    if defline is None or rawseq is None:
        print(f"[WARN] {inpath.name}: no FASTA record found -> skipping")
        return

    # split at first '/'
    if "/" in rawseq:
        left_raw, right_raw = rawseq.split("/", 1)
    else:
        left_raw, right_raw = rawseq, ""

    left = clean_seq(left_raw)
    right = clean_seq(right_raw) if right_raw else ""

    # build headers
    target_id = extract_target_id(defline, inpath.stem)
    header_target = f"protein|{target_id}"
    header_binder = f"protein|binder{idx}"

    records = []
    # always write target record if non-empty
    if left:
        records.append((header_target, left))
    else:
        print(f"[WARN] {inpath.name}: left (target) sequence is empty after cleaning -> skipping target record")

    # write binder record only if predicted (right) sequence exists
    if right:
        records.append((header_binder, right))

    if not records:
        print(f"[WARN] {inpath.name}: no valid sequences to write after cleaning -> skipping file")
        return

    out_file = outdir / f"{inpath.stem}_converted.fasta"
    write_fasta_file(out_file, records)
    print(f"[OK] Wrote {out_file.name} with {len(records)} record(s): {', '.join(h for h,_ in records)}")

def main():
    p = argparse.ArgumentParser(description="Split LEFT/RIGHT sequences from LAST record into two protein FASTA records with standard headers.")
    p.add_argument("-i", "--in", dest="inpath", required=True, help="Input FASTA file or folder")
    p.add_argument("-o", "--out", dest="outdir", required=True, help="Output folder (will be created if missing)")
    args = p.parse_args()

    inp = Path(args.inpath)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    files = []
    if inp.is_file():
        files = [inp]
    elif inp.is_dir():
        files = sorted(list(inp.glob("*.fa")) + list(inp.glob("*.fasta")))
    else:
        print("Input not found:", inp, file=sys.stderr)
        sys.exit(2)

    if not files:
        print("No .fa/.fasta files found in", inp, file=sys.stderr)
        sys.exit(1)

    for idx, f in enumerate(files):
        process_file(f, outdir, idx)

if __name__ == "__main__":
    main()