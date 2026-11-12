# comment_sweep.py 模块 docstring 原档（留档）

- 源文件：wash/comment_sweep.py 模块 docstring（程序化逐字提取（ast.get_docstring），未删改一字）
- 留档日期：2026-11-13
- 如实注记：本件 docstring 自 v31 入账即为英文（全 git 史无中文原档，git log --follow -- wash/comment_sweep.py 实查）；本档存五字段重排（annotation-standard-v1.0 Purpose./Interface./Dependencies./Evidence./Exit-codes.）前的原 docstring 以备溯源。本文件为历史存档，内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。

---
comment_sweep.py — comment-domain sweep sidecar (comment_pack.json applier).

Purpose:
    Applies the comment_pack.json sweeps to a Rocq/Coq source file:
      1. flag-word exchange inside comment spans only (nested-comment and
         string-literal aware state machine; never inside strings, never in
         code positions, never before the first code character);
      2. optional leading-header replacement from a --header-map JSON file
         (basename -> header text; the leading comment region before the
         first code character is replaced wholesale with the mapped data).
    Code lines are never touched: every application asserts mechanically
    that the code-strip projection (file text minus comment spans) is
    byte-identical before and after, and that a second application changes
    nothing (idempotence, fail-loud).

Inputs:
    --file path/to/file.v            target source (never modified on dry-run)
    --pack path/to/comment_pack.json sweep pack (default: next to this script)
    --header-map map.json            optional {basename: header text} data for
                                     the leading-header replacement step
    --json out.json                  write a sweep report
    --apply                          write the swept file (default: dry-run)

Outputs:
    stdout report — flag swaps, header replacement, header shape validation,
    code-line-equality projection.  Exit codes: 0 = ran (dry-run or applied
    with idempotence verified), 1 = code-line drift / idempotence failure
    (fail-loud), 2 = usage, 9 = file missing.

Minimal usage:
    python3 comment_sweep.py --file path/to/file.v                # dry-run
    python3 comment_sweep.py --file f.v --header-map m.json --apply
    python3 comment_sweep.py --selftest                            # vectors
