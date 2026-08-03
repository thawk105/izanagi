# -*- coding: utf-8 -*-
"""P3 後続段 4 driver — coder 自律ループの機械部分 (design v1 §4)。

**位置づけ:** 後続段 4 = coder (LLM) が初めて変異の値・方向を自律生成する段。
reward hacking 圧力が最も高い。iteration フロー (design v1 §4 の 1 周):

    1. planner (LLM):  current_perf (絶対 throughput を含む) + leading-indicators +
       whiteboard → 方向提案 (proposal スキーマは具体値 field を持たない)
       whiteboard は delta_pct field だけを fail-closed にし、direction / magnitude /
       result の値は checkpoint から無検証で入り得る ([T-287] の残余)
       justification / uncertainty の自由文は journal / report に残る
    2. coder   (LLM):  方向 + baseline (絶対 throughput 等の現行指標) → 具体 backoff 値 +
       hole コード (過去候補の勝ち筋値・critic の機序帰属の専用 field は持たない)
    3. harness (本Py): coder コードを EVOLVE-BLOCK hole に挿入 → diff 検疫 (4a)
       - reject  → diff-quarantine rejection を WAL に焼き critic へ (bench に進めない)
       - pass    → run_campaign (build×2/verify/bench) に委譲 → WAL
    4. harness (本Py): 緑 (LI) + 赤 (rejection/liveness/diff-quarantine) digest を組む
    5. critic  (LLM):  帰属 + 次方向
    6. harness (本Py): whiteboard 射影 + 停止判定 (critic attribution 専用 field は
       ないが、generic field の値は検証しない)

**ループ主導権はメインセッション** (design v1 §4)。本モジュールは LLM を spawn しない —
planner/coder/critic の構造化出力を **引数として受け取り** 機械部分だけを回す
(critic-experiment が tools=Bash のみで guided.py 出力だけ見るのと同型のリーク制御:
Model Y = coder に filesystem browse を与えず、harness が context を射影する)。

**diff 検疫の baseline = silo-backoff-fixed.patch 適用後の working-tree** (design v1 §5
Q1 の確定、D39)。骨格 (#if/#else/#endif + stock 枝 + マーカー) は template patch が入れる
不変フレーム。coder の編集面は #if 合成枝 (hole) の 1 行のみ。baseline を「骨格適用後」に
錨づけることで、骨格挿入自体は diff に出ず coder の hole 変更だけが検疫対象になる
(HEAD=stock 基準だと骨格挿入が coder 変更に紛れる — 敵対検証 2026-07-07 の underspec 指摘)。

fixture proposal で機械 E2E を回す実走口は main() (`--no-build` で build を省いた配線
dry-run、既定は kickoff 規模で実 build/verify/bench)。実 LLM の planner/coder/critic は
メインセッションが spawn し本モジュールの関数へ proposal を渡す。
"""
from __future__ import annotations

import argparse
import contextlib
import difflib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign import ident, wal                                    # noqa: E402
from campaign.build_admission import (BuildAdmissionError, BuildRunContext, GeneratorId,  # noqa: E402
                                      add_coder_build_authority_argument,
                                      build_run_context)
from campaign.diff_quarantine import (DiffQuarantine,              # noqa: E402
                                      DiffQuarantineResult,
                                      parse_template_file)
from campaign.layout import (CampaignLayout,                       # noqa: E402
                             exploration_campaign_layout)
from campaign.loop import run_campaign                             # noqa: E402
from campaign.model import (STAGE_ABORT, STAGE_BUILD_START,         # noqa: E402
                            STAGE_COMMIT, STAGE_VERIFY_DONE,
                            CampaignConfig, Genome)
from campaign.pipeline import PerfConfig                           # noqa: E402
from campaign.projection_guard import (                            # noqa: E402
    assert_closed_proposal_schema,
    assert_no_ability_probe_material,
)
from critic.digest import (DIFF_QUARANTINE_REASON,                  # noqa: E402
                           build_digest, load_diff_rejections,
                           load_liveness_rejections, load_rejections,
                           load_verify_abort_signals, render_rejections,
                           render_text)

# ---- campaign 定数 (p3_s4_red 様式。実走前に pin/env を確認する) -----------------
PIN = "028f34d"                       # 段4/D38 時点で凍結した pin (当時の submodule HEAD、
                                       # 現行 pin の正本は pin.CURRENT_PIN だが歴史的 campaign 凍結のため literal 保持)
ENV_TAG = "linux-baremetal"           # 計測層タグ (規律: 計測層以外の数値を混ぜない)
CLK = 1800
NUMA = ["numactl", "--interleave=all"]

MARKER_ID = "silo-backoff-magnitude"
SOURCE_REL = "include/backoff.hh"     # EVOLVE_BLOCK_SOURCES のメンバ (段 4 loop はこの 1 面のみ駆動)
TEMPLATE_PATCH = "patches/silo-backoff-fixed.patch"  # 骨格 (hole) を敷く不変フレーム

_BASE = {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0}

# 停止条件 (design v1 §4、D39 で凍結)。
MAX_ITER = 10
MAX_WALLTIME_S = 3600
CONVERGE_STREAK = 3                   # 同一方向・magnitude=small が N 連続 → 収束
REVERSE_STREAK = 2                    # critic が逆方向を N 回推奨 + 改善なし → 枯渇


# ==== 提案・状態の型 (LLM 出力と harness 状態) =================================

@dataclass
class PlannerProposal:
    """planner-v4 の出力 (値・機序なし)。"""
    axis: str
    direction: str                    # increase | decrease | explore_both
    magnitude: str                    # small | medium | large
    justification: str = ""
    uncertainty: str = ""


@dataclass
class CoderProposal:
    """coder-v4-autonomous の出力 (値 + hole コード)。"""
    axis: str
    value: float                      # 1..1000 の backoff 量
    implementation: str               # "double now_backoff = <式>;"
    justification: str = ""
    confidence: str = "medium"


@dataclass
class WhiteboardEntry:
    """proposal と harness result を保持する whiteboard の 1 行。

    critic attribution 専用 field はないが、direction / magnitude / result の値を検証する
    型ではなく、checkpoint から値・機序を含む文字列が入り得る ([T-287] の残余)。
    delta_pct field だけは planner 射影時に None を fail-closed 強制する。"""
    iteration: int
    direction: str
    magnitude: str
    result: str                       # success | fail | rejected
    delta_pct: Optional[float] = None   # 性能変化率 (率、具体 throughput 値でない)。段 4 は
                                        # 常に None = 段 6 予約 (統計的 delta/検証相は D39 残存リスク c)


