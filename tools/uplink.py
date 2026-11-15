#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""uplink: standard intake gate for external return packages.

    Purpose.  One CLI gate for external return packages (zip plus md5
      plus per-file manifest): `verify` checks declared digests and
      prints a per-file evidence list; `intake` re-checks and, only on
      green, appends one register line (schema `rocqwash-uplink/1`);
      `pr-prep` renders a pull-request draft.  A digest mismatch or a
      missing declared member is fail-loud red.

    Interface.  faces `verify` / `intake` / `pr-prep` (flags `--package`,
      `--digest`, `--manifest`, `--source-seat`, `--landed-ref`,
      `--register`, `--dry-run`, `--out`, `--signature`) and a top-level
      `--selftest`; schema fields cited verbatim: `package`,
      `source-seat`, `md5`, `verified`, `landed-ref`, `exit`.

    Dependencies.  Python 3 stdlib only (argparse, hashlib, json, os,
      re, sys); zero network by design; self-contained zip reader
      (central directory plus RFC 1951 inflate; import list is closed).

    Evidence.  --selftest frozen vectors on temporary fixtures (zero
      writes outside them): verify row matrix on stored and deflate
      members, the red-row matrix, refusal codes, idempotent register
      append, dry-run zero write, checksum invariance, drafts.

    Exit-codes.  0 green; 1 fail-loud red (digest mismatch, missing or
      unlisted member, verify red under intake, an unverified register
      row, selftest red); 2 usage, IO, or invalid input content; 9
      missing input or structured refusal (absent input file, entry not
      found, ZIP64, encrypted, unsupported method, over budget).
