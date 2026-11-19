#!/usr/bin/env python3
"""pipeline_stub.py - i18n translation-pipeline interface stub (E4 seed).

Purpose.  Carry the interface shape of the zh<->en bidirectional
  four-linkage pipeline (normalization / standardization /
  internationalization / de-AI-flavor) with zero implementation: every
  operation raises `PipelineStub`; the stub never fakes a pipeline result.
  The engine body lives in `tools/i18n_pipeline.py` (`i18n_translate`,
  `i18n_verify` companions).
Interface.  `python3 seeds/i18n/pipeline_stub.py --selftest` verifies the
  interface shape and prints a STUB banner; any other invocation prints
  the STUB banner plus usage.  Six operations with fixed signatures:
  `segment_document(text, direction)`, `translate_segments(segments,
  model_id, prompt_template_ref)`, `apply_linkages(segments, linkage_ids)`,
  `verify_faces(run_manifest)`, `tenpoint_review(target_artifact)`,
  `sync_ledger_append(ledger_path, rows)`.  Data contract: the SPEC
  markdown file in this directory (sections 2, 3, 5, 9, 10), discoverable
  by directory listing.
Dependencies.  Python 3 standard library only (`argparse`, `inspect`,
  `sys`); zero network, zero writes, zero side effects on every face.
Evidence.  `--selftest` probes every operation in `OPERATIONS` with
  signature-counted `None` placeholders and passes only when each raises
  `PipelineStub`; sibling `seeds/i18n/test_snippet.py` runs this stub
  under `-I` asserting exit 0 with a STUB marker; suite segment
  `tests/t_engines_seeds.py` drives the same check
  (`test_i18n_pipeline_stub_selftest`).
Exit-codes.  0 = `--selftest` passed, interface shape intact; 1 =
  `--selftest` found interface drift (constant or raise behavior); 2 =
  usage error (any invocation other than `--selftest`).
"""

import argparse
import inspect
import sys

PIPELINE_ID = "rocqwash-i18n/0.0.0-stub"

# Seed provenance record, kept as a module metadata line (historical fact;
# the prose face carries no date stamps).
SEED_LINE = "RQW12 seed integration, 2026-11-14"

DIRECTIONS = ("zh2en", "en2zh")

# The four linkages of SPEC section 3. Values are data-face pointers, not
# implementations; each linkage consumes sibling seeds plus read-only
# snapshots of the originals registered in SPEC section 12.
LINKAGES = {
    "normalization": "seeds/termbase/termbase.json (E3 seed)",
    "standardization": "seeds/jargon/jargon-map.json (E2 seed); "
                       "docs/jargon-to-standard-mapping-v1.md (in-repo md form)",
    "internationalization": "SPEC section 2 preservation list; norm_lint "
                            "--cjk-threshold; em-dash density rule",
    "de_ai_flavor": "seeds/ai_flavor/word-map.json (E1 seed); "
                    "ai_flavor_selfcheck.sh battery precedent",
}

OPERATIONS = (
    "segment_document",
    "translate_segments",
    "apply_linkages",
    "verify_faces",
    "tenpoint_review",
    "sync_ledger_append",
)


class PipelineStub(NotImplementedError):
    """Raised by every pipeline operation in this stub (interface only).

    Keeping a distinct subtype lets --selftest probe the interface shape
    mechanically and lets callers fail loud with a clear STUB marker.
    """

    def __init__(self, op):
        super().__init__(
            "STUB: %s is interface-only in seeds/i18n/pipeline_stub.py "
            "(zero implementation; see SPEC section 10)" % op
        )


def segment_document(text, direction):
    """Split a document into prose segments (SPEC section 4 P1).

    Contract: protect code, identifiers, CLI flags, math, citations, paths;
    emit segment-ledger rows (SPEC section 9). STUB: raises, no behavior.
    """
    raise PipelineStub("segment_document")