@dataclass
class LoopState:
    """ループ状態。iteration は **WAL 由来でない独立カウンタ** — loop が増分し WAL からは
    読まない。online_digest の LeakageError (n>iterations) を将来このループに配線する際に
    恒真化させないための不変 (本ループでは LeakageError 未配線 = D26 の教訓を先取り)。"""
    whiteboard: List[WhiteboardEntry] = field(default_factory=list)
    iteration: int = 0
    start_ts: float = 0.0                # monotonic (プロセス内。永続化しない — 跨ぐと無意味)
    start_wall: float = 0.0             # 絶対 epoch (checkpoint 経由の cross-process wall budget)
    reverse_recommendations: int = 0    # critic の逆方向推奨の連続回数


@dataclass
class StopDecision:
    stop: bool
    reason: str                       # converged|reverse-exhausted|budget-*|continue


# ==== hole 挿入 + diff 検疫 (4a) ==============================================

def _indent_of(line: str) -> str:
    return line[:len(line) - len(line.lstrip())]


def render_hole(base_text: str, marker, implementation: str) -> str:
    """base_text (骨格適用後) の hole 行群を coder の implementation で置換する。

    hole = marker.hole_first .. marker.hole_last (現テンプレは単一行)。元の hole 行の
    インデントを保って implementation を挿入する (行頭が空白+コードになり、diff 検疫の
    二次検査 '_DIRECTIVE_RE (行頭 #)' に偶発ヒットしない — coder 規約の harness 側担保)。"""
    lines = base_text.split('\n')
    indent = _indent_of(lines[marker.hole_first - 1])
    new_body = [indent + ln if ln else ln for ln in implementation.split('\n')]
    out = lines[:marker.hole_first - 1] + new_body + lines[marker.hole_last:]
    return '\n'.join(out)


def make_working_diff(base_text: str, edited_text: str, source_rel: str) -> str:
    """base_text→edited_text の unified diff (git diff HEAD 相当だが baseline は
    骨格適用後の working-tree)。diff_quarantine.parse_diff が読む `+++ b/<path>` +
    `@@` 形式を difflib で生成する。"""
    base = base_text.splitlines(keepends=True)
    edited = edited_text.splitlines(keepends=True)
    return "".join(difflib.unified_diff(
        base, edited, fromfile=f"a/{source_rel}", tofile=f"b/{source_rel}"))


def quarantine(sub: str, implementation: str,
               marker_id: str = MARKER_ID,
               source_rel: str = SOURCE_REL,
               write: bool = True) -> Tuple[DiffQuarantineResult, str, str, str]:
    """骨格適用後の working-tree に coder の implementation を挿入し diff 検疫する。

    **前提: 呼び出し元が既に applied(TEMPLATE_PATCH) 下にある** (working-tree に骨格が
    入っている)。手順:
      1. backoff.hh (骨格入り) を base_text として読む
      2. parse_template_file で marker を取り source_rel を差し替える (basename 推定を上書き)
      3. hole を implementation で置換 → edited_text (write=True でファイルに書く)
      4. working_diff = make_working_diff(base, edited)、head_text=base で validate

    Returns: (DiffQuarantineResult, base_text, edited_text, working_diff)。
    passed=False なら呼び出し元は build に進めず reject を WAL/critic へ (規律2 hard gate)。
    parse_template_file が None を返す (テンプレ骨格が壊れている) 場合は MALFORMED 相当の
    fails-closed 結果を合成して返す (骨格が読めなければ検疫できない = reject)。"""
    path = os.path.join(sub, source_rel)
    with open(path, encoding="utf-8") as f:
        base_text = f.read()
    marker = parse_template_file(path, marker_id)
    if marker is None:
        res = DiffQuarantineResult(
            passed=False, reason="テンプレ骨格をパースできない (fails-closed)",
            digest={"rejection_type": "diff-quarantine", "subtype": "malformed",
                    "reason": "テンプレ骨格をパースできない",
                    "diff_region": source_rel, "template_diff_id": marker_id,
                    "evidence": "parse_template_file が None (骨格構造の破れ)"})
        return res, base_text, base_text, ""
    marker.source_rel = source_rel
    edited_text = render_hole(base_text, marker, implementation)
    working_diff = make_working_diff(base_text, edited_text, source_rel)
    res = DiffQuarantine(marker, working_diff, head_text=base_text).validate()
    if write:
        if res.passed:
            with open(path, "w", encoding="utf-8") as f:
                f.write(edited_text)
    return res, base_text, edited_text, working_diff


# ==== diff-quarantine reject の WAL 記録 (片肺の書き手側) ======================

def diffq_variant_id(genome: Genome, implementation: str) -> str:
    """diff 検疫で reject された variant の WAL キー。build しない (src_token 無し) ため
    pipeline.variant_id は使えない — genome + 提案コードのハッシュで一意化する。"""
    import hashlib
    h = hashlib.sha256((genome.canonical() + "|impl=" + implementation).encode()).hexdigest()[:12]
    return f"diffq-{h}"


def record_diff_reject(layout: CampaignLayout, genome: Genome, implementation: str,
                       res: DiffQuarantineResult, env_tag: str = ENV_TAG) -> str:
    """diff 検疫 reject を WAL に BUILD_START→ABORT(reason=diff-quarantine) で焼く。

    load_diff_rejections がこの形を読み返し critic に渡す (規律3: 検疫が reject を出した
    だけで消費されない片肺を作らない)。build/verify には到達しないので verify payload も
    fitness も無い (正しさゲート手前の失格 = 採用しない、規律2)。"""
    v = diffq_variant_id(genome, implementation)
    wal.log(layout, v, STAGE_BUILD_START, env_tag,
            {"genome": genome.canonical(), "src_token": ""})
    wal.log(layout, v, STAGE_ABORT, env_tag,
            {"reason": DIFF_QUARANTINE_REASON,
             "genome": genome.canonical(),
             "diff_quarantine": res.digest or {}})
    return v


# ==== critic 入力 digest (緑 + 赤、還流 on/off スイッチ) =======================