"""
# Extended contract (kept outside the five-field block; annotation budget):
#
# Face contract (input / output / side effects / exits, per face):
#   verify
#     input:  --package ZIP (required); optional --digest (a 32-hex string,
#             or a sidecar file holding one bare 32-hex line or one
#             md5sum-style line naming the archive); optional --manifest
#             (md5sum-style rows "<hex>  <name>", '#' comments allowed);
#             at least one of --digest/--manifest is required.
#     output: stdout evidence rows: archive line, archive-digest row,
#             per-member rows (ok / mismatch / missing / unlisted /
#             declared-surface / dir / info), final summary line.
#     side effects: none (read-only face; the archive is parsed in memory).
#     exits:  0 green; 1 any red row; 2 usage, IO, or invalid input
#             content (malformed manifest/digest, corrupt archive);
#             9 missing input (absent package/sidecar/manifest) or
#             structured refusal (ZIP64, encrypted, unsupported method,
#             multi-disk, over budget).
#   intake
#     input:  `--package`, `--source-seat`, `--landed-ref` (all required,
#             non-empty); optional --digest/--manifest/--register;
#             --dry-run reports the would-append line and writes nothing.
#     output: the same verify evidence rows, then `appended`,
#             `duplicate-skip` or `dry-run` line naming the register.
#     side effects: appends exactly one line to the register file (default
#             <repo>/docs/uplink-intake.jsonl) and nothing else; the
#             register parent directory must already exist; a corrupt
#             register line refuses before any write; register lines
#             whose first character is `#` are schema comment lines and
#             are skipped by every reader face.
#     exits:  0 appended / duplicate-skipped / dry-run; 1 verify red (no
#             write); 2 usage, IO, or invalid input content; 9 missing
#             input or structured refusal.
#   pr-prep
#     input:  --package (exact `package` value of one register entry),
#             --out (draft file path, required; an implicit write is
#             refused), optional --register (alias `--registry`),
#             optional --signature (one free-text line rendered above
#             the table).
#     output: the draft file (deterministic bytes; same input gives the
#             same bytes) plus a stdout `draft written` line; several
#             matching entries render the latest one and say how many
#             matched.
#     side effects: writes the --out file only; it never opens a pull
#             request, never runs a subprocess, never touches the network.
#     exits:  0 draft written; 1 the matched entry is not verified-true
#             (invariant, no draft); 2 usage or IO error (draft path);
#             9 register or entry missing.
#
# Package form: a zip archive plus an optional digest sidecar and an
#   optional md5sum-style manifest.  A manifest row whose name is the
#   archive's own basename checks the archive digest.  The manifest file
#   riding inside the archive is reported as a declared-surface row (it is
#   the declaring face, never an unlisted member).
#
# Zip reader: self-contained central-directory parser plus RFC 1951
#   inflate (fixed and dynamic huffman, stored blocks).  Member digests
#   are md5 over the decompressed bytes; the zip CRC-32 is checked too
#   (a mismatch means the member bytes are corrupt, exit 2).  Stored
#   (method 0) and deflate (method 8) members are supported; ZIP64
#   markers, encrypted entries, other compression methods, multi-disk
#   archives and archives beyond the reader budget (2 GiB) are structured
#   refusals (exit 9), reported loudly, never skipped.
#
# Determinism: same input bytes give byte-identical stdout and drafts; no
#   clock, no randomness, no locale; rows sort by member name; nothing
#   reads the wall clock at any point (the schema carries no timestamp by
#   design, so entry content never depends on run time).
#
# Read-only pledge: `verify` writes nothing anywhere; `intake` writes the
#   register file only; `pr-prep` writes the --out file only; every other
#   byte of the repository tree is untouched (asserted by --selftest on a
#   fixture tree).
#
# NETRED: no network by design; every exchange rides offline files, so
#   there is no rate-limit, credential or fetch face to register.

import argparse
import hashlib
import json
import os
import re
import sys

SCHEMA = "rocqwash-uplink/1"
REGISTER_NAME = "uplink-intake.jsonl"
SELFTEST_MARK = "UPLINK-SELFTEST PASS"
ZIP_BUDGET_BYTES = 2 * 1024 * 1024 * 1024
ENTRY_FIELDS = ("package", "source-seat", "md5", "verified", "landed-ref",
                "exit")
_HEX32 = re.compile(r"[0-9a-fA-F]{32}\Z")
_MANIFEST_ROW = re.compile(r"([0-9a-fA-F]{32})[ \t]+\*?(.+)\Z")
_DIGEST_LINE = re.compile(r"([0-9a-fA-F]{32})(?:[ \t]+\*?(.*))?\Z")

# RFC 1951 length and distance tables (symbol 257..285 and 0..29).
_LENGTH_BASE = (3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35,
                43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258)
_LENGTH_EXTRA = (0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3,
                 4, 4, 4, 4, 5, 5, 5, 5, 0)
_DIST_BASE = (1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257,
              385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289,
              16385, 24577)
_DIST_EXTRA = (0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9,
               9, 10, 10, 11, 11, 12, 12, 13, 13)
_CLEN_ORDER = (16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1,
               15)


class InputError(Exception):
    """A failure with a decided exit code; the face prints it and exits."""

    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code


def _u16(blob, offset):
    return blob[offset] | (blob[offset + 1] << 8)


def _u32(blob, offset):
    return (blob[offset] | (blob[offset + 1] << 8) |
            (blob[offset + 2] << 16) | (blob[offset + 3] << 24))


def _make_crc_table():
    table = []
    for n in range(256):
        value = n
        for _ in range(8):
            value = (value >> 1) ^ (0xEDB88320 if value & 1 else 0)
        table.append(value)
    return table


_CRC_TABLE = _make_crc_table()


def _crc32(data):
    """CRC-32 (the zip member integrity check), table-driven, pure python."""
    crc = 0xFFFFFFFF
    for byte in data:
        crc = _CRC_TABLE[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF


def _md5_hex(data):
    return hashlib.md5(data).hexdigest()


class _CorruptStream(Exception):
    """Raised when a deflate member cannot be decoded; callers exit 2."""


class _Inflater:
    """RFC 1951 decoder over one member's compressed byte range."""

    def __init__(self, blob, pos, end):
        self.blob = blob
        self.pos = pos
        self.end = end
        self.bitbuf = 0
        self.bitcnt = 0

    def _bits(self, need):
        while self.bitcnt < need:
            if self.pos >= self.end:
                raise _CorruptStream("deflate stream truncated")
            self.bitbuf |= self.blob[self.pos] << self.bitcnt
            self.pos += 1
            self.bitcnt += 8
        value = self.bitbuf & ((1 << need) - 1)
        self.bitbuf >>= need
        self.bitcnt -= need
        return value

    def _align(self):
        drop = self.bitcnt & 7
        if drop:
            self._bits(drop)

    def _raw(self, count):
        if self.pos + count > self.end:
            raise _CorruptStream("stored block overruns the member")
        chunk = self.blob[self.pos:self.pos + count]
        self.pos += count
        return chunk

    def _build(self, lengths, incomplete_ok=False):
        counts = [0] * 16
        for length in lengths:
            if length:
                counts[length] += 1
        counts[0] = 0
        left = 1
        for length in range(1, 16):
            left = (left << 1) - counts[length]
            if left < 0:
                raise _CorruptStream("over-subscribed huffman code")
        offsets = [0] * 16
        for length in range(1, 15):
            offsets[length + 1] = offsets[length] + counts[length]
        symbols = [0] * sum(counts)
        for sym, length in enumerate(lengths):
            if length:
                symbols[offsets[length]] = sym
                offsets[length] += 1
        if left > 0 and not incomplete_ok:
            raise _CorruptStream("incomplete huffman code")
        return counts, symbols

    def _decode(self, table):
        counts, symbols = table
        code = 0
        first = 0
        index = 0
        for length in range(1, 16):
            code |= self._bits(1)
            count = counts[length]
            if code - first < count:
                return symbols[index + (code - first)]
            index += count
            first = (first + count) << 1
            code <<= 1
        raise _CorruptStream("invalid huffman code")

    def _dynamic_tables(self):
        hlit = self._bits(5) + 257
        hdist = self._bits(5) + 1
        hclen = self._bits(4) + 4
        clens = [0] * 19
        for i in range(hclen):
            clens[_CLEN_ORDER[i]] = self._bits(3)
        cl_table = self._build(clens)
        lengths = []
        while len(lengths) < hlit + hdist:
            sym = self._decode(cl_table)
            if sym < 16:
                lengths.append(sym)
            elif sym == 16:
                if not lengths:
                    raise _CorruptStream("length repeat with no previous "
                                         "length")
                lengths.extend([lengths[-1]] * (3 + self._bits(2)))
            elif sym == 17:
                lengths.extend([0] * (3 + self._bits(3)))
            else:
                lengths.extend([0] * (11 + self._bits(7)))
        if len(lengths) != hlit + hdist:
            raise _CorruptStream("code-length run overruns the declared "
                                 "count")
        lit = self._build(lengths[:hlit])
        dist_lengths = lengths[hlit:]
        single = sum(1 for value in dist_lengths if value) <= 1
        dist = self._build(dist_lengths, incomplete_ok=single)
        return lit, dist

    def _inflate_block(self, out, lit, dist):
        while True:
            sym = self._decode(lit)
            if sym < 256:
                out.append(sym)
                continue
            if sym == 256:
                return
            if sym > 285:
                raise _CorruptStream("invalid length symbol")
            idx = sym - 257
            length = _LENGTH_BASE[idx] + self._bits(_LENGTH_EXTRA[idx])
            dsym = self._decode(dist)
            if dsym > 29:
                raise _CorruptStream("invalid distance symbol")
            distance = _DIST_BASE[dsym] + self._bits(_DIST_EXTRA[dsym])
            if distance > len(out):
                raise _CorruptStream("distance reaches before the member "
                                     "start")
            start = len(out) - distance
            if distance >= length:
                out += out[start:start + length]
            else:
                for i in range(length):
                    out.append(out[start + i])

    def run(self):
        out = bytearray()
        fixed = None
        final = 0
        while not final:
            final = self._bits(1)
            btype = self._bits(2)
            if btype == 0:
                self._align()
                length = self._bits(16)
                nlen = self._bits(16)
                if length != (nlen ^ 0xFFFF):
                    raise _CorruptStream("stored block length check failed")
                out += self._raw(length)
            elif btype in (1, 2):
                if btype == 1:
                    if fixed is None:
                        # the fixed distance code is incomplete by design
                        # (30 five-bit codes, RFC 1951 section 3.2.6); the
                        # unused codes 30 and 31 decode to a loud corrupt
                        # stream instead of a silent wrong byte
                        fixed = (self._build([8] * 144 + [9] * 112 + [7] * 24
                                             + [8] * 8),
                                 self._build([5] * 30, incomplete_ok=True))
                    lit, dist = fixed
                else:
                    lit, dist = self._dynamic_tables()
                self._inflate_block(out, lit, dist)
            else:
                raise _CorruptStream("invalid deflate block type")
        return bytes(out)


class _Member:
    """One archive member: declared facts plus its computed md5."""

    def __init__(self, name, norm_name, method, usize, md5hex, is_dir):
        self.name = name
        self.norm_name = norm_name
        self.method = method
        self.usize = usize
        self.md5 = md5hex
        self.is_dir = is_dir


def _method_name(method):
    return "stored" if method == 0 else "deflate"


class _Archive:
    """Parsed archive: its own md5 and its members, sorted by member name."""

    def __init__(self, path, digest, members):
        self.path = path
        self.digest = digest
        self.members = sorted(members, key=lambda m: m.norm_name)


