#!/usr/bin/env bash
# cw.sh — unified entry for the rocqwash tool suite: the v29-v32 seven-tool
#         release plus the v35-v39 five-tool release plus the v37 three-tool
#         release plus the v38 aggregate doctor plus the v39 trio (doc-lint,
#         netname-normalize, select-audit) plus the v40 baseline-diff plus
#         the v45 render-events ledger renderer plus the v46
#         `red-dispatch`/`registry-audit` pair plus the v47 registry-fix
#         prescription applier plus the annotation-face normalization
#         linter (norm-lint) — twenty-five tools in total
#         (repository root, bash 3.2 compatible)
#
# Usage: bash cw.sh <tool> [args...]
#
# 工具表 Tools (one usage line + target script per tool; args and exit codes pass through 1:1):
#   scan4       token-level qualified-identifier census -> scan/scan_v4_token.py
#               cw.sh scan4 --file <f.v> [--json out.json] [--ids S] [--text]
#   cure        consumer-cure canonical pack (dry-run by default) -> wash/cure_applier.py
#               cw.sh cure --file <f.v> [--pack P] [--only IDS] [--json out] [--apply]
#   probe       batch closure-compatibility probe engine -> wash/probe_engine.py
#               cw.sh probe --candidates <tsv> --src DIR --world DIR --out ledger.json [--fresh]
#   chain       multi-ledger merge chain-root graph -> tools/chain_graph.py
#               cw.sh chain <ledger.json...> [--json out] [--md out] [--top N]
#   sync-ledger probe-ledger x status-ledger merge sync -> tools/ledger_sync.py
#               cw.sh sync-ledger --probe <json> --ledger <tsv> --out <tsv> [--report r.json]
#   erasure     extraction erasure-position classification advisor -> verify/erasure_classifier.py
#               cw.sh erasure --mli <f.mli> [--json scan.json] [--resolve N1,N2] [--md-out f.md]
#   dual-scan   dual-scanner cross-check driver -> scan/dual_scan.py
#               cw.sh dual-scan --dir DIR | --file <f.v> [--out report.json]
#   doctor      dyld toolchain-breakage diagnostics (diagnose only + restore advice; never executes)
#                                                    -> tools/toolchain_dyld_doctor.py
#               cw.sh doctor [--worker PATH] [--donor DIR] [--json out.json] [--smoke --coqc PATH]
#   net-probe   network-window probe (double-probe stable window; a single probe never authorizes emission) -> tools/net_probe.py
#               cw.sh net-probe [--endpoints URL,..] [--rounds N] [--interval S] [--stable-window] [--json out]
#   triage      CI red-run triage (five families + green-run classification spectrum) -> tools/ci_triage.py
#               cw.sh triage --repo ORG/REPO --run ID [--logs] | --offline JOBS.json [--json out]
#   union       registry union surgery (dry-run by default) -> tools/registry_union.py
#               cw.sh union --base B --main M --branch X --kind order [--out o --apply] | --git REPO --ref-*
#   pushci      push-CI one-shot pipeline (emission gate -> push -> watch -> heal -> verdict +- merge)
#                                                    -> tools/pushci.py
#               cw.sh pushci --repo-path DIR --branch B [--pre-scan-gate4] [--merge] [--max-heal N] [--json out] [--dry-run]
#   sentinel    real-time watch sentinel (three signal sources -> JSONL event stream; once/loop dual mode)
#                                                    -> tools/cw_sentinel.py
#               cw.sh sentinel --once | --loop [--interval S] [--watch-repo ORG/REPO [--branch B]...] [--watch-ledgers DIR] [--watch-buildlog FILE] [--state-file F] [--emit F] [--on-red 'CMD'] [--on-red-preset NAME]... [--on-red-arg K=V] [--injector F] [--json out]
#   wash-shape  canonical five-pass shaping pipeline (lexical/token/header/EOL/anchor; plan writes nothing by default)
#                                                    -> tools/wash_shape.py
#               cw.sh wash-shape --file A.v [--file B.v...] | --dir TREE [--only KINDS] [--apply] [--header-map M] [--header-map-preset NAME] [--anchor-src DIR] [--json OUT] [--loop --interval S --events F] [--injector SCEN.json]
#   unclog      blockage-unclogging closed loop (probe collection -> chain-root pick -> cure application -> re-check -> verdict; dry-run by default)
#                                                    -> tools/unclog.py
#               cw.sh unclog --src DIR --world DIR [--candidates TSV | --chain-ledgers JSON...] [--apply] [--audit] [--probe-parallel K] [--rounds N] [--json out] [--events F] [--loop --interval S] [--injector DIR]
#   cw-doctor   aggregate health check, four domains (environment/network/registry/clogs -> health score + advice; diagnosis only)
#                                                    -> tools/cw_doctor.py
#               cw.sh cw-doctor [--json out.json] [--registry PATH] [--src DIR --sample N] [--injector DIR]
#   doc-lint    docs-to-implementation consistency linter, three checks (tool table / counts / flags; verdict consistent|drift)
#                                                    -> tools/doc_lint.py
#               cw.sh doc-lint [--repo DIR] [--json OUT] [--help-cap N]
#   netname-normalize  .v.v double-suffix clean-name normalization (mapping table + --apply rename with md5 verification)
#                                                    -> tools/netname_normalize.py
#               cw.sh netname-normalize [--dir DIR] [--apply] [--map out.tsv] [--json out]
#   select-audit batch-selection auditor (selection list vs order.txt full-table grep dedup + Require-surface audit v6)
#                                                    -> tools/select_audit.py
#               cw.sh select-audit [--order ORDER] [--select LIST] [--grep RX] [--requires F.v] [--json out]
#   baseline-diff clog-baseline differ (two unclog --audit baselines -> added/removed/persistent three lists + four-state verdict; argv order old then new)
#                                                    -> tools/baseline_diff.py
#               cw.sh baseline-diff OLD.json NEW.json [--json out.json] [--md out.md]
#   render-events  sentinel-event JSONL to markdown ledger (three-dimension distribution + per-event table; malformed-line tolerant)
#                                                    -> tools/render_events.py
#               cw.sh render-events --events F.jsonl [--dir DIR] [--md out.md] [--json out] [--top N]
#   dispatch    red-event router (sentinel red events -> action presets; three tiers report-only/suggest/auto)
#                                                    -> tools/red_dispatch.py
#               cw.sh dispatch --event-file <json> [--preset report-only|suggest|auto] [--json OUT] [--state-file F] [--cooldown S] [--repo-path DIR] [--param K=V] [--dry-run]
#   audit       registry hygiene auditor (dual-book read-only four-account output + deterministic prescription; --apply does not exist)
#                                                    -> tools/registry_audit.py
#               cw.sh audit --order ORDER --project _CoqProject | --git REPO --ref REF [--live-src DIR] [--anchor-src DIR] [--fix-plan] [--json out] [--md out]
#   registry-fix registry prescription applier (applies audit fix-plan items one by one; dry-run by default)
#                                                    -> tools/registry_fix.py
#               cw.sh registry-fix --audit-json AUDIT.json --order ORDER.txt --project _CoqProject [--anchor-src DIR] [--json REPORT.json] [--apply] [--work-dir DIR]
#   norm-lint   annotation-face normalization linter, report-only first form (header banner + five-field block / jargon mapping-table faces / CJK residue / forbidden classes / header budget; findings are data, the exit code never escalates on them)
#                                                    -> tools/norm_lint.py
#               cw.sh norm-lint --tree DIR | --file PATH [--jargon-map P] [--cjk-threshold F] [--cjk-whitelist P] [--json P] [--md P]
#   help        this help (help <tool> = the tool's one-line usage hint)
#
# 路由契约 Routing contract:
#   1. All paths resolve relative to the repository root (ROOT is derived from
#      this script's own directory) — zero hardcoded absolute paths; the repo
#      can be relocated freely.
#   2. Arguments and exit codes pass through 1:1 (direct exec; fail-loud,
#      never rewritten); same contract as cli/rocqwash.
#   3. Exit codes: 0=pass; 2=unknown tool; 9=target script missing; anything
#      else follows each tool's own convention and passes through
#      (per-tool conventions: --help/--selftest=0; argparse usage errors /
#      FAIL-LOUD assertion failures=2; missing target files=9).
#      pushci passes through its verdict seal (success/dry-run=0;
#      heal-exhausted/unstable/toolchain=1; fix-content/gate4-block=2;
#      9=target missing). The v37 trio follows the same shape: 0=green /
#      inspection complete / unclogged; 1=data-side incomplete (shaping
#      partial / plan-miss; wall / rounds-exhausted — red is data, not tool
#      failure; reported loudly on stdout); 2=usage error; 9=missing /
#      fail-loud.
#      cw-doctor, same shape: 0=healthy (aggregate score >= 90); 1=degraded
#      (red is data, not tool failure; reported loudly on stdout);
#      2=usage error; 9=missing / fail-loud.
#      doc-lint, same shape: 0=consistent (all three checks drift-free);
#      1=drift (any check drifted; red is data, not tool failure; reported
#      loudly on stdout); 2=usage error (--help-cap<1); 9=missing (required
#      input absent / tool --help red or timed out, fail-loud).
#      baseline-diff, same shape: 0=improved/stable (reds fewer or equal);
#      1=degraded/incomparable (reds increased, or honest refusal on a
#      changed candidate set; red is data, not tool failure; reported loudly
#      on stdout); 2=usage error / malformed input (schema mismatch / ledger
#      self-consistency broken); 9=path missing.
#      dispatch, same shape: 0=processing complete (red is data, not tool
#      failure; a dispatched rc!=0 / timeout / dedup skip is recorded without
#      touching the exit code); 2=usage error (--param guard / --dry-run
#      tier mismatch / negative --cooldown); 9=missing input (event file
#      absent / missing fields listed item by item / unresolvable parameter /
#      metacharacter refused at construction / malformed state refused).
#      audit, same shape: 0=report emitted (findings are data; count>0
#      still exits 0; reported loudly on stdout); 2=usage error (parameter
#      mismatch / no input surface / only one of the two books given);
#      9=missing input (book files / git show / live-src / anchor-src
#      absent).
#      registry-fix, same shape: 0=dry-run report emitted, or --apply
#      written plus all three assertions passed; 2=usage error (schema
#      mismatch / missing fix_plan / same-parameter breach / entry key
#      missing / AssertBlast assertion failure — the report carries evidence
#      after a rollback); 9=missing input (audit JSON / the two books / the
#      audit tool / anchor-src directory absent).
#      norm-lint, same shape: 0=accounted (report-only: findings are data,
#      the exit code never escalates on them); 1=selftest red (an assertion
#      in the five selftest vectors failed); 2=usage error (no scan face /
#      both --tree and --file / --gate or --strict reserved / negative
#      --cjk-threshold); 9=missing input (tree or file absent / jargon map
#      unreadable / CJK whitelist unreadable).
#   4. bash 3.2 compatible (no associative arrays, no bash-4+ features);
#      read-only routing layer — itself writes nothing.
#
# 覆盖面注 Coverage note: cli/rocqwash routes the pre-v29 modules (scan/names/
# wash/verify/seam/certify/watch). The v29-v32 tools and the v35-v39 five tools
# (doctor/net-probe/triage/union/pushci in tools/) plus the v37 three tools
# (cw_sentinel/wash_shape/unclog) plus the v38 aggregate doctor (cw_doctor)
# live in module directories that now
# hold several generic entries each, where the auto-router's ambiguity guard
# (exit 4) deliberately declines to guess — this entry fills that gap by
# explicit tool name. The two entries are complementary.

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
cw.sh — unified entry for the rocqwash tool suite (24 tools · bash 3.2 compatible)
（中文过渡注 zh transition note: this help is English-first; the full original Chinese quick reference is archived in README-cw.zh.md）