def translate_segments(segments, model_id, prompt_template_ref):
    """Translate segments at a model site (SPEC section 4 P2, section 5).

    Contract: per-segment annotation mandatory (annotation_site="model",
    model_id recorded per segment); zero silent machine translation.
    STUB: raises, no behavior, no model call.
    """
    raise PipelineStub("translate_segments")


def apply_linkages(segments, linkage_ids):
    """Apply the four linkages over translated segments (SPEC section 4 P3).

    Contract: order L1 normalization, L2 standardization, L3
    internationalization, L4 de-AI-flavor; linkage hits are findings, and
    rewrites land in the same ledger. STUB: raises, no behavior.
    """
    raise PipelineStub("apply_linkages")


def verify_faces(run_manifest):
    """Run the mechanical verify faces (SPEC section 4 P4).

    Contract: norm_lint --jargon-map + CJK threshold, doc_lint, AI-flavor
    battery, --selftest of touched tools. STUB: raises, no behavior.
    """
    raise PipelineStub("verify_faces")


def tenpoint_review(target_artifact):
    """Human ten-point single-face gate (SPEC section 4 P5, section 6).

    Contract: verdict per file per point with line citations; verdicts
    ALL-PASS / N-FAIL / BLOCKED; FAIL never edits the source. STUB: raises;
    this stage is human-performed even after the engine grows.
    """
    raise PipelineStub("tenpoint_review")


def sync_ledger_append(ledger_path, rows):
    """Append rows to the segment ledger (SPEC section 4 P6, section 9).

    Contract: append-only ledger, English keys, no free-text process
    narrative inside rows. STUB: raises, no behavior.
    """
    raise PipelineStub("sync_ledger_append")


def selftest(out):
    """Verify the interface shape; print a STUB banner; return exit code 0.

    Checks: banner printed, constants present, and every operation in
    OPERATIONS raises PipelineStub when probed. Probe = call with None
    placeholders for the required positional parameters (signature-counted)
    inside try/except; reaching the body and raising PipelineStub is the
    expected pass path, and each stub body raises before touching anything.
    """
    out.write("STUB: %s (interface shape only, zero implementation)\n" % PIPELINE_ID)
    problems = []
    if DIRECTIONS != ("zh2en", "en2zh"):
        problems.append("direction constants drifted")
    if set(LINKAGES) != {
        "normalization", "standardization", "internationalization", "de_ai_flavor",
    }:
        problems.append("linkage keys drifted from SPEC section 3")
    for op in OPERATIONS:
        fn = globals().get(op)
        if not callable(fn):
            problems.append("%s: missing" % op)
            continue
        try:
            params = inspect.signature(fn).parameters.values()
            required = sum(
                1 for p in params
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                and p.default is p.empty
            )
            fn(*([None] * required))
        except PipelineStub:
            out.write("STUB: %s -> PipelineStub (interface-only, ok)\n" % op)
        except Exception as exc:  # a stub must raise PipelineStub, nothing else
            problems.append("%s: raised %r instead of PipelineStub" % (op, exc))
        else:
            problems.append("%s: callable but did not raise (stub faking a "
                            "result is forbidden)" % op)
    if problems:
        for item in problems:
            out.write("STUB: FAIL %s\n" % item)
        out.write("STUB: selftest FAIL (%d problem(s))\n" % len(problems))
        return 1
    out.write("STUB: selftest PASS (interface shape intact, zero "
              "implementation, %d operations)\n" % len(OPERATIONS))
    return 0


def main(argv=None):
    """CLI entry: --selftest prints STUB and exits 0; anything else is usage."""
    parser = argparse.ArgumentParser(
        prog="pipeline_stub.py",
        description="rocqwash E4 i18n translation-pipeline interface stub "
                    "(STUB: no engine body; see the SPEC markdown file in "
                    "this directory).",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="verify the interface shape, print a STUB banner, exit 0",
    )
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest(sys.stdout)
    sys.stdout.write("STUB: %s (no engine body; try --selftest)\n" % PIPELINE_ID)
    parser.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