def _find_eocd(blob):
    """Locate the end-of-central-directory record; -1 when absent."""
    low = len(blob) - 22 - 65535
    if low < 0:
        low = 0
    pos = len(blob) - 22
    while pos >= low:
        if blob[pos:pos + 4] == b"PK\x05\x06":
            comment_len = _u16(blob, pos + 20)
            if pos + 22 + comment_len == len(blob):
                return pos
        pos -= 1
    return -1


def _decode_name(raw, flags):
    if flags & 0x800:
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InputError(2, "member name is not decable as utf-8: %s"
                             % exc)
    return raw.decode("cp437")


def load_archive(path):
    """Read and parse one zip archive in memory; raise InputError on any
    unreadable, corrupt or unsupported shape (2 / 2 / 9 respectively)."""
    if not os.path.isfile(path):
        raise InputError(9, "package not found: %s" % path)
    size = os.path.getsize(path)
    if size > ZIP_BUDGET_BYTES:
        raise InputError(9, "archive beyond the reader budget (%d bytes): %s"
                         % (size, path))
    try:
        with open(path, "rb") as handle:
            blob = handle.read()
    except OSError as exc:
        raise InputError(2, "package unreadable: %s (%s)" % (path, exc))
    digest = _md5_hex(blob)
    eocd = _find_eocd(blob)
    if eocd < 0:
        raise InputError(2, "not a zip archive (no end-of-central-directory "
                            "record): %s" % path)
    if _u16(blob, eocd + 4) != 0 or _u16(blob, eocd + 6) != 0:
        raise InputError(9, "multi-disk archives are refused: %s" % path)
    total_entries = _u16(blob, eocd + 10)
    cd_size = _u32(blob, eocd + 12)
    cd_offset = _u32(blob, eocd + 16)
    if 0xFFFFFFFF in (cd_size, cd_offset, total_entries):
        raise InputError(9, "ZIP64 archives are refused: %s" % path)
    members = []
    pos = cd_offset
    for _ in range(total_entries):
        if pos + 46 > len(blob) or blob[pos:pos + 4] != b"PK\x01\x02":
            raise InputError(2, "central directory damaged at byte %d: %s"
                             % (pos, path))
        flags = _u16(blob, pos + 8)
        method = _u16(blob, pos + 10)
        crc = _u32(blob, pos + 16)
        csize = _u32(blob, pos + 20)
        usize = _u32(blob, pos + 24)
        nlen = _u16(blob, pos + 28)
        elen = _u16(blob, pos + 30)
        clen = _u16(blob, pos + 32)
        offset = _u32(blob, pos + 42)
        name = _decode_name(blob[pos + 46:pos + 46 + nlen], flags)
        pos += 46 + nlen + elen + clen
        if 0xFFFFFFFF in (csize, usize, offset):
            raise InputError(9, "ZIP64 member marker on %r: %s" % (name, path))
        if flags & 0x1:
            raise InputError(9, "encrypted member %r is refused: %s"
                             % (name, path))
        is_dir = name.endswith("/")
        norm_name = name.replace("\\", "/")
        if is_dir:
            members.append(_Member(name, norm_name, method, 0, "", True))
            continue
        if method not in (0, 8):
            raise InputError(9, "compression method %d on %r is refused: %s"
                             % (method, name, path))
        if offset + 30 > len(blob) or blob[offset:offset + 4] != b"PK\x03\x04":
            raise InputError(2, "local header damaged for %r: %s"
                             % (name, path))
        local_nlen = _u16(blob, offset + 26)
        local_elen = _u16(blob, offset + 28)
        start = offset + 30 + local_nlen + local_elen
        if start + csize > len(blob):
            raise InputError(2, "member %r data overruns the archive: %s"
                             % (name, path))
        data = blob[start:start + csize]
        if method == 8:
            inflater = _Inflater(data, 0, len(data))
            try:
                raw = inflater.run()
            except _CorruptStream as exc:
                raise InputError(2, "member %r deflate stream corrupt (%s): "
                                    "%s" % (name, exc, path))
        else:
            raw = data
        if len(raw) != usize:
            raise InputError(2, "member %r size disagreement (central %d, "
                                "decoded %d): %s" % (name, usize, len(raw),
                                                     path))
        if _crc32(raw) != crc:
            raise InputError(2, "member %r CRC-32 mismatch (corrupt bytes): "
                                "%s" % (name, path))
        members.append(_Member(name, norm_name, method, usize,
                               _md5_hex(raw), False))
    if not any(not member.is_dir for member in members):
        raise InputError(2, "archive holds no file members: %s" % path)
    return _Archive(path, digest, members)