Usage: bash cw.sh <tool> [args...]

工具 Tools:
  scan4       token-level qualified-identifier census -> scan/scan_v4_token.py
              cw.sh scan4 --file <f.v> [--json out.json] [--ids S] [--text]
  cure        consumer-cure canonical pack (dry-run by default) -> wash/cure_applier.py
              cw.sh cure --file <f.v> [--pack P] [--only IDS] [--json out] [--apply]
  probe       batch closure-compatibility probe engine -> wash/probe_engine.py
              cw.sh probe --candidates <tsv> --src DIR --world DIR --out ledger.json [--fresh]
  chain       multi-ledger merge chain-root graph -> tools/chain_graph.py
              cw.sh chain <ledger.json...> [--json out] [--md out] [--top N]
  sync-ledger probe-ledger x status-ledger merge sync -> tools/ledger_sync.py
              cw.sh sync-ledger --probe <json> --ledger <tsv> --out <tsv> [--report r.json]
  erasure     extraction erasure-position classification advisor -> verify/erasure_classifier.py
              cw.sh erasure --mli <f.mli> [--json scan.json] [--resolve N1,N2] [--md-out f.md]
  dual-scan   dual-scanner cross-check driver -> scan/dual_scan.py
              cw.sh dual-scan --dir DIR | --file <f.v> [--out report.json]
  doctor      dyld toolchain-breakage diagnostics (diagnose only + restore advice; never executes)
                                                   -> tools/toolchain_dyld_doctor.py
              cw.sh doctor [--worker PATH] [--donor DIR] [--json out.json] [--smoke --coqc PATH]
  net-probe   network-window probe (double-probe stable window; a single probe never authorizes emission) -> tools/net_probe.py
              cw.sh net-probe [--endpoints URL,..] [--rounds N] [--interval S] [--stable-window] [--json out]
  triage      CI red-run triage (five families + green-run classification spectrum) -> tools/ci_triage.py
              cw.sh triage --repo ORG/REPO --run ID [--logs] | --offline JOBS.json [--json out]
  union       registry union surgery (dry-run by default) -> tools/registry_union.py
              cw.sh union --base B --main M --branch X --kind order [--out o --apply] | --git REPO --ref-*
  pushci      push-CI one-shot pipeline (emission gate -> push -> watch -> heal -> verdict +- merge)
                                                   -> tools/pushci.py
              cw.sh pushci --repo-path DIR --branch B [--pre-scan-gate4] [--merge] [--max-heal N] [--json out] [--dry-run]
  sentinel    real-time watch sentinel (three signal sources -> JSONL event stream; once/loop dual mode)
                                                   -> tools/cw_sentinel.py
              cw.sh sentinel --once | --loop [--interval S] [--watch-repo ORG/REPO [--branch B]...] [--watch-ledgers DIR] [--watch-buildlog FILE] [--state-file F] [--emit F] [--on-red 'CMD'] [--on-red-preset NAME]... [--on-red-arg K=V] [--injector F] [--json out]
  wash-shape  canonical five-pass shaping pipeline (lexical/token/header/EOL/anchor; plan writes nothing by default)
                                                   -> tools/wash_shape.py
              cw.sh wash-shape --file A.v [--file B.v...] | --dir TREE [--only KINDS] [--apply] [--header-map M] [--header-map-preset NAME] [--anchor-src DIR] [--json OUT] [--loop --interval S --events F] [--injector SCEN.json]
  unclog      blockage-unclogging closed loop (probe collection -> chain-root pick -> cure application -> re-check -> verdict; dry-run by default)
                                                   -> tools/unclog.py
              cw.sh unclog --src DIR --world DIR [--candidates TSV | --chain-ledgers JSON...] [--apply] [--audit] [--probe-parallel K] [--rounds N] [--json out] [--events F] [--loop --interval S] [--injector DIR]
  cw-doctor   aggregate health check, four domains (environment/network/registry/clogs -> health score + advice; diagnosis only)
                                                   -> tools/cw_doctor.py
              cw.sh cw-doctor [--json out.json] [--registry PATH] [--src DIR --sample N] [--injector DIR]
  doc-lint    docs-to-implementation consistency linter, three checks (tool table / counts / flags; verdict consistent|drift)
                                                   -> tools/doc_lint.py
              cw.sh doc-lint [--repo DIR] [--json OUT] [--help-cap N]
  netname-normalize  .v.v double-suffix clean-name normalization (mapping table + --apply rename with md5 verification)
                                                   -> tools/netname_normalize.py
              cw.sh netname-normalize [--dir DIR] [--apply] [--map out.tsv] [--json out]
  select-audit batch-selection auditor (selection list vs order.txt full-table grep dedup + Require-surface audit v6)
                                                   -> tools/select_audit.py
              cw.sh select-audit [--order ORDER] [--select LIST] [--grep RX] [--requires F.v] [--json out]
  baseline-diff clog-baseline differ (two unclog --audit baselines -> added/removed/persistent three lists + four-state verdict; argv order old then new)
                                                   -> tools/baseline_diff.py
              cw.sh baseline-diff OLD.json NEW.json [--json out.json] [--md out.md]
  render-events  sentinel-event JSONL to markdown ledger (three-dimension distribution + per-event table; malformed-line tolerant)
                                                   -> tools/render_events.py
              cw.sh render-events --events F.jsonl [--dir DIR] [--md out.md] [--json out] [--top N]
  dispatch    red-event router (sentinel red events -> action presets; three tiers report-only/suggest/auto)
                                                   -> tools/red_dispatch.py
              cw.sh dispatch --event-file <json> [--preset report-only|suggest|auto] [--json OUT] [--state-file F] [--cooldown S] [--repo-path DIR] [--param K=V] [--dry-run]
  audit       registry hygiene auditor (dual-book read-only four-account output + deterministic prescription; --apply does not exist)
                                                   -> tools/registry_audit.py
              cw.sh audit --order ORDER --project _CoqProject | --git REPO --ref REF [--live-src DIR] [--anchor-src DIR] [--fix-plan] [--json out] [--md out]
  registry-fix registry prescription applier (applies audit fix-plan items one by one; dry-run by default)
                                                   -> tools/registry_fix.py
              cw.sh registry-fix --audit-json AUDIT.json --order ORDER.txt --project _CoqProject [--anchor-src DIR] [--json REPORT.json] [--apply] [--work-dir DIR]
  norm-lint   annotation-face normalization linter, report-only first form (header banner + five-field block / jargon mapping-table faces / CJK residue / forbidden classes / header budget; findings are data, the exit code never escalates on them)
                                                   -> tools/norm_lint.py
              cw.sh norm-lint --tree DIR | --file PATH [--jargon-map P] [--cjk-threshold F] [--cjk-whitelist P] [--json P] [--md P]
  help        this help (help <tool> = the tool's one-line usage hint)

退出码 Exit codes: 0=pass  2=unknown-tool  9=target-script-missing  others = each tool's own convention, passed through
路由说明 Routing notes:
  - Arguments and exit codes pass through 1:1 (direct exec; fail-loud, never rewritten); same contract as cli/rocqwash.
  - All paths resolve relative to the repository root (ROOT is derived from this script's own directory) — the repo can be relocated freely; zero hardcoded absolute paths.
  - `cw.sh <tool>` with no args prints the tool's one-line hint to stderr, then passes through; `cw.sh help <tool>` prints the hint only.
EOF
}

# One-line usage hints (shared verbatim by `help <tool>` and the pre-passthrough no-args hint)
hint_for() {  # $1=tool
  case "$1" in
    scan4)       echo "cw.sh scan4 --file <f.v> [--json out.json] [--ids S] [--text]   # token-level qualified-identifier census -> scan/scan_v4_token.py" ;;
    cure)        echo "cw.sh cure --file <f.v> [--pack P] [--only IDS] [--json out] [--apply]   # consumer-cure canonical pack (dry-run by default) -> wash/cure_applier.py" ;;
    probe)       echo "cw.sh probe --candidates <tsv> --src DIR --world DIR --out ledger.json [--fresh]   # batch closure-compatibility probe -> wash/probe_engine.py" ;;
    chain)       echo "cw.sh chain <ledger.json...> [--json out] [--md out] [--top N]   # multi-ledger merge chain-root graph -> tools/chain_graph.py" ;;
    sync-ledger) echo "cw.sh sync-ledger --probe <json> --ledger <tsv> --out <tsv> [--report r.json]   # probe-ledger x status-ledger merge -> tools/ledger_sync.py" ;;
    erasure)     echo "cw.sh erasure --mli <f.mli> [--json scan.json] [--resolve N1,N2] [--md-out f.md]   # extraction erasure-position classification advisor -> verify/erasure_classifier.py" ;;
    dual-scan)   echo "cw.sh dual-scan --dir DIR | --file <f.v> [--out report.json]   # dual-scanner cross-check -> scan/dual_scan.py" ;;
    doctor)      echo "cw.sh doctor [--worker PATH] [--donor DIR] [--json out.json] [--smoke --coqc PATH]   # dyld toolchain-breakage diagnostics (diagnose only + restore advice; never executes) -> tools/toolchain_dyld_doctor.py" ;;
    net-probe)   echo "cw.sh net-probe [--endpoints URL,..] [--rounds N] [--interval S] [--stable-window] [--json out]   # network-window probe (double-probe stable window) -> tools/net_probe.py" ;;
    triage)      echo "cw.sh triage --repo ORG/REPO --run ID [--logs] | --offline JOBS.json [--json out]   # CI red-run triage (five families + green-run) -> tools/ci_triage.py" ;;
    union)       echo "cw.sh union --base B --main M --branch X --kind order [--out o --apply] | --git REPO --ref-base RB --ref-main RM --ref-branch XB   # registry union surgery (dry-run by default) -> tools/registry_union.py" ;;
    pushci)      echo "cw.sh pushci --repo-path DIR --branch B [--pre-scan-gate4] [--merge] [--max-heal N] [--json out] [--dry-run]   # push-CI one-shot pipeline (emission gate -> push -> watch -> heal -> verdict +- merge; seven-state verdict success/fix-content/toolchain/unstable/heal-exhausted/gate4-block/dry-run) -> tools/pushci.py" ;;
    sentinel)    echo "cw.sh sentinel --once | --loop [--interval S] [--watch-repo ORG/REPO [--branch B]...] [--watch-ledgers DIR] [--watch-buildlog FILE] [--state-file F] [--emit F] [--on-red 'CMD'] [--on-red-preset NAME]... [--on-red-arg K=V] [--injector F] [--json out]   # real-time watch sentinel (three signal sources CI runs / ledger chain-roots / buildlog tokens -> JSONL event stream; red is data not tool failure; no action by default; --on-red-preset five presets unclog/pushci/wash-shape/triage/cw-doctor, repeatable = chained in the given order, one failure continues the chain; mutually exclusive with --on-red; side-effect actions require --emit, both channels share the same guard) -> tools/cw_sentinel.py" ;;
    wash-shape)  echo "cw.sh wash-shape --file A.v [--file B.v...] | --dir TREE [--only KINDS] [--apply] [--header-map M] [--header-map-preset NAME] [--anchor-src DIR] [--json OUT] [--loop --interval S --events F] [--injector SCEN.json]   # canonical five-pass shaping pipeline (lexical/token/header/EOL/anchor; plan writes nothing by default; --apply applies, then re-runs the five passes for verification; --header-map-preset named header-template library tests/fixtures/header_map_v1.json, mutually exclusive with --header-map in the same slot) -> tools/wash_shape.py" ;;
    unclog)      echo "cw.sh unclog --src DIR --world DIR [--candidates TSV | --chain-ledgers JSON...] [--apply] [--audit] [--probe-parallel K] [--rounds N] [--top N] [--pack FILE] [--json out] [--events F] [--loop --interval S --loop-max N] [--injector DIR]   # blockage-unclogging closed loop (probe collection -> chain_graph chain-root pick -> cure_applier application -> re-scan/re-probe verification -> verdict unclogged/wall/rounds-exhausted/audit; dry-run by default; frozen-listed files refused loudly; --audit read-only clog baseline, zero writes, mutually exclusive with --apply/--loop; --probe-parallel K threads probe parallelism, jobs dimension recorded in the timing section) -> tools/unclog.py" ;;
    cw-doctor)   echo "cw.sh cw-doctor [--json out.json] [--workdir DIR] [--registry PATH] [--src DIR --sample N [--world DIR]] [--worker PATH] [--donor DIR] [--endpoints URL,..] [--guard PATH] [--timeout S] [--injector DIR]   # aggregate health check, four domains (dyld environment / net_probe network / registry anchor audit / clog probe + chain_graph -> aggregate health score 0-100 + verdict healthy/degraded + advice; diagnosis only, never executes; --injector offline-testable) -> tools/cw_doctor.py" ;;
    doc-lint)    echo "cw.sh doc-lint [--repo DIR] [--json OUT] [--help-cap N]   # docs-to-implementation consistency linter, three checks (1. cw.sh four-place tool-table cross-check + tools/ generic-entry reconciliation 2. CASES vs tests/README.md vs README.md counts 3. doc flag references vs each tool's real --help output; verdict consistent|drift; red is data not tool failure) -> tools/doc_lint.py" ;;
    netname-normalize) echo "cw.sh netname-normalize [--dir DIR] [--apply] [--map out.tsv] [--json out]   # .v.v double-suffix clean-name normalizer (mapping table + --apply rename with md5 verification) -> tools/netname_normalize.py" ;;
    select-audit) echo "cw.sh select-audit [--order ORDER] [--select LIST] [--grep RX] [--requires F.v] [--json out]   # batch-selection auditor (selection list vs tree order.txt full-table grep dedup + Require-surface audit v6 criteria) -> tools/select_audit.py" ;;
    render-events) echo "cw.sh render-events --events F.jsonl [--dir DIR] [--md out.md] [--json out] [--top N]   # sentinel-event JSONL to markdown ledger (kind/family/action three-dimension distribution + per-event table; malformed-line tolerant rc1; red is data not tool failure) -> tools/render_events.py" ;;
    baseline-diff) echo "cw.sh baseline-diff OLD.json NEW.json [--json out.json] [--md out.md]   # clog-baseline differ (two unclog --audit clog baselines, argv order old then new -> new_blocks/resolved_blocks/persistent three lists + score_delta; verdict improved/degraded/stable/incomparable; self-consistency precheck rejects hand-edited ledgers; timing excluded; red is data not tool failure) -> tools/baseline_diff.py" ;;
    dispatch)    echo "cw.sh dispatch --event-file <json> [--preset report-only|suggest|auto] [--json OUT] [--state-file F] [--cooldown S] [--repo-path DIR] [--param K=V] [--dry-run]   # red-event router (sentinel red events -> action presets; three presets: report-only default zero execution / suggest copy-paste command block / auto explicit only under a 60s cap, rc!=0 recorded without touching the exit code; dedup state + cooldown; all routes wired onto existing cw.sh routes, zero new engines; family-A content-red never auto-fixed, emits a fix list; red is data not tool failure) -> tools/red_dispatch.py" ;;
    audit)       echo "cw.sh audit --order ORDER --project _CoqProject | --git REPO --ref REF [--live-src DIR] [--anchor-src DIR] [--fix-plan] [--json out] [--md out]   # registry hygiene auditor (order.txt/_CoqProject dual-book read-only four-account output: duplicates / anchor collisions / seq-form / malformed / missing anchors / orphans / live topology + --fix-plan deterministic prescription, zero writes; --apply does not exist; keys and anchor canon reused from registry_union, zero re-invention; findings are data, exit 0) -> tools/registry_audit.py" ;;
    registry-fix) echo "cw.sh registry-fix --audit-json AUDIT.json --order ORDER.txt --project _CoqProject [--anchor-src DIR] [--json REPORT.json] [--apply] [--work-dir DIR]   # registry prescription applier (applies registry_audit --fix-plan prescriptions one by one; three prescription kinds DEDUP keep-first / anchor re-stamp / ORPHAN-ADD skip; dry-run by default; --apply writes, then three assertions hold or rollback; staging fully in-memory, zero writes; same-parameter discipline binds audit and applier verbatim) -> tools/registry_fix.py" ;;
    norm-lint)   echo "cw.sh norm-lint --tree DIR | --file PATH [--jargon-map P] [--cjk-threshold F] [--cjk-whitelist P] [--json P] [--md P]   # annotation-face normalization linter, report-only first form (prose faces of .py/.sh/.md: header banner + five-field block Purpose./Interface./Dependencies./Evidence./Exit-codes. verbatim; jargon mapping-table faces word-boundary; CJK residue warn; forbidden classes warn; header budget 30; findings are data, the exit code never escalates on them; *.zh.md and docs/zh/ archives skipped; default jargon map docs/jargon-to-standard-mapping-v1.md) -> tools/norm_lint.py" ;;
    *) return 1 ;;
  esac
}