def make_critic_digest(layout: CampaignLayout, tag: str = "p3-s4",
                       reflux: bool = True) -> str:
    """critic に渡す digest テキストを組む。

    緑 (render_text: committed LI) + 赤 (render_rejections: verify-red/liveness/
    diff-quarantine)。**reflux=False (還流 off ablation) では赤節を落とす** — critic に
    rejection の構造化 anomaly を還流させない対照アーム (main-experiment の LLM ablation、
    合流 1 点の切替。phase3.md 段 6 の第 3 アーム reason-only は段 6)。緑 LI は両アーム
    共通 (性能数値は trace-disabled build 由来、規律1)。"""
    green = render_text([build_digest(tag, {}, layout)])
    if not reflux:
        return green
    livs, other = load_liveness_rejections(layout)
    red = render_rejections(
        load_rejections(layout), livs, other,
        load_verify_abort_signals(layout),
        diff_rejections=load_diff_rejections(layout))
    return green + "\n\n" + red


# ==== whiteboard 射影 (機序を落とす) =========================================

def project_whiteboard(state: LoopState, planner: PlannerProposal,
                       result: str, delta_pct: Optional[float] = None) -> WhiteboardEntry:
    """proposal と harness result を whiteboard の 5 field へ射影する (design v1 §4)。

    critic attribution 専用 field はないが、direction / magnitude / result の内容は検証せず、
    checkpoint から値・機序を含む文字列が入り得る ([T-287] の残余)。delta_pct field だけは
    planner 射影時に None を fail-closed 強制する。result の想定値は success (certified 緑) |
    fail (verify/liveness 赤) | rejected (diff 検疫 reject)。"""
    e = WhiteboardEntry(iteration=state.iteration, direction=planner.direction,
                        magnitude=planner.magnitude, result=result, delta_pct=delta_pct)
    state.whiteboard.append(e)
    return e


def whiteboard_for_planner(state: LoopState) -> List[Dict]:
    """planner-v4 / coder-v4 入力の whiteboard フィールド。

    段 4 はこの whiteboard 射影経路の delta_pct field に限って None を fail-closed
    強制する (規律2/6)。direction / magnitude / result の値は checkpoint から無検証で
    入り得る ([T-287] の残余)。これは planner 入力全体の性能値遮断ではない。絶対
    throughput は別 field の current_perf で planner へ、baseline で coder へ渡り、
    planner には leading_indicators も渡る。delta_pct field は load 側 state_from_dict
    と二重で塞ぎ、in-memory 経路 (project_whiteboard が誤って非 None を書く) も射影の
    関所で止める (監査 2026-07-08)。"""
    out = []
    for e in state.whiteboard:
        if not _DELTA_PCT_LIVE and e.delta_pct is not None:
            raise WhiteboardLeakError(
                f"段 4 の delta_pct≡None 不変が planner 射影で破れた "
                f"(iteration={e.iteration} delta_pct={e.delta_pct!r}、規律2/6)")
        out.append({"iteration": e.iteration, "direction": e.direction,
                    "magnitude": e.magnitude, "result": e.result, "delta_pct": e.delta_pct})
    return out


# ==== 停止判定 (design v1 §4、D39) ===========================================

def check_stop(state: LoopState) -> StopDecision:
    """収束 / 逆方向枯渇 / 予算尽き を機械判定する。

    - Budget: iteration >= MAX_ITER または wall-clock >= MAX_WALLTIME_S。
    - Convergence: 同一方向かつ magnitude=small が CONVERGE_STREAK 連続。段階的な
      magnitude 変化 (small→medium→large) は「異なる提案」として収束と扱わない。
    - Reverse-exhausted: critic の逆方向推奨が REVERSE_STREAK 回以上 + 直近改善なし
      (state.reverse_recommendations は critic 帰属を消費するメインセッションが更新)。"""
    # wall budget: checkpoint 経由 (main-session 駆動) では start_wall (絶対 epoch) を使う —
    # 各 iteration は別 Bash プロセスゆえ monotonic は跨ぐと無意味。start_wall 未設定 (in-process
    # fixture / test) では従来どおり monotonic を使う (後方互換。既存 test は start_ts のみ設定)。
    if state.start_wall:
        elapsed = time.time() - state.start_wall
    else:
        elapsed = time.monotonic() - state.start_ts if state.start_ts else 0.0
    if state.iteration >= MAX_ITER:
        return StopDecision(True, "budget-iterations")
    if elapsed >= MAX_WALLTIME_S:
        return StopDecision(True, "budget-walltime")
    # 収束は **評価が成立した** 提案だけで測る。diff 検疫 reject (result=rejected) は評価
    # 未成立ゆえ収束に数えない — reject 連続を「収束」と取り違えない (規律3、D39 決定2a)。
    evaluated = [e for e in state.whiteboard if e.result != "rejected"]
    tail = evaluated[-CONVERGE_STREAK:]
    if (len(tail) >= CONVERGE_STREAK
            and all(e.direction == tail[0].direction and e.magnitude == "small"
                    for e in tail)):
        return StopDecision(True, "converged")
    if state.reverse_recommendations >= REVERSE_STREAK:
        # 「直近改善なら止めない」escape は delta_pct が算出される段 6 で live 化する。段 4 は
        # delta_pct 未算出 (常に None、段 6 予約) ゆえ escape は明示的に無効 = reverse-exhausted は
        # reverse_recommendations 単独で判定する (恒真ガードを置かない、D39 残存リスク c/決定2b)。
        recent = state.whiteboard[-1] if state.whiteboard else None
        improved = recent is not None and recent.delta_pct is not None and recent.delta_pct > 0
        if not improved:
            return StopDecision(True, "reverse-exhausted")
    return StopDecision(False, "continue")


# ==== LoopState checkpoint/resume (main-session 駆動の cross-process 永続化) ====
#
# 段 4b の実ループはメインセッションが iteration を回す (Model Y、D39 決定7)。各 iteration は
# 別々の Bash 呼び出し = fresh Python プロセスゆえ、LoopState (whiteboard/iteration/reverse) を
# **ディスクに checkpoint** しないと iteration 間で状態が消え feedback loop が死ぬ (planner が
# 前 iteration の result を見れない)。D39 決定2 の「予算枯渇時に whiteboard を checkpoint し段 6
# へ inherit」の実体でもある。checkpoint は WAL でなく loop 状態の投影 — 正本は WAL (レコード)、
# checkpoint は planner に射影する abstract 状態 (機序なし・値なし、決定3 の型と同じ最小フィールド)。


def loop_state_path(layout: CampaignLayout) -> str:
    return os.path.join(layout.root, "loop_state.json")


class WhiteboardLeakError(ValueError):
    """段 4 の delta_pct≡None 不変が checkpoint 経由で破れた = 勝ち筋チャネル (性能値) の混入
    (規律2/6)。型で名前を whitelist するだけでは leak 防御にならない — 値チャネルが空であることを
    検査する (監査 2026-07-08 の real finding。anchor finding 同型 = 謳うだけの保証を発火させる)。"""