def parse_digest_arg(value, package_path):
    """--digest accepts a 32-hex string or a sidecar file; returns the hex."""
    if _HEX32.match(value):
        return value.lower()
    try:
        with open(value, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        raise InputError(9, "digest sidecar not found: %s (%s)" % (value,
                                                                   exc))
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        matched = _DIGEST_LINE.match(stripped)
        if not matched:
            raise InputError(2, "digest sidecar line is malformed: %s"
                             % stripped)
        hex_value = matched.group(1).lower()
        declared_name = (matched.group(2) or "").strip()
        if declared_name:
            declared = os.path.basename(declared_name.replace("\\", "/"))
            package = os.path.basename(package_path.replace("\\", "/"))
            if declared != package:
                raise InputError(2, "digest sidecar names a different file "
                                    "(%s, expected %s)" % (declared, package))
        return hex_value
    raise InputError(2, "digest sidecar holds no digest line: %s" % value)


def parse_manifest(path):
    """--manifest is an md5sum-style file; returns rows (hex, norm name)."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        raise InputError(9, "manifest not found: %s (%s)" % (path, exc))
    rows = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        matched = _MANIFEST_ROW.match(stripped)
        if not matched:
            raise InputError(2, "manifest line %d is malformed: %s"
                             % (lineno, stripped))
        name = matched.group(2).strip()
        if not name:
            raise InputError(2, "manifest line %d names no file: %s"
                             % (lineno, stripped))
        rows.append((matched.group(1).lower(), name.replace("\\", "/")))
    if not rows:
        raise InputError(2, "manifest declares no files: %s" % path)
    return rows


def _member_row(prefix, member, declared=None):
    tail = "method=%s %s" % (_method_name(member.method), member.norm_name)
    if member.is_dir:
        return "member dir %s" % member.norm_name
    if declared is None:
        return "%s md5=%s size=%d %s" % (prefix, member.md5, member.usize,
                                         tail)
    return "%s declared=%s computed=%s size=%d %s" % (prefix, declared,
                                                      member.md5,
                                                      member.usize, tail)


def verify_rows(package_path, archive, digest_decl, manifest_rows,
                manifest_path):
    """Compute the evidence rows and the red flag for one package check."""
    rows = []
    red = False
    ok = mismatch = missing = unlisted = dirs = 0
    rows.append("archive %s" % package_path)
    rows.append("archive-digest computed=%s" % archive.digest)
    if digest_decl is not None:
        if digest_decl == archive.digest:
            rows.append("archive-digest ok %s" % archive.digest)
            ok += 1
        else:
            rows.append("archive-digest mismatch declared=%s computed=%s"
                        % (digest_decl, archive.digest))
            mismatch += 1
            red = True
    members = dict((member.norm_name, member)
                   for member in archive.members if not member.is_dir)
    declared = set()
    archive_norm = os.path.basename(package_path.replace("\\", "/"))
    surface = ""
    if manifest_rows is not None:
        rows.append("manifest declared-rows=%d" % len(manifest_rows))
        surface = os.path.basename(manifest_path.replace("\\", "/"))
        for hex_value, name in manifest_rows:
            if name == archive_norm:
                if hex_value == archive.digest:
                    rows.append("archive-digest ok %s" % archive.digest)
                    ok += 1
                else:
                    rows.append("archive-digest mismatch declared=%s "
                                "computed=%s" % (hex_value, archive.digest))
                    mismatch += 1
                    red = True
                continue
            member = members.get(name)
            if member is None:
                rows.append("member missing declared=%s %s" % (hex_value,
                                                               name))
                missing += 1
                red = True
                continue
            declared.add(name)
            if member.md5 == hex_value:
                rows.append(_member_row("member ok", member))
                ok += 1
            else:
                rows.append(_member_row("member mismatch", member,
                                        declared=hex_value))
                mismatch += 1
                red = True
    else:
        for member in archive.members:
            if not member.is_dir:
                rows.append(_member_row("member info", member))
    for member in archive.members:
        if member.is_dir:
            rows.append("member dir %s" % member.norm_name)
            dirs += 1
            continue
        if member.norm_name in declared:
            continue
        if manifest_rows is not None and member.norm_name == surface:
            rows.append(_member_row("declared-surface", member))
            continue
        if manifest_rows is not None:
            rows.append(_member_row("member unlisted", member))
            unlisted += 1
            red = True
    rows.append("verify %s ok=%d mismatch=%d missing=%d unlisted=%d dir=%d "
                "archive=%s"
                % ("red" if red else "green", ok, mismatch, missing,
                   unlisted, dirs, package_path))
    return rows, red


def cmd_verify(args):
    if not args.digest and not args.manifest:
        raise InputError(2, "nothing to verify against: pass --digest or "
                            "--manifest")
    archive = load_archive(args.package)
    digest_decl = None
    if args.digest:
        digest_decl = parse_digest_arg(args.digest, args.package)
    manifest_rows = None
    if args.manifest:
        manifest_rows = parse_manifest(args.manifest)
    rows, red = verify_rows(args.package, archive, digest_decl,
                            manifest_rows, args.manifest)
    for line in rows:
        sys.stdout.write(line + "\n")
    if red:
        sys.stderr.write("uplink verify: red rows present; nothing is "
                         "skipped silently\n")
        return 1
    return 0


def resolve_register(explicit):
    if explicit:
        return explicit
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(repo, "docs", REGISTER_NAME)


def read_register(path):
    """Parse the register JSONL; None when absent; InputError(9) on damage.
    Lines whose first character is `#` are schema comment lines and are
    skipped (the register schema pins that form)."""
    if not os.path.isfile(path):
        return None
    entries = []
    with open(path, "r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                obj = json.loads(line)
            except ValueError as exc:
                raise InputError(9, "register line %d is not valid JSON (%s):"
                                    " %s" % (lineno, exc, path))
            if not isinstance(obj, dict):
                raise InputError(9, "register line %d is not a JSON object: "
                                    "%s" % (lineno, path))
            entries.append(obj)
    return entries


def _same_entry(existing, entry):
    for field in ENTRY_FIELDS:
        if existing.get(field) != entry.get(field):
            return False
    return True


def cmd_intake(args):
    if not args.source_seat.strip():
        raise InputError(2, "--source-seat must be a non-empty identifier")
    if not args.landed_ref.strip():
        raise InputError(2, "--landed-ref must be a non-empty reference")
    if not args.digest and not args.manifest:
        raise InputError(2, "nothing to verify against: pass --digest or "
                            "--manifest")
    archive = load_archive(args.package)
    digest_decl = None
    if args.digest:
        digest_decl = parse_digest_arg(args.digest, args.package)
    manifest_rows = None
    if args.manifest:
        manifest_rows = parse_manifest(args.manifest)
    rows, red = verify_rows(args.package, archive, digest_decl,
                            manifest_rows, args.manifest)
    for line in rows:
        sys.stdout.write(line + "\n")
    if red:
        sys.stderr.write("uplink intake: verify red; nothing appended\n")
        return 1
    register = resolve_register(args.register)
    entries = read_register(register)
    entry = {
        "schema": SCHEMA,
        "package": args.package,
        "source-seat": args.source_seat,
        "md5": archive.digest,
        "verified": True,
        "landed-ref": args.landed_ref,
        "exit": 0,
    }
    if entries is not None:
        for existing in entries:
            if _same_entry(existing, entry):
                sys.stdout.write("duplicate-skip package=%s register=%s\n"
                                 % (args.package, register))
                return 0
    line = json.dumps(entry, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))
    if args.dry_run:
        sys.stdout.write("dry-run would-append package=%s md5=%s "
                         "register=%s\n" % (args.package, archive.digest,
                                            register))
        return 0
    parent = os.path.dirname(os.path.abspath(register))
    if not os.path.isdir(parent):
        raise InputError(2, "register directory missing: %s" % parent)
    with open(register, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
    sys.stdout.write("appended package=%s register=%s\n" % (args.package,
                                                            register))
    return 0


def _table_cell(value):
    return str(value).replace("|", "\\|")


def cmd_pr_prep(args):
    register = resolve_register(args.register)
    entries = read_register(register)
    if entries is None:
        raise InputError(9, "register not found: %s" % register)
    matches = [entry for entry in entries
               if entry.get("package") == args.package]
    if not matches:
        raise InputError(9, "no intake entry for package: %s" % args.package)
    entry = matches[-1]
    if entry.get("verified") is not True:
        raise InputError(1, "the matched entry is not verified-true; no "
                            "draft is rendered")
    lines = []
    lines.append("# PR draft: return package intake %s"
                 % _table_cell(entry.get("package", args.package)))
    lines.append("")
    if args.signature:
        lines.append(args.signature)
        lines.append("")
    lines.append("| field | value |")
    lines.append("|---|---|")
    absent = []
    for field in ENTRY_FIELDS:
        if field in entry and entry[field] is not None:
            lines.append("| %s | %s |" % (field, _table_cell(entry[field])))
        else:
            absent.append(field)
    lines.append("")
    lines.append("- register: %s" % register)
    lines.append("- entries matched: %d; the latest entry is rendered"
                 % len(matches))
    if absent:
        lines.append("- fields absent from the entry: %s" % ", ".join(absent))
    lines.append("- verification was attested by the verify face at intake "
                 "time")
    lines.append("- generated by tools/uplink.py pr-prep; this file does not "
                 "open a pull request")
    lines.append("")
    text = "\n".join(lines)
    out_parent = os.path.dirname(os.path.abspath(args.out))
    if not os.path.isdir(out_parent):
        raise InputError(2, "draft directory missing (create it first): %s"
                         % out_parent)
    payload = text.encode("utf-8")
    with open(args.out, "wb") as handle:
        handle.write(payload)
    sys.stdout.write("draft written path=%s bytes=%d\n"
                     % (args.out, len(payload)))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="uplink.py",
        description="Standard intake gate for external return packages "
                    "(verify / intake / pr-prep; schema rocqwash-uplink/1; "
                    "md5 mismatch and missing declared members are "
                    "fail-loud).")
    parser.add_argument("--selftest", action="store_true",
                        help="run the temporary-fixture vector group")
    sub = parser.add_subparsers(dest="command", metavar="FACE")
    face_verify = sub.add_parser(
        "verify", help="check one return package against its declared "
                       "digests (read-only)")
    face_verify.add_argument("--package", required=True,
                             help="return package zip path")
    face_verify.add_argument("--digest", default="",
                             help="32-hex digest or sidecar file of the "
                                  "archive itself")
    face_verify.add_argument("--manifest", default="",
                             help="md5sum-style per-file manifest")
    face_intake = sub.add_parser(
        "intake", help="verify a package and, only on green, append one "
                       "register line")
    face_intake.add_argument("--package", required=True,
                             help="return package zip path")
    face_intake.add_argument("--source-seat", required=True,
                             dest="source_seat",
                             help="non-empty producer identifier recorded "
                                  "as the `source-seat` field")
    face_intake.add_argument("--landed-ref", required=True,
                             dest="landed_ref",
                             help="non-empty reference recorded as the "
                                  "`landed-ref` field")
    face_intake.add_argument("--digest", default="",
                             help="32-hex digest or sidecar file of the "
                                  "archive itself")
    face_intake.add_argument("--manifest", default="",
                             help="md5sum-style per-file manifest")
    face_intake.add_argument("--register", "--registry", dest="register",
                             default="", metavar="PATH",
                             help="register path override (default "
                                  "docs/uplink-intake.jsonl)")
    face_intake.add_argument("--dry-run", action="store_true",
                             dest="dry_run",
                             help="report the would-append line, write "
                                  "nothing")
    face_pr = sub.add_parser(
        "pr-prep", help="render the pull-request description draft of one "
                        "register entry (never opens a pull request)")
    face_pr.add_argument("--package", required=True,
                         help="exact `package` value of a register entry")
    face_pr.add_argument("--out", required=True,
                         help="draft file path (an implicit write is "
                              "refused)")
    face_pr.add_argument("--register", "--registry", dest="register",
                         default="", metavar="PATH",
                         help="register path override (default "
                              "docs/uplink-intake.jsonl)")
    face_pr.add_argument("--signature", default="",
                         help="one free-text line rendered above the table")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        if args.command:
            parser.error("--selftest takes no face")
        return selftest()
    faces = {"verify": cmd_verify, "intake": cmd_intake,
             "pr-prep": cmd_pr_prep}
    face = faces.get(args.command)
    if face is None:
        parser.print_usage(sys.stderr)
        sys.stderr.write("uplink: a face is required: verify | intake | "
                         "pr-prep\n")
        return 2
    try:
        return face(args)
    except InputError as exc:
        sys.stderr.write("uplink %s: %s\n" % (args.command, exc))
        return exc.code


def selftest():
    """Temporary-fixture vectors; prints SELFTEST PASS, exits 0 on green."""
    fails = []
    base = os.environ.get("TEMP") or os.environ.get("TMP") or os.getcwd()
    root = os.path.join(base, "uplink_selftest_%d" % os.getpid())
    _force_mkdir(root)
    try:
        _selftest_vectors(root, fails)
    finally:
        # fixture cleanup only; tool logic never swallows errors this way
        _force_rmtree(root)
    if fails:
        for line in fails:
            sys.stderr.write("SELFTEST FAIL %s\n" % line)
        return 1
    sys.stdout.write("%s (19 vectors)\n" % SELFTEST_MARK)
    return 0


def _force_mkdir(path):
    os.makedirs(path, exist_ok=True)


def _force_rmtree(path):
    """Best-effort fixture cleanup (mirrors the house tools' rmtree face)."""
    for dirpath, dirnames, filenames in os.walk(path, topdown=False):
        for name in filenames:
            try:
                os.remove(os.path.join(dirpath, name))
            except OSError:
                pass
        for name in dirnames:
            try:
                os.rmdir(os.path.join(dirpath, name))
            except OSError:
                pass
    try:
        os.rmdir(path)
    except OSError:
        pass


def _write_fixture(root, rel, data):
    path = os.path.join(root, rel)
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)
    return path


def _tree_snapshot(tree_root):
    """Map of rel path to md5 over every file below tree_root."""
    snapshot = {}
    for dirpath, _dirnames, filenames in os.walk(tree_root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, tree_root).replace("\\", "/")
            with open(full, "rb") as handle:
                snapshot[rel] = _md5_hex(handle.read())
    return snapshot


def _zip_bytes(members, cd_flags=0, force_usize=None, comment=b""):
    """Assemble a zip archive byte image from member tuples
    (name, method, raw, comp); comp is the compressed body for method 8."""
    out = bytearray()
    central = bytearray()
    count = 0
    for name, method, raw, comp in members:
        data = raw if method == 0 else comp
        crc = _crc32(raw)
        offset = len(out)
        nb = name.encode("utf-8")
        out += b"PK\x03\x04"
        out += (20).to_bytes(2, "little")
        out += (0).to_bytes(2, "little")
        out += method.to_bytes(2, "little")
        out += (0).to_bytes(2, "little")
        out += (0).to_bytes(2, "little")
        out += crc.to_bytes(4, "little")
        out += len(data).to_bytes(4, "little")
        out += len(raw).to_bytes(4, "little")
        out += len(nb).to_bytes(2, "little")
        out += (0).to_bytes(2, "little")
        out += nb
        out += data
        usize = len(raw) if force_usize is None else force_usize
        central += b"PK\x01\x02"
        central += (20).to_bytes(2, "little")
        central += (20).to_bytes(2, "little")
        central += cd_flags.to_bytes(2, "little")
        central += method.to_bytes(2, "little")
        central += (0).to_bytes(2, "little")
        central += (0).to_bytes(2, "little")
        central += crc.to_bytes(4, "little")
        central += len(data).to_bytes(4, "little")
        central += usize.to_bytes(4, "little")
        central += len(nb).to_bytes(2, "little")
        central += (0).to_bytes(2, "little")
        central += (0).to_bytes(2, "little")
        central += (0).to_bytes(2, "little")
        central += (0).to_bytes(2, "little")
        central += (0).to_bytes(4, "little")
        central += offset.to_bytes(4, "little")
        central += nb
        count += 1
    cd_offset = len(out)
    out += central
    out += b"PK\x05\x06"
    out += (0).to_bytes(2, "little")
    out += (0).to_bytes(2, "little")
    out += count.to_bytes(2, "little")
    out += count.to_bytes(2, "little")
    out += len(central).to_bytes(4, "little")
    out += cd_offset.to_bytes(4, "little")
    out += len(comment).to_bytes(2, "little")
    out += comment
    return bytes(out)


_PLAIN_A = b"alpha payload line\n"
_PLAIN_B = (b"uplink return package sample content line one\n"
            b"uplink return package sample content line two\n")
_PLAIN_B_MD5 = "dd31847848482dd55085e6a714fc64fb"
_PLAIN_B_CRC = 769206387
_DEFLATE_B = bytes.fromhex(
    "2b2dc8c9cccb56284a2d292dca5328484cce4e4c4f55284ecc2dc8495548cecf"
    "2b49cd2b51002a4955c8cf4be52a255a7549793e1700")
_PLAIN_C = b"beta\n"


def _std_zip():
    return _zip_bytes([
        ("data/alpha.txt", 0, _PLAIN_A, None),
        ("data/sample.txt", 8, _PLAIN_B, _DEFLATE_B),
        ("data/beta.txt", 0, _PLAIN_C, None),
    ])


def _selftest_vectors(root, fails):
    """The frozen vector group; appends one line per red check to fails."""
    package = _write_fixture(root, "pkg/return.zip", _std_zip())
    zip_digest = _md5_hex(_std_zip())

    # V16 pins: crc32 implementation and the canned deflate vector.
    if _crc32(_PLAIN_B) != _PLAIN_B_CRC:
        fails.append("V16 crc32 pin drifted on the canned plain bytes")
    if _crc32(b"a") != 0xE8B7BE43:
        fails.append("V16 crc32 pin drifted on the one-byte vector")
    if _md5_hex(_PLAIN_B) != _PLAIN_B_MD5:
        fails.append("V16 canned deflate plain-bytes md5 drifted")

    # V1: digest-only verify is green and prints the per-file evidence list.
    rc, out = _run(["verify", "--package", package,
                    "--digest", zip_digest])
    if rc != 0 or "archive-digest ok" not in out or "verify green" not in out:
        fails.append("V1 digest-only verify should be green rc=0 "
                     "(rc=%d out=%r)" % (rc, out))
    if "member info md5=%s" % _md5_hex(_PLAIN_A) not in out:
        fails.append("V1 member info rows missing from the evidence list")

    # V1b: a sidecar file form of --digest is accepted when it names the
    # archive; an archive comment does not break the EOCD search.
    commented = _zip_bytes([("data/alpha.txt", 0, _PLAIN_A, None)],
                           comment=b"gate-evidence")
    pkg2 = _write_fixture(root, "pkg/commented.zip", commented)
    sidecar = _write_fixture(
        root, "pkg/commented.zip.md5",
        ("%s  commented.zip\n" % _md5_hex(commented)).encode("utf-8"))
    rc, out = _run(["verify", "--package", pkg2, "--digest", sidecar])
    if rc != 0 or "verify green" not in out:
        fails.append("V1b sidecar digest verify should be green rc=0 "
                     "(rc=%d out=%r)" % (rc, out))

    # V2: a manifest listing every member plus the archive itself is green.
    manifest = _write_fixture(root, "pkg/MANIFEST.txt", (
        "# return package manifest\n"
        "%s  data/alpha.txt\n"
        "%s  data/sample.txt\n"
        "%s  data/beta.txt\n"
        "%s  return.zip\n" % (_md5_hex(_PLAIN_A), _PLAIN_B_MD5,
                              _md5_hex(_PLAIN_C),
                              zip_digest)).encode("utf-8"))
    rc, out = _run(["verify", "--package", package, "--manifest", manifest])
    if rc != 0 or "verify green ok=4" not in out:
        fails.append("V2 manifest verify should be green with ok=4 "
                     "(rc=%d out=%r)" % (rc, out))
    if "member mismatch" in out or "member unlisted" in out:
        fails.append("V2 manifest verify produced red rows: %r" % out)

    # V3: a wrong archive digest is fail-loud red rc=1.
    wrong = "0" * 32
    rc, out = _run(["verify", "--package", package, "--digest", wrong])
    if rc != 1 or "archive-digest mismatch" not in out or \
            "verify red" not in out:
        fails.append("V3 wrong digest should be red rc=1 (rc=%d out=%r)"
                     % (rc, out))

    # V4: a wrong member md5 in the manifest is fail-loud red rc=1.
    bad_manifest = _write_fixture(root, "pkg/BAD1.txt", (
        "%s  data/alpha.txt\n" % ("1" * 32)).encode("utf-8"))
    rc, out = _run(["verify", "--package", package,
                    "--manifest", bad_manifest])
    if rc != 1 or "member mismatch" not in out:
        fails.append("V4 wrong member md5 should be red rc=1 "
                     "(rc=%d out=%r)" % (rc, out))

    # V5: a declared member absent from the archive is fail-loud red rc=1.
    ghost = _write_fixture(root, "pkg/BAD2.txt", (
        "%s  data/ghost.txt\n" % ("2" * 32)).encode("utf-8"))
    rc, out = _run(["verify", "--package", package, "--manifest", ghost])
    if rc != 1 or "member missing declared=" not in out:
        fails.append("V5 missing declared member should be red rc=1 "
                     "(rc=%d out=%r)" % (rc, out))

    # V6: a member not declared by the manifest is unlisted and red rc=1.
    partial = _write_fixture(root, "pkg/PARTIAL.txt", (
        "%s  data/alpha.txt\n" % _md5_hex(_PLAIN_A)).encode("utf-8"))
    rc, out = _run(["verify", "--package", package,
                    "--manifest", partial])
    if rc != 1 or "member unlisted" not in out:
        fails.append("V6 unlisted member should be red rc=1 "
                     "(rc=%d out=%r)" % (rc, out))

    # V7: input faces are rc=9 for missing input files, rc=2 for invalid
    # input content (not-a-zip, nothing to verify against, malformed
    # manifest).
    rc, out = _run(["verify", "--package", os.path.join(root, "nope.zip"),
                    "--digest", zip_digest])
    if rc != 9:
        fails.append("V7 missing package should be rc=9 (rc=%d)" % rc)
    garbage = _write_fixture(root, "pkg/garbage.bin", b"not a zip at all")
    rc, out = _run(["verify", "--package", garbage, "--digest", "0" * 32])
    if rc != 2:
        fails.append("V7 not-a-zip should be rc=2 (rc=%d)" % rc)
    rc, out = _run(["verify", "--package", package])
    if rc != 2:
        fails.append("V7 no digest and no manifest should be rc=2 (rc=%d)"
                     % rc)
    malformed = _write_fixture(root, "pkg/BADFORM.txt",
                               b"zzzz  data/alpha.txt\n")
    rc, out = _run(["verify", "--package", package,
                    "--manifest", malformed])
    if rc != 2:
        fails.append("V7 malformed manifest should be rc=2 (rc=%d)" % rc)
    rc, out = _run(["verify", "--package", package, "--digest",
                    os.path.join(root, "absent-sidecar.txt")])
    if rc != 9:
        fails.append("V7 missing digest sidecar should be rc=9 (rc=%d)" % rc)
    rc, out = _run(["verify", "--package", package, "--manifest",
                    os.path.join(root, "absent-manifest.txt")])
    if rc != 9:
        fails.append("V7 missing manifest file should be rc=9 (rc=%d)" % rc)

    # V8: structured refusals are rc=9 (encrypted flag, unknown method,
    # ZIP64 marker).
    encrypted_bytes = _zip_bytes([("data/alpha.txt", 0, _PLAIN_A, None)],
                                 cd_flags=1)
    encrypted = _write_fixture(root, "pkg/enc.zip", encrypted_bytes)
    rc, out = _run(["verify", "--package", encrypted, "--digest",
                    _md5_hex(encrypted_bytes)])
    if rc != 9:
        fails.append("V8 encrypted member should be rc=9 (rc=%d)" % rc)
    alien_bytes = _zip_bytes([("data/x.bin", 12, b"\x00\x00", b"\x00\x00")])
    alien = _write_fixture(root, "pkg/m12.zip", alien_bytes)
    rc, out = _run(["verify", "--package", alien, "--digest",
                    _md5_hex(alien_bytes)])
    if rc != 9:
        fails.append("V8 unsupported method should be rc=9 (rc=%d)" % rc)
    zip64_bytes = _zip_bytes([("data/alpha.txt", 0, _PLAIN_A, None)],
                             force_usize=0xFFFFFFFF)
    zip64 = _write_fixture(root, "pkg/z64.zip", zip64_bytes)
    rc, out = _run(["verify", "--package", zip64, "--digest",
                    _md5_hex(zip64_bytes)])
    if rc != 9:
        fails.append("V8 ZIP64 marker should be rc=9 (rc=%d)" % rc)

    # V9: intake appends one schema line on green; a byte-identical repeat
    # duplicate-skips without writing; dry-run writes nothing.
    reg_dir = os.path.join(root, "repo9", "docs")
    os.makedirs(reg_dir, exist_ok=True)
    register = os.path.join(reg_dir, REGISTER_NAME)
    rc, out = _run(["intake", "--package", package,
                    "--source-seat", "outer-line-a",
                    "--landed-ref", "incoming/return-a",
                    "--digest", zip_digest, "--register", register])
    if rc != 0 or "appended package=" not in out:
        fails.append("V9 intake should append rc=0 (rc=%d out=%r)"
                     % (rc, out))
    with open(register, "r", encoding="utf-8") as handle:
        first_bytes = handle.read()
    entry = json.loads(first_bytes.strip().splitlines()[-1])
    if entry.get("schema") != SCHEMA:
        fails.append("V9 register schema drifted: %r" % entry.get("schema"))
    if (entry.get("package"), entry.get("source-seat"),
            entry.get("md5"), entry.get("verified"),
            entry.get("landed-ref"), entry.get("exit")) != \
            (package, "outer-line-a", zip_digest, True,
             "incoming/return-a", 0):
        fails.append("V9 register fields drifted: %r" % entry)
    rc, out = _run(["intake", "--package", package,
                    "--source-seat", "outer-line-a",
                    "--landed-ref", "incoming/return-a",
                    "--digest", zip_digest, "--register", register])
    if rc != 0 or "duplicate-skip package=" not in out:
        fails.append("V9 repeat intake should duplicate-skip rc=0 "
                     "(rc=%d out=%r)" % (rc, out))
    with open(register, "r", encoding="utf-8") as handle:
        if handle.read() != first_bytes:
            fails.append("V9 duplicate intake changed register bytes")
    dry_register = os.path.join(root, "repo9dry", "docs", REGISTER_NAME)
    rc, out = _run(["intake", "--package", package,
                    "--source-seat", "outer-line-a",
                    "--landed-ref", "incoming/return-a",
                    "--digest", zip_digest, "--register", dry_register,
                    "--dry-run"])
    if rc != 0 or "dry-run would-append" not in out:
        fails.append("V9 dry-run intake should report rc=0 (rc=%d out=%r)"
                     % (rc, out))
    if os.path.exists(dry_register):
        fails.append("V9 dry-run intake created the register file")

    # V10: intake on a red verify appends nothing.
    red_register = os.path.join(root, "repo10", "docs", REGISTER_NAME)
    rc, out = _run(["intake", "--package", package,
                    "--source-seat", "outer-line-a",
                    "--landed-ref", "incoming/return-a",
                    "--digest", wrong, "--register", red_register])
    if rc != 1 or os.path.exists(red_register):
        fails.append("V10 intake on red verify should be rc=1 with no "
                     "register (rc=%d exists=%r)"
                     % (rc, os.path.exists(red_register)))

    # V11: an empty `--source-seat` or `--landed-ref` is invalid input rc=2.
    rc, out = _run(["intake", "--package", package, "--source-seat", " ",
                    "--landed-ref", "r", "--digest", zip_digest,
                    "--register", register])
    if rc != 2:
        fails.append("V11 blank source identity should be rc=2 (rc=%d)" % rc)

    # V12: a corrupt register line refuses before any write (intake and
    # pr-prep both rc=9, the missing-or-damaged-input face).
    bad_reg_dir = os.path.join(root, "repo12", "docs")
    os.makedirs(bad_reg_dir, exist_ok=True)
    bad_register = os.path.join(bad_reg_dir, REGISTER_NAME)
    with open(bad_register, "w", encoding="utf-8") as handle:
        handle.write('{"package": "ok"}\nnot-json{\n')
    with open(bad_register, "r", encoding="utf-8") as handle:
        before = handle.read()
    rc, out = _run(["intake", "--package", package,
                    "--source-seat", "outer-line-a",
                    "--landed-ref", "incoming/return-a",
                    "--digest", zip_digest, "--register", bad_register])
    if rc != 9:
        fails.append("V12 intake on corrupt register should be rc=9 "
                     "(rc=%d)" % rc)
    with open(bad_register, "r", encoding="utf-8") as handle:
        if handle.read() != before:
            fails.append("V12 intake on corrupt register wrote bytes")
    rc, out = _run(["pr-prep", "--package", package, "--out",
                    os.path.join(root, "out12", "draft.md"),
                    "--register", bad_register])
    if rc != 9:
        fails.append("V12 pr-prep on corrupt register should be rc=9 "
                     "(rc=%d)" % rc)

    # V13: pr-prep renders a deterministic draft; unknown entry and
    # missing register are rc=2.
    out_dir = os.path.join(root, "out13")
    os.makedirs(out_dir, exist_ok=True)
    draft = os.path.join(out_dir, "draft.md")
    rc, out = _run(["pr-prep", "--package", package, "--out", draft,
                    "--register", register,
                    "--signature", "draft signature line"])
    if rc != 0 or "draft written" not in out:
        fails.append("V13 pr-prep should write the draft rc=0 "
                     "(rc=%d out=%r)" % (rc, out))
    with open(draft, "rb") as handle:
        draft_bytes = handle.read()
    if b"| source-seat | outer-line-a |" not in draft_bytes or \
            b"| landed-ref | incoming/return-a |" not in draft_bytes or \
            b"| verified | True |" not in draft_bytes:
        fails.append("V13 draft table rows missing: %r" % draft_bytes[:400])
    draft2 = os.path.join(out_dir, "draft2.md")
    rc, out = _run(["pr-prep", "--package", package, "--out", draft2,
                    "--register", register,
                    "--signature", "draft signature line"])
    with open(draft2, "rb") as handle:
        if handle.read() != draft_bytes:
            fails.append("V13 draft rerun is not byte-identical")
    rc, out = _run(["pr-prep", "--package", "no-such-pkg", "--out", draft,
                    "--register", register])
    if rc != 9:
        fails.append("V13 unknown package should be rc=9 (rc=%d)" % rc)
    rc, out = _run(["pr-prep", "--package", package, "--out", draft,
                    "--register", os.path.join(root, "absent-reg.jsonl")])
    if rc != 9:
        fails.append("V13 missing register should be rc=9 (rc=%d)" % rc)
    rc, out = _run(["pr-prep", "--package", package,
                    "--out", os.path.join(root, "missing-dir", "d.md"),
                    "--register", register])
    if rc != 2:
        fails.append("V13 draft into a missing directory should be rc=2 "
                     "(rc=%d)" % rc)

    # V13b: the `--registry` alias resolves the same register face; a
    # register whose first lines are `#` schema comments reads fine.
    with open(register, "r", encoding="utf-8") as handle:
        reg_body = handle.read()
    with open(register, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("# schema comment line one\n" + reg_body)
    draft3 = os.path.join(out_dir, "draft3.md")
    rc, out = _run(["pr-prep", "--package", package, "--out", draft3,
                    "--registry", register])
    if rc != 0 or "draft written" not in out:
        fails.append("V13b pr-prep via the --registry alias should be "
                     "rc=0 (rc=%d out=%r)" % (rc, out))

    # V13c: an entry that is not verified-true refuses with rc=1.
    unv_dir = os.path.join(root, "repo13c", "docs")
    os.makedirs(unv_dir, exist_ok=True)
    unv_register = os.path.join(unv_dir, REGISTER_NAME)
    unverified = dict(entry)
    unverified["verified"] = False
    with open(unv_register, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(unverified, ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":")) + "\n")
    draft4 = os.path.join(out_dir, "draft4.md")
    rc, out = _run(["pr-prep", "--package", package, "--out", draft4,
                    "--register", unv_register])
    if rc != 1:
        fails.append("V13c pr-prep on an unverified entry should be rc=1 "
                     "(rc=%d)" % rc)
    if os.path.exists(draft4):
        fails.append("V13c pr-prep on an unverified entry wrote a draft")

    # V14: the read-only oath.  Around an intake plus a pr-prep run, every
    # file of the fixture tree except the register and the draft keeps its
    # bytes; the register grows by exactly one line.
    tree = os.path.join(root, "repo14")
    tree_docs = os.path.join(tree, "docs")
    os.makedirs(tree_docs, exist_ok=True)
    sentinel = _write_fixture(tree, "code/tool.py", b"sentinel bytes\n")
    tree_register = os.path.join(tree_docs, REGISTER_NAME)
    before = _tree_snapshot(tree)
    rc, out = _run(["intake", "--package", package,
                    "--source-seat", "outer-line-a",
                    "--landed-ref", "incoming/return-a",
                    "--digest", zip_digest, "--register", tree_register])
    if rc != 0:
        fails.append("V14 intake inside the fixture tree should be green "
                     "(rc=%d)" % rc)
    after = _tree_snapshot(tree)
    if before.get("code/tool.py") != after.get("code/tool.py"):
        fails.append("V14 sentinel file changed under intake")
    for rel, digest in after.items():
        if rel == os.path.relpath(tree_register, tree).replace("\\", "/"):
            continue
        if rel in before and before[rel] != digest:
            fails.append("V14 pre-existing file changed: %s" % rel)
    if len(after) != len(before) + 1:
        fails.append("V14 tree grew by more than the register line: %r"
                     % sorted(after))
    with open(tree_register, "r", encoding="utf-8") as handle:
        if len(handle.read().strip().splitlines()) != 1:
            fails.append("V14 register does not hold exactly one line")

    # V15: CLI contract (no face rc=2, unknown face rc=2 via argparse).
    rc, out = _run([])
    if rc != 2:
        fails.append("V15 bare invocation should be rc=2 (rc=%d)" % rc)


class _Sink:
    """Minimal text sink so selftest captures stdout and stderr in-process."""

    def __init__(self):
        self.parts = []

    def write(self, text):
        self.parts.append(text)

    def getvalue(self):
        return "".join(self.parts)


def _run(argv):
    """Run one CLI vector in-process and return (rc, stdout)."""
    saved = (sys.stdout, sys.stderr)
    sys.stdout = sink_out = _Sink()
    sys.stderr = sink_err = _Sink()
    try:
        rc = main(list(argv))
    finally:
        sys.stdout, sys.stderr = saved
    return rc, sink_out.getvalue()


if __name__ == "__main__":
    sys.exit(main())
