#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_pushci.py — tools/pushci.py 六场景铸例壳（tests/·pushci 一键流水线测试席·
20261111）

pushci 一键流水线（preflight 发射闸→push→watch→NETRED 自愈 rerun→verdict→可选
merge）的场景测试：六场景 fixture（tests/fixtures/pushci_scenarios/*.json·GitHub
API 真形 canned 响应按轮次序列）经实现原生 flat 注入形（夹具原件 verbatim→
DIR/scenario.json·「canned 键即认」）驱动 tools/pushci.py 全离线全注入跑通，逐场景
判 exit 码／report.final／heal 轮数／关键 stage 字段／调用流水实证：

  1 工具自证    pushci --selftest 冻结矢量（rc 0·PUSHCI-SELFTEST PASS）
  2 helper 自证 tmp-git 仓 fixture：真 git 仅 init/add/commit/remote 层（repo_path
                由 fixture 建仓·push 永不真跑——场景层 git 全走 --git-caller canned）
  3 S1 绿径     preflight 双闸（flat 形缺省绿·响亮注记在册）→push 注入（get-url/
                rev-parse/push/ls-remote 四调·远端为准）→watch 2 轮 run success→
                verdict success exit 0·零 heal（rounds 空 last_triage None）·零 merge
  4 S2 NETRED 愈合  attempt1 failure NETRED（B 族·canned.jobs[0] 真判类）→probe
                STABLE（canned.probe[0]）→rerun 201（run_id 咬合）→attempt2 success→
                verdict success exit 0·heal_rounds==1
  5 S3 内容红   failure A-content-red→verdict fix-content exit 2·零 rerun 实证
                ＝report.heal.rounds 空（契约原言）＋fired_total==0＋api_calls 零
                POST；判类 outcome 在册 heal.last_triage
  6 S4 heal 耗尽  NETRED×3（--max-heal 2·canned.jobs 三 entry 逐判类消耗·两轮
                probe STABLE→rerun 201 仍 NETRED）→verdict heal-exhausted exit 1
  7 S5 merge 流  run success→PUT merge 200（--pr 42·flat 形 pulls GET 须显传）→
                report.merge.merge_sha 非空 exit 0
  8 S6 dry-run  --dry-run 计划输出·零 API 调用（api_calls.json==[]）零 git 调用
                （calls.json==[]）→verdict dry-run exit 0
  9 幂等        六场景各两跑（同仓同 canned）：report 字节恒同；若含漂移则全部
                差异叶须落墙钟类窄键名（否则红·禁静默放宽）
  10 CLI 五码   --help 0／未知形参 2／缺必给 2／repo 缺失 9／injector-git-caller
                单边 2

零副作用律：全部场景 tmp 仓 fixture（每跑 HEAD sha 与 status --porcelain 前后逐
字节不变）；远端 URL 恒指不可达假域 pushci.invalid（结构性零真网络）＋push 层必经
--git-caller canned 注入（调用流水 calls.json 逐调实证·真 git 子进程零发射）；
--sleep-scale 0 恒传＋--netrc 恒指不存在路径（凭据惰性读证）；api_calls.json 与
canned 期望流水逐位对拍（欠发/过发/错序皆红）。

映射层（fixture→injector·薄）：fixture 原件 verbatim 拷贝→DIR/scenario.json
（实现 flat 形「canned 键即认」·schema/summary/argv/expect 等未知键实现忽略）；
git-caller canned 由 fixture head_sha/branch 推导（四调序＝实现实调序）；
expected_api_sequence 由 canned 纯推导（逐轮 GET·同轮 rerun·末轮 merge）→与
api_calls.json 逐位对拍。

用法：
  bash tools/cpu_guard.sh -MaxWaitSec 120 -- python3 -B tests/test_pushci.py
  python3 -B tests/test_pushci.py        # 手动（-B 禁 __pycache__）

退出码：0=十节全绿；1=任一红（fail-loud 响亮逐条列红·红例打印 file:line）。
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUSHCI = os.path.join(REPO, "tools", "pushci.py")
FIXDIR = os.path.join(REPO, "tests", "fixtures", "pushci_scenarios")
SCHEMA = "rocqwash-pushci/1"

# canned 测试域（实现与夹具共认：假域远端·ORG/REPO 由 URL 末两段推导·结构性零网）
TEST_REPO = "octo-org/rocqwash-verify"
REMOTE_URL = "https://pushci.invalid/%s.git" % TEST_REPO
RUNS_PATH = "/repos/%s/actions/runs?per_page=30" % TEST_REPO

# 契约 verdict 七态（任务书钦面·禁放宽）
VERDICTS = ("success", "fix-content", "toolchain", "unstable",
            "heal-exhausted", "gate4-block", "dry-run")

SCENARIOS = ["s1_green_path", "s2_netred_heal", "s3_content_red",
             "s4_heal_exhausted", "s5_merge_flow", "s6_dry_run"]

# 墙钟类键名（幂等判的例外面·窄类不放宽：仅此形键可跨跑漂移）
WALLCLOCK_KEY_RX = re.compile(
    r"(^|_)(at|time|timestamp|generated|wallclock|now|iso|date)(_t)?$|_at$", re.I)

INJ_TIMEOUT_SEC = 60   # 单场景子进程墙钟帽（超时=红·防 canned 失配死旋）


# ---- 通用小件 ---------------------------------------------------------------

def real_git():
    """真 git（PATH 解析·零硬编码绝对路径）。缺位 fail-loud。"""
    g = shutil.which("git")
    if not g:
        raise RuntimeError("git 不在 PATH（tmp-git helper 真 git 仅 init/commit 层）")
    return g


def run(argv, env=None, timeout=INJ_TIMEOUT_SEC):
    """子进程跑（stdout+stderr 合流·超时即红）。"""
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=env, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def load_json(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path, obj):
    """确定性落盘（sort_keys·git-caller 场景写盘用·承 house 落盘口径）。"""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)


def load_scenario(name):
    return load_json(os.path.join(FIXDIR, name + ".json"))


def base_env():
    """凭据净室：测试子进程永不带真 token（网络面另由 --netrc 缺失路径惰性读证）。"""
    env = dict(os.environ)
    for k in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN"):
        env.pop(k, None)
    return env


# ---- tmp-git 仓 fixture（真 git 仅 init/add/commit/remote 层）----------------

def make_tmp_repo(root, name, branch, remote_url):
    """git init -b <branch>＋add＋commit＋remote add origin。push/ls-remote/fetch
    真调用零发射——场景层 git 全走 --git-caller canned（实现注入点①）＋远端 URL
    恒假域（结构性不可达）。"""
    repo = os.path.join(root, name)
    git = real_git()
    cfg = ["-c", "user.name=pushci-test", "-c", "user.email=pushci@test.invalid"]
    rc, out = run([git, "init", "-q", "-b", branch, repo])
    assert rc == 0, "git init 应 0: %s" % out
    with io.open(os.path.join(repo, "pushci_probe.txt"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write("branch=%s\n" % branch)
    rc, out = run([git, "-C", repo] + cfg + ["add", "pushci_probe.txt"])
    assert rc == 0, "git add 应 0: %s" % out
    rc, out = run([git, "-C", repo] + cfg + ["commit", "-q", "-m", "pushci fixture"])
    assert rc == 0, "git commit 应 0: %s" % out
    rc, out = run([git, "-C", repo, "remote", "add", "origin", remote_url])
    assert rc == 0, "git remote add 应 0: %s" % out
    return repo


def head_and_status(repo):
    """仓面快照（HEAD sha＋porcelain）→ 零副作用判据用（真 git·只读）。"""
    git = real_git()
    rc, out = run([git, "-C", repo, "rev-parse", "HEAD"])
    assert rc == 0, "rev-parse HEAD 应 0: %s" % out
    rc2, out2 = run([git, "-C", repo, "status", "--porcelain"])
    assert rc2 == 0, "status 应 0: %s" % out2
    return out.strip(), out2


# ---- 映射层：fixture → injector（flat verbatim）＋git-caller 场景 -------------

def rerun_round_map(scen):
    """rerun[j] → 第 j+1 轮（第 j+1 次 watch 轮观测 NETRED·同轮 triage→probe→rerun）。"""
    return {j + 1: rr for j, rr in enumerate(scen["canned"]["rerun"])}


def build_injector(scen, inj_dir, git_json_path):
    """薄映射层：夹具原件 verbatim → DIR/scenario.json（实现 flat 形「canned 键
    即认」·schema/scenario/summary/argv/expect 未知键实现忽略）；git-caller 场景
    由 fixture head_sha/branch 推导。返回 git-caller 场景路径。"""
    os.makedirs(inj_dir)
    shutil.copyfile(os.path.join(FIXDIR, scen["scenario"] + ".json"),
                    os.path.join(inj_dir, "scenario.json"))
    dump_json(git_json_path, {"responses": build_git_responses(scen)})
    return git_json_path


def build_git_responses(scen):
    """git-caller canned（四调序＝实现实调序）：get-url→rev-parse（本地 tip）→
    push→ls-remote（远端 tip 复核·「远端为准」）。dry-run 零调用（空表）。"""
    if scen["argv"]["dry_run"]:
        return []
    return [
        {"args_contains": ["get-url"], "rc": 0, "stdout": REMOTE_URL + "\n"},
        {"args_contains": ["rev-parse"], "rc": 0,
         "stdout": scen["head_sha"] + "\n"},
        {"args_contains": ["push"], "rc": 0, "stdout": "To %s\n" % REMOTE_URL},
        {"args_contains": ["ls-remote"], "rc": 0,
         "stdout": "%s\trefs/heads/%s\n" % (scen["head_sha"], scen["branch"])},
    ]


def expected_api_sequence(scen):
    """canned 纯推导期望 API 流水（逐轮 GET·同轮 rerun·末轮 merge）→ 与
    api_calls.json 逐位对拍（按轮次脚本化的实证判）。"""
    canned = scen["canned"]
    rmap = rerun_round_map(scen)
    n = len(canned["runs"])
    seq = []
    for r in range(1, n + 1):
        seq.append({"round": r, "method": "GET", "path": RUNS_PATH, "status": 200})
        rr = rmap.get(r)
        if rr:
            run_id = canned["runs"][r - 1]["workflow_runs"][0]["id"]
            seq.append({"round": r, "method": "POST",
                        "path": "/repos/%s/actions/runs/%s/rerun"
                                % (TEST_REPO, run_id),
                        "status": rr["status"]})
    if canned["merge"] is not None:
        seq.append({"round": n, "method": "PUT",
                    "path": "/repos/%s/pulls/%s/merge"
                            % (TEST_REPO, scen["argv"]["pr"]),
                    "status": canned["merge"]["status"]})
    return seq


# ---- CLI 拼装（契约旗标）----------------------------------------------------

def pushci_argv(scen, inj_dir, git_json, repo, report_path, netrc_missing):
    """--repo-path/--branch/--injector DIR/--git-caller/--sleep-scale 0/--json
    ＋场景 extras（--merge/--pr/--max-heal/--dry-run）。--steps 缺省全跑（契约
    形在册·场景恒全管线）。--netrc 恒指不存在路径＝凭据惰性读证。"""
    argv = [sys.executable, "-B", PUSHCI,
            "--repo-path", repo,
            "--branch", scen["branch"],
            "--remote", "origin",
            "--injector", inj_dir,
            "--git-caller", git_json,
            "--netrc", netrc_missing,
            "--sleep-scale", "0",
            "--json", report_path]
    a = scen["argv"]
    if a.get("max_heal") is not None:
        argv += ["--max-heal", str(a["max_heal"])]
    if a.get("merge"):
        argv += ["--merge", "--pr", str(a["pr"])]
    if a.get("dry_run"):
        argv += ["--dry-run"]
    return argv


# ---- report 字段访问（契约语义固定·路径承实现实形）--------------------------

def report_fields(rep):
    """verdict（七态）/final{conclusion,verdict}/heal{rounds=fired 账,fired_total,
    last_triage}/merge{pr,merged,merge_sha}/watch{rounds,run_id,conclusion}/
    preflight/push/plan/mode。"""
    st = rep.get("stages") or {}
    return {
        "verdict": rep.get("verdict"),
        "final": rep.get("final") or {},
        "heal": st.get("heal"),
        "merge": st.get("merge"),
        "watch": st.get("watch") or {},
        "preflight": st.get("preflight") or {},
        "push": st.get("push") or {},
        "plan": rep.get("plan"),
        "mode": rep.get("mode"),
    }


# ---- 场景执行 ----------------------------------------------------------------

def run_scenario(scen, root, tag, repo=None, netrc_missing=None):
    """单场景一跑：injector（flat verbatim）＋git-caller 场景铸成→pushci 子进程→
    结果账。repo 可复用（幂等两跑同仓同 canned）。"""
    if repo is None:
        repo = make_tmp_repo(root, "repo_%s_%s" % (tag, scen["scenario"]),
                             scen["branch"], REMOTE_URL)
    inj_dir = os.path.join(root, "inj_%s_%s" % (tag, scen["scenario"]))
    git_json = os.path.join(root, "git_%s_%s.json" % (tag, scen["scenario"]))
    build_injector(scen, inj_dir, git_json)
    before = head_and_status(repo)
    report_path = os.path.join(root, "report_%s_%s.json" % (tag, scen["scenario"]))
    argv = pushci_argv(scen, inj_dir, git_json, repo, report_path,
                       netrc_missing or os.path.join(root, "absent.netrc"))
    rc, out = run(argv, env=base_env())
    after = head_and_status(repo)
    calls_path = git_json[:-len(".json")] + ".calls.json"
    git_calls = load_json(calls_path) if os.path.isfile(calls_path) else None
    api_path = os.path.join(inj_dir, "api_calls.json")
    api_calls = load_json(api_path) if os.path.isfile(api_path) else None
    report = load_json(report_path) if os.path.isfile(report_path) else None
    return {"rc": rc, "stdout": out, "report": report, "report_path": report_path,
            "git_calls": git_calls, "api_calls": api_calls,
            "before": before, "after": after, "repo": repo, "argv": argv,
            "inj_dir": inj_dir}


def assert_common(scen, res):
    """逐场景共判：exit 码/schema/mode/verdict/final/仓面零副作用。"""
    exp = scen["expect"]
    assert res["rc"] == exp["exit"], "exit 应 %d 实测 %d\nstdout=%s" % (
        exp["exit"], res["rc"], res["stdout"][-900:])
    assert res["report"] is not None, "report 未落盘（--json 应出账）\n%s" % \
        res["stdout"][-900:]
    rep = res["report"]
    assert rep.get("schema") == SCHEMA, \
        "report schema 应 %s 实测 %r" % (SCHEMA, rep.get("schema"))
    f = report_fields(rep)
    assert f["verdict"] in VERDICTS, "verdict 须契约七态实测 %r" % f["verdict"]
    assert f["verdict"] == exp["verdict"], \
        "verdict 应 %s 实测 %s\nstdout=%s" % (exp["verdict"], f["verdict"],
                                              res["stdout"][-600:])
    assert f["final"].get("verdict") == exp["verdict"], \
        "report.final.verdict 应 %s 实测 %r" % (exp["verdict"], f["final"])
    assert f["final"].get("conclusion") == exp["final_conclusion"], \
        "report.final.conclusion 应 %r 实测 %r" % (exp["final_conclusion"],
                                                   f["final"].get("conclusion"))
    assert res["before"] == res["after"], \
        "仓面漂移＝副作用违例: before=%r after=%r" % (res["before"], res["after"])
    return f


def assert_call_ledgers(scen, res):
    """调用流水对拍：api_calls 与 canned 纯推导期望逐位恒同；git_calls 计数与
    四调序注入形（get-url→rev-parse→push→ls-remote·全 rc0·dry-run 零调）。"""
    exp = scen["expect"]
    assert res["api_calls"] is not None, "api_calls.json 未落盘（injector 实证面缺）"
    assert res["api_calls"] == expected_api_sequence(scen), \
        "API 流水与 canned 期望序列失配:\n 期望=%r\n 实测=%r" % (
            expected_api_sequence(scen), res["api_calls"])
    assert len(res["api_calls"]) == exp["api_calls"], \
        "API 调用数应 %d 实测 %d" % (exp["api_calls"], len(res["api_calls"]))
    assert res["git_calls"] is not None, "calls.json 未落盘（git 注入实证面缺）"
    assert len(res["git_calls"]) == exp["git_calls"], \
        "git 调用数应 %d 实测 %d: %r" % (exp["git_calls"], len(res["git_calls"]),
                                         res["git_calls"])
    for g in res["git_calls"]:
        assert g.get("rc") == 0, "canned git 调用应 rc=0: %r" % g
    if not scen["argv"]["dry_run"]:
        push_call, confirm_call = res["git_calls"][2], res["git_calls"][3]
        assert "push" in push_call["args"] \
            and "http.version=HTTP/1.1" in push_call["args"], \
            "push 层应在册且带 http.version=HTTP/1.1（实现推送形）: %r" % push_call
        assert "ls-remote" in confirm_call["args"] \
            and ("refs/heads/%s" % scen["branch"]) in confirm_call["args"], \
            "push 后 ls-remote 复核应在册（远端为准）: %r" % confirm_call


def check_s1(scen, res):
    f = assert_common(scen, res)
    exp = scen["expect"]
    assert_call_ledgers(scen, res)
    # preflight 双闸（flat 形缺省绿·响亮注记在册）
    assert f["preflight"].get("toolchain") == {"verdict": "healthy", "rc": 0}, \
        "preflight.toolchain 应 healthy/0 实测 %r" % f["preflight"].get("toolchain")
    assert f["preflight"].get("net") == {"verdict": "STABLE", "rc": 0}, \
        "preflight.net 应 STABLE/0 实测 %r" % f["preflight"].get("net")
    assert any("flat 注入形" in e for e in
               (res["report"].get("evidence") or [])), \
        "flat 形 preflight 缺省绿应响亮注记在册: %r" % res["report"].get("evidence")
    # push 段：sha=远端 tip（ls-remote 复核·远端为准）·单发 rc0·无 ghproxy
    assert f["push"].get("sha") == scen["head_sha"], \
        "push.sha 应远端 tip sha 实测 %r" % f["push"].get("sha")
    assert f["push"].get("attempts") == [{"target": "origin", "rc": 0}], \
        "push.attempts 应单发 rc0 实测 %r" % f["push"].get("attempts")
    assert f["push"].get("ghproxy_used") is False, "绿径不应走 ghproxy"
    # watch 段：2 轮 run success
    assert f["watch"].get("rounds") == exp["watch_rounds"], \
        "watch.rounds 应 %d 实测 %r" % (exp["watch_rounds"],
                                        f["watch"].get("rounds"))
    assert f["watch"].get("run_id") == exp["run_id"], \
        "watch.run_id 应 %r 实测 %r" % (exp["run_id"], f["watch"].get("run_id"))
    assert f["watch"].get("conclusion") == "success", \
        "watch.conclusion 应 success 实测 %r" % f["watch"].get("conclusion")
    # 零 heal（rounds 空·last_triage None）＋零 merge
    assert f["heal"] == {"rounds": [], "fired_total": 0, "last_triage": None}, \
        "S1 零 heal 实证：heal 段应空账实测 %r" % (f["heal"],)
    assert f["merge"] is None, "merge 未启用应无 merge 段实测 %r" % (f["merge"],)
    return ("S1 绿径（exit 0·verdict success·preflight 双闸注记·push 四调注入·"
            "远端为准·零 heal 零 merge）")


def check_s2(scen, res):
    f = assert_common(scen, res)
    exp = scen["expect"]
    assert_call_ledgers(scen, res)
    h = f["heal"] or {}
    assert len(h.get("rounds") or []) == exp["heal_rounds"], \
        "heal_rounds 应 ==%d 实测 %r" % (exp["heal_rounds"], h.get("rounds"))
    r0 = (h.get("rounds") or [{}])[0]
    assert r0.get("round") == 1 and r0.get("family") == "B-netred", \
        "heal 轮应 B-netred 实测 %r" % r0
    assert r0.get("action") == "rerun-after-stable-window", \
        "heal action 应 rerun-after-stable-window 实测 %r" % r0.get("action")
    assert r0.get("probe") == "STABLE", \
        "heal probe 应 STABLE（canned.probe[0]·双探稳窗过才准 rerun）实测 %r" % \
        r0.get("probe")
    assert r0.get("fired") is True and r0.get("http") == 201, \
        "rerun 应发射（fired/http=201）实测 %r" % r0
    assert h.get("fired_total") == 1, "fired_total 应 1 实测 %r" % h.get("fired_total")
    assert (h.get("last_triage") or {}).get("family") == "B-netred", \
        "last_triage 应 B-netred 实测 %r" % h.get("last_triage")
    assert f["watch"].get("rounds") == exp["watch_rounds"], \
        "watch.rounds 应 %d 实测 %r" % (exp["watch_rounds"],
                                        f["watch"].get("rounds"))
    assert f["watch"].get("run_id") == exp["run_id"], \
        "attempt2 同 run id（rerun 复用）应 %r 实测 %r" % (
            exp["run_id"], f["watch"].get("run_id"))
    posts = [c for c in res["api_calls"] if c["method"] == "POST"]
    assert len(posts) == 1 and "/rerun" in posts[0]["path"], \
        "恰一次 rerun POST 实测 %r" % posts
    return "S2 NETRED 愈合（heal_rounds==1·probe STABLE→rerun 201→attempt2 success）"


def check_s3(scen, res):
    f = assert_common(scen, res)
    assert_call_ledgers(scen, res)
    h = f["heal"] or {}
    # 契约原言：零 rerun 实证＝report.heal.rounds 空
    assert h.get("rounds") == [], \
        "零 rerun 实证①：report.heal.rounds 应空实测 %r" % (h.get("rounds"),)
    assert h.get("fired_total") == 0, \
        "零 rerun 实证②：fired_total 应 0 实测 %r" % h.get("fired_total")
    posts = [c for c in res["api_calls"] if c["method"] == "POST"]
    assert posts == [], \
        "零 rerun 实证③：api_calls 应零 POST 实测 %r" % posts
    lt = h.get("last_triage") or {}
    assert lt.get("family") == "A-content-red" \
        and lt.get("action") == "fix-content", \
        "内容红判类应 A-content-red/fix-content（last_triage）实测 %r" % lt
    assert any("零 rerun" in e for e in
               ((res["report"].get("evidence") or [])
                + list(lt.get("evidence") or []))), \
        "证据面应响亮在册（零 rerun）: %r" % res["report"].get("evidence")
    return ("S3 内容红（verdict fix-content·exit 2·零 rerun 三重实证 heal.rounds "
            "空/fired_total=0/api 零 POST·判类在册 last_triage）")


def check_s4(scen, res):
    f = assert_common(scen, res)
    exp = scen["expect"]
    assert_call_ledgers(scen, res)
    h = f["heal"] or {}
    assert len(h.get("rounds") or []) == exp["heal_rounds"], \
        "heal.rounds 应 %d（帽 --max-heal 2）实测 %r" % (exp["heal_rounds"],
                                                        h.get("rounds"))
    assert h.get("fired_total") == exp["heal_rounds"], \
        "fired_total 应 %d 实测 %r" % (exp["heal_rounds"], h.get("fired_total"))
    assert all(r.get("fired") is True and r.get("http") == 201
               and r.get("family") == "B-netred"
               for r in (h.get("rounds") or [])), \
        "两轮愈合皆 B-netred→probe STABLE→rerun 201 实测 %r" % (h.get("rounds"),)
    assert (h.get("last_triage") or {}).get("family") == "B-netred", \
        "last_triage 应 B-netred 实测 %r" % h.get("last_triage")
    assert f["watch"].get("rounds") == exp["watch_rounds"], \
        "watch.rounds 应 %d（三 NETRED 轮）实测 %r" % (
            exp["watch_rounds"], f["watch"].get("rounds"))
    assert any("帽" in e for e in (res["report"].get("evidence") or [])), \
        "证据面应响亮在册（heal 帽达）: %r" % res["report"].get("evidence")
    return "S4 heal 耗尽（NETRED×3·--max-heal 2·verdict heal-exhausted·exit 1）"


def check_s5(scen, res):
    f = assert_common(scen, res)
    exp = scen["expect"]
    assert_call_ledgers(scen, res)
    m = f["merge"] or {}
    assert m.get("pr") == exp["pr_number"], \
        "merge.pr 应 %r 实测 %r" % (exp["pr_number"], m.get("pr"))
    assert m.get("merged") is True, "merge.merged 应 true 实测 %r" % m.get("merged")
    assert m.get("attempts") == [200], \
        "PUT merge 应 200 单发实测 %r" % m.get("attempts")
    assert m.get("merge_sha"), \
        "report.merge.merge_sha 应非空实测 %r" % (m.get("merge_sha"),)
    assert m.get("merge_sha") == exp["merge_sha"], \
        "merge_sha 应 canned %s 实测 %s" % (exp["merge_sha"], m.get("merge_sha"))
    puts = [c for c in res["api_calls"] if c["method"] == "PUT"]
    assert len(puts) == 1 \
        and "/pulls/%d/merge" % exp["pr_number"] in puts[0]["path"], \
        "恰一次 PUT merge 实测 %r" % puts
    return "S5 merge 流（PUT 200·merge_sha 坐实·exit 0）"


def check_s6(scen, res):
    f = assert_common(scen, res)
    assert f["mode"] == "dry-run", "mode 应 dry-run 实测 %r" % f["mode"]
    assert f["plan"], "dry-run 应有计划输出（report.plan 非空）"
    assert res["git_calls"] == [], \
        "S6 零 git 调用实证＝calls.json 空·实测 %r" % res["git_calls"]
    assert res["api_calls"] == [], \
        "S6 零 API 调用实证＝api_calls.json 空·实测 %r" % res["api_calls"]
    assert res["stdout"].strip(), "dry-run 应有计划 stdout"
    assert "PLAN [2] push" in res["stdout"], \
        "计划应含 push 段行: %s" % res["stdout"][-500:]
    assert scen["branch"] in res["stdout"], \
        "计划输出应含分支名（计划实证）: %s" % res["stdout"][-500:]
    return "S6 dry-run（零 API 零 git 调用流水实证·计划在册·verdict dry-run·exit 0）"


CHECKS = {
    "s1_green_path": check_s1,
    "s2_netred_heal": check_s2,
    "s3_content_red": check_s3,
    "s4_heal_exhausted": check_s4,
    "s5_merge_flow": check_s5,
    "s6_dry_run": check_s6,
}


# ---- 幂等（字节恒同优先·墙钟窄类例外）---------------------------------------

def diff_paths(a, b, prefix=""):
    """两 JSON 结构逐叶对差 → 差异叶路径表。"""
    out = []
    if type(a) is not type(b):
        return [prefix or "<root>"]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(prefix + "/" + k)
            else:
                out.extend(diff_paths(a[k], b[k], prefix + "/" + k))
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append("%s[len %d vs %d]" % (prefix, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(diff_paths(x, y, "%s[%d]" % (prefix, i)))
    elif a != b:
        out.append(prefix or "<root>")
    return out


def idempotence_verdict(path_a, path_b):
    """两跑 report 幂等判 → (ok, note)。字节恒同最优先；否则全部差异叶须落墙钟
    类窄键名（任务书例外面·其余任何漂移皆红）。"""
    ba = io.open(path_a, "rb").read()
    bb = io.open(path_b, "rb").read()
    if ba == bb:
        return True, "字节恒同"
    diffs = diff_paths(load_json(path_a), load_json(path_b))
    bad = [d for d in diffs
           if not WALLCLOCK_KEY_RX.search(d.rsplit("/", 1)[-1].split("[")[0])]
    if bad:
        return False, "非墙钟差异叶: %r" % bad
    return True, "仅墙钟类叶漂移（%d 叶）→ 按契约只比 verdict 与结构键集" % len(diffs)


def _keyset(obj, prefix=""):
    """结构键集（递归·幂等比面）。"""
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(prefix + "/" + k)
            keys |= _keyset(v, prefix + "/" + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            keys |= _keyset(v, "%s[%d]" % (prefix, i))
    return keys


# ---- 分节 -------------------------------------------------------------------

def guard(section, fails, fn):
    """分节执行壳：异常捕获→红账（file:line 定位·fail-loud 不吞）。"""
    try:
        return fn(), None
    except Exception as exc:  # noqa: BLE001 — 全体异常记账汇总响亮（禁静默）
        msg = exc.args[0] if exc.args else str(exc)
        if not isinstance(exc, AssertionError):
            msg = "非断言异常 %s: %s" % (type(exc).__name__, msg)
        fails.append((section, sys.exc_info(), msg))
        return None, exc


def sec_selftest(fails):
    def _go():
        rc, out = run([sys.executable, "-B", PUSHCI, "--selftest"])
        assert rc == 0, "pushci --selftest 应 rc=0 实测 %d\n%s" % (rc, out[-900:])
        assert "PUSHCI-SELFTEST PASS" in out, \
            "stdout 缺冻结标记\n%s" % out[-900:]
        return "selftest 冻结矢量绿（PUSHCI-SELFTEST PASS）"
    return guard("sec1_selftest", fails, _go)[0]


def sec_helper(fails):
    def _go():
        tmp = tempfile.mkdtemp(prefix="pushci_helper_")
        try:
            repo = make_tmp_repo(tmp, "r1", "topic-helper",
                                 "https://pushci.invalid/octo-org/"
                                 "rocqwash-verify.git")
            head, porc = head_and_status(repo)
            assert len(head) == 40 and porc == "", \
                "tmp 仓应单 commit 净树: head=%r porc=%r" % (head, porc)
            git = real_git()
            rc, out = run([git, "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"])
            assert rc == 0 and out.strip() == "topic-helper", \
                "分支应为 fixture branch: %s" % out
            rc, out = run([git, "-C", repo, "remote", "get-url", "--push",
                           "origin"])
            assert rc == 0 and out.strip() == \
                "https://pushci.invalid/octo-org/rocqwash-verify.git", \
                "remote 应 canned 假域形（结构性零真网络）: %s" % out
            return ("tmp-git helper 绿（真 git 仅 init/add/commit/remote 层·"
                    "push 层由场景 --git-caller 注入·远端假域结构性零真网络）")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return guard("sec2_helper", fails, _go)[0]


def sec_scenarios(fails, root):
    notes = []
    for name in SCENARIOS:
        scen = load_scenario(name)

        def _go():
            return CHECKS[name](scen, run_scenario(scen, root, "run1"))

        note, _ = guard(name, fails, _go)
        notes.append(note)
    return notes


def sec_idempotence(fails, root):
    notes = []
    for name in SCENARIOS:
        scen = load_scenario(name)

        def _go():
            repo = make_tmp_repo(root, "repo_idem_%s" % name, scen["branch"],
                                 REMOTE_URL)
            r1 = run_scenario(scen, root, "idem1", repo=repo)
            r2 = run_scenario(scen, root, "idem2", repo=repo)
            exp = scen["expect"]
            assert r1["rc"] == r2["rc"] == exp["exit"], \
                "两跑 exit 应恒 %d（实测 %d/%d）" % (exp["exit"], r1["rc"], r2["rc"])
            assert r1["report"] is not None and r2["report"] is not None, \
                "两跑 report 皆应落盘"
            ok, note = idempotence_verdict(r1["report_path"], r2["report_path"])
            assert ok, "幂等红: %s" % note
            f1 = report_fields(r1["report"])
            f2 = report_fields(r2["report"])
            assert f1["verdict"] == f2["verdict"] == exp["verdict"], \
                "两跑 verdict 恒同且合规: %r vs %r" % (f1["verdict"], f2["verdict"])
            assert _keyset(r1["report"]) == _keyset(r2["report"]), \
                "两跑 report 结构键集恒同"
            return "%s 两跑幂等（%s）" % (name, note)

        note, _ = guard("idem_" + name, fails, _go)
        notes.append(note)
    return notes


def sec_cli_codes(fails):
    def _go():
        tmp = tempfile.mkdtemp(prefix="pushcli_codes_")
        try:
            rc, out = run([sys.executable, "-B", PUSHCI, "--help"])
            assert rc == 0 and "usage" in out, \
                "--help 应 rc=0 含 usage 实测 %d\n%s" % (rc, out[-400:])
            rc, out = run([sys.executable, "-B", PUSHCI, "--bogus-flag"])
            assert rc == 2, "未知形参应 rc=2 实测 %d\n%s" % (rc, out[-400:])
            rc, out = run([sys.executable, "-B", PUSHCI])
            assert rc == 2, "缺必给应 rc=2 实测 %d\n%s" % (rc, out[-400:])
            rc, out = run([sys.executable, "-B", PUSHCI, "--repo-path",
                           os.path.join(tmp, "no_repo"), "--branch", "x"])
            assert rc == 9, "repo 缺失应 rc=9 实测 %d\n%s" % (rc, out[-400:])
            rc, out = run([sys.executable, "-B", PUSHCI, "--repo-path", tmp,
                           "--branch", "x", "--injector", os.path.join(tmp, "inj")])
            assert rc == 2, "injector 单边应 rc=2 实测 %d\n%s" % (rc, out[-400:])
            return "CLI 五码（help0·未知形参2·缺必给2·repo 缺失9·injector 单边2）"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return guard("sec_cli_codes", fails, _go)[0]


# ---- 主流程 -----------------------------------------------------------------

def frame_loc(exc_info):
    """红例定位：本文件最深帧 → file:line。"""
    for fr in reversed(traceback.extract_tb(exc_info[2])):
        if os.path.abspath(fr.filename) == os.path.abspath(__file__):
            return "%s:%d" % (fr.filename, fr.lineno)
    return "%s:?" % os.path.basename(__file__)


def main():
    print("== test_pushci: pushci 六场景铸例壳（repo=%s）==" % REPO)
    if not os.path.isfile(PUSHCI):
        print("FAIL-LOUD: tools/pushci.py 缺席——场景节不可跑（fail-loud）")
        return 1
    fails = []
    notes = []
    tmp = tempfile.mkdtemp(prefix="rocqwash_pushci_test_")
    try:
        notes.append(sec_selftest(fails))
        notes.append(sec_helper(fails))
        notes.extend(sec_scenarios(fails, tmp))
        notes.extend(sec_idempotence(fails, tmp))
        notes.append(sec_cli_codes(fails))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for n in notes if n)
    print("== test_pushci: %d 过 / %d 红 ==" % (passed, len(fails)))
    for n in notes:
        if n:
            print("PASS:", n)
    for label, exc, msg in fails:
        print("FAIL %s at %s: %s" % (label, frame_loc(exc), msg))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