# delta_pct は段 4 では常に None (統計的 delta/検証相は段 6 予約、D39 残存リスク c)。段 4 で非 None が
# 現れる = drift/改竄/段6 checkpoint 流用による性能値の混入 → planner に流入すると iteration 毎の利得
# から採用値を逆算できる structural inference (規律2/6)。段 6 で delta_pct を live 化するときはここを
# True にして明示ゲートを開ける (それまでは load と planner 射影の両方で None を fail-closed 強制)。
_DELTA_PCT_LIVE = False


def state_to_dict(state: LoopState) -> Dict:
    """checkpoint へ焼く辞書。start_ts (monotonic) は永続化しない (跨ぐと無意味) —
    wall budget は start_wall (絶対 epoch) が担う。whiteboard は決定3 の 5 フィールドのみ
    (機序フィールドを持たない = structural inference 経路を型で塞ぐ、規律2/6)。"""
    return {"iteration": state.iteration, "start_wall": state.start_wall,
            "reverse_recommendations": state.reverse_recommendations,
            "whiteboard": [{"iteration": e.iteration, "direction": e.direction,
                            "magnitude": e.magnitude, "result": e.result,
                            "delta_pct": e.delta_pct} for e in state.whiteboard]}


_WB_FIELDS = {"iteration", "direction", "magnitude", "result", "delta_pct"}
_TOP_FIELDS = {"iteration", "start_wall", "reverse_recommendations", "whiteboard"}


def state_from_dict(d: Dict) -> LoopState:
    """checkpoint 辞書から復元 — checkpoint はディスク上の外部状態 (信頼境界の外、規律6) ゆえ
    schema を fail-closed に強制する (監査 2026-07-08)。

    (1) **top-level は既知 4 フィールドを必須化**し未知キーを拒否する。欠落を無音デフォルト
        (`d.get(k, 0)`) にすると drift/改竄 checkpoint で iteration/reverse カウンタが暗黙リセット
        され、budget-iterations / reverse-exhausted の**予算ゲートが fail-open** する (直列計測資源
        の予算超過、規律4)。リーク側 (whiteboard entry) は塞いで予算側は塞がない非対称を解消する。
    (2) **whiteboard entry は既知 5 フィールドに絞り** (未知キー = 機序漏れの疑い、決定3)、段 4 は
        **delta_pct≡None を値契約として強制**する (型で名前を whitelist するだけでは勝ち筋チャネル
        の混入を防げない、規律2/6)。"""
    unknown = set(d) - _TOP_FIELDS
    if unknown:
        raise ValueError(f"checkpoint top-level に未知フィールド {unknown} — schema drift/改竄の疑い (規律6)")
    missing = _TOP_FIELDS - set(d)
    if missing:
        raise ValueError(f"checkpoint に必須フィールド {missing} 欠落 — 予算/収束カウンタの暗黙"
                         f"リセット (予算ゲート fail-open) を防ぐため fail-closed (規律2/4/6)")
    wb = []
    for e in d["whiteboard"]:
        extra = set(e) - _WB_FIELDS
        if extra:
            raise ValueError(f"whiteboard entry に未知フィールド {extra} — 機序漏れの疑い (決定3)")
        delta = e.get("delta_pct")
        if not _DELTA_PCT_LIVE and delta is not None:
            raise WhiteboardLeakError(
                f"段 4 の delta_pct≡None 不変が破れた (delta_pct={delta!r}) — 勝ち筋チャネルの "
                f"checkpoint 経由混入 (規律2/6)。段 6 で live 化するまで None 固定")
        wb.append(WhiteboardEntry(
            iteration=int(e["iteration"]), direction=e["direction"],
            magnitude=e["magnitude"], result=e["result"], delta_pct=delta))
    return LoopState(whiteboard=wb, iteration=int(d["iteration"]),
                     start_wall=float(d["start_wall"]),
                     reverse_recommendations=int(d["reverse_recommendations"]))


def save_loop_state(layout: CampaignLayout, state: LoopState) -> str:
    """LoopState を atomic に checkpoint する (os.replace = 途中で落ちても壊れた checkpoint を
    残さない、WAL 哲学)。tmp は **PID 付き一意名** — 同一 campaign に複数プロセスが当たっても
    共有 tmp の rename 衝突/部分読みを避ける (最終 os.replace は last-writer-wins のまま。段 4b は
    単一駆動が前提だが tmp 一意化は安価な標準化、監査 2026-07-08)。"""
    layout.ensure()
    p = loop_state_path(layout)
    tmp = f"{p}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state_to_dict(state), f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)
    return p


def load_loop_state(layout: CampaignLayout) -> Optional[LoopState]:
    """checkpoint があれば復元。無ければ None (呼び出し元が初期化する)。"""
    p = loop_state_path(layout)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return state_from_dict(json.load(f))


# ==== mutation-red 汎用ゲート (D38 残消化、design v1 §4(d)) ====================

_WS_RE = re.compile(r"\s+")


def _norm_expr(e: str) -> str:
    return _WS_RE.sub("", e.strip())


_TRIVIAL_TRUE_RE = re.compile(
    r"^(true|1|(.+)==\2|(.+)>=\3|(.+)<=\4)$", re.IGNORECASE)

_CONST_CMP_RE = re.compile(r"^(-?\d+(?:\.\d+)?)(==|!=|>=|<=|>|<)(-?\d+(?:\.\d+)?)$")


def _is_constant_tautology(c: str) -> bool:
    """両辺が数値定数の比較で常に真か (mutation で決して赤にならない = 恒真)。"""
    m = _CONST_CMP_RE.match(c)
    if not m:
        return False
    import operator
    ops = {"==": operator.eq, "!=": operator.ne, ">=": operator.ge,
           "<=": operator.le, ">": operator.gt, "<": operator.lt}
    return ops[m.group(2)](float(m.group(1)), float(m.group(3)))