# Passthrough execution (tool -> repo-root-relative script mapping; a missing script exits 9; with no args the one-line hint prints first, then passthrough)
run_tool() {  # $1=tool  $2=target-script (relative to ROOT)  rest=args passthrough
  local tool="$1" rel="$2"
  shift 2
  local script="$ROOT/$rel"
  if [ ! -f "$script" ]; then
    echo "cw.sh $tool: missing $rel" >&2
    exit 9
  fi
  if [ "$#" -eq 0 ]; then
    hint_for "$tool" >&2
  fi
  exec python3 "$script" "$@"
}

case "${1:-}" in
  scan4)       shift; run_tool scan4       "scan/scan_v4_token.py"        "$@" ;;
  cure)        shift; run_tool cure        "wash/cure_applier.py"         "$@" ;;
  probe)       shift; run_tool probe       "wash/probe_engine.py"         "$@" ;;
  chain)       shift; run_tool chain       "tools/chain_graph.py"         "$@" ;;
  sync-ledger) shift; run_tool sync-ledger "tools/ledger_sync.py"         "$@" ;;
  erasure)     shift; run_tool erasure     "verify/erasure_classifier.py" "$@" ;;
  dual-scan)   shift; run_tool dual-scan   "scan/dual_scan.py"            "$@" ;;
  doctor)      shift; run_tool doctor      "tools/toolchain_dyld_doctor.py" "$@" ;;
  net-probe)   shift; run_tool net-probe   "tools/net_probe.py"           "$@" ;;
  triage)      shift; run_tool triage      "tools/ci_triage.py"           "$@" ;;
  union)       shift; run_tool union       "tools/registry_union.py"      "$@" ;;
  pushci)      shift; run_tool pushci      "tools/pushci.py"              "$@" ;;
  sentinel)    shift; run_tool sentinel    "tools/cw_sentinel.py"         "$@" ;;
  wash-shape)  shift; run_tool wash-shape  "tools/wash_shape.py"          "$@" ;;
  unclog)      shift; run_tool unclog      "tools/unclog.py"              "$@" ;;
  cw-doctor)   shift; run_tool cw-doctor   "tools/cw_doctor.py"           "$@" ;;
  doc-lint)    shift; run_tool doc-lint    "tools/doc_lint.py"            "$@" ;;
  netname-normalize) shift; run_tool netname-normalize "tools/netname_normalize.py" "$@" ;;
  select-audit) shift; run_tool select-audit "tools/select_audit.py"        "$@" ;;
  render-events) shift; run_tool render-events "tools/render_events.py"     "$@" ;;
  baseline-diff) shift; run_tool baseline-diff "tools/baseline_diff.py"     "$@" ;;
  dispatch)    shift; run_tool dispatch    "tools/red_dispatch.py"          "$@" ;;
  audit)       shift; run_tool audit       "tools/registry_audit.py"        "$@" ;;
  registry-fix) shift; run_tool registry-fix "tools/registry_fix.py"        "$@" ;;
  norm-lint)   shift; run_tool norm-lint   "tools/norm_lint.py"             "$@" ;;
  help|-h|--help)
    if [ "$#" -ge 2 ]; then
      if hint_for "$2"; then
        exit 0
      else
        echo "cw.sh help: unknown tool: $2（未知工具·legal: scan4|cure|probe|chain|sync-ledger|erasure|dual-scan|doctor|net-probe|triage|union|pushci|sentinel|wash-shape|unclog|cw-doctor|doc-lint|netname-normalize|select-audit|baseline-diff|render-events|dispatch|audit|registry-fix|norm-lint）" >&2
        exit 2
      fi
    fi
    usage
    exit 0 ;;
  "") usage; exit 0 ;;
  *)
    echo "cw.sh: unknown tool: $1（未知工具·legal: scan4|cure|probe|chain|sync-ledger|erasure|dual-scan|doctor|net-probe|triage|union|pushci|sentinel|wash-shape|unclog|cw-doctor|doc-lint|netname-normalize|select-audit|baseline-diff|render-events|dispatch|audit|registry-fix|norm-lint|help）" >&2
    usage >&2
    exit 2 ;;
esac
