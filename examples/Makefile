# examples/Makefile — rocqwash 单文件全链演示 / single-file full-chain demo
#
# 链路 Chain:  scan -> names -> (N=N compare) -> wash -> verify
#
# 诚实律 Honesty rule:
#   真跑的步骤如实输出；未落地模块/缺失编译器的步骤打印 SKIP（NOT-RUN，非通过、非绿）。
#   Real steps run for real; pending-module / no-compiler steps print SKIP (NOT-RUN,
#   never counted as a pass).
#
# 用法 Usage:  make demo   |   make scan names nn wash verify clean

ROOT  := $(abspath $(CURDIR)/..)
CLI   := $(ROOT)/cli/rocqwash
GUARD := bash $(ROOT)/tools/cpu_guard.sh
BUILD := $(CURDIR)/build

DEMO        := demo_prop_leak.v
WASHED      := washed/demo_prop_leak_washed.v
WASHED_BASE := demo_prop_leak_washed.v
WASHLG      := washed/demo_ledger.json

.PHONY: demo scan names nn wash verify clean

demo: scan names nn wash verify
	@echo
	@echo "== demo done：scan/names/nn = RUN（真实执行）；wash/verify = 见上方 RUN/SKIP 标记（SKIP=NOT-RUN 非通过）=="

scan:
	@mkdir -p "$(BUILD)"
	@echo "== [1/5] scan 原件（预期：结论位 RED 命中清单——报清单不报清白）=="
	@$(CLI) scan --file "$(DEMO)" --json "$(BUILD)/scan_demo.json" --hits-csv "$(BUILD)/scan_demo_hits.csv"

names:
	@mkdir -p "$(BUILD)"
	@echo "== [2/5] names 原件（census 口径·计数断言 N=5）=="
	@$(CLI) names "$(DEMO)" --expect 5 --names-out "$(BUILD)/names_demo.txt" --json "$(BUILD)/names_demo.json"

nn:
	@echo "== [3/5] names N=N 有序全等断言（原件 vs 洗后对照件）=="
	@$(CLI) names "$(DEMO)" --compare "$(WASHED)" --expect 5

wash:
	@mkdir -p "$(BUILD)"
	@if $(CLI) wash "$(DEMO)" --patch "$(WASHLG)" --out "$(BUILD)/$(WASHED_BASE)"; then \
	  if cmp -s "$(BUILD)/$(WASHED_BASE)" "$(WASHED)"; then \
	    echo "== [4/5] wash RUN（wash_engine 台账机械执行·16 patch 全 APPLY）"; \
	    echo "   引擎输出与参照件 $(WASHED) 逐字节恒同（cmp PASS·幂等重放 applied=0 skipped=N）"; \
	  else \
	    echo "FAIL [4/5] wash：引擎输出与参照件漂移（cmp FAIL）"; exit 1; \
	  fi; \
	else rc=$$?; \
	  if [ "$$rc" -eq 3 ] || [ "$$rc" -eq 4 ]; then \
	    echo "SKIP [4/5] wash：cli exit rc=$$rc（无台账不洗——SKIP=NOT-RUN 非通过）。"; \
	    echo "     洗后目标形态以对照件提供（规范映射：结论位 bare=→Id / nat≤→NatLe）：$(WASHED)"; \
	  else \
	    echo "FAIL [4/5] wash：cli 退出码 $$rc"; exit 1; \
	  fi; \
	fi

verify:
	@mkdir -p "$(BUILD)/compile"
	@cp "$(WASHED)" "$(BUILD)/compile/$(WASHED_BASE)"
	@if command -v rocq >/dev/null 2>&1; then comp="rocq c"; \
	elif command -v coqc >/dev/null 2>&1; then comp="coqc"; \
	else comp=""; fi; \
	if [ -n "$$comp" ]; then \
	  echo "== [5/5a] verify 编译段：cpu_guard 包裹 $$comp =="; \
	  $(GUARD) -Reg /tmp/rocqwash_demo_reg -Front 0 -Mid 1 -- $$comp -native-compiler no -Q "$(BUILD)/compile" "" "$(BUILD)/compile/$(WASHED_BASE)"; \
	else \
	  echo "SKIP [5/5a] verify 编译段：本机无 rocq/coqc → NOT-RUN（非通过）。"; \
	fi
	@if $(CLI) verify "$(WASHED)"; then \
	  echo "== [5/5b] verify R4 RUN =="; \
	else rc=$$?; \
	  if [ "$$rc" -eq 3 ] || [ "$$rc" -eq 4 ]; then \
	    echo "SKIP [5/5b] verify R4 段：cli exit rc=$$rc (verify/ has no unified per-file entry)→ NOT-RUN（非通过）。"; \
	  else \
	    echo "FAIL [5/5b] verify：cli 退出码 $$rc"; exit 1; \
	  fi; \
	fi

clean:
	rm -rf "$(BUILD)"