def mutation_red_gate(assert_condition: str, invariant: str) -> Tuple[bool, str]:
    """auditor が追加する assert の **非恒真性** を構文検査する (design v1 §4(d))。

    ガード = `assert condition != invariant`: assert 条件が invariant (常に成り立つ性質)
    と構造的に同一なら恒真 = mutation で決して赤にならない = 謳うだけで発火しない保証
    (規律3 の「正しさシグナルを後付けにしない」の対偶: 発火しない gate は無価値)。

    これは **構文レベルの一次篩** — 実 mutation で赤になるかの担保は positive control
    実走 (段 3 s3_lock_coverage 様式の broken patch 赤緑) が別途行う (auditor.md L62 が
    「非恒真性の実際の担保は driver の mutation-red レコード」と前提化済み)。段 4 の
    編集面は backoff hole のみ (lock 経路は段 5) ゆえ auditor 新 assert は限定的で、
    本ゲートは枠組み + 恒真 assert を弾くテストで実証する。段 5 で lock 経路が開くと
    実 mutation 確認が load-bearing になる。

    本篩が弾くのは構文的に自明な恒真のみ (true/1・両辺同一比較・定数比較)。文脈依存の
    意味的恒真 (unsigned 変数の `x>=0` 等) は **fail-open で通す** — 構文検査の原理的限界
    (D33: text 検査の文脈認識化は不可能かつ罠)。ゆえに本ゲートは load-bearing でなく、実
    mutation で赤になるかの担保は positive control 実走 (段 5 s3_lock_coverage 様式) が負う。

    Returns: (ok, reason)。ok=False なら恒真 (reject すべき assert)。"""
    c = _norm_expr(assert_condition)
    inv = _norm_expr(invariant)
    if not c:
        return False, "assert 条件が空 (発火しない)"
    if c == inv:
        return False, (f"恒真: assert 条件が invariant と構造的に同一 "
                       f"({assert_condition!r}) — mutation で赤にならない")
    if _TRIVIAL_TRUE_RE.match(c):
        return False, f"恒真: assert 条件が自明に真 ({assert_condition!r})"
    if _is_constant_tautology(c):
        return False, f"恒真: assert 条件が定数比較で常に真 ({assert_condition!r})"
    return True, ""


# ==== campaign 設定 + 機械判定 (p3_s4_red 様式) ==============================

def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def default_cfg(reflux: bool = True) -> CampaignConfig:
    """段 4 自律ループの campaign 設定。reflux (還流 on/off) は search_config に焼き、
    LLM ablation の対照を identity で分離する (別 campaign = 別 output dir、混ざらない)。"""
    return CampaignConfig(
        spec_slug="p3-s4-loop", search_tag="s4-autonomous",
        spec_content=("P3 後続段 4: coder 自律ループ。planner が方向 (値なし) を提案し "
                      "coder が勝ち筋値を見ずに backoff 値を合成、diff 検疫 (4a) を通した "
                      "hole 変異のみ build/verify/bench に進む。critic 帰属を次 iteration に "
                      "還流 (LLM ablation の on アーム)。fixture red を正系列に混ぜない"),
        ccbench_commit=PIN,
        search_config={"scale": "silo", "axis": MARKER_ID,
                       "reflux": "on" if reflux else "off",
                       "records": 100_000, "threads": 4},
        trial="p3-s4-loop")


def default_perf() -> PerfConfig:
    """配線規模 (kickoff/red と同じ、性能比較用 calibration ではない — 規律4)。
    実 fitness 比較に入る段では calibrator が決めた records/threads/reps に差し替える。"""
    return PerfConfig(records=100_000, threads=4,
                      workload={"ycsb_rratio": "50", "ycsb_zipf_skew": "0.9",
                                "ycsb_rmw": "false"}, extime=1, reps=2)


# ==== 帰属整合 (value ↔ hole literal、D39 決定7 の機械強制) ====================

class AttributionMismatch(ValueError):
    """coder.value と implementation の backoff literal が食い違う = 帰属汚染 (規律6/D39 決定7)。
    メインセッション (Model Y の loop 主導) が catch し coder に再提案させる想定 — harness は
    値と走る literal の不一致を素通しせず、ここで止める (謳うだけの整合規約にしない)。"""


_NOW_BACKOFF_RE = re.compile(r"now_backoff\s*=\s*(-?\d+(?:\.\d+)?)")
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def assert_value_literal_consistent(coder: CoderProposal) -> None:
    """coder.value と implementation の backoff literal の整合を機械強制する (D39 決定7)。

    Model Y では coder (untrusted、規律6) が value と implementation を独立フィールドで供給する。
    両者が食い違うと genome{BACKOFF_FIXED=int(value)} に紐付く certified fitness が実際に走った
    別 literal binary の性能になり **帰属が汚染される** (どの値が効いたかの還流信号が自己矛盾)。
    D39 決定7 はこれを「整合規約」と呼ぶが規約は謳うだけでは発火しない — harness が機械照合する。

    判定: implementation の `now_backoff = <lit>` 代入 literal が value と数値一致すること。
    代入 literal を抽出できない (自由式) 場合は fails-closed で value が implementation に数値
    として現れることを要求する (段 4 の編集面は backoff literal のみ、D39 決定1)。"""
    m = _NOW_BACKOFF_RE.search(coder.implementation)
    if m is not None:
        if float(m.group(1)) != float(coder.value):
            raise AttributionMismatch(
                f"帰属汚染: coder.value={coder.value} だが implementation の now_backoff "
                f"literal={m.group(1)} — genome{{BACKOFF_FIXED={int(coder.value)}}} に別 literal "
                f"binary の結果が紐付く (規律6/D39 決定7)")
        return
    lits = {float(x) for x in _NUM_RE.findall(coder.implementation)}
    if float(coder.value) not in lits:
        raise AttributionMismatch(
            f"帰属汚染: coder.value={coder.value} が implementation に数値として現れない "
            f"({coder.implementation!r}) — value と走る literal の一致を機械確認できない "
            f"(規律6/D39 決定7)")


# ==== 1 iteration の機械 E2E (fixture proposal で実走) ========================

