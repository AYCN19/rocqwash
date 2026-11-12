# cure_applier.py 模块 docstring 原档（留档）

- 源文件：wash/cure_applier.py 模块 docstring（程序化逐字提取（ast.get_docstring），未删改一字）
- 留档日期：2026-11-13
- 如实注记：本件 docstring 自 v29 入账即为英文（全 git 史无中文原档，git log --follow -- wash/cure_applier.py 实查）；本档存五字段重排（annotation-standard-v1.0 Purpose./Interface./Dependencies./Evidence./Exit-codes.）前的原 docstring 以备溯源。本文件为历史存档，内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。

---
cure_applier.py — applier for the consumer-cure canonical pack (5 + 10 patterns).

Purpose:
    Applies the deterministic rewrite patterns from cure_pack.json to a Rocq/Coq
    source file.  Consumer-position cures (bridge wraps, goal-opening bridges,
    opaque-reflexivity replacement, qualified successor references, NatLe
    supply bridges) exist as canonical, idempotent rewrites: applying the pack
    twice changes nothing on the second run — the applier asserts this
    mechanically after every --apply.

    v31 additions (20261103 wash-campaign field report): statement-face
    downshift patterns (Qle/Qlt carrier faces, scoped-notation comparisons),
    Import-shadow direct-face qualification (two exclusive variants), and
    NatLe premise-lift / drop-wrap pairs.  New engine "face-regex" scopes a
    trigger to statement faces or proof regions with per-face token guards.
    Patterns may declare "exclusive_group": two selected patterns of one group
    both matching is a variant-choice conflict and fails loud (exit 4) —
    the caller must pick one variant via --only.

    v32 additions (S07-lineage adaptation forms, W66 field report): the
    argument-less-interface adaptation family — parameterized-shell drop
    (cure32_A, face-regex with a :=-binding-right guard), notation rebind
    (cure32_B, new "line-insert" engine: one line after the last world
    import), projection-bridge bare form (cure32_C(a), @field carrier
    instance -> bare field through the global instance) and predicate-face
    convergence (cure32_C(b), token map whose targets must be the consuming
    supply lemma's conclusion constant names — a delta-equivalent synonym
    compiles but leaks Obj.magic at extraction, so the name is normative).
    A report-only "station-report" engine ships the binder-shell station:
    it counts the argumented-Class binders whose full removal is manual
    surgery (intros lines / call sites) and must return to zero after the
    surgery.  v32 engine fix: the exclusive-group conflict path now writes
    its --json report before exiting 4 (previously crashed with
    UnboundLocalError when --json was given).

    v34 additions (CI #178 extraction-defect families, 20261104 reverse-
    revision round): the two born-clean fake-green lineages enter the pack
    as cures.  E3 generic-interface instantiation — the abstract-carrier
    application stations of a generic supply lemma are rewritten to the
    concrete-carrier specialization shim call, and the line-insert engine
    generates the shim Definition after the last import (the station
    pattern face-excludes the shim's own body, which keeps the canonical
    abstract application verbatim); E2 record polymorphic field — the
    un-annotated field-consumption Definition is restated as an explicit-
    type-annotated middleware, the downstream arity stations follow, and a
    report-only station asserts the sweep completion.  All five v34
    patterns reuse the v32 engines; no new engine ships in v34.

    v39 addition (20261111 corpus-survey wave, evidence-gated): one
    pattern from the b48-52 wash wave (ConstructiveWorld-Set commit
    9a51c74) — interface-quantified connective qualification.  Bare
    order connectives (lt/le/plus) in statement faces of files carrying
    the exact section context 'Context {RI0 : RealInterfaceEnhanced}'
    are pinned to the @S01_BaseRing.lt/le/plus RI0 projection form.
    A new template_fn "ifq_conn_qualify" branches the rewrite on the
    matched connective via the pattern's token_targets map; the
    face-regex engine is reused unchanged (no new engine), so the
    file_include gate (the exact context face), the Definition/Fixpoint
    decl_exclude and the binder-declaration colon lookahead all apply.
    Survey discipline held: candidate forms with thinner citations
    (single-file rebind variant, semantic Id-setoid re-casts, witness
    re-points, the v31/v32 pending families) stayed in the pending
    list — none cast.

Inputs:
    --file path/to/file.v           target source (never modified on dry-run)
    --pack path/to/cure_pack.json   pattern pack (default: cure_pack.json
                                    next to this script)
    --only id1,id2                  restrict to a subset of pattern ids
    --json out.json                 write an application report
    --apply                         write the cured file (default: dry-run)

Outputs:
    stdout report — per pattern: trigger matches found, rewrites applied.
    --json report — {pattern_id: {matches: n, applied: n}} plus file md5s.
    Exit codes: 0 = ran (dry-run or applied with idempotence verified),
    1 = idempotence assertion failed (fail-loud), 2 = usage,
    4 = exclusive-group conflict (two variants of one group matched — pick
        one via --only), 5 = pattern id unknown, 9 = file missing.

Minimal usage:
    python3 cure_applier.py --file path/to/file.v              # dry-run
    python3 cure_applier.py --file path/to/file.v --apply      # cure + verify
    python3 cure_applier.py --selftest                          # in-memory vectors