def _resolve_duplicate(layout: CampaignLayout, planner: PlannerProposal,
                       state: LoopState, summary, log=print) -> Dict:
    """重複提案 (run_campaign がリカバリでスキップし summary.results が空) を解決する。

    coder が独立に選んだ値が既存 genome (同一 src_token) と一致し、同一 variant_id が
    既に terminal (前 iteration で certified/aborted 済み) だと run_campaign はリカバリで
    再評価せず summary.results が空になる (loop.py の skip 経路)。これを新規の失敗と
    取り違えない (規律3: 正しさ/評価シグナルを後付けにしない・なぜこうなったかを構造化
    して返す — ここは壊れていない)。variant id は run_campaign が applied(...) 内で確定した
    `summary.skipped_variants` だけを使い、既存 WAL レコードから証拠を復元する。ここで
    source_digest.resolve を再実行してはならない — 呼び手の revert 後 tree からは stock id
    (別 variant) しか出ず、別 variant の WAL 証拠で成否を誤分類し (whiteboard/checkpoint は
    id を持たず分類だけが汚染)、trigger 系 driver では誤った variant id が provenance へ
    永続化する ([T-157]、id 確定点の単一化 = D23/D24。監査 2026-07-09、段 4b iteration 2 の
    実走 = coder が iteration 1 と独立に同じ値を再提案した実例で発見)。
    identity_skipped (id 未確定) の分は skipped_variants に無い → 成功を捏造せず fail 側。"""
    dup_v = summary.skipped_variants[0] if summary.skipped_variants else None
    recs = wal.records_by_stage(layout, dup_v) if dup_v else {}
    commit_payload = recs.get(STAGE_COMMIT)
    verify_payload = recs.get(STAGE_VERIFY_DONE, {})
    if commit_payload is not None:
        project_whiteboard(state, planner, "success", delta_pct=None)
        log(f"  重複提案 (既存 certified variant {dup_v} と同一 genome、新規評価はスキップ)")
        return {"outcome": "duplicate", "variant": dup_v,
                "fitness_tps": commit_payload.get("fitness_tps"),
                "verdict": verify_payload.get("verdict", ""), "records": recs}
    project_whiteboard(state, planner, "fail")
    log(f"  重複提案 (既存 aborted variant {dup_v} と同一 genome)")
    return {"outcome": "aborted", "variant": dup_v,
            "verdict": verify_payload.get("verdict", ""), "records": recs}


def run_one_iteration(cfg: CampaignConfig, perf: PerfConfig,
                      planner: PlannerProposal, coder: CoderProposal,
                      state: LoopState, sub: str, do_build: bool,
                      layout: Optional[CampaignLayout] = None, log=print,
                      cache_root: str = "",
                      build_context: Optional[BuildRunContext] = None) -> Dict:
    """1 iteration の機械部分を回す (LLM proposal は引数で受け取る)。

    do_build=True: applied(TEMPLATE_PATCH) 下で挿入→検疫→(pass なら)run_campaign。
    do_build=False: 挿入→検疫のみ (配線 dry-run、build/verify/bench を省く)。

    `cache_root` (段5 git worktree 隔離): `sub` が呼び手の `patchharness.checkout()` で
    作った使い捨て worktree の場合、build 出力だけは固定共有パス配下に据え置きたい
    呼び手が明示する (省略時は `sub` 直下 = 従来動作と完全互換)。ccbench_dir は常に
    `sub` そのもの (patch/coder 編集がある実際の tree を build に使う)。

    layout=None なら cfg 由来 layout を導出する。**注入 layout は reject WAL/records/checkpoint/
    digest を同一 layout に co-locate させるため** (drive_iteration が checkpoint と同じ layout を
    渡す — さもないと reject WAL が cfg 由来 layout に、checkpoint/digest が注入 layout に分裂し
    digest が空になる、監査 2026-07-08)。

    Returns: {"outcome": rejected|certified|aborted|dry-pass, "variant": ..., ...}。
    """
    from campaign.patchharness import applied
    if build_context is None and not do_build:
        build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    genome = Genome("silo", {**_BASE, "BACK_OFF": 1,
                             "BACKOFF_FIXED": int(coder.value)})
    # 帰属整合の機械強制 (D39 決定7): value と hole literal が食い違うと certified fitness が
    # genome{BACKOFF_FIXED=value} に紐付くのに binary は別 literal で走り帰属が汚染される (規律6)。
    assert_value_literal_consistent(coder)
    if layout is None:
        layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    elif do_build and layout.root != exploration_campaign_layout(
            str(ident.campaign_id(cfg))).root:
        # build 経路は run_campaign が cfg 由来 layout に WAL を書く — 注入 layout がそれと食い違うと
        # WAL と reject/records/digest が分裂する。build 時は一致を強制 (production は layout=None
        # ゆえ常に一致。注入は dry/test 専用の hermetic 化、監査 2026-07-08)。
        raise ValueError(f"build 経路の layout 注入は cfg 由来と一致必須 (WAL 分裂防止): "
                         f"{layout.root} != cfg 由来")
    layout.ensure()
    # reject も campaign の初回 WAL write なので、repair 無しの identity gate を先行する。
    ident.ensure_campaign_identity(
        cfg, layout, admission_policy=build_context.policy,
    )

    if not do_build:
        # dry-run: 骨格を一時適用せず、骨格入りソースを合成して検疫だけ試す経路は
        # 実 working-tree を汚さない (test 用)。ここでは applied を通す本経路を使う。
        with applied(os.path.join(_repo_root(), TEMPLATE_PATCH), PIN, sub):
            res, _b, _e, _d = quarantine(sub, coder.implementation, write=False)
        if not res.passed:
            v = record_diff_reject(layout, genome, coder.implementation, res)
            project_whiteboard(state, planner, "rejected")
            return {"outcome": "rejected", "variant": v, "digest": res.digest}
        return {"outcome": "dry-pass", "variant": None}

    with applied(os.path.join(_repo_root(), TEMPLATE_PATCH), PIN, sub):
        res, _b, _e, _d = quarantine(sub, coder.implementation, write=True)
        if not res.passed:
            v = record_diff_reject(layout, genome, coder.implementation, res)
            project_whiteboard(state, planner, "rejected")
            log(f"  diff 検疫 reject: {res.subtype} — {res.reason}")
            return {"outcome": "rejected", "variant": v, "digest": res.digest}
        # 検疫通過 → build×2 / verify / bench を run_campaign に委譲。coder 編集は
        # working-tree にあり source_digest.resolve が preprocess 後 digest で src_token を
        # 非 stock に上げる。genome の BACKOFF_FIXED と hole literal を coder.value で揃える。
        summary = run_campaign(cfg, [genome], perf, ENV_TAG, CLK, numactl=NUMA, log=log,
                              ccbench_dir=sub, cache_root=cache_root,
                              build_context=build_context,
                              campaign_namespace="exploration")
    v = next((r.variant for r in summary.results), None)
    if v is None and summary.skipped > 0:
        return _resolve_duplicate(layout, planner, state, summary, log=log)
    recs = wal.records_by_stage(layout, v) if v else {}
    r = summary.results[0] if summary.results else None
    if r and r.certified and not r.aborted:
        project_whiteboard(state, planner, "success", delta_pct=None)  # 段 6 予約 (率算出は統計的 delta とセット、D39 残存リスク c)
        return {"outcome": "certified", "variant": v, "fitness_tps": r.fitness_tps,
                "verdict": r.verdict, "records": recs}
    project_whiteboard(state, planner, "fail")
    return {"outcome": "aborted", "variant": v,
            "verdict": (r.verdict if r else ""), "records": recs}


# ==== 段 4b 駆動口 (実 planner/coder proposal を受けて 1 iteration を継続) =========

def _fold_critic_reverse(state: LoopState, prior_critic_reverse: Optional[bool]) -> None:
    """前 iteration の critic feedback (逆方向推奨だったか) を reverse_recommendations に畳む。

    critic 帰属の消費はメインセッションの職務 (Model Y、D39 決定2/7) — 本 harness は critic の
    自然文帰属を読まず、「逆方向を推奨したか否か」の bool だけを受け取り機械カウンタに反映する
    (機序を harness に持ち込まない = whiteboard 射影と同じ規律2/6)。True → +1 (逆方向推奨の連続)、
    False → 0 リセット (順方向路線が続く)、None → 変更なし (iteration 1 入口 or feedback 未供給)。"""
    if prior_critic_reverse is True:
        state.reverse_recommendations += 1
    elif prior_critic_reverse is False:
        state.reverse_recommendations = 0


def load_proposal_file(path: str) -> Tuple[PlannerProposal, CoderProposal, Optional[bool]]:
    """メインセッションが spawn した planner/coder の構造化出力 (+ 前 critic の逆方向 bool) を
    JSON ファイルから読む。schema:

        {"planner": {axis, direction, magnitude, justification?, uncertainty?},
         "coder":   {axis, value, implementation, justification?, confidence?},
         "prior_critic_reverse": true|false|null}

    Model Y の入力射影点 — メインセッションはここに **abstract な proposal だけ** を書く
    (勝ち筋値・機序を harness へ運ぶ経路にしない)。value↔literal 整合は run_one_iteration が
    機械強制する (D39 決定7)。"""
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    assert_closed_proposal_schema(
        d, require_auditor=False, require_coder_value=True,
    )
    p, c = d["planner"], d["coder"]
    planner = PlannerProposal(
        axis=p["axis"], direction=p["direction"], magnitude=p["magnitude"],
        justification=p.get("justification", ""), uncertainty=p.get("uncertainty", ""))
    coder = CoderProposal(
        axis=c["axis"], value=float(c["value"]), implementation=c["implementation"],
        justification=c.get("justification", ""), confidence=c.get("confidence", "medium"))
    # prior_critic_reverse は null か bool のみを許す。非 bool (文字列 "true"・整数 1 等) は
    # _fold_critic_reverse の `is True`/`is False` で黙って no-op し reverse-exhausted の停止
    # フィードバックが fail-open する — planner/coder の必須キーと同じく fail-closed にする
    # (schema 検証を片方だけ緩めない、規律2、監査 2026-07-08)。
    prior = d.get("prior_critic_reverse")
    if prior is not None and not isinstance(prior, bool):
        raise ValueError(f"prior_critic_reverse は null か bool のみ (got {type(prior).__name__}: "
                         f"{prior!r}) — 非 bool は停止フィードバックを fail-open させる (規律2)")
    assert_no_ability_probe_material(d)
    return planner, coder, prior


def drive_iteration(cfg: CampaignConfig, perf: PerfConfig,
                    planner: PlannerProposal, coder: CoderProposal,
                    prior_critic_reverse: Optional[bool], sub: str, do_build: bool,
                    layout: Optional[CampaignLayout] = None, log=print,
                    cache_root: str = "",
                    build_context: Optional[BuildRunContext] = None) -> Dict:
    """段 4b の 1 iteration をメインセッション駆動で回す (checkpoint 経由の cross-process 継続)。

    手順: checkpoint 復元 (無ければ start_wall 付き初期化) → 前 critic feedback 畳込み →
    **入口 check_stop** (逆方向枯渇/予算/収束を iteration 消費前に判定 = 無駄打ちしない。停止なら
    run_one_iteration を呼ばない = build/verify/bench に進めない) → iteration++ →
    run_one_iteration → checkpoint 保存 → digest 書き出し → 末尾 check_stop (新 whiteboard を
    反映した収束判定) を返す。checkpoint は各 iteration で atomic 更新 (落ちても次 iteration が拾える)。

    Returns: run_one_iteration の dict + {"stop_reason", "iteration", "ran"}。ran=False は
    入口停止 (iteration 未消費) を表す。"""
    if build_context is None and not do_build:
        build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    if layout is None:
        layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    layout.ensure()
    state = load_loop_state(layout)
    if state is None:
        state = LoopState(start_wall=time.time())
    _fold_critic_reverse(state, prior_critic_reverse)

    pre = check_stop(state)
    if pre.stop:
        save_loop_state(layout, state)
        log(f"  入口停止 (iteration 消費せず): {pre.reason}")
        return {"outcome": "stopped-before", "variant": None,
                "stop_reason": pre.reason, "iteration": state.iteration, "ran": False}

    state.iteration += 1
    # 同一 layout を run_one_iteration に渡す — reject WAL/records と checkpoint/digest を
    # co-locate させ layout 分裂 (digest 空) を防ぐ (監査 2026-07-08)。
    out = run_one_iteration(cfg, perf, planner, coder, state, sub,
                            do_build=do_build, layout=layout, log=log,
                            cache_root=cache_root, build_context=build_context)
    save_loop_state(layout, state)

    digest_txt = make_critic_digest(
        layout, reflux=(cfg.search_config.get("reflux") == "on"))
    with open(os.path.join(layout.root, "s4_loop_digest.txt"), "w", encoding="utf-8") as f:
        f.write(digest_txt)

    post = check_stop(state)
    out.update({"stop_reason": post.reason, "iteration": state.iteration, "ran": True})
    return out


def main(argv: Optional[List[str]] = None) -> int:
    """fixture proposal で 1 iteration の機械 E2E を実走する (配線実証)。

    実 LLM (planner/coder/critic) はメインセッションが spawn する — 本 main は harness
    の機械経路 (挿入→検疫→評価→WAL→digest→whiteboard→停止判定) が通ることを、人間が
    与えた fixture backoff 値で確認する口。--no-build で build/verify/bench を省く。"""
    ap = argparse.ArgumentParser(description="P3 後続段 4 coder 自律ループ (機械 E2E)")
    ap.add_argument("--no-build", action="store_true",
                    help="build/verify/bench を省き挿入→検疫の配線のみ確認")
    add_coder_build_authority_argument(ap)
    ap.add_argument("--value", type=float, default=20.0,
                    help="fixture の backoff 値 (coder proposal の代わり)")
    ap.add_argument("--reflux", choices=["on", "off"], default="on",
                    help="critic 還流 on/off (LLM ablation の対照アーム)")
    ap.add_argument("--run-iteration", metavar="PROPOSAL.json",
                    help="段 4b 駆動: 実 planner/coder proposal (JSON) を受けて checkpoint 継続で "
                         "1 iteration を回す (メインセッションが毎 iteration これを呼ぶ)")
    ap.add_argument("--isolate-worktree", action="store_true",
                    help="段5 git worktree 隔離: 共有 external/ccbench でなく使い捨て "
                         "worktree で apply/build/verify する (既定 OFF = 既存動作と完全互換)")
    a = ap.parse_args(argv if argv is not None else sys.argv[1:])
    if not a.no_build and a.coder_build_authority is None:
        raise BuildAdmissionError("--allow-coder-derived-build の明示 opt-in が必要")
    build_context = build_run_context(
        generator_id=GeneratorId.BACKOFF_SWEEP,
        coder_authority=None if a.no_build else a.coder_build_authority,
    )

    root = _repo_root()
    fixed_sub = os.path.join(root, "external", "ccbench")
    from campaign import patchharness
    from campaign.p2_2 import _assert_single_tenant
    if not a.no_build:
        _assert_single_tenant()
    patchharness.assert_pinned_clean(fixed_sub, PIN)

    cfg = default_cfg(reflux=(a.reflux == "on"))
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    perf = default_perf()

    # 段5 git worktree 隔離 (opt-in): 有効時は 1 回だけ使い捨て worktree を作り、build
    # キャッシュだけ固定共有パス配下に据え置く (cache_key は内容キーなので worktree 間で
    # 共有して問題ない)。無効時は contextlib.nullcontext で固定共有パスをそのまま使う
    # (既存動作と完全互換、進行中 campaign の campaign-id/WAL に触れない)。
    if a.isolate_worktree:
        wt_cm = patchharness.checkout(PIN, base_dir=fixed_sub)
        cache_root = os.path.join(fixed_sub, "build-variants")
    else:
        wt_cm = contextlib.nullcontext(fixed_sub)
        cache_root = ""

    # === 段 4b 駆動口: 実 proposal を受けて checkpoint 継続で 1 iteration ===
    if a.run_iteration:
        planner, coder, prior_rev = load_proposal_file(a.run_iteration)
        print(f"=== 段 4b iteration (proposal={a.run_iteration}, "
              f"reflux={a.reflux}, build={not a.no_build}, prior_critic_reverse={prior_rev}, "
              f"isolate_worktree={a.isolate_worktree}) ===")
        with wt_cm as sub:
            out = drive_iteration(cfg, perf, planner, coder, prior_rev, sub,
                                  do_build=not a.no_build, cache_root=cache_root,
                                  build_context=build_context)
        layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
        print(f"  ran={out['ran']} outcome={out['outcome']} "
              f"variant={out.get('variant')} iteration={out['iteration']}")
        print(f"  停止判定: {out['stop_reason']}")
        print(f"  checkpoint: {loop_state_path(layout)}")
        print(f"  digest: {os.path.join(layout.root, 's4_loop_digest.txt')}")
        # 停止判定が機械的に返り、checkpoint が焼かれていれば駆動口として健全。
        ok = (out["stop_reason"] in ("continue", "converged", "reverse-exhausted",
                                     "budget-iterations", "budget-walltime")
              and os.path.exists(loop_state_path(layout)))
        return 0 if ok else 1
    state = LoopState(start_ts=time.monotonic())
    state.iteration = 1

    # fixture proposal (人間が与える = kickoff と同じリーク制御。coder の自律発案の代役)。
    planner = PlannerProposal(axis=MARKER_ID, direction="explore_both", magnitude="small",
                              justification="fixture (機械 E2E 用)")
    coder = CoderProposal(axis=MARKER_ID, value=a.value,
                          implementation=f"double now_backoff = {a.value};",
                          justification="fixture", confidence="low")

    print(f"=== 段 4 loop 1 iteration (機械 E2E, value={a.value}, "
          f"reflux={a.reflux}, build={not a.no_build}, "
          f"isolate_worktree={a.isolate_worktree}) ===")
    with wt_cm as sub:
        out = run_one_iteration(cfg, perf, planner, coder, state, sub,
                                do_build=not a.no_build, cache_root=cache_root,
                                build_context=build_context)
    print(f"  outcome={out['outcome']} variant={out.get('variant')}")

    layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    digest_txt = make_critic_digest(layout, reflux=(a.reflux == "on"))
    out_path = os.path.join(layout.root, "s4_loop_digest.txt")
    layout.ensure()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(digest_txt)

    stop = check_stop(state)

    # WAL 機械判定 (宣言でなくレコードを gate に — kickoff/D30 様式)。
    dqs = load_diff_rejections(layout)
    # iteration の WAL 非依存を **差分**で実証する (1==1 の恒真 assert にしない): loop の
    # iteration は WAL レコード数と一致しない = WAL から導出していないことの witness (D39 決定2)。
    n_wal = len(list(wal.read_records(layout)))
    checks = {
        f"iteration(={state.iteration}) が WAL レコード数(={n_wal})と独立 (WAL 由来でない)":
            state.iteration == 1 and n_wal != state.iteration,
        "critic digest 書き出し": os.path.exists(out_path),
        "停止判定が機械的に返る": stop.reason in (
            "continue", "converged", "reverse-exhausted",
            "budget-iterations", "budget-walltime"),
    }
    if out["outcome"] != "dry-pass":
        checks["whiteboard に 1 行射影 (機序なし)"] = len(state.whiteboard) == 1
        checks["whiteboard entry が方向/結果のみ (機序フィールド無し)"] = (
            len(state.whiteboard) == 1
            and set(vars(state.whiteboard[0])) == {
                "iteration", "direction", "magnitude", "result", "delta_pct"})
    if out["outcome"] == "rejected":
        checks["diff-quarantine reject が WAL に焼かれ load_diff_rejections が復元"] = (
            any(d.variant == out["variant"] and d.subtype for d in dqs))
        checks["reject が whiteboard で result=rejected"] = (
            state.whiteboard[0].result == "rejected")
    elif out["outcome"] == "certified":
        checks["certified で fitness_tps あり"] = out.get("fitness_tps") is not None
        checks["certified で whiteboard result=success"] = (
            state.whiteboard[0].result == "success")

    print("\n=== 判定 (WAL/状態 機械確認) ===")
    ok = all(checks.values())
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    print(f"\ncampaign dir: {layout.root}")
    print(f"停止判定: stop={stop.stop} reason={stop.reason}")
    print(f"\n段 4 loop 1 iteration 判定: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
