# -*- coding: utf-8 -*-
"""tools/check_docs.py の恒真ゲート回帰 (F9) + positive control (machine 非依存)。

pytest では保留対象を可視に skip する。D335 の恒久保留により、素の
`python3 orchestrator/tests/test_check_docs.py` 実行には
`IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command` が要る。

背景 (F9): LIVING_DOCS の手書き列挙対象が改名/削除で不在になると、旧実装は
`if not doc.exists(): continue` で黙って skip し、その doc への lint が発火せず
「恒真な保証」に化けていた。本テストは positive control =「列挙対象を 1 個わざと
消すと違反が出る」を、合成した最小 repo に対して固定する (規律3 の positive control)。

戦略: 実 check_docs.py を tmp/tools/ へ複製し REPO を tmp に付け替える。check_docs が
読むファイル群を trivial 内容で合成し、baseline が「違反なし」であることを確認した上で、
列挙対象を 1 個消して「不在 = 違反」に変わることを検査する。列挙名は check_docs 本体の
_ENUMERATED_DOCS から導出するので docs の増減で腐らない。
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import time

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_ORCH)
sys.path.insert(0, os.path.join(_REPO, "tools"))

import check_docs  # noqa: E402


_S09_ACCEPTANCE_ORDER_LITERAL = (
    "全 commit・受入結果を固定し、tested main/tip と監査 commit 列を実測して "
    "`DW-O23` を行う。"
)
_SYNTHETIC_STAGE6_WAITER_ITEM = (
    "6. **レビュー・fix (codex 並列):** 敵対レビュー 2 本、fix、変異 matrix、受入再走を行う。\n"
    "   受入投入は `tools/dev_wave_wait.py acceptance --lease-optional` を使う。\n"
)
_SYNTHETIC_STAGE9_WAITER_ITEM = (
    "9. **終端・local main (親):** 共通 land operation で監査済み成果だけを取り込み、結果を確定して終了する。\n"
    "   受入・land の終端で必ず `tools/dev_wave_wait.py acceptance` で `release` し、\n"
    "   land 成功時と巻戻し時に `message` を照合済み peer へ 1 度送る。\n"
)
_SYNTHETIC_DEV_WAVE_STATE_MACHINE = (
    "## 9 段状態機械\n\n"
    "5. **実装 (codex 並列):** 所有を分離して実装する。\n"
    + _SYNTHETIC_STAGE6_WAITER_ITEM
    + "7. **記録 (親):** 記録する。\n"
    + _SYNTHETIC_STAGE9_WAITER_ITEM
    + "\n"
)
_SYNTHETIC_DW_C00_WAITER_LINE = (
    "待ち手は 1 条件 1 本とし、通知ごとに作り直さず `tools/dev_wave_wait.py` を使う。"
    "生産者を止める\n"
)
_SYNTHETIC_DW_O01_WAITER_LINE = (
    "待機は `tools/dev_wave_wait.py producer` を使い、`--pid-file` は producer script 自身が "
    "`echo $$` で書く。\n"
)

_SYNTHETIC_DEV_WAVE_COMMAND_START_SECTION = """## 入力と開始

- 第一声から進捗、裁定、最終報告、`result:` まで、ユーザー向け出力はすべて日本語にする。
- `CLAUDE.md` のクラス 3 起動手順を実行し、引数があれば対象にする: $ARGUMENTS
- wave 開始時に `docs/skill-self-improvement.md` の発火 gate・routing・dev-wave を読み、
  専用 handoff に「dev-wave 改善候補」節を作る。
- 無人継続の外部 supervisor は、最初の `claude -p` spawn 前に
  `docs/dev-wave/core.md` の `DW-CTX` を読む。

"""
_PRE_WAVE_DEV_WAVE_COMMAND_START_SECTION = """## 入力と開始

- 第一声から進捗、裁定、最終報告、`result:` まで、ユーザー向け出力はすべて日本語にする。
- `CLAUDE.md` のクラス 3 起動手順を実行し、引数があれば対象にする: $ARGUMENTS
- wave 開始時に `docs/skill-self-improvement.md` の「発火 gate」と「dev-wave」を読み、
  専用 handoff に「dev-wave 改善候補」節を作る。
- 無人継続の外部 supervisor は、最初の `claude -p` spawn 前に
  `docs/dev-wave/core.md` の `DW-CTX` を読む。

"""
_SYNTHETIC_CODEX_DEV_WAVE_START_SECTION = """## 開始する

0. prompt 本文の最初の非空行が `AGENTS.md`「単独段 dispatch の例外」節と同一形式の宣言・射影を
   満たす場合は、以下 1〜5 を適用せず、宣言と射影が指示する資料だけを読む。宣言が欠落・形式不正・
   重複、または射影対象を読めない場合はこの例外を使わず、以下の手順に従う。
1. リポジトリ直下の `AGENTS.md` と `CLAUDE.md` を全文読み、依頼をクラス 3 として起動する。
2. ユーザーが指定した対象を優先する。対象がなければ worklog 末尾の「次の一手」から 1 件選ぶ。
3. `.claude/commands/dev-wave.md` を全文読む。同ファイルを 9 段状態機械、段 dispatch、条件 dispatch、
   巻き戻し、停止条件の共通 dispatcher として扱う。
4. `docs/skill-self-improvement.md` の発火 gate・routing・dev-wave 終端を読み、専用 handoff に
   `dev-wave 改善候補` 節を作る。
5. main では編集しない。既存の専用 Codex worktree があれば状態と対象を照合して再利用し、
   なければ local main の HEAD から `.codex/worktrees/` 配下に専用 branch/worktree を作る。

参照先の節は、dispatcher が指定する段または条件の直前に読み直す。記憶や本 Skill の要約で代用しない。
参照先が不在、読取不能、非一意、または期限後に条件成立が判明した場合は dispatcher どおり
fail-closed に停止または巻き戻す。

"""
_PRE_WAVE_CODEX_DEV_WAVE_START_SECTION = """## 開始する

1. リポジトリ直下の `AGENTS.md` と `CLAUDE.md` を全文読み、依頼をクラス 3 として起動する。
2. ユーザーが指定した対象を優先する。対象がなければ worklog 末尾の「次の一手」から 1 件選ぶ。
3. `.claude/commands/dev-wave.md` を全文読む。同ファイルを 9 段状態機械、段 dispatch、条件 dispatch、
   巻き戻し、停止条件の共通 dispatcher として扱う。
4. `docs/skill-self-improvement.md` の発火 gate と dev-wave 終端を読み、専用 handoff に
   `dev-wave 改善候補` 節を作る。
5. main では編集しない。既存の専用 Codex worktree があれば状態と対象を照合して再利用し、
   なければ local main の HEAD から `.codex/worktrees/` 配下に専用 branch/worktree を作る。

参照先の節は、dispatcher が指定する段または条件の直前に読み直す。記憶や本 Skill の要約で代用しない。
参照先が不在、読取不能、非一意、または期限後に条件成立が判明した場合は dispatcher どおり
fail-closed に停止または巻き戻す。

"""
_SYNTHETIC_SELF_ROUTING_SECTION = """## routing

1. 新しい失敗型・near miss・既存防壁の破れは `docs/failures.md` へ送る。
   同型再発なら新しい F を作らず、既存 F に「再発: 日付」を追記する。
2. 長期の設計、権限、正本、interface を変える採用済み判断は `docs/decisions.md` へ送る。
   未裁定または大きい変更を既成事実にせず、裁定パッケージとしてユーザーへ返す。
3. dev-wave 固有の手順は発火段に対応する `docs/dev-wave/` の既存 leaf 節へ統合し、意味を保って
   統合できない場合だけ新しい節・ファイルを候補にする。新規 L2 節の登録は鏡像の
   「発火実績あり × 義務が現に機械代替されていない × 同じ意味検索で反証も同一発火点の
   既存正本もなし」を満たす場合だけとする (D271)。L2 (条件成立時だけ読む節) の削除を裁定
   パッケージへ送れるのは「発火実績なし × テスト/機械検査で義務代替済み」の両条件を満たす
   節だけで、実施はユーザー裁定に限る。「発火実績なし」は ID 件数でなく repo 全体
   (insights・memo 含む) の意味検索で反証されないことを確認する。
4. cleanup-branches / rulings の短い手順は各 command の既存節を是正する。
   長い事故説明は F ポインタにし、裁定待ち・branch 状態・可変データを command へ書かない。
5. 同じ内容を複数の行き先へ全文複製しない。入口は命令と dispatch、reference は実行手順、
   failures は事象・原因・恒久対応、decisions は採用理由を担う。

"""
_PRE_WAVE_SELF_ROUTING_SECTION = """## routing

1. 新しい失敗型・near miss・既存防壁の破れは `docs/failures.md` へ送る。
   同型再発なら新しい F を作らず、既存 F に「再発: 日付」を追記する。
2. 長期の設計、権限、正本、interface を変える採用済み判断は `docs/decisions.md` へ送る。
   未裁定または大きい変更を既成事実にせず、裁定パッケージとしてユーザーへ返す。
3. dev-wave 固有の手順は発火段に対応する `docs/dev-wave/` の既存 leaf 節へ統合する。
   新しい節・ファイルは、既存節へ意味を保って統合できない場合だけ候補にする。
   節の削除を裁定パッケージへ送れるのは、L2 (条件成立時だけ読む節) のうち「発火実績なし ×
   テスト/機械検査で義務代替済み」の両条件を満たすものだけとする。「発火実績なし」は
   ID 件数でなく repo 全体 (insights・memo 含む) の意味検索で反証されないことを確認する。
   削除の実施はユーザー裁定に限る。
4. cleanup-branches / rulings の短い手順は各 command の既存節を是正する。
   長い事故説明は F ポインタにし、裁定待ち・branch 状態・可変データを command へ書かない。
5. 同じ内容を複数の行き先へ全文複製しない。入口は命令と dispatch、reference は実行手順、
   failures は事象・原因・恒久対応、decisions は採用理由を担う。

"""
_SYNTHETIC_DW_O18_SECTION = """## DW-O18 — テスト cwd と非帰属赤の着地

cwd=repo root。nested subprocess import path偽赤は回帰外。file選択走は`from tests import`確立後に限り未確立赤も偽赤。

受入赤返却時が判定主体の境界。待ち手は赤返却だけ。人・AIが判定し根拠をworklogへ残す。assertion本文・差分実体で判定、署名一致禁止。非帰属赤の着地5分超禁止、悩まない(D690)。自分起因は直す。N走完全一致はflakeでも非帰属の証拠でもない。差分到達不能は単独再走、非再現なら受入再走。同一tipで各1回だけ。再赤/決定的赤でもhold登録簿へ登録しない(契約testが1件に固定、F1000)。真に決定的な不安定testはその1件のpin更新を個別に諮り、判定不能・原因未理解は除外せず共に停止。停止条件外は治すか上記の制限内で投げ直しwaveを止めない。受理は`child-green`だけ、赤の受領証禁止。

"""
_SYNTHETIC_DW_O25_SECTION = """## DW-O25 — ff-only land の全史 provenance 関門

D254 に従い、land は `locked_main != 着地tip` のときだけ lock を解放して全史 provenance 監査を自ら走らせ、480 秒以内の rc=0 を必須とする。赤は `RC_PROVENANCE = 29` で main を 1 bit も変えず拒否し、CLI flag・環境変数・警告化の逃がし道を作らない。
lock 再取得後に全検査をやり直し、`tip_sha` / `checker_blob_sha` / `executed_bytes_sha` / `returncode` を束縛した receipt を lock 内で再照合する。`already-landed` の no-op と active fold transaction の recovery では監査を起動しない。
"""
_SYNTHETIC_DW_O26_SECTION = """## DW-O26 — 焦点走の consumer test 拡張

`DW-O18` の焦点走 file 集合は、変更 test file と、変更 production file を参照関係で引いた consumer
test。private symbol は consumer 表に出ないので symbol 名で production を grep する。
欠くと静的レビューが見落とした破れを取り逃す（F242）。production file を変えた wave は repo 全体の
inventory test 4 群（`test_campaign.py` の certified-writer caller inventory、
`test_official_perf_closure.py` の perf file inventory、`test_p3_exploration_namespace.py`、
`test_p3_b4_wiring_probe.py`）を参照関係に依らず焦点走に含める。同一 worktree の dispatch は全種直列。
変更 test file は受入前に単独走で確認する。新規 test file を足す走は file 集合列挙のメタテストも含める。
並行 wave が自分の編集 file を所有するなら main 取込み済みの木の既存走行に相乗りし受入後に足さない。
"""
_SYNTHETIC_DW_O28_SECTION = """## DW-O28 — land 後の自己撤去

land成功・job終端後main worktreeから`python3 tools/dev_wave_cleanup.py`で撤去(絶対path、`--main-worktree <MAIN>`は両方に)。
撤去はrepo全体で1本ずつ(Lustre過負荷)、rc=75は数分後再試行。
先にmanifest(`DW-S05-A`)の子木を`remove-child --manifest <M> --child-worktree <P> --evidence-dir <D>`で(回収waveは旧分も)、次にwaveを`--wave-worktree <WAVE> --wave-branch <BRANCH> --tested-wave-tip-sha <TIP>`で撤去、他へ引き渡さない。
toolは非占有・main祖先性(子木は所有path一致か、wave land済なら履歴bundle+dirty退避)・manifest束縛を検査。不成立・不明は拒否し木とbranchを残す(以後rc=30)。manifest現行branchは`<D>`へbundle後(HEADがmain祖先なら省く)に`-D`。`<D>`はjob後も残る所。
F26:`git worktree remove`/`git submodule deinit`不可。wave branchは`-d`のみ、手打ち`-D`禁止。残る子木はunlockし理由をworklogへ。
"""
_SYNTHETIC_DW_C01_SECTION = """## DW-C01 — 実測で是正した作法

`DW-O01/O08/O17/O20`より優先。
- `--lane`はconsult、`--reasoning`はplan/consultで必須。他段指定/必須段無指定はrc=2。
- 待ち手はpid file実在後に張る。先行は子の生存中も即戻る。
- 隔離worktreeのdetachは`.sh`2枚(launcher/detach)へ。直に叩くとguard拒否。
- 複数起点は全隣接区間の異なる正値で判別。
- 変異harnessはbaseline緑必須。既存赤は根拠を台帳へ書き`--deselect`。
- 全新規worktreeを`python3 tools/dev_wave_submodule_init.py --worktree <ABSOLUTE>`で再帰初期化する。
- 呼出し規約変更取込は、両親の変更行が非競合でも全呼出しを数える。
- 段6fixも受理・拒否の含意を2文に分け、通る正例を添える。
- merge/`add`/commitは親、子は競合解決だけ。
- 子の成果物はrepo内に書かせ、親が実行後repo外へ退避。
- Web検索は必要な段だけ明示して使う。
"""

_SYNTHETIC_OPERATION_SECTION_IDS = (
    "DW-O01", "DW-O02", "DW-O03", "DW-O04", "DW-O05", "DW-O06",
    "DW-O08", "DW-O09", "DW-O10", "DW-O11", "DW-O12", "DW-O13",
    "DW-O14", "DW-O16", "DW-O17", "DW-O18", "DW-O19", "DW-O20",
    "DW-O23", "DW-O25",
)
_SYNTHETIC_REGISTERED_OPERATION_SECTION_IDS = (
    *_SYNTHETIC_OPERATION_SECTION_IDS, "DW-O26", "DW-O27", "DW-O28",
)
_SYNTHETIC_ALL_OPERATIONS_REF = (
    "`docs/dev-wave/operations.md`: `DW-O01`〜`DW-O06`, `DW-O08`〜`DW-O14`, "
    "`DW-O16`〜`DW-O20`, `DW-O23`, `DW-O25`"
)
_SYNTHETIC_STAGE_5_6_CONDITIONAL_ROWS = (
    "| 段 5 |C| `docs/dev-wave/operations.md`: `DW-O01`〜`DW-O06`, "
    "`DW-O08`〜`DW-O14`, `DW-O16`〜`DW-O20`, `DW-O23`, `DW-O25` |",
    "| 段 6 |C| `docs/dev-wave/operations.md`: `DW-O01`〜`DW-O06`, "
    "`DW-O08`〜`DW-O14`, `DW-O16`〜`DW-O20`, `DW-O23`, `DW-O25` |",
)
_SYNTHETIC_CONDITION_18_ROW = (
    "| 18 | 親のテスト・受入前と赤処理前 | "
    "`docs/dev-wave/operations.md`: `DW-O18`, `DW-O26`, `DW-O27` |"
)
_SYNTHETIC_CONDITION_25_ROW = (
    "| 25 | main を進める land を起動する直前 | "
    "`docs/dev-wave/operations.md`: `DW-O25` |"
)
_SYNTHETIC_CONDITION_26_ROW = (
    "| 26 | 起動/待機/検査/submodule/取込/fix前 | "
    "`docs/dev-wave/core.md`: `DW-C01` |"
)
_SYNTHETIC_CONDITION_27_ROW = (
    "| 27 | land 成功後の自己撤去直前 | "
    "`docs/dev-wave/operations.md`: `DW-O28` |"
)
_SYNTHETIC_SINGLE_DISPATCH_DECLARATION = (
    "単独段 dispatch: stage=<plan|consult|author|review|fix|focus>; "
    "sandbox=<read-only|workspace-write>; parent=<絶対パス>"
)
_SYNTHETIC_SINGLE_DISPATCH_OPERATIONS_REFERENCE = (
    "prompt 先頭は AGENTS.md の単独段例外と同形式。"
)
_SYNTHETIC_SINGLE_DISPATCH_PROJECTION_HEADING = "必読事項の射影:"
_SYNTHETIC_SINGLE_DISPATCH_PROJECTION_ITEM = (
    "- `/tmp/synthetic-required.md` — 読めなければ即停止"
)
_SYNTHETIC_SINGLE_DISPATCH_LAUNCHER_STAGES = (
    'STAGES = ("plan", "consult", "author", "review", "fix", "focus")\n'
)
_SYNTHETIC_AGENTS_SINGLE_DISPATCH_SECTION = (
    "# synthetic agents\n\n"
    "## 単独段 dispatch の例外\n\n"
    "prompt 本文の最初の非空行だけを対象にする。\n"
    f"`{_SYNTHETIC_SINGLE_DISPATCH_DECLARATION}`\n"
    f"{_SYNTHETIC_SINGLE_DISPATCH_PROJECTION_HEADING}\n"
    f"{_SYNTHETIC_SINGLE_DISPATCH_PROJECTION_ITEM}\n"
    "\n## 作業開始\n\n通常の起動手順。\n"
)

_SYNTHETIC_ADMISSION_ENTRIES = {
    "tools/pegasus/collect_receipt.py": {
        "class": "unknown",
        "reason": "synthetic unknown",
        "primary_gate": "synthetic deny",
        "evidence": "unmeasured synthetic input",
    },
    "tools/pegasus/fetch_third_party.py": {
        "class": "local-ok",
        "reason": "synthetic measured local path",
        "primary_gate": "synthetic cli",
        "evidence": "runbook §7.0 実測",
    },
    "tools/pegasus/smoke_probe.sh": {
        "class": "dispatch-required",
        "reason": "synthetic job body",
        "primary_gate": "synthetic PBS allocation",
        "evidence": "static job-body classification",
    },
    "tools/pegasus/submit_certify.sh": {
        "class": "local-ok",
        "reason": "synthetic submitter",
        "primary_gate": "synthetic qsub",
        "evidence": "legacy-admitted (未実測)",
    },
    "tools/pegasus/submit_silo_ladder_rung1.sh": {
        "class": "local-ok",
        "reason": "synthetic grandfather warning",
        "primary_gate": "synthetic qsub",
        "evidence": "legacy-admitted (未実測)",
    },
}

_SYNTHETIC_PROJECTION_TABLE = """| path | class | evidence |
|---|---|---|
| `tools/pegasus/collect_receipt.py` | `unknown` | `unmeasured synthetic input` |
| `tools/pegasus/fetch_third_party.py` | `local-ok` | `runbook §7.0 実測` |
| `tools/pegasus/smoke_probe.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/submit_certify.sh` | `local-ok` | `legacy-admitted (未実測)` |
| `tools/pegasus/submit_silo_ladder_rung1.sh` | `local-ok` | `legacy-admitted (未実測)` |"""

_SYNTHETIC_UNKNOWN_TABLE = """| 経路 | なぜ `unknown` か |
|---|---|
| `tools/pegasus/collect_receipt.py` | 入力が未計測 |
| `tools/pegasus/submit_certify.sh` | registry 上は `local-ok` / `legacy-admitted (未実測)` として grandfather 済み |
| `tools/pegasus/submit_silo_ladder_rung1.sh` | registry 上は `local-ok` / `legacy-admitted (未実測)` として grandfather 済み |"""

_SYNTHETIC_MEASURED_TABLE = """| 経路 | 観測ピーク | certified peak | 分類 |
|---|---|---|---|
| `tools/pegasus/fetch_third_party.py fetch` | 10 MiB | 138 MiB | local-ok |
| 同 `fetch` | 9 MiB | 137 MiB | local-ok |"""

_SYNTHETIC_DISPATCH_RUNBOOK = f"""# synthetic Pegasus runbook

## 7. synthetic execution policy

### 7.0 判定基準はディレクトリではなくメモリ量

{_SYNTHETIC_PROJECTION_TABLE}

| task | 子 script |
|---|---|
| `tests` | `tools/run_tests.py` |
| `provenance` | `tools/check_ai_provenance.py` |

{_SYNTHETIC_UNKNOWN_TABLE}

{_SYNTHETIC_MEASURED_TABLE}

### 7.1 synthetic next section

body
"""

_SYNTHETIC_ADMISSION_README = """# synthetic Pegasus tools

## 0. 実行体と admission

| path | 手順上の実行 site | registry class |
|---|---|---|
| `tools/pegasus/collect_receipt.py` | `compute-only` | `unknown` |
| `tools/pegasus/fetch_third_party.py` | `login-direct` | `local-ok` |
| `tools/pegasus/smoke_probe.sh` | `qsub-job-body` | `dispatch-required` |
| `tools/pegasus/submit_certify.sh` | `login-direct` | `local-ok` |

```bash
# admission-site: qsub-job-body
qsub tools/pegasus/smoke_probe.sh
```

```bash
# admission-site: login-direct
python3 tools/pegasus/fetch_third_party.py fetch
tools/pegasus/submit_certify.sh
```

`tools/pegasus/collect_receipt.py` は login では拒否される。
"""

_SYNTHETIC_DISPATCH_SOURCE = """from dataclasses import dataclass

@dataclass(frozen=True)
class _TaskSpec:
    child_script: tuple[str, ...]

TASKS = {
    "tests": _TaskSpec(child_script=("tools", "run_tests.py")),
    "provenance": _TaskSpec(
        child_script=("tools", "check_ai_provenance.py"),
    ),
}
"""


# operations 由来の条件 dispatch key (O07/O15/O21/O22/O24 を除く 20 件)。
# 合成 fixture を production contract と独立させるため、ここでは手書きする。
_OPERATION_CONDITION_KEYS = [
    "01", "02", "03", "04", "05", "06", "08", "09", "10", "11",
    "12", "13", "14", "16", "17", "18", "19", "20", "23", "25",
]


_PLACEHOLDER_DEBT_WORKLOG = (
    "  repo scan invariant (F34) は本 docs commit 後に再走 <反映>。"
)
_PLACEHOLDER_DEBT_ARCHIVE_ACCEPTANCE = (
    "- **受入**: <受入全走結果を反映> / check_docs / check_ai_provenance (324) / "
    "repo scan invariant (F34) 緑 <反映>。"
)
_PLACEHOLDER_MENTION_WORKLOG_F36 = (
    "- **F36 新設**: 受入・検査の結果欄の `<反映>` プレースホルダが独立 3 wave + insight 1 本で残存し、"
)
_PLACEHOLDER_MENTION_WORKLOG_T094_A = (
    "- **[T-094]**: 機械検出を**採用**し設計も確定 — 検出は `<反映>` / `<受入結果を反映>` /"
)
_PLACEHOLDER_MENTION_WORKLOG_T094_B = (
    "  `<受入全走結果を反映>` の exact 3 文字列、対象は `docs/worklog.md` と verbatim でない"
)
_PLACEHOLDER_DEBT_INSIGHT = (
    "- 受入全走: <受入結果を反映>。check_docs / check_ai_provenance (324) / "
    "repo scan invariant (F34): <反映>。"
)
_PLACEHOLDER_MENTION_INSIGHT_A = (
    "   4件の `<反映>` は F34 恒久対応の実行証拠にならない。`check_docs` も意味的な反映漏れを検出しないと明記する "
    "(`tools/check_docs.py:7-10`)。独立3 wave は族一般化条件を満たす (`docs/dev-wave/core.md:45-48`) ため、"
    "P8 の「新 gate なので見送る」は根拠不足。  "
)
_PLACEHOLDER_MENTION_INSIGHT_B = (
    "  裁定パッケージでは、候補検出対象を少なくとも `<反映>`、`<受入結果を反映>`、"
    "`<受入全走結果を反映>` の exact literal、対象を `docs/worklog.md`、"
    "`docs/archive/worklog-*.md`、非-verbatim の `output/insights/*.md` とし、既存四件は path だけでなく"
    "「含有行 digest + token count」で固定する案を比較すべきである。単なる `<[^>]*反映[^>]*>` は"
    "日本語メタ変数や欠陥説明の引用を誤検出する。"
)
_PLACEHOLDER_ARCHIVE_NAME = "worklog-phase3-0722-0724.md"
_KNOWN_CARRY_ID_MISMATCH_ARCHIVE_NAME = "worklog-phase3-0726-73-78.md"
_KNOWN_CARRY_SOURCE_H2 = (
    "## 2026-07-31 (77) — [T-205] provenance 履歴監査を計算ノードへ移して高速化し、"
    "Codex author 契約に正規の waiver を開く (コード + docs、branch "
    "worktree-dev-wave-t205-provenance-compute、受入 = Pegasus gen_S 計算ノード request "
    "`874788` / 監査 `874793`)"
)
_KNOWN_CARRY_ID_MISMATCH_ARCHIVE = f"""# synthetic known carry mismatches

## 2026-07-26 (73) — synthetic carry target

### 次の一手
- [T-899] deferred bridge

## 2026-07-26 (74) — synthetic bridge 74

- [T-899] consumed

### 次の一手

## 2026-07-26 (75) — synthetic bridge 75

### 次の一手

## 2026-07-26 (76) — synthetic bridge 76

### 次の一手

{_KNOWN_CARRY_SOURCE_H2}

### 次の一手
- [T-208] 変わらず ((73) 参照)
- [T-209] 変わらず ((73) 参照)
- [T-210] 変わらず ((73) 参照)
- [T-211] 変わらず ((73) 参照)

## 2026-07-26 (78) — synthetic known-carry sink

- [T-208] consumed
- [T-209] consumed
- [T-210] consumed
- [T-211] consumed

### 次の一手
"""

_PLACEHOLDER_WORKLOG_ENTRIES = f"""## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 (test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)

{_PLACEHOLDER_DEBT_WORKLOG}

### 次の一手

## 2026-07-25 (3) — [T-068][T-077][T-078] を R 発効により確定的に closure (docs-only・コード 0 byte、branch worktree-dev-wave-e2e-real-seal、計測なし)

{_PLACEHOLDER_MENTION_WORKLOG_F36}

### 次の一手

## 2026-07-25 (4) — /rulings: 裁定待ち 5 件をユーザーが推奨どおり一括裁定 — official 解禁を承認 (D86 起票、計測なし)

{_PLACEHOLDER_MENTION_WORKLOG_T094_A}
{_PLACEHOLDER_MENTION_WORKLOG_T094_B}

### 次の一手
"""

_CLEAN_WORKLOG = f"""# synthetic worklog

## ローテーション

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — second

- [T-001] consumed

### 次の一手
1. [T-002] continue
"""

_CLEAN_PHASE3 = """# synthetic phase

## 見送り台帳 (synthetic)

- [T-900] deferred item

### 裁定・完了記録

- completed item

## 残存リスク

- risk
"""

_SYNTHETIC_R33_DECISION_SECTION = """## D570. dev-wave n-pilot R33 admission authority

**機械 pin:**

- authority slug: `t1142-n-pilot-r33-admission-authority`
- R33 admission contract: role=`n_pilot_r33`; generation=`n-pilot-r33`; pilot_rounds=33; allocation_count=3; cell_count=12; schedule_row_count=396.
"""

_SYNTHETIC_R33_PENDING_FRAGMENT = """---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1142-n-pilot-admission-redesign
seq: 1
---

## {{D:t1142-n-pilot-r33-admission-authority}}. n-pilot R33 admission authority

**機械 pin:**

- authority slug: `t1142-n-pilot-r33-admission-authority`
- R33 admission contract: role=`n_pilot_r33`; generation=`n-pilot-r33`; pilot_rounds=33; allocation_count=3; cell_count=12; schedule_row_count=396.
"""

_SYNTHETIC_DEV_WAVE_DESCRIPTION = (
    "Run one Izanagi development wave through its brief, Codex planning and "
    "adversarial review, implementation, mutation and acceptance checks, "
    "recording, and bounded termination workflow. Use only for an explicit "
    "$dev-wave invocation; implicit invocation is disabled. Do not use it for "
    "a CC synthesis campaign."
)
_PRE_WAVE_CODEX_DEV_WAVE_DESCRIPTION = (
    "Run one Izanagi development wave through its brief, Codex planning and "
    "adversarial review, implementation, mutation and acceptance checks, "
    "recording, and bounded termination workflow. Use when the user asks to "
    "run, continue, or perform a dev-wave, or requests the repository's "
    "standard nine-stage development loop; do not use it for a CC synthesis "
    "campaign."
)
_SYNTHETIC_DEV_WAVE_OPENAI_YAML = """interface:
  display_name: "Dev Wave"
  short_description: "Izanagi の開発 wave を共通契約に従って実行"
  default_prompt: "Use $dev-wave to run one Izanagi development wave for the specified task."

policy:
  allow_implicit_invocation: false
"""
_SYNTHETIC_CLEANUP_DESCRIPTION = (
    "Safely back up and clean up merged or stale local Izanagi branches and worktrees through the shared dispatcher. Use for branch or worktree cleanup; deletion needs explicit $cleanup-branches."
)
_EXPECTED_CLEANUP_SKILL_SHA256 = (
    "076089079683c0850354f43281df5ac05cfc3461b6b9f0cab1bdb221e24319a7"
)
_EXPECTED_CLEANUP_COMMAND_SHA256 = (
    "7b5379534f7ed5a061ac276001006f00cd49d3a9ca89cedeea9e4874f88d8d5f"
)
_SYNTHETIC_CLEANUP_SKILL = """---
name: cleanup-branches
description: Safely back up and clean up merged or stale local Izanagi branches and worktrees through the shared dispatcher. Use for branch or worktree cleanup; deletion needs explicit $cleanup-branches.
---

# Cleanup Branches

共通の cleanup dispatcher を読み、その手順を複製せず Codex 固有の安全縮退を重ねて実行する。

## 共通 dispatcher を使う

1. リポジトリ直下の `AGENTS.md` と `CLAUDE.md` を全文読む。`$cleanup-branches` で明示起動された
   掃除だけクラス 2 とし、質問・相談・説明・レビューはクラス 1 の read-only として何も削除しない。
2. `.claude/commands/cleanup-branches.md` を全文読み、冒頭の最優先 mutation boundary から末尾の
   自己改善終端までを全工程へ不可分に適用する。クラス 2 や外側の作業種別は許可集合を拡張しない。
   command が不在または読取不能なら停止する。
3. command の `$ARGUMENTS` は本 Skill に渡された対象限定と読み替える。未指定なら command の全量棚卸し契約に従う。
4. command と本 overlay が衝突する場合は、削除範囲が狭くなる安全側へ縮退して対象と未実行操作を報告する。

## Codex 固有の安全 overlay

- Claude 固有の `ExitWorktree` が使えると仮定しない。cwd を対象外へ固定できなければ F51 とし、
  現在の worktree directory の削除と prune を行わない。
- `/proc/*/cwd` の miss は非使用の証拠に数えず、この Codex session の所有を証明できない
  worktree は command の削除対象でも保持して報告する。
- 各破壊操作の直前に dispatcher の全 eligibility と canonical path、process residency を再評価する。
  unknown、棚卸し後の change、新しい residency があれば停止する。
- `git worktree prune --dry-run --verbose` は報告用 preview としてだけ実行する。Codex は real
  `git worktree prune` と command §3 の mv を実行せず、preview と残作業を人間へ引き渡す。
- 未追跡 `output/` (`exploration/`・`env/`) を抱える worktree は、command §2 の原本確認 (insight
  「証拠の所在」節) を経るまで保持して報告する。
- dirty の撤去や引き渡し script は command §3 の退避検算 (tar の `-C` 順・非 dir entry 数照合) を前提にし、
  検算を欠く撤去手順を人間へ渡さない (F1034)。
- sandbox または shared Git metadata の権限が不足する場合は権限を拡大しない。安全に実行できた操作、
  対象、未実行操作を人間へ返す。

## 境界を守る

hook の配線と限界は `hooks/README.md` が正本である。設定の存在を防護の証拠に数えず、
同文書の保護境界を手動で守る。push と remote branch 操作は人間に残す。

自己改善候補も共有 command の終端に従い final で報告するだけとし、別 dev-wave へ自動移行しない。
"""
_SYNTHETIC_CLEANUP_OPENAI_YAML = """interface:
  display_name: "Cleanup Branches"
  short_description: "Izanagi の古い・取込済み branch と worktree を退避して整理"
  default_prompt: "Use $cleanup-branches to back up and clean up merged or stale branches and worktrees."
"""
_SYNTHETIC_CLEANUP_COMMAND = """---
description: 古い・取込済みの branch と worktree を退避してから掃除する (submodule 罠対応、push 系はユーザー引き渡し)
argument-hint: [任意: 対象限定 (branch/worktree 名)。省略時は全量棚卸し]
---

## 0. 最優先 mutation boundary

この command の受領から final response 完了までを cleanup 実行とする。成功・削除 0 件・罠発見・
検査赤・途中停止を含め、**本節は `CLAUDE.md` の一般クラス 2 規律より優先する**。クラス 2 は
repo 内容や履歴の変更権限を与えない。対象限定の引数: $ARGUMENTS

状態変更の allowlist は、(1) §2 の削除対象 branch の `git branch -d`/`-D`、(2) §2 の撤去対象 worktree の
§3 の unlock・detach・branch 解放・ゴミ置き場への mv と実体削除・条件付き prune、(3) §2 の退避と
計画表・script・log の repo 外退避 dir への書込、(4) land 調整役 session への連絡だけである。
Codex はさらに real prune を許さない。§1〜§4 の読み取り検査と final での報告は
state mutation ではなく許可する。overlay は許可集合を狭めるだけで、本 command は再許可しない。

**未列挙の state mutation は目的・修復・一般クラス 2 規律を理由にしても禁止する。** とくに
branch/worktree の新規作成、surviving worktree の tracked/untracked file・index・設定の作成/編集、
handoff/worklog/spool/insight/failure/decision の作成、`git add/commit/amend/merge/rebase/cherry-pick/reset`、
同一実行内の自己改善、local main/commit graph/remote の変更、push を禁止する。repo file を変更しない
cleanup では project tests・build・provenance 監査も行わない。未確定事項・新しい罠・prompt 不備は
final で裁定候補として返し、実装・記録は明示起動された別 dev-wave だけが行う。

## 1. 棚卸し (削除の前に全量を見る)

- §2 の安い条件が先、高い判定は通過対象のみ。
- `git worktree list --porcelain` / `git branch -a` を列挙。全 local branch の
  `git rev-list --count --left-right <b>...main` (左=ahead 右=behind) と tip 時刻、
  ahead>0 のみ `git cherry main <b>` を各 1 command に集約。未着地は §5 の報告へ
- 除外対象含む全 worktree の `GIT_OPTIONAL_LOCKS=0 git status --short` を §4 用に保存。
  独立な読み取り並列可。読み取り・占有検査の起動親/wrapper (検査時も生存する親含む) の argv に対象 path 禁止。
  対象入り argv の全読み取り終了後、§2 の安い条件通過対象のみ §3 の占有検査へ。
- `python3 tools/audit_dangling_commits.py --offrepo-scan off` を単独実行
  (パイプ禁止、rc直後保存、F152)。分岐: `docs/unreachable-object-ledger.md`
- 全削除・撤去候補を 1 回で `python3 tools/check_branch_rescue.py --ledger-check --branch <b>...
  --retire-worktree <absolute-path>...` に渡す。rc0完全/2不完全/3通知/64usage・JSON は退避 dir と §5 へ。
  rc2 は削除を止めない。worktree 200 本超は `git worktree list` が 8 秒上限を超え必ず rc2 なので、
  §3 の撤去後・branch 削除前に branch 候補だけで再走し、再び rc2 なら JSON を残して進む

## 2. 残す対象と退避 (残す対象以外は退避して消す)

- 残す: main / primary checkout、§3 の占有、HEAD・tip が直近 (目安: 稼働 wave の開始以降か 6h 以内) に
  動いた木・branch、稼働 session (ListAgents・投げ文) の主題の木・branch (棚卸し後に同系列の新 wave が
  起動すればその系列も)、現行 docs (phase doc・worklog 末尾の次の一手・decisions) が残すと名指しした branch
  (grep は main の tracked docs だけ、`main-worklog-*.md` 等の写しは数えない)、land 中の wave の branch、
  稼働 wave の manifest (job dir の `child-worktrees.json`) に載る子木、棚卸し後の新規
- 原本の置き場 (insight が名指す木・`dev-wave-jobs/` の投入木、未追跡 `output/` の原本) は写しがあっても、
  登録だけ外す形でも消さず報告。移管は別 dev-wave (F1034)
- 他は施錠・ahead>0・dirty・未着地・rescue 判定不能でも退避して消す。損失ゼロは要件でない。範囲は AI が
  Codex 2 役 (決定役・攻撃役の read-only consult) で決め、ユーザーへ確認・実行を回さない
- 消す前に repo 外 `/work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-<日付>/` へ退避: ahead>0 の削除 branch は
  1 本の bundle (`^main`、`create`+`verify`+`list-heads` 一致)、main に無い detached HEAD と submodule HEAD
  (main 側 module repo に無いもの) は木ごとの bundle、追跡差分は `diff HEAD --binary`、未追跡は
  `ls-files -o --exclude-standard` と `output/` 下の ignored を tar (§3 の件数照合)。submodule 内の差分・未追跡も同様
- ahead=0 は `git branch -d`、-d 拒否と ahead>0 は退避後に `-D`。名前と期待 tip の表で一括削除
- 高い条件: 削除直前に tip・HEAD が棚卸し時と同じで占有が無いことを再確認し、外れたら残す。
  対象内で作業中は先に main checkout へ退出

## 3. worktree の削除手順 (F26)

削除の直前に対象ごと `python3 tools/check_worktree_occupancy.py <worktree>`。rc0 のみ進み、
rc1=占有/rc2=判定不能は停止。submodule は `git worktree remove` 禁止、F26 の手順にする:

1. 施錠木は §2 の退避後に `git worktree unlock`。land 調整役 session がいれば
   CLEANUP-READY → OK を待つ → 撤去後に CLEANUP-DONE
2. `git -C <worktree> checkout --detach`、`git branch -d <branch>` (§2 の条件で `-D`)
3. 木を同じ file system のゴミ置き場 `/work/1/SFC/tanab/tmp/cleanup-trash-<日付>/` へ `mv` (rename で数秒/本)
4. 全 mv 後の `git worktree prune --dry-run --verbose` の全候補＝今回 mv した対象なら `git worktree prune` を 1 回。
   land 調整役がいれば PRUNE OK を待つ。他 wave の撤去途中の登録が混ざれば、持ち主が同意した分を足した
   集合と完全一致した時だけ打ち、それ以外は real prune せず引渡し
5. prune 後、ゴミ置き場の実体を `python3 tools/cleanup_remove_dirs.py -- <2 path>` で 2 本ずつ背景で消す
   (渡した全 path を同時に rm する。Lustre では多並列にしない、1 本 75〜250 秒)。rc0 以外は残して報告。
   全 job の終了 status と path 不在を確かめてから §4 へ

撤去・削除 script は対象を本文に名指しする (計画 file から読む script は auto mode の判定が拒否する)。
拒否されてもユーザーへ実行を回さない。名指しの形へ直して再申請し、なお拒否なら迂回せず final で報告する。
退避の tar は `-C <worktree>` を `-T` の前に置き、`ls-files -o` の list 数を tar の非 dir entry 数が
下回れば撤去しない (F1034)。

**`git submodule deinit` は使わない**。誤実行時は追加修復せず停止し、必要な
`git submodule update --init external/ccbench` を final で引き渡す。正本は `docs/failures.md` F26。

ExitWorktree の remove を `discard_changes: true` で押し切らず、main が当該 commit を含むと
確認して `action: keep` で抜け、本節で畳む。
cwd 固定の背景セッションや occupied worktree は、
detach・unlock・branch/directory 削除・prune を行わず、そのまま引き渡す (F51)。

## 4. 事後検査

- `git worktree list` / `git branch` が期待どおり
- `git submodule status` — main checkout の external/ccbench が初期化済み (`-` なし) で pin 一致
- §1 の status と比べ、surviving worktree・index・repo file に新しい差分が無い

## 5. ユーザー引き渡し (AI は push しない)

remote branch 削除・main の push はせず対象を列挙。残した木・branch は理由 (占有・直近・主題・名指し・原本)、
消したものは bundle・tar の path・sha256・verify 結果と rescue JSON の path を示し、損失 commit の
台帳転記と原本の移管候補を別 dev-wave へ引き渡す。
push が毎回別 object の `loose object <sha> ... is corrupt` で落ち、名指し object が正常なら Lustre 読込失敗の疑い。
修復・fsck 前に primary の main checkout で送る範囲だけ pack 化してから再 push:
`printf 'main\\n^origin/main\\n' | git pack-objects --revs -q .git/objects/pack/pack`。
元の object は消さない (D1115 と非衝突)。全体 repack は 10 分超で不要。

## 6. 自己改善候補の終端

記載と実挙動の食い違い・新しい罠・手順不足は `docs/skill-self-improvement.md` の routing 候補として
final で報告するだけにする。同一 cleanup 実行・継続・自己 spawn では編集や記録へ移行しない。
"""


def _write(root: str, rel: str, content: str) -> None:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _write_bytes(root: str, rel: str, content: bytes) -> None:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)


def _enumerated_rels() -> list[str]:
    """check_docs 本体の _ENUMERATED_DOCS を実 REPO 相対パスへ落とす (増減に追従)。"""
    return sorted(str(p.relative_to(check_docs.REPO)) for p in check_docs._ENUMERATED_DOCS)


def _write_backlog_docs(
    root: str,
    worklog_text: str = _CLEAN_WORKLOG,
    phase3_text: str = _CLEAN_PHASE3,
) -> None:
    _write(root, os.path.join("docs", "worklog.md"), worklog_text)
    _write(root, os.path.join("docs", "phase3.md"), phase3_text)


def _write_empty_spool_layout(root: str) -> None:
    """validate_spool_tree が受理する pending 0 件の正規 layout を作る。"""

    _write(root, "docs/spool/README.md", "# synthetic spool\n")
    _write(root, "docs/spool/FOLDED.md", "# synthetic folded receipts\n")
    for ledger in ("worklog", "decisions", "failures"):
        _write(
            root,
            f"docs/spool/{ledger}/README.md",
            f"# synthetic {ledger} spool\n",
        )


def _archive_readme(*names: str) -> str:
    all_names = (_PLACEHOLDER_ARCHIVE_NAME, *names)
    return (
        "# archive\n\n## 現在の収容物\n\n"
        + "".join(f"- `{name}`\n" for name in all_names)
    )


def _numbered_archive_claim_line(
    name: str,
    date: str,
    lo: int,
    hi: int | None = None,
    *,
    end_date: str | None = None,
    continuation: str | None = None,
) -> str:
    value = f"- `{name}` — worklog の {date} ({lo})"
    if hi is not None:
        value += "〜"
        if end_date is not None:
            value += f"{end_date} "
        value += f"({hi})"
    value += " 分"
    if continuation is not None:
        value += f"\n  {continuation}"
    return value + "\n"


def _archive_with_entries(
    *entries: tuple[str, str],
    extra_h2: str | None = None,
) -> str:
    chunks = ["# numbered synthetic archive\n"]
    for date, ordinal in entries:
        chunks.append(
            f"\n## {date} ({ordinal}) — synthetic entry {ordinal}\n\n"
            "### 次の一手\n"
        )
    if extra_h2 is not None:
        chunks.append(
            f"\n## {extra_h2}\n\n"
            "### 次の一手\n"
        )
    return "".join(chunks)


def _write_archive_index(root: str, *lines: str) -> None:
    _write(
        root,
        "docs/archive/README.md",
        "# archive\n\n## 現在の収容物\n\n"
        f"- `{_PLACEHOLDER_ARCHIVE_NAME}`\n"
        + "".join(lines),
    )


def _write_command_guard_docs(root: str) -> None:
    def refs(pairs: set[tuple[str, str]] | frozenset[tuple[str, str]]) -> str:
        grouped: dict[str, list[str]] = {}
        for path, section in sorted(pairs):
            grouped.setdefault(path, []).append(section)
        chunks = []
        for path, sections in grouped.items():
            if path == "docs/skill-self-improvement.md":
                chunks.append(f"`{path}` の全節")
            elif (
                path == "docs/dev-wave/operations.md"
                and sections == list(_SYNTHETIC_OPERATION_SECTION_IDS)
            ):
                chunks.append(_SYNTHETIC_ALL_OPERATIONS_REF)
            else:
                ids = ", ".join(f"`{section}`" for section in sections)
                chunks.append(f"`{path}`: {ids}")
        return "; ".join(chunks)

    stage_rows = []
    for mode, contract in (
        ("U", check_docs.STAGE_UNCONDITIONAL_DISPATCH_CONTRACT),
        ("C", check_docs.STAGE_CONDITIONAL_DISPATCH_CONTRACT),
    ):
        for key, pairs in contract.items():
            if mode == "C" and key in {"段 5", "段 6"}:
                continue
            grouped: dict[str, set[tuple[str, str]]] = {}
            for path, section in pairs:
                grouped.setdefault(path, set()).add((path, section))
            for path, path_pairs in sorted(grouped.items()):
                if key == "段 6" and path == "docs/dev-wave/workers.md":
                    s05 = {
                        pair for pair in path_pairs
                        if pair[1].startswith("DW-S05-")
                    }
                    s06 = path_pairs - s05
                    stage_rows.append(f"| {key} |{mode}| {refs(s05)} |")
                    stage_rows.append(f"| {key} |{mode}| {refs(s06)} |")
                else:
                    stage_rows.append(f"| {key} |{mode}| {refs(path_pairs)} |")
    stage_rows.extend(_SYNTHETIC_STAGE_5_6_CONDITIONAL_ROWS)
    condition_rows = "\n".join([
        *(
            f"| {key} | {check_docs.CONDITION_TRIGGER_CONTRACT[key]} | "
            f"{refs(pairs)} |"
            for key, pairs in check_docs.CONDITION_DISPATCH_CONTRACT.items()
            if key not in {"18", "25", "26", "27"}
        ),
        _SYNTHETIC_CONDITION_18_ROW,
        _SYNTHETIC_CONDITION_25_ROW,
        _SYNTHETIC_CONDITION_26_ROW,
        _SYNTHETIC_CONDITION_27_ROW,
    ])
    dev_wave = f"""---
description: synthetic dev-wave
argument-hint: [synthetic]
disable-model-invocation: true
---

{_SYNTHETIC_DEV_WAVE_COMMAND_START_SECTION}## 読み込み契約

条件には最遅読了段がある。`DW-O08`、`DW-O09`、`DW-O10` は段 1 brief 前、
`DW-O13` は段 2 プラン前が期限である。期限後に成立したら成果物を invalidate し、
前者は段 1 brief、後者は段 2 から再実行する。巻き戻し後は段・条件を再評価し、
旧成果物を流用してはならない。

コード・テスト・実行可能資材（以下「実装面」）は軽量版でも
Codex `role=author` が書き、親は実装面を直接編集せず統合する。

{_SYNTHETIC_DEV_WAVE_STATE_MACHINE}
## 段 dispatch

{check_docs.DEV_WAVE_STAGE_DISPATCH_LEGEND}

{check_docs.DEV_WAVE_STAGE_DISPATCH_HEADER}
|---|---|---|
{chr(10).join(stage_rows)}

段 6 で fix を codex へ再投する子は、`DW-S05-A`、`DW-S05-B`、`DW-S05-C` を
全文継承する。段 6 時点で成立している全条件の `DW-Oxx` も fix 操作の直前に読む。

## 条件 dispatch

{check_docs.DEV_WAVE_CONDITION_DISPATCH_HEADER}
|---|---|---|
{condition_rows}
"""
    cleanup = _SYNTHETIC_CLEANUP_COMMAND
    rulings = """---
description: synthetic rulings
argument-hint: [synthetic]
---

$ARGUMENTS
docs/skill-self-improvement.md
"""
    next_tasks = """---
description: synthetic next-tasks
argument-hint: [synthetic]
---

docs/skill-self-improvement.md
"""
    _write(root, ".claude/commands/dev-wave.md", dev_wave)
    _write(root, "tools/dev_wave_land.py", "# synthetic land helper\n")
    _write(root, "tools/dev_wave_cleanup.py", "# synthetic cleanup helper\n")
    _write(
        root,
        "tools/dev_wave_codex.py",
        _SYNTHETIC_SINGLE_DISPATCH_LAUNCHER_STAGES,
    )
    _write(root, "tools/dev_wave_wait.py", "# synthetic canonical waiter\n")
    _write(root, "tools/dev_wave_submodule_init.py", "# synthetic submodule initializer\n")
    _write(root, ".claude/commands/cleanup-branches.md", cleanup)
    _write(root, ".claude/commands/rulings.md", rulings)
    _write(root, ".claude/commands/next-tasks.md", next_tasks)
    codex_skill = f"""---
name: dev-wave
description: {_SYNTHETIC_DEV_WAVE_DESCRIPTION}
---

# Dev Wave

""" + _SYNTHETIC_CODEX_DEV_WAVE_START_SECTION + """## Codex 向けに適合する

""" + check_docs.CODEX_DEV_WAVE_NATURAL_LANGUAGE_STOP_LITERAL + """
""" + check_docs.CODEX_DEV_WAVE_PROTECTED_PATH_AUTHORING_LITERAL + """
manager は実装面を直接編集しない。
worker は docs/dev-wave/workers.md と docs/dev-wave/operations.md に従い、codex exec で起動して
collaboration child で代替しない。
`.codex/role-adapters/*.json` は起動しない。`hooks/README.md` を手動で守る。
supervised manifest は実行せず、段 1〜9 と local main の契約に従う。

## 1 wave を閉じる

段 9 は dispatcher が指定する共通 land 契約だけに従い、Codex 固有の取り込み手順を重ねない。
"""
    _write(root, ".agents/skills/dev-wave/SKILL.md", codex_skill)
    _write(
        root,
        ".agents/skills/dev-wave/agents/openai.yaml",
        _SYNTHETIC_DEV_WAVE_OPENAI_YAML,
    )
    codex_rulings_skill = """---
name: rulings
description: synthetic Codex rulings skill
---

# Rulings

""" + "\n".join(check_docs.CODEX_RULINGS_SKILL_LITERALS) + "\n"
    _write(root, ".agents/skills/rulings/SKILL.md", codex_rulings_skill)
    _write(
        root,
        ".agents/skills/rulings/agents/openai.yaml",
        check_docs.CODEX_RULINGS_OPENAI_YAML,
    )
    codex_next_tasks_skill = """---
name: next-tasks
description: synthetic Codex next-tasks skill
---

# Next Tasks

""" + "\n".join(check_docs.CODEX_NEXT_TASKS_SKILL_LITERALS) + "\n"
    _write(root, ".agents/skills/next-tasks/SKILL.md", codex_next_tasks_skill)
    _write(
        root,
        ".agents/skills/next-tasks/agents/openai.yaml",
        check_docs.CODEX_NEXT_TASKS_OPENAI_YAML,
    )
    _write(
        root,
        ".agents/skills/cleanup-branches/SKILL.md",
        _SYNTHETIC_CLEANUP_SKILL,
    )
    _write(
        root,
        ".agents/skills/cleanup-branches/agents/openai.yaml",
        _SYNTHETIC_CLEANUP_OPENAI_YAML,
    )

    for rel, contract_sections in check_docs.REQUIRED_REFERENCE_SECTIONS.items():
        sections = (
            _SYNTHETIC_REGISTERED_OPERATION_SECTION_IDS
            if rel == "docs/dev-wave/operations.md"
            else sorted(contract_sections)
        )
        rendered_sections = []
        for section in sections:
            body = "body"
            if rel == "docs/dev-wave/workers.md" and section == "DW-S02":
                body += "\n\n" + check_docs.DEV_WAVE_DW_S02_REASONING_XHIGH_LITERAL
            if rel == "docs/dev-wave/workers.md" and section == "DW-S03":
                body += "\n\n" + check_docs.DEV_WAVE_DW_S03_REASONING_XHIGH_LITERAL
            if rel == "docs/dev-wave/workers.md" and section == "DW-S05-A":
                body += "\n\n" + check_docs.DEV_WAVE_DW_S05_A_REASONING_XHIGH_SENTENCE
            if rel == "docs/dev-wave/workers.md" and section == "DW-S06-A":
                body += "\n\n" + check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_SENTENCE
            if rel == "docs/dev-wave/workers.md" and section == "DW-S06-C":
                body += "\n\n" + check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_SENTENCE
            if rel == "docs/dev-wave/operations.md" and section == "DW-O01":
                body += (
                    "\n\n"
                    + _SYNTHETIC_DW_O01_WAITER_LINE.rstrip("\n")
                    + "\n\n"
                    + check_docs.DEV_WAVE_DW_O01_DISPATCH_ROUTE_LITERAL
                    + "\n\n"
                    + check_docs.DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL
                )
            if rel == "docs/dev-wave/operations.md" and section == "DW-O02":
                body += "\n\n" + _SYNTHETIC_SINGLE_DISPATCH_OPERATIONS_REFERENCE
            if rel == "docs/dev-wave/core.md" and section == "DW-C00":
                body += "\n\n" + _SYNTHETIC_DW_C00_WAITER_LINE.rstrip("\n")
            if rel == "docs/dev-wave/core.md" and section == "DW-S09":
                body += (
                    "\n\n"
                    + _S09_ACCEPTANCE_ORDER_LITERAL
                    + "\n"
                    + check_docs.DEV_WAVE_LAND_UNIQUE_ROUTE_LITERAL
                )
            if rel == "docs/dev-wave/operations.md" and section == "DW-O23":
                body += "\n\n`tools/dev_wave_land.py`"
            if rel == "docs/dev-wave/operations.md" and section == "DW-O18":
                rendered_sections.append(_SYNTHETIC_DW_O18_SECTION.rstrip("\n"))
            elif rel == "docs/dev-wave/operations.md" and section == "DW-O25":
                rendered_sections.append(_SYNTHETIC_DW_O25_SECTION.rstrip("\n"))
            elif rel == "docs/dev-wave/operations.md" and section == "DW-O26":
                rendered_sections.append(_SYNTHETIC_DW_O26_SECTION.rstrip("\n"))
            elif rel == "docs/dev-wave/operations.md" and section == "DW-O28":
                rendered_sections.append(_SYNTHETIC_DW_O28_SECTION.rstrip("\n"))
            elif rel == "docs/dev-wave/core.md" and section == "DW-C01":
                rendered_sections.append(_SYNTHETIC_DW_C01_SECTION.rstrip("\n"))
            else:
                rendered_sections.append(f"## {section} — synthetic\n\n{body}")
        text = "# synthetic reference\n\n" + "\n\n".join(rendered_sections) + "\n"
        if rel == "docs/dev-wave/operations.md":
            # exact pin 済みの節 slice を次の H2 直前の改行までに保つ。
            text = text.replace(
                _SYNTHETIC_DW_O25_SECTION.rstrip("\n")
                + "\n\n## DW-O26",
                _SYNTHETIC_DW_O25_SECTION.rstrip("\n")
                + "\n## DW-O26",
                1,
            )
            text = text.replace(
                _SYNTHETIC_DW_O26_SECTION.rstrip("\n")
                + "\n\n## DW-O27",
                _SYNTHETIC_DW_O26_SECTION.rstrip("\n")
                + "\n## DW-O27",
                1,
            )
        literals = check_docs.CODEX_FIRST_REFERENCE_LITERALS.get(rel, ())
        if literals:
            text += "\n" + "\n".join(literals) + "\n"
        _write(root, rel, text)

    self_doc = """# synthetic self

## 発火 gate

body

""" + _SYNTHETIC_SELF_ROUTING_SECTION + """## command 入口の編集条件

body

## command 別の終端

### dev-wave

body

### cleanup-branches

body

### rulings

body

### next-tasks

body

## 検査と commit 境界

body
"""
    _write(root, "docs/skill-self-improvement.md", self_doc)

    provenance_entry = """# synthetic provenance entry

## 条件 dispatch

| key | 発火条件 | 読む節 |
|---|---|---|
| correction | 固定 target の forward correction を扱う | `docs/provenance/correction.md`: `PR-C01`, `PR-C02`, `PR-C03` |
| message-file | commit 前に message を検査する | `docs/provenance/audit.md`: `PR-A01` |
| history | commit 後・別 range の履歴を監査する | `docs/provenance/audit.md`: `PR-A02`; `docs/provenance/correction.md`: `PR-C03` |
| analysis | provenance を比較や改善判断に使う | `docs/provenance/audit.md`: `PR-A03` |
"""
    correction = """# synthetic correction reference

## PR-C01 — synthetic

body

## PR-C02 — synthetic

body

## PR-C03 — synthetic

body
"""
    audit = """# synthetic audit reference

## PR-A01 — synthetic

body

## PR-A02 — synthetic

body

## PR-A03 — synthetic

body
"""
    _write(root, "docs/ai-provenance.md", provenance_entry)
    _write(root, "docs/provenance/correction.md", correction)
    _write(root, "docs/provenance/audit.md", audit)


def _write_dispatch_inventory_fixture(root: str) -> None:
    _write(root, "docs/pegasus-runbook.md", _SYNTHETIC_DISPATCH_RUNBOOK)
    _write(
        root,
        "tools/pegasus/dispatch_compute.py",
        _SYNTHETIC_DISPATCH_SOURCE,
    )
    shutil.copy(
        check_docs.REPO / "tools" / "pegasus_admission_registry.py",
        os.path.join(root, "tools", "pegasus_admission_registry.py"),
    )
    registry = {
        "schema_version": "pegasus-admission-registry/v1",
        "entries": _SYNTHETIC_ADMISSION_ENTRIES,
    }
    _write(
        root,
        "tools/pegasus/admission_registry.json",
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
    )
    _write(root, "tools/pegasus/README.md", _SYNTHETIC_ADMISSION_README)


def _assert_violation(root: str, *needles: str) -> subprocess.CompletedProcess:
    res = _run_check(root)
    assert res.returncode == 1, f"違反 fixture が赤にならなかった:\n{res.stdout}\n{res.stderr}"
    for needle in needles:
        assert needle in res.stdout, f"{needle!r} が finding にない:\n{res.stdout}"
    return res


def _replace_once(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, (old, text.count(old))
    return text.replace(old, new, 1)


def _replace_carry_ledger_assignment(text: str, value: str) -> str:
    start_marker = "KNOWN_CARRY_ID_MISMATCHES = {"
    end_marker = "\nEXPECTED_KNOWN_CARRY_ID_MISMATCHES = "
    assert text.count(start_marker) == 1
    assert text.count(end_marker) == 1
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    old = text[start:end]
    assert text.count(old) == 1
    return text.replace(
        old,
        f"KNOWN_CARRY_ID_MISMATCHES = {value}",
        1,
    )


def _enable_known_carry_mismatch_fixture(root: str) -> None:
    """実台帳と対応する採番 archive を一体で opt-in する。"""

    checker_rel = "tools/check_docs.py"
    checker_text = _read(root, checker_rel)
    checker_text = _replace_once(
        checker_text,
        "KNOWN_CARRY_ID_MISMATCHES = {}",
        f"KNOWN_CARRY_ID_MISMATCHES = {check_docs.KNOWN_CARRY_ID_MISMATCHES!r}",
    )
    checker_text = _replace_once(
        checker_text,
        "EXPECTED_KNOWN_CARRY_ID_MISMATCHES = 0",
        "EXPECTED_KNOWN_CARRY_ID_MISMATCHES = 4",
    )
    checker_text = _replace_once(
        checker_text,
        "MIN_EXPECTED_CARRY_REFERENCE_COUNT = 0",
        "MIN_EXPECTED_CARRY_REFERENCE_COUNT = 4",
    )
    _write(root, checker_rel, checker_text)

    archive_rel = f"docs/archive/{_KNOWN_CARRY_ID_MISMATCH_ARCHIVE_NAME}"
    _write(root, archive_rel, _KNOWN_CARRY_ID_MISMATCH_ARCHIVE)
    readme_rel = "docs/archive/README.md"
    readme = _read(root, readme_rel)
    placeholder_line = f"- `{_PLACEHOLDER_ARCHIVE_NAME}`\n"
    claim = _numbered_archive_claim_line(
        _KNOWN_CARRY_ID_MISMATCH_ARCHIVE_NAME,
        "2026-07-26",
        73,
        78,
    )
    _write(
        root,
        readme_rel,
        _replace_once(readme, placeholder_line, placeholder_line + claim),
    )


def _build_min_repo() -> str:
    """check_docs が『違反なし』を返す最小合成 repo を tmp に作り、root を返す。

    trivial 内容 (行番号参照/現況再掲/pin literal/D 参照/パス参照をどれも含まない) と、
    保存則を満たす最小 worklog / 見送り台帳を用意し、baseline を違反なしにする。
    """
    root = tempfile.mkdtemp(prefix="izanagi_checkdocs_")
    # 実 check_docs.py を複製 — REPO は __file__ 由来なので tmp/tools/ に置くと tmp を指す。
    _dst = os.path.join(root, "tools", "check_docs.py")
    os.makedirs(os.path.dirname(_dst))
    shutil.copy(check_docs.__file__, _dst)
    with open(_dst, encoding="utf-8") as fixture_checker:
        checker_text = fixture_checker.read()
    checker_text = _replace_carry_ledger_assignment(checker_text, "{}")
    checker_text = _replace_once(
        checker_text,
        "EXPECTED_KNOWN_CARRY_ID_MISMATCHES = 4",
        "EXPECTED_KNOWN_CARRY_ID_MISMATCHES = 0",
    )
    checker_text = _replace_once(
        checker_text,
        "MIN_EXPECTED_CARRY_REFERENCE_COUNT = 404_326",
        "MIN_EXPECTED_CARRY_REFERENCE_COUNT = 0",
    )
    with open(_dst, "w", encoding="utf-8") as fixture_checker:
        fixture_checker.write(checker_text)
    authority_dst = os.path.join(
        root, "tools", "dev_waves", "launch_authority.py"
    )
    os.makedirs(os.path.dirname(authority_dst))
    shutil.copy(
        check_docs.REPO / "tools" / "dev_waves" / "launch_authority.py",
        authority_dst,
    )
    shutil.copy(check_docs.REPO / "tools" / "spool_fold.py", os.path.dirname(_dst))
    _write_empty_spool_layout(root)

    # 手書き列挙 doc (LIVING_DOCS の glob 前スナップショット) を trivial 内容で用意。
    for rel in _enumerated_rels():
        _write(root, rel, "# placeholder living doc\n")

    # check_docs が main() 内で無条件に read するファイル群。
    _write(root, os.path.join("orchestrator", "campaign", "pin.py"),
           'CURRENT_PIN = "abc1234def5678"\n')
    admission_dst = os.path.join(
        root, "orchestrator", "campaign", "s8b_holdout_admission.py",
    )
    os.makedirs(os.path.dirname(admission_dst), exist_ok=True)
    shutil.copy(
        check_docs.REPO / "orchestrator" / "campaign" /
        "s8b_holdout_admission.py",
        admission_dst,
    )
    _write(
        root,
        os.path.join("orchestrator", "tests", "flaky_test_holds.py"),
        "# synthetic path placeholder\n",
    )
    _write(
        root,
        os.path.join("tools", "check_acceptance_reds.py"),
        "# synthetic path placeholder\n",
    )
    _write(root, os.path.join("docs", "decisions.md"),
           "## D1. placeholder decision\n\n本文。\n\n"
           "## D254. placeholder decision\n\n本文。\n\n"
           "## D271. placeholder decision\n\n本文。\n\n"
           "## D690. placeholder decision\n\n本文。\n\n"
           "## D703. placeholder decision\n\n本文。\n\n"
           + _SYNTHETIC_R33_DECISION_SECTION)
    _write(root, os.path.join("docs", "failures.md"),
           "# placeholder failures\n\n"
           "## F242. placeholder failure\n\n本文。\n")
    _write(root, os.path.join("docs", "archive", "README.md"),
           _archive_readme())
    _write(
        root,
        os.path.join("docs", "archive", _PLACEHOLDER_ARCHIVE_NAME),
        "# synthetic archive\n\n"
        "## 2026-07-24 (4) — 統合 E2E: 実 seal を official floor 経路に通す (D79(7) 部分閉鎖、branch worktree-dev-wave-e2e-real-seal、計測なし)\n\n"
        f"{_PLACEHOLDER_DEBT_ARCHIVE_ACCEPTANCE}\n"
        "\n"
        "## 2026-07-24 (5) — [T-086] PKG-2: FROZEN_MANIFEST exact key-set 暫定 assert (test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)\n\n"
        f"{_PLACEHOLDER_DEBT_WORKLOG}\n\n"
        "### 次の一手\n\n"
        f"{_PLACEHOLDER_WORKLOG_ENTRIES}",
    )
    _write(
        root,
        os.path.join("output", "insights", "2026-07-24_e2e-real-seal.md"),
        f"{_PLACEHOLDER_DEBT_INSIGHT}\n",
    )
    _write(
        root,
        os.path.join(
            "output",
            "insights",
            "2026-07-25_t068-t077-t078-closure-verbatim.md",
        ),
        f"{_PLACEHOLDER_MENTION_INSIGHT_A}\n"
        f"{_PLACEHOLDER_MENTION_INSIGHT_B}\n",
    )
    # backlog guard の必須構造。phase3.md は上の列挙 placeholder を上書きする。
    _write_backlog_docs(root)
    _write(root, "AGENTS.md", _SYNTHETIC_AGENTS_SINGLE_DISPATCH_SECTION)
    _write_command_guard_docs(root)
    _write_dispatch_inventory_fixture(root)
    return root


def _run_check(
    root: str,
    *args: str,
    timeout: float | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, os.path.join(root, "tools", "check_docs.py"), *args],
        capture_output=True, text=True,
        timeout=timeout,
    )


# 2026-08-26、Pegasus login node 上で tools/run_tests.py の bounded local
# cgroup scope を使い、xdist 無効 (-n 0) で対象 node を1回実測した。母集合は正例・
# 負例アームそれぞれの投入側と赤処理側の4標本で、投入側は0.0961/0.0948秒、
# 赤処理側は0.0596/0.0599秒、maxは0.0961秒 (node全体は1.32秒)。artifactと
# processの2.0秒はmaxの約20.8倍、reapの1.0秒は約10.4倍である。
_CONDITION_CONTEXT_ARTIFACT_TIMEOUT_SECONDS = 2.0
_CONDITION_CONTEXT_PROCESS_TIMEOUT_SECONDS = 2.0
_CONDITION_CONTEXT_REAP_TIMEOUT_SECONDS = 1.0
_CONDITION_CONTEXT_EXIT_MARGIN_SECONDS = 30.0
_CONDITION_CONTEXT_TEST_LIMIT_SECONDS = 300.0
_CONDITION_CONTEXT_SUBMISSION_CODE = r"""
import json
import os
from pathlib import Path
import sys

repo_root, artifact_path = sys.argv[1:]
sys.path.insert(0, str(Path(repo_root) / "tools"))
import check_docs

text = (Path(repo_root) / ".claude" / "commands" / "dev-wave.md").read_text(
    encoding="utf-8"
)
resolved = check_docs.resolve_condition_sections(text, "テスト・受入")
print(json.dumps(
    {
        "pid": os.getpid(),
        "resolved": resolved,
        "resolved_value_types": {
            key: type(value).__name__ for key, value in resolved.items()
        },
    },
    ensure_ascii=False,
), flush=True)
Path(artifact_path).write_text(
    json.dumps({"acceptance": "red"}),
    encoding="utf-8",
)
"""
_CONDITION_CONTEXT_RED_CODE = r"""
import json
import os
from pathlib import Path
import sys

artifact_path, repo_root = sys.argv[1:]
artifact = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
assert artifact == {"acceptance": "red"}
sys.path.insert(0, str(Path(repo_root) / "tools"))
import check_docs

text = (Path(repo_root) / ".claude" / "commands" / "dev-wave.md").read_text(
    encoding="utf-8"
)
resolved = check_docs.resolve_condition_sections(text, "赤処理")
stdin_data = sys.stdin.read()
print(json.dumps({
    "pid": os.getpid(),
    "resolved": resolved,
    "resolved_value_types": {
        key: type(value).__name__ for key, value in resolved.items()
    },
    "argv": sys.argv[1:],
    "environment": dict(os.environ),
    "stdin": stdin_data,
}, ensure_ascii=False), flush=True)
"""


def _wait_for_context_artifact(path: str, process: subprocess.Popen) -> None:
    deadline = time.monotonic() + _CONDITION_CONTEXT_ARTIFACT_TIMEOUT_SECONDS
    while True:
        if os.path.isfile(path):
            return
        if process.poll() is not None:
            raise AssertionError(
                f"投入 context が赤 artifact を作らず終了した: rc={process.returncode}"
            )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(
                process.args,
                _CONDITION_CONTEXT_ARTIFACT_TIMEOUT_SECONDS,
            )
        time.sleep(min(0.01, remaining))


def _reap_context_process(process: subprocess.Popen) -> None:
    try:
        process.communicate(timeout=_CONDITION_CONTEXT_REAP_TIMEOUT_SECONDS)
        return
    except subprocess.TimeoutExpired:
        process.terminate()
    try:
        process.communicate(timeout=_CONDITION_CONTEXT_REAP_TIMEOUT_SECONDS)
        return
    except subprocess.TimeoutExpired:
        process.kill()
    process.communicate(timeout=_CONDITION_CONTEXT_REAP_TIMEOUT_SECONDS)


def _run_condition_18_separate_contexts(root: str, artifact_name: str) -> dict:
    artifact_path = os.path.join(root, artifact_name)
    assert not os.path.exists(artifact_path)
    empty_environment: dict[str, str] = {}
    submission_command = [
        sys.executable,
        "-c",
        _CONDITION_CONTEXT_SUBMISSION_CODE,
        root,
        artifact_path,
    ]
    red_command = [
        sys.executable,
        "-c",
        _CONDITION_CONTEXT_RED_CODE,
        artifact_path,
        root,
    ]
    processes: list[subprocess.Popen] = []
    try:
        submission_started = time.perf_counter()
        submission_process = subprocess.Popen(
            submission_command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=empty_environment,
        )
        processes.append(submission_process)
        _wait_for_context_artifact(artifact_path, submission_process)
        submission_stdout, submission_stderr = submission_process.communicate(
            timeout=_CONDITION_CONTEXT_PROCESS_TIMEOUT_SECONDS
        )
        submission_elapsed = time.perf_counter() - submission_started
        assert submission_process.returncode == 0, submission_stderr
        submission_ended = time.perf_counter()
        submission_payload = json.loads(submission_stdout)
        assert submission_payload["pid"] == submission_process.pid
        assert json.loads(_read(root, artifact_name)) == {"acceptance": "red"}

        red_started = time.perf_counter()
        red_process = subprocess.Popen(
            red_command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=empty_environment,
        )
        processes.append(red_process)
        red_stdout, red_stderr = red_process.communicate(
            timeout=_CONDITION_CONTEXT_PROCESS_TIMEOUT_SECONDS
        )
        red_elapsed = time.perf_counter() - red_started
        assert red_process.returncode == 0, red_stderr
        red_payload = json.loads(red_stdout)
        assert red_payload["pid"] == red_process.pid
        return {
            "artifact_path": artifact_path,
            "submission": submission_payload,
            "red": red_payload,
            "submission_command": submission_command,
            "red_command": red_command,
            "red_environment": empty_environment,
            "elapsed": {
                "submission": submission_elapsed,
                "red": red_elapsed,
            },
            "sequence": {
                "submission_ended": submission_ended,
                "red_started": red_started,
            },
        }
    finally:
        for process in reversed(processes):
            _reap_context_process(process)


def _violation_count(res: subprocess.CompletedProcess) -> int:
    match = re.search(r"^check_docs: (\d+) 件の違反$", res.stdout, re.MULTILINE)
    assert match is not None, f"違反件数 header を解析できない:\n{res.stdout}"
    return int(match.group(1))


def _finding_set(res: subprocess.CompletedProcess) -> set[str]:
    return {
        line.removeprefix("  - ")
        for line in res.stdout.splitlines()
        if line.startswith("  - ")
    }


def _admission_findings(res: subprocess.CompletedProcess) -> list[str]:
    prefix = check_docs._ADMISSION_PREFIX
    return [
        line.removeprefix("  - ")
        for line in res.stdout.splitlines()
        if line.startswith(f"  - {prefix}")
    ]


def _assert_admission_count(
    root: str,
    expected: int,
    *needles: str,
) -> subprocess.CompletedProcess:
    res = _run_check(root)
    admission = _admission_findings(res)
    assert len(admission) == expected, (
        f"admission finding 件数が不一致: expected={expected}, "
        f"actual={admission}\nstdout={res.stdout}\nstderr={res.stderr}"
    )
    for finding in admission:
        assert finding.startswith(check_docs._ADMISSION_PREFIX)
    for needle in needles:
        assert any(needle in finding for finding in admission), (
            f"{needle!r} が admission finding にない: {admission}"
        )
    if expected:
        assert res.returncode == 1, res.stdout
    assert "Traceback" not in res.stdout + res.stderr
    return res


def _assert_admission_exact(
    root: str,
    *details: str,
) -> subprocess.CompletedProcess:
    res = _run_check(root)
    expected = {check_docs._ADMISSION_PREFIX + detail for detail in details}
    actual = set(_admission_findings(res))
    assert actual == expected, (
        f"admission finding 集合が不一致: expected={sorted(expected)}, "
        f"actual={sorted(actual)}\nstdout={res.stdout}\nstderr={res.stderr}"
    )
    assert len(_admission_findings(res)) == len(expected), (
        f"admission finding に重複がある: {_admission_findings(res)}"
    )
    assert res.returncode == (1 if expected else 0), res.stdout
    assert "Traceback" not in res.stdout + res.stderr
    return res


def _rewrite_registry(root: str, mutate) -> None:
    rel = "tools/pegasus/admission_registry.json"
    with open(os.path.join(root, rel), encoding="utf-8") as stream:
        document = json.load(stream)
    mutate(document)
    _write(
        root,
        rel,
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
    )


# ===== baseline: 合成 repo は違反なし (positive control の土台) =====

def test_synthetic_repo_baseline_clean():
    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, f"baseline が違反ありになった:\n{res.stdout}\n{res.stderr}"
        assert "違反なし" in res.stdout, res.stdout
        assert _admission_findings(res) == []
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_registry_load_failures_are_one_fail_closed_finding():
    cases = {
        "json missing": lambda root: os.remove(
            os.path.join(root, "tools/pegasus/admission_registry.json")
        ),
        "loader missing": lambda root: os.remove(
            os.path.join(root, "tools/pegasus_admission_registry.py")
        ),
        "invalid schema": lambda root: _rewrite_registry(
            root,
            lambda document: document.__setitem__("schema_version", "broken"),
        ),
        "unknown class": lambda root: _rewrite_registry(
            root,
            lambda document: document["entries"][
                "tools/pegasus/collect_receipt.py"
            ].__setitem__("class", "mystery"),
        ),
    }
    for label, mutate in cases.items():
        root = _build_min_repo()
        try:
            mutate(root)
            _assert_admission_count(root, 1, "canonical registry を確定できない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_loader_executes_source_even_with_unchecked_stale_pyc():
    """unchecked pyc が失敗しても、現 source の正常動作を採る。"""
    root = _build_min_repo()
    try:
        rel = "tools/pegasus_admission_registry.py"
        loader = os.path.join(root, rel)
        source = _read(root, rel)
        _write(root, rel, "raise SystemExit(0)\n")
        py_compile.compile(
            loader,
            doraise=True,
            invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
        )
        _write(root, rel, source)

        result = _run_check(root)
        assert result.returncode == 0, (
            f"unchecked stale pyc が source より優先された:\n"
            f"{result.stdout}\n{result.stderr}"
        )
        assert "違反なし" in result.stdout, result.stdout
        assert _admission_findings(result) == []
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_loader_system_exit_never_evaporates_checker():
    loaders = {
        "top level": "raise SystemExit(0)\n",
        "function": (
            "def load_admission_registry(repo_root):\n"
            "    raise SystemExit(0)\n"
        ),
    }
    for label, source in loaders.items():
        root = _build_min_repo()
        try:
            _write(root, "tools/pegasus_admission_registry.py", source)
            result = _assert_admission_count(
                root,
                1,
                "canonical registry を確定できない",
                "SystemExit",
            )
            assert result.returncode == 1, f"{label}: {result.stdout}"
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_poisoned_exception_string_never_evaporates_checker():
    root = _build_min_repo()
    try:
        _write(
            root,
            "tools/pegasus_admission_registry.py",
            "class Poisoned(BaseException):\n"
            "    def __str__(self):\n"
            "        raise SystemExit(0)\n\n"
            "def load_admission_registry(repo_root):\n"
            "    raise Poisoned()\n",
        )
        _assert_admission_exact(
            root,
            "canonical registry を確定できない — Poisoned",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_outer_wrapper_fail_closed_on_poisoned_subchecker():
    root = _build_min_repo()
    try:
        checker = "tools/check_docs.py"
        source = _read(root, checker)
        needle = "def _check_admission_runbook(\n"
        replacement = (
            "def _check_admission_runbook(\n"
            "    text: str,\n"
            "    registry: dict[str, dict[str, str]],\n"
            "    findings: list[str],\n"
            ") -> None:\n"
            "    class Poisoned(BaseException):\n"
            "        def __str__(self):\n"
            "            raise SystemExit(0)\n"
            "    raise Poisoned()\n\n"
            "def _disabled_check_admission_runbook(\n"
        )
        assert source.count(needle) == 1
        _write(root, checker, source.replace(needle, replacement, 1))
        _assert_admission_exact(
            root,
            "admission checker 内部失敗を fail-closed 化 — Poisoned",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_projection_mutations_each_have_one_primary_finding():
    collect_row = (
        "| `tools/pegasus/collect_receipt.py` | `unknown` | "
        "`unmeasured synthetic input` |"
    )
    smoke_row = (
        "| `tools/pegasus/smoke_probe.sh` | `dispatch-required` | "
        "`static job-body classification` |"
    )
    extra_row = "| `tools/pegasus/extra.py` | `unknown` | `unmeasured` |"
    cases = {
        "row deletion": lambda text: text.replace(collect_row + "\n", "", 1),
        "row addition": lambda text: text.replace(smoke_row, smoke_row + "\n" + extra_row, 1),
        "class change": lambda text: text.replace(
            collect_row,
            collect_row.replace("`unknown`", "`local-ok`"),
            1,
        ),
        "evidence change": lambda text: text.replace(
            collect_row,
            collect_row.replace("unmeasured synthetic input", "changed evidence"),
            1,
        ),
        "duplicate": lambda text: text.replace(collect_row, collect_row + "\n" + collect_row, 1),
        "malformed": lambda text: text.replace(collect_row, "| `tools/pegasus/collect_receipt.py` | `unknown` |", 1),
        "malformed header": lambda text: text.replace(
            "| path | class | evidence |",
            "| path | class |",
            1,
        ),
        "malformed separator": lambda text: text.replace(
            "|---|---|---|",
            "|---|--|---|",
            1,
        ),
        "escaped pipe": lambda text: text.replace(
            collect_row,
            collect_row.replace("synthetic input", "synthetic \\| input"),
            1,
        ),
        "broken code span": lambda text: text.replace(
            collect_row,
            collect_row.replace("`unmeasured synthetic input`", "`unmeasured synthetic input"),
            1,
        ),
        "moved section": lambda text: text.replace(
            _SYNTHETIC_PROJECTION_TABLE + "\n\n",
            "",
            1,
        ).replace("### 7.1 synthetic next section", "### 7.1 synthetic next section\n\n" + _SYNTHETIC_PROJECTION_TABLE, 1),
        "fenced hidden": lambda text: text.replace(
            _SYNTHETIC_PROJECTION_TABLE,
            "```text\n" + _SYNTHETIC_PROJECTION_TABLE + "\n```",
            1,
        ),
        "comment hidden": lambda text: text.replace(
            _SYNTHETIC_PROJECTION_TABLE,
            "<!--\n" + _SYNTHETIC_PROJECTION_TABLE + "\n-->",
            1,
        ),
    }
    for label, mutate in cases.items():
        root = _build_min_repo()
        try:
            rel = "docs/pegasus-runbook.md"
            _write(root, rel, mutate(_read(root, rel)))
            _assert_admission_count(root, 1)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_non_pegasus_registry_entry_requires_projection_only():
    root = _build_min_repo()
    path = "tools/claude_session_ledger.py"
    entry = {
        "class": "unknown",
        "reason": "inputs are hard-capped; isolated-scope and cap-boundary measurements are unavailable",
        "primary_gate": "hook deny pending isolated-scope admission evidence",
        "evidence": "compute-node shared-service cgroup delta sampling at commit 04d85f93 (not runbook 7.0 isolated-scope evidence; non-certifying); default --json argv, 25 of 1045 files read, 4728545 bytes, limit_reached; 5 positive-delta samples of 6, all command rc=2; max +19.7 MiB, +128 MiB margin = 147.7 MiB",
    }
    row = (
        f"| `{path}` | `unknown` | "
        "`compute-node shared-service cgroup delta sampling at commit 04d85f93 "
        "(not runbook 7.0 isolated-scope evidence; non-certifying); default --json "
        "argv, 25 of 1045 files read, 4728545 bytes, limit_reached; 5 positive-delta "
        "samples of 6, all command rc=2; max +19.7 MiB, +128 MiB margin = 147.7 MiB` |"
    )
    try:
        def add_entry(document):
            entries = dict(document["entries"])
            entries[path] = entry
            document["entries"] = {
                key: entries[key] for key in sorted(entries)
            }

        _rewrite_registry(root, add_entry)
        detail = (
            "runbook §7.0 投影表が registry と集合完全一致しない — "
            "registry_only=[('tools/claude_session_ledger.py', 'unknown', "
            "'compute-node shared-service cgroup delta sampling at commit 04d85f93 "
            "(not runbook 7.0 isolated-scope evidence; non-certifying); default "
            "--json argv, 25 of 1045 files read, 4728545 bytes, limit_reached; 5 "
            "positive-delta samples of 6, all command rc=2; max +19.7 MiB, +128 "
            "MiB margin = 147.7 MiB')], runbook_only=[]"
        )
        _assert_admission_exact(root, detail)

        rel = "docs/pegasus-runbook.md"
        runbook = _read(root, rel)
        first_row = (
            "| `tools/pegasus/collect_receipt.py` | `unknown` | "
            "`unmeasured synthetic input` |"
        )
        assert runbook.count(first_row) == 1
        _write(root, rel, runbook.replace(first_row, row + "\n" + first_row, 1))
        _assert_admission_exact(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_non_pegasus_runbook_measurement_is_absent_from_measured_table():
    root = _build_min_repo()
    path = "tools/claude_session_ledger.py"
    entry = {
        "class": "unknown",
        "reason": "synthetic non-Pegasus measurement",
        "primary_gate": "synthetic deny",
        "evidence": "runbook §7.0 実測",
    }
    row = f"| `{path}` | `unknown` | `runbook §7.0 実測` |"
    try:
        def add_entry(document):
            entries = dict(document["entries"])
            entries[path] = entry
            document["entries"] = {
                key: entries[key] for key in sorted(entries)
            }

        _rewrite_registry(root, add_entry)
        rel = "docs/pegasus-runbook.md"
        runbook = _read(root, rel)
        first_row = (
            "| `tools/pegasus/collect_receipt.py` | `unknown` | "
            "`unmeasured synthetic input` |"
        )
        assert runbook.count(first_row) == 1
        _write(root, rel, runbook.replace(first_row, row + "\n" + first_row, 1))
        _assert_admission_exact(
            root,
            "runbook §7.0 実測表の path 集合が registry と不一致 — "
            "registry=['tools/claude_session_ledger.py', "
            "'tools/pegasus/fetch_third_party.py'], "
            "runbook=['tools/pegasus/fetch_third_party.py']",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_registry_mutations_have_exact_attributed_finding_sets():
    cases = {
        "class": (
            lambda document: document["entries"][
                "tools/pegasus/collect_receipt.py"
            ].__setitem__("class", "local-ok"),
            {
                "runbook §7.0 投影表が registry と集合完全一致しない — "
                "registry_only=[('tools/pegasus/collect_receipt.py', 'local-ok', "
                "'unmeasured synthetic input')], "
                "runbook_only=[('tools/pegasus/collect_receipt.py', 'unknown', "
                "'unmeasured synthetic input')]",
                "unknown 表の admission 説明が registry と不整合 — "
                "tools/pegasus/collect_receipt.py",
                "Pegasus README 宣言表の class が registry と不一致 — "
                "tools/pegasus/collect_receipt.py",
            },
        ),
        "evidence": (
            lambda document: document["entries"][
                "tools/pegasus/submit_certify.sh"
            ].__setitem__("evidence", "runbook §7.0 実測"),
            {
                "runbook §7.0 投影表が registry と集合完全一致しない — "
                "registry_only=[('tools/pegasus/submit_certify.sh', 'local-ok', "
                "'runbook §7.0 実測')], "
                "runbook_only=[('tools/pegasus/submit_certify.sh', 'local-ok', "
                "'legacy-admitted (未実測)')]",
                "unknown 表の admission 説明が registry と不整合 — "
                "tools/pegasus/submit_certify.sh",
                "runbook §7.0 実測表の path 集合が registry と不一致 — "
                "registry=['tools/pegasus/fetch_third_party.py', "
                "'tools/pegasus/submit_certify.sh'], "
                "runbook=['tools/pegasus/fetch_third_party.py']",
            },
        ),
    }
    for label, (mutate, expected) in cases.items():
        root = _build_min_repo()
        try:
            _rewrite_registry(root, mutate)
            _assert_admission_exact(root, *sorted(expected))
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_unknown_table_rejects_non_unknown_and_incomplete_legacy_rows():
    collect = "| `tools/pegasus/collect_receipt.py` | 入力が未計測 |"
    legacy = (
        "| `tools/pegasus/submit_certify.sh` | registry 上は `local-ok` / "
        "`legacy-admitted (未実測)` として grandfather 済み |"
    )
    cases = {
        "dispatch required": lambda text: text.replace(
            collect,
            "| `tools/pegasus/smoke_probe.sh` | 入力が未計測 |",
            1,
        ),
        "missing local-ok": lambda text: text.replace(
            legacy,
            legacy.replace("`local-ok` / ", ""),
            1,
        ),
        "missing exact evidence": lambda text: text.replace(
            legacy,
            legacy.replace("`legacy-admitted (未実測)`", "legacy entry"),
            1,
        ),
    }
    for label, mutate in cases.items():
        root = _build_min_repo()
        try:
            rel = "docs/pegasus-runbook.md"
            _write(root, rel, mutate(_read(root, rel)))
            _assert_admission_count(root, 1, "unknown 表")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_unknown_table_requires_grandfather_warning_golden():
    row = (
        "| `tools/pegasus/submit_silo_ladder_rung1.sh` | registry 上は "
        "`local-ok` / `legacy-admitted (未実測)` として grandfather 済み |"
    )
    cases = {
        "deleted": (
            lambda text: text.replace(row + "\n", "", 1),
            "unknown 表に必須 grandfather 警告がない — "
            "missing=['tools/pegasus/submit_silo_ladder_rung1.sh']",
        ),
        "empty": (
            lambda text: re.sub(
                r"(?ms)(\| 経路 \| なぜ `unknown` か \|\n\|---\|---\|)\n.*?"
                r"(?=\n\n\| 経路 \| 観測ピーク)",
                r"\1",
                text,
                count=1,
            ),
            "unknown 表に必須 grandfather 警告がない — "
            "missing=['tools/pegasus/submit_silo_ladder_rung1.sh']",
        ),
        "double slash": (
            lambda text: text.replace(
                row,
                row.replace(
                    "tools/pegasus/submit_silo_ladder_rung1.sh",
                    "tools//pegasus/submit_silo_ladder_rung1.sh",
                ),
                1,
            ),
            "unknown 表に非 canonical Pegasus path がある — "
            "['tools//pegasus/submit_silo_ladder_rung1.sh']",
        ),
        "case change": (
            lambda text: text.replace(
                row,
                row.replace(
                    "tools/pegasus/submit_silo_ladder_rung1.sh",
                    "tools/Pegasus/submit_silo_ladder_rung1.sh",
                ),
                1,
            ),
            "unknown 表に非 canonical Pegasus path がある — "
            "['tools/Pegasus/submit_silo_ladder_rung1.sh']",
        ),
        "fullwidth slash": (
            lambda text: text.replace(
                row,
                row.replace(
                    "tools/pegasus/submit_silo_ladder_rung1.sh",
                    "tools／pegasus／submit_silo_ladder_rung1.sh",
                ),
                1,
            ),
            "unknown 表に非 canonical Pegasus path がある — "
            "['tools／pegasus／submit_silo_ladder_rung1.sh']",
        ),
    }
    for label, (mutate, expected) in cases.items():
        root = _build_min_repo()
        try:
            rel = "docs/pegasus-runbook.md"
            _write(root, rel, mutate(_read(root, rel)))
            _assert_admission_exact(root, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_measured_table_requires_exact_registry_path_set():
    first = "| `tools/pegasus/fetch_third_party.py fetch` | 10 MiB | 138 MiB | local-ok |"
    inherited = "| 同 `fetch` | 9 MiB | 137 MiB | local-ok |"
    cases = {
        "missing": (
            lambda text: text.replace(first + "\n" + inherited, "", 1),
            "runbook §7.0 実測表の path 集合が registry と不一致 — "
            "registry=['tools/pegasus/fetch_third_party.py'], runbook=[]",
        ),
        "extra": (
            lambda text: text.replace(
                inherited,
                inherited + "\n| `tools/pegasus/smoke_probe.sh run` | 1 MiB | 129 MiB | local-ok |",
                1,
            ),
            "runbook §7.0 実測表の path 集合が registry と不一致 — "
            "registry=['tools/pegasus/fetch_third_party.py'], "
            "runbook=['tools/pegasus/fetch_third_party.py', 'tools/pegasus/smoke_probe.sh']",
        ),
        "non local classification": (
            lambda text: text.replace(
                first,
                first.replace("local-ok", "unknown"),
                1,
            ),
            "runbook §7.0 実測表に非 local-ok 行がある",
        ),
    }
    for label, (mutate, expected) in cases.items():
        root = _build_min_repo()
        try:
            rel = "docs/pegasus-runbook.md"
            _write(root, rel, mutate(_read(root, rel)))
            _assert_admission_exact(root, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_runbook_orphan_pipe_row_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        text = _read(root, rel).replace(
            "\n### 7.1 synthetic next section",
            "\n\n| orphan row |\n\n### 7.1 synthetic next section",
            1,
        )
        _write(root, rel, text)
        _assert_admission_count(root, 1, "orphan row")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_readme_declaration_and_fenced_target_mutations_are_rejected():
    collect = "| `tools/pegasus/collect_receipt.py` | `compute-only` | `unknown` |"
    fetch = "| `tools/pegasus/fetch_third_party.py` | `login-direct` | `local-ok` |"
    smoke = "| `tools/pegasus/smoke_probe.sh` | `qsub-job-body` | `dispatch-required` |"
    submit = "| `tools/pegasus/submit_certify.sh` | `login-direct` | `local-ok` |"
    cases = {
        "coverage deletion": lambda text: text.replace(collect + "\n", "", 1),
        "login direct non-local": lambda text: text.replace(
            smoke,
            smoke.replace("`qsub-job-body`", "`login-direct`"),
            1,
        ),
        "qsub local": lambda text: text.replace(
            submit,
            submit.replace("`login-direct`", "`qsub-job-body`"),
            1,
        ),
        "unregistered path": lambda text: text.replace(
            fetch,
            fetch + "\n| `tools/pegasus/unregistered.py` | `compute-only` | `unknown` |",
            1,
        ),
        "variable target": lambda text: text.replace(
            "qsub tools/pegasus/smoke_probe.sh",
            "qsub tools/pegasus/smoke_probe.sh\nqsub \"$P/pegasus/smoke_probe.sh\"",
            1,
        ),
        "invalid site": lambda text: text.replace(
            collect,
            collect.replace("`compute-only`", "`somewhere`"),
            1,
        ),
        "class mismatch": lambda text: text.replace(
            collect,
            collect.replace("`unknown`", "`dispatch-required`"),
            1,
        ),
        "duplicate": lambda text: text.replace(fetch, fetch + "\n" + fetch, 1),
        "malformed": lambda text: text.replace(fetch, "| `tools/pegasus/fetch_third_party.py` | `login-direct` |", 1),
        "hidden": lambda text: text.replace(
            "| path | 手順上の実行 site | registry class |\n|---|---|---|",
            "```text\n| path | 手順上の実行 site | registry class |\n|---|---|---|",
            1,
        ).replace(submit, submit + "\n```", 1),
    }
    for label, mutate in cases.items():
        root = _build_min_repo()
        try:
            rel = "tools/pegasus/README.md"
            _write(root, rel, mutate(_read(root, rel)))
            _assert_admission_count(root, 1)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_readme_site_tags_and_three_site_values_are_exact():
    qsub_tag = "# admission-site: qsub-job-body"
    qsub_command = "qsub tools/pegasus/smoke_probe.sh"
    login_tag = "# admission-site: login-direct"
    collect_row = "| `tools/pegasus/collect_receipt.py` | `compute-only` | `unknown` |"
    smoke_row = "| `tools/pegasus/smoke_probe.sh` | `qsub-job-body` | `dispatch-required` |"
    cases = {
        "missing tag": (
            lambda text: text.replace(qsub_tag + "\n", "", 1),
            lambda line: (
                "Pegasus README の registry 実行体を含む fenced command に "
                f"admission-site tag がない — line={line}"
            ),
        ),
        "duplicate tag": (
            lambda text: text.replace(qsub_tag, qsub_tag + "\n" + qsub_tag, 1),
            lambda line: (
                "Pegasus README の fenced block に admission-site tag が重複 — "
                f"line={line}"
            ),
        ),
        "tag not first": (
            lambda text: text.replace(qsub_tag, "\n" + qsub_tag, 1),
            lambda line: (
                "Pegasus README の admission-site tag が fenced block の先頭行でない — "
                f"line={line}"
            ),
        ),
        "unknown tag": (
            lambda text: text.replace(qsub_tag, "# admission-site: nowhere", 1),
            lambda line: "Pegasus README の admission-site tag が閉集合外 — nowhere",
        ),
        "qsub path is not qsub argument": (
            lambda text: text.replace(qsub_command, qsub_command.replace("qsub", "bash"), 1),
            lambda line: (
                "Pegasus README の qsub-job-body 実行体が qsub 引数でない — "
                "tools/pegasus/smoke_probe.sh"
            ),
        ),
        "qsub declaration has no qsub argument": (
            lambda text: text.replace(qsub_command + "\n", "", 1),
            lambda line: (
                "Pegasus README の qsub-job-body 宣言集合が qsub 引数集合と不一致 — "
                "declaration=['tools/pegasus/smoke_probe.sh'], qsub=[]"
            ),
        ),
        "site swap": (
            lambda text: text.replace(
                collect_row,
                collect_row.replace("`compute-only`", "`qsub-job-body`"),
                1,
            ).replace(
                smoke_row,
                smoke_row.replace("`qsub-job-body`", "`compute-only`"),
                1,
            ),
            lambda line: (
                "Pegasus README の fenced command site が宣言表と不一致 — "
                "path=tools/pegasus/smoke_probe.sh, tag=qsub-job-body, "
                "declaration=compute-only"
            ),
        ),
        "compute path in login block": (
            lambda text: text.replace(
                login_tag,
                login_tag + "\npython3 tools/pegasus/collect_receipt.py",
                1,
            ),
            lambda line: (
                "Pegasus README の fenced command site が宣言表と不一致 — "
                "path=tools/pegasus/collect_receipt.py, tag=login-direct, "
                "declaration=compute-only"
            ),
        ),
    }
    for label, (mutate, expected_for_line) in cases.items():
        root = _build_min_repo()
        try:
            rel = "tools/pegasus/README.md"
            original = _read(root, rel)
            first_line = original[:original.index("```bash")].count("\n") + 2
            _write(root, rel, mutate(original))
            _assert_admission_exact(root, expected_for_line(first_line))
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_readme_rejects_empty_and_noncanonical_path_surfaces():
    table_rows = "\n".join(
        line
        for line in _SYNTHETIC_ADMISSION_README.splitlines()
        if line.startswith("| `tools/pegasus/")
    )
    command = "qsub tools/pegasus/smoke_probe.sh"
    cases = {
        "empty declaration": (
            lambda text: text.replace(table_rows + "\n", "", 1),
            "Pegasus README 宣言表が空である",
        ),
        "double slash": (
            lambda text: text.replace(command, command.replace("tools/", "tools//"), 1),
            "Pegasus README に非 canonical Pegasus path がある — "
            "['tools//pegasus/smoke_probe.sh']",
        ),
        "case change": (
            lambda text: text.replace(command, command.replace("pegasus", "Pegasus"), 1),
            "Pegasus README に非 canonical Pegasus path がある — "
            "['tools/Pegasus/smoke_probe.sh']",
        ),
        "fullwidth slash": (
            lambda text: text.replace(
                command,
                command.replace("tools/pegasus/", "tools／pegasus／"),
                1,
            ),
            "Pegasus README に非 canonical Pegasus path がある — "
            "['tools／pegasus／smoke_probe.sh']",
        ),
    }
    for label, (mutate, expected) in cases.items():
        root = _build_min_repo()
        try:
            rel = "tools/pegasus/README.md"
            _write(root, rel, mutate(_read(root, rel)))
            _assert_admission_exact(root, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_admission_readme_positive_command_and_negative_prose_controls_are_clean():
    root = _build_min_repo()
    try:
        text = _read(root, "tools/pegasus/README.md")
        assert "qsub tools/pegasus/smoke_probe.sh" in text
        assert "python3 tools/pegasus/fetch_third_party.py fetch" in text
        assert "login では拒否される" in text
        text += """

## 1. 非 admission の履歴資料

<!--
| path | 手順上の実行 site | registry class |
|---|---|---|
| historical | only | row |
-->

`tools/pegasus/smoke_probe.sh` は code span の参照であり command ではない。
https://example.invalid/tools/pegasus/smoke_probe.sh

```bash
tools/pegasus/collect_receipt.py はログインで実行してはならない
```

```text
過去事故の逐語: qsub tools/pegasus/smoke_probe.sh
```

```diff
- qsub tools/pegasus/smoke_probe.sh
+ python3 tools/pegasus/collect_receipt.py
```
"""
        _write(root, "tools/pegasus/README.md", text)
        runbook = _read(root, "docs/pegasus-runbook.md").replace(
            "### 7.1 synthetic next section",
            "<!--\n| unrelated | hidden |\n|---|---|\n| data | only |\n-->\n\n"
            "### 7.1 synthetic next section",
            1,
        )
        _write(root, "docs/pegasus-runbook.md", runbook)
        result = _assert_admission_count(root, 0)
        assert result.returncode == 0, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_admission_main_call_cannot_be_removed_without_evaporation_control_failing():
    root = _build_min_repo()
    try:
        checker = "tools/check_docs.py"
        source = _read(root, checker)
        call = "    _check_pegasus_admission_docs(findings)\n"
        assert source.count(call) == 1
        _write(root, checker, source.replace(call, "", 1))
        runbook = "docs/pegasus-runbook.md"
        text = _read(root, runbook).replace(
            "`unmeasured synthetic input`",
            "`changed evidence`",
            1,
        )
        _write(root, runbook, text)
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
        assert _admission_findings(result) == []
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_main_rejects_schema_violation():
    """N19: main() の spool guard 呼出しを消す変異を schema 違反で殺す。"""

    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/spool/worklog/2026-08-02-wave-1.md",
            "---\n"
            "schema: broken-schema\n"
            "ledger: worklog\n"
            "authored: 2026-08-02\n"
            "wave: wave\n"
            "seq: 1\n"
            "title: synthetic\n"
            "---\n"
            "## 本文\n\nbody\n\n## 次の一手差分\n",
        )
        res = _assert_violation(root, "spool schema", "broken-schema")
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_import_failure_is_finding_without_traceback():
    """spool_fold import 失敗を握り潰さず fail-closed finding にする。"""

    root = _build_min_repo()
    try:
        os.remove(os.path.join(root, "tools", "spool_fold.py"))
        res = _assert_violation(root, "spool schema guard の import 失敗")
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_n20_spool_guard_rejects_active_transaction_in_git_repo():
    """N20: 実 Git worktree の transaction state 残存を必ず finding にする。"""

    root = _build_min_repo()
    try:
        subprocess.run(
            ["git", "-C", root, "init", "-q"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        resolved = subprocess.run(
            ["git", "-C", root, "rev-parse", "--git-path", "izanagi-spool-fold-state.json"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        state_path = resolved if os.path.isabs(resolved) else os.path.join(root, resolved)
        _write_bytes(root, os.path.relpath(state_path, root), b"{}\n")
        _assert_violation(root, "spool transaction-active", "fold transaction が active")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_accepts_only_explicit_exact_complete_active_transaction():
    """M08: active state の宣言省略・ID 違いを拒否し exact ID だけ受理する。"""

    root = _build_min_repo()
    try:
        subprocess.run(
            ["git", "-C", root, "init", "-q"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        subprocess.run(
            ["git", "-C", root, "config", "user.name", "Fixture"], check=True,
        )
        subprocess.run(
            ["git", "-C", root, "config", "user.email", "fixture@example.invalid"],
            check=True,
        )
        subprocess.run(["git", "-C", root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", root, "commit", "-qm", "base"], check=True)
        _write(
            root,
            "docs/spool/decisions/2026-08-02-wave-1.md",
            "---\n"
            "schema: izanagi-spool-v1\n"
            "ledger: decisions\n"
            "authored: 2026-08-02\n"
            "wave: wave\n"
            "seq: 1\n"
            "---\n"
            "## {{D:active-transaction}}. active transaction fixture\n\nbody\n",
        )
        subprocess.run(["git", "-C", root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", root, "commit", "-qm", "fragment"], check=True)

        source = os.path.join(root, "tools", "spool_fold.py")
        spec = importlib.util.spec_from_file_location("_active_spool_fixture", source)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
            plan = module.plan_fold(root, fold_date="2026-08-02")
            module.apply_fold(root, plan)
        finally:
            sys.modules.pop(spec.name, None)

        strict = _run_check(root)
        wrong = _run_check(root, "--expect-active-transaction", "0" * 64)
        exact = _run_check(
            root,
            "--expect-active-transaction",
            plan.transaction_id,
        )
        assert strict.returncode == 1
        assert "spool transaction-active" in strict.stdout
        assert wrong.returncode == 1
        assert "active transaction ID" in wrong.stdout
        assert exact.returncode == 0, exact.stdout + exact.stderr
        assert "違反なし" in exact.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_git_marker_with_broken_rev_parse_fails_closed():
    """`.git` があるのに admin path を解決できない repo 候補は非 Git 扱いしない。"""

    root = _build_min_repo()
    try:
        _write(root, ".git", "gitdir: missing-admin-dir\n")
        _assert_violation(root, "spool transaction-state", "Git admin path を解決できない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_preservation_rule_still_rejects_implicit_drop():
    """N21: 既存 D70 保存則を弱める変異を active ID の暗黙脱落で殺す。"""

    root = _build_min_repo()
    try:
        worklog = _read(root, "docs/worklog.md")
        _write(
            root,
            "docs/worklog.md",
            worklog.replace("- [T-001] consumed\n\n", "", 1),
        )
        _assert_violation(root, "次の一手 ID [T-001]", "見送り台帳にもない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_raised_rulings_budget_still_rejects_new_limit():
    """N22: rulings の引上げ後予算を 1 byte 超える入力で gate 生存を固定する。"""

    assert check_docs.COMMAND_LIMITS[".claude/commands/rulings.md"].max_bytes == 5_623

    root = _build_min_repo()
    try:
        _pad_to_bytes(root, ".claude/commands/rulings.md", 5_624)
        _assert_violation(root, ".claude/commands/rulings.md", "予算 5623 bytes")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_command_budget_literal_is_exact():
    """入口上限・現物・plus-one 拒否を独立 literal で固定する。"""

    rel = ".claude/commands/dev-wave.md"
    assert check_docs.COMMAND_LIMITS[rel] == check_docs.TextLimit(9_520, 140)
    assert len(_read(_REPO, rel).encode("utf-8")) == 9_519

    root = _build_min_repo()
    try:
        _pad_to_bytes(root, rel, 9_521)
        result = _run_check(root)
        assert result.returncode == 1, result.stdout
        assert f"{rel}: 9521 bytes > 予算 9520 bytes" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_next_tasks_command_budget_literal_is_exact():
    """next-tasks の入口上限・現物・plus-one 拒否を独立 literal で固定する。"""

    rel = ".claude/commands/next-tasks.md"
    assert check_docs.COMMAND_LIMITS[rel] == check_docs.TextLimit(27_100, 100)
    assert len(_read(_REPO, rel).encode("utf-8")) == 27_060

    root = _build_min_repo()
    try:
        _pad_to_bytes(root, rel, 27_101)
        result = _run_check(root)
        assert result.returncode == 1, result.stdout
        assert f"{rel}: 27101 bytes > 予算 27100 bytes" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_empty_layout_is_clean():
    """pending 0 件の正規 spool layout は check_docs を塞がない。"""

    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_valid_pending_fragment_is_clean():
    """正しい pending fragment の存在自体は finding にしない。"""

    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/spool/decisions/2026-08-02-wave-1.md",
            "---\n"
            "schema: izanagi-spool-v1\n"
            "ledger: decisions\n"
            "authored: 2026-08-02\n"
            "wave: wave\n"
            "seq: 1\n"
            "---\n"
            "## {{D:synthetic-decision}}. synthetic decision\n\nbody\n",
        )
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_reports_failure_supersede_issue():
    """supersede の validate issue を check_docs main の spool finding へ伝播する。"""

    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/spool/failures/2026-08-10-wave-1.md",
            "---\n"
            "schema: izanagi-spool-v1\n"
            "ledger: failures\n"
            "authored: 2026-08-10\n"
            "wave: wave\n"
            "seq: 1\n"
            "---\n"
            "## supersede 追記\n\n"
            "- F1 **supersede: 2026-13-45** — invalid calendar date\n",
        )
        result = _assert_violation(
            root,
            "spool failure-supersede-shape",
            "supersede 追記 item の shape が不正",
        )
        assert "Traceback" not in result.stdout + result.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_unresolved_reference_propagates_to_main():
    """未解決 spool 参照は main() の rc=1 へ伝播する。"""

    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/spool/decisions/2026-08-02-wave-1.md",
            "---\n"
            "schema: izanagi-spool-v1\n"
            "ledger: decisions\n"
            "authored: 2026-08-02\n"
            "wave: wave\n"
            "seq: 1\n"
            "---\n"
            "## {{D:synthetic-decision}}. {{T:missing-task}} remains\n\nbody\n",
        )
        _assert_violation(root, "spool symbol-undefined", "{{T:missing-task}}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_missing_layout_is_finding():
    """docs/spool 自体の不在を黙って skip しない。"""

    root = _build_min_repo()
    try:
        shutil.rmtree(os.path.join(root, "docs", "spool"))
        _assert_violation(root, "docs/spool:1: spool spool-layout")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_symlink_and_unexpected_members_fail_closed():
    """spool 内の symlink・想定外 member を受理せず、finding 順も固定する。"""

    root = _build_min_repo()
    try:
        folded = os.path.join(root, "docs", "spool", "FOLDED.md")
        os.remove(folded)
        os.symlink("README.md", folded)
        _assert_violation(root, "spool regular-file", "symlink/非 regular file は不可")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        _write(root, "docs/spool/z-extra.md", "z\n")
        _write(root, "docs/spool/a-extra.md", "a\n")
        res = _assert_violation(root, "spool-member", "a-extra.md", "z-extra.md")
        assert res.stdout.index("a-extra.md") < res.stdout.index("z-extra.md")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_guard_unexpected_validator_exception_is_finding():
    """validator の予期しない例外も traceback を漏らさず fail-closed にする。"""

    root = _build_min_repo()
    try:
        _write(
            root,
            "tools/spool_fold.py",
            "def validate_spool_tree(repo):\n"
            "    raise RuntimeError('synthetic validator crash')\n",
        )
        res = _assert_violation(
            root,
            "spool schema guard の実行失敗",
            "RuntimeError: synthetic validator crash",
        )
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_tree_is_excluded_from_all_legacy_doc_scans():
    """docs/spool/** は LIVING/placeholder/archive/handoff scan の対象外に保つ。"""

    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/spool/README.md",
            "# spool legacy-scan bait\n\n"
            "docs/README.md:999\n"
            "現在は Phase 999\n"
            "<反映>\n",
        )
        _write(
            root,
            "docs/spool/FOLDED.md",
            "# folded legacy-scan bait\n\n"
            "handoff 状態 header は意図的に置かない。\n",
        )
        _write(
            root,
            "docs/spool/worklog/README.md",
            "# archive scan bait\n\n## archive 形式でない H2\n",
        )
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "違反なし" in res.stdout
        assert "件の警告" not in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_layer_budget_contract_is_literal():
    assert not hasattr(check_docs, "REFERENCE_LIMITS")
    assert not hasattr(check_docs, "DEV_WAVE_AGGREGATE_BYTES")
    assert check_docs.DEV_WAVE_REFERENCE_FILES == {
        "docs/dev-wave/core.md",
        "docs/dev-wave/workers.md",
        "docs/dev-wave/mutation.md",
        "docs/dev-wave/operations.md",
    }
    assert check_docs.DEV_WAVE_L1_BYTES_MAX == 10_625
    assert check_docs.DEV_WAVE_L1_5_BYTES_MAX == 9_788
    assert check_docs.DEV_WAVE_L2_SECTION_BYTES_MAX == 1_000
    assert check_docs.DEV_WAVE_STAGE_DISPATCH_LEGEND == (
        "種別は U=無条件、C=条件 dispatch 成立時。"
    )
    assert check_docs.DEV_WAVE_STAGE_DISPATCH_HEADER == (
        "| 入る直前 | 種別 | 必ず読む節 |"
    )
    assert check_docs.DEV_WAVE_CONDITION_DISPATCH_HEADER == (
        "| # | 発火条件 | 読む節 |"
    )
    assert check_docs.NORMATIVE_DISPATCH_ALLOWLIST == {
        *check_docs.DEV_WAVE_REFERENCE_FILES,
        "docs/skill-self-improvement.md",
    }
    assert check_docs.DEV_WAVE_L1_STAGE_KEYS == {
        "wave 開始", "段 1", "段 4", "段 7", "段 8 preflight", "段 9",
    }
    assert check_docs.DEV_WAVE_L1_5_STAGE_KEYS == {
        "段 2 preflight", "段 3 preflight", "段 5", "段 6",
    }

    unconditional = check_docs.STAGE_UNCONDITIONAL_DISPATCH_CONTRACT
    l1 = set().union(*(
        unconditional.get(key, set()) for key in check_docs.DEV_WAVE_L1_STAGE_KEYS
    ))
    l1_5 = set().union(*(
        unconditional.get(key, set()) for key in check_docs.DEV_WAVE_L1_5_STAGE_KEYS
    )) - l1
    registered = {
        (path, section)
        for path, sections in check_docs.REQUIRED_REFERENCE_SECTIONS.items()
        for section in sections
    }
    l1 &= registered
    l1_5 &= registered
    l2 = registered - l1 - l1_5
    assert l1 == {
        *(('docs/dev-wave/core.md', section) for section in {
            'DW-C00', 'DW-STOP', 'DW-S01', 'DW-G01', 'DW-G02', 'DW-G03',
            'DW-G04', 'DW-G05', 'DW-S04', 'DW-S07', 'DW-S08', 'DW-S09',
            'DW-CTX',
        }),
        ('docs/dev-wave/mutation.md', 'DW-M01'),
        ('docs/dev-wave/operations.md', 'DW-O23'),
    }
    assert l1_5 == {
        *(('docs/dev-wave/workers.md', f'DW-S0{i}') for i in (2, 3)),
        *(('docs/dev-wave/workers.md', f'DW-S0{i}-{suffix}')
          for i in (5, 6) for suffix in ('A', 'B', 'C')),
        *(('docs/dev-wave/mutation.md', f'DW-M{i:02d}')
          for i in (2, 3, 4, 5, 6, 8)),
        *(('docs/dev-wave/operations.md', section)
          for section in ('DW-O01', 'DW-O02', 'DW-O05')),
    }
    assert l2 == {
        ('docs/dev-wave/core.md', 'DW-C01'),
        ('docs/dev-wave/mutation.md', 'DW-M07'),
        *(('docs/dev-wave/operations.md', section) for section in (
            'DW-O03', 'DW-O04', 'DW-O06', 'DW-O08', 'DW-O09', 'DW-O10',
            'DW-O11', 'DW-O12', 'DW-O13', 'DW-O14', 'DW-O16', 'DW-O17',
            'DW-O18', 'DW-O19', 'DW-O20', 'DW-O25', 'DW-O26', 'DW-O27', 'DW-O28',
        )),
    }


def _dispatch_inventory_findings(
    result: subprocess.CompletedProcess,
) -> set[str]:
    return {
        finding
        for finding in _finding_set(result)
        if "dispatch inventory drift" in finding
    }


def _assert_tasks_source_mutation_rejected(suffix: str, needle: str) -> None:
    findings: list[str] = []
    inventory = check_docs._dispatch_inventory_from_source(
        _SYNTHETIC_DISPATCH_SOURCE + suffix,
        findings,
    )
    assert inventory is None
    assert len(findings) == 1, findings
    assert "TASKS 写像を静的に確定できない" in findings[0]
    assert needle in findings[0]


def test_dispatch_inventory_rejects_post_definition_assign():
    """定義後の ``TASKS = replacement`` 再束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected("\nTASKS = {}\n", "束縛/削除")


def test_dispatch_inventory_rejects_post_definition_annassign():
    """定義後の注釈付き ``TASKS: dict = ...`` 再束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected("\nTASKS: dict = {}\n", "束縛/削除")


def test_dispatch_inventory_rejects_post_definition_augassign():
    """定義後の ``TASKS |= replacement`` 変更変異を殺す。"""
    _assert_tasks_source_mutation_rejected("\nTASKS |= {}\n", "束縛/削除")


def test_dispatch_inventory_rejects_post_definition_subscript_assign():
    """定義後の ``TASKS[key] = spec`` 変更変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        '\nTASKS["extra"] = _TaskSpec(child_script=("tools", "extra.py"))\n',
        "要素/属性への書込み",
    )


def test_dispatch_inventory_rejects_post_definition_del():
    """定義後の ``del TASKS[key]`` 削除変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        '\ndel TASKS["tests"]\n',
        "要素/属性への書込み",
    )


def test_dispatch_inventory_rejects_post_definition_update():
    """定義後の ``TASKS.update(...)`` 変更変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        '\nTASKS.update({"extra": _TaskSpec(child_script=("tools", "extra.py"))})\n',
        "TASKS.update()",
    )


def test_dispatch_inventory_rejects_post_definition_pop():
    """定義後の ``TASKS.pop(...)`` 変更変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        '\nTASKS.pop("tests")\n',
        "TASKS.pop()",
    )


def test_dispatch_inventory_rejects_post_definition_for_binding():
    """定義後の ``for TASKS in ...`` 束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\nfor TASKS in ():\n    pass\n",
        "束縛/削除",
    )


def test_dispatch_inventory_rejects_post_definition_with_binding():
    """定義後の ``with ... as TASKS`` 束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\nwith context() as TASKS:\n    pass\n",
        "束縛/削除",
    )


def test_dispatch_inventory_rejects_post_definition_comprehension_binding():
    """定義後の comprehension target ``TASKS`` 束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\nshadow = [TASKS for TASKS in ()]\n",
        "束縛/削除",
    )


def test_dispatch_inventory_rejects_post_definition_import_binding():
    """定義後の import による ``TASKS`` 再束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\nfrom replacement import mapping as TASKS\n",
        "import による TASKS 再束縛",
    )


def test_dispatch_inventory_rejects_post_definition_globals_write():
    """定義後の ``globals()[\"TASKS\"] = ...`` 再束縛変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        '\nglobals()["TASKS"] = {}\n',
        "動的 namespace 経由の書込み",
    )


def test_dispatch_inventory_rejects_tasks_alias_subscript_write():
    """``alias = TASKS; alias[key] = spec`` alias 書込み変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\nalias = TASKS\n"
        'alias["tests"] = _TaskSpec(child_script=("tools", "extra.py"))\n',
        "TASKS の alias 束縛",
    )


def test_dispatch_inventory_rejects_tasks_container_unpack_alias():
    """container unpack 経由の TASKS alias 書込み変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\n(alias,) = (TASKS,)\n"
        'alias["extra"] = _TaskSpec(child_script=("tools", "extra.py"))\n',
        "TASKS の alias 束縛",
    )


def test_dispatch_inventory_rejects_tasks_alias_in_assignment_rhs_subtree():
    """RHS subtree に埋めた TASKS alias 書込み変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        '\nalias = {"registry": (TASKS,)}["registry"][0]\n'
        'alias["extra"] = _TaskSpec(child_script=("tools", "extra.py"))\n',
        "TASKS の alias 束縛",
    )


def test_dispatch_inventory_rejects_tasks_alias_through_list_comp():
    """ListComp の iterator から取り出した TASKS alias を拒否する。"""
    _assert_tasks_source_mutation_rejected(
        "\nalias = [value for value in (TASKS,)][0]\n"
        'alias["extra"] = _TaskSpec(child_script=("tools", "extra.py"))\n',
        "TASKS の alias 束縛",
    )


def test_dispatch_inventory_rejects_tasks_alias_through_set_comp():
    """SetComp の element closure に保持した TASKS alias を拒否する。"""
    _assert_tasks_source_mutation_rejected(
        "\nfactory = next(iter({(lambda: TASKS) for _ in (0,)}))\n"
        "alias = factory()\n"
        'alias["extra"] = _TaskSpec(child_script=("tools", "extra.py"))\n',
        "TASKS の alias 束縛",
    )


def test_dispatch_inventory_rejects_tasks_alias_through_dict_comp():
    """DictComp の value に保持した TASKS alias を拒否する。"""
    _assert_tasks_source_mutation_rejected(
        "\nalias = {key: value for key, value in ((0, TASKS),)}[0]\n"
        'alias["extra"] = _TaskSpec(child_script=("tools", "extra.py"))\n',
        "TASKS の alias 束縛",
    )


def test_dispatch_inventory_rejects_tasks_alias_through_generator_exp():
    """GeneratorExp の iterator から取り出した TASKS alias を拒否する。"""
    _assert_tasks_source_mutation_rejected(
        "\nalias = next(value for value in (TASKS,))\n"
        'alias["extra"] = _TaskSpec(child_script=("tools", "extra.py"))\n',
        "TASKS の alias 束縛",
    )


def test_dispatch_inventory_rejects_tasks_function_default_capture():
    """function default に捕捉した TASKS の後続変更変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\ndef add_extra(alias=TASKS):\n"
        '    alias["extra"] = _TaskSpec(child_script=("tools", "extra.py"))\n'
        "add_extra()\n",
        "TASKS の function default capture",
    )


def test_dispatch_inventory_rejects_dict_update_through_tasks_alias():
    """``dict.update(alias, ...)`` による TASKS alias 変更変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\nalias = TASKS\n"
        "dict.update(alias, {"
        '"extra": _TaskSpec(child_script=("tools", "extra.py"))})\n',
        "TASKS の alias 束縛",
    )


def test_dispatch_inventory_rejects_tasks_as_mutating_call_argument():
    """``dict.update(TASKS, ...)`` 実引数 escape 変異を殺す。"""
    _assert_tasks_source_mutation_rejected(
        "\ndict.update(TASKS, {"
        '"extra": _TaskSpec(child_script=("tools", "extra.py"))})\n',
        "TASKS の実引数渡し",
    )


def test_dispatch_inventory_accepts_real_dispatcher_tasks_reads():
    """添字・membership・``tuple(TASKS)`` を alias と誤認する変異を殺す。"""
    source = (check_docs.REPO / "tools/pegasus/dispatch_compute.py").read_text()
    findings: list[str] = []
    assert check_docs._dispatch_inventory_from_source(source, findings) == {
        "tests": "tools/run_tests.py",
        "provenance": "tools/check_ai_provenance.py",
        "mutation": "tools/mutation_worktree.py",
        "generic": "<argv>",
    }
    assert findings == []


def test_dispatch_inventory_accepts_literal_tasks_definition():
    """正規の literal TASKS 定義を過剰拒否する変異を殺す。"""
    findings: list[str] = []
    assert check_docs._dispatch_inventory_from_source(
        _SYNTHETIC_DISPATCH_SOURCE,
        findings,
    ) == {
        "tests": "tools/run_tests.py",
        "provenance": "tools/check_ai_provenance.py",
    }
    assert findings == []


def test_dispatch_inventory_raw_html_section_is_rejected():
    """§7.0 見出しと表を raw ``pre`` block 内へ移す変異を殺す。"""
    text = _SYNTHETIC_DISPATCH_RUNBOOK.replace(
        "### 7.0 判定基準はディレクトリではなくメモリ量\n",
        "<pre>\n### 7.0 判定基準はディレクトリではなくメモリ量\n",
        1,
    ).replace(
        "\n### 7.1 synthetic next section",
        "\n</pre>\n\n### 7.1 synthetic next section",
        1,
    )
    findings: list[str] = []
    assert check_docs._dispatch_inventory_from_runbook(text, findings) is None
    assert findings == [
        "tools/check_docs.py: dispatch inventory drift — "
        "docs/pegasus-runbook.md の `### 7.0` 節が 0 件"
    ]


def test_dispatch_inventory_wrong_parent_section_is_rejected():
    """§7.0 を無関係な親 ``## 8`` の配下へ移す変異を殺す。"""
    text = _SYNTHETIC_DISPATCH_RUNBOOK.replace(
        "### 7.0 判定基準はディレクトリではなくメモリ量",
        "## 8. unrelated\n\n### 7.0 判定基準はディレクトリではなくメモリ量",
        1,
    )
    findings: list[str] = []
    assert check_docs._dispatch_inventory_from_runbook(text, findings) is None
    assert findings == [
        "tools/check_docs.py: dispatch inventory drift — "
        "docs/pegasus-runbook.md の `### 7.0` が親 `## 7` の直下でない"
    ]


def test_dispatch_inventory_accepts_equivalent_markdown_spacing():
    """有効な見出し字下げと表セル空白を拒む過剰拒否変異を殺す。"""
    text = _SYNTHETIC_DISPATCH_RUNBOOK.replace(
        "## 7. synthetic execution policy",
        "  ## 7. synthetic execution policy",
        1,
    ).replace(
        "### 7.0 判定基準はディレクトリではなくメモリ量",
        "   ### 7.0　判定基準はディレクトリではなくメモリ量",
        1,
    ).replace(
        "| task | 子 script |",
        "|task      |子 script|",
        1,
    )
    findings: list[str] = []
    assert check_docs._dispatch_inventory_from_runbook(text, findings) == {
        "tests": "tools/run_tests.py",
        "provenance": "tools/check_ai_provenance.py",
    }
    assert findings == []


def test_dispatch_inventory_outer_pipe_less_added_row_is_rejected():
    """外周 pipe のない3行目を表終端として無視する変異を殺す。"""
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        text = _read(root, rel).replace(
            "| `provenance` | `tools/check_ai_provenance.py` |\n",
            "| `provenance` | `tools/check_ai_provenance.py` |\n"
            "`extra` | `tools/extra.py`\n",
            1,
        )
        _write(root, rel, text)
        result = _run_check(root)
        assert result.returncode == 1, result.stdout
        assert _dispatch_inventory_findings(result) == {
            "tools/check_docs.py: dispatch inventory drift — "
            "{task: child_script} が不一致 — TASKS_only=[], "
            "runbook_only=['extra'], child_script={}"
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_shared_top_level_items_are_unchanged_by_raw_html_prefix():
    """raw HTML block mask を共有トップレベル項目 scanner へ戻す変異を殺す。"""
    body = "- [T-001] visible item\n"
    prefix = "<x = >\n<x>\n"
    assert check_docs._top_level_ids(prefix + body) == check_docs._top_level_ids(body)


def test_shared_provenance_sections_are_unchanged_by_raw_html_prefix():
    """raw HTML block mask を共有 provenance scanner へ戻す変異を殺す。"""
    text = "## PR-A01 — visible\n\nbody\n"
    baseline = check_docs._visible_markdown_text(text)
    prefixed = check_docs._visible_markdown_text("<x = >\n<x>\n" + text)
    assert check_docs._reference_id_sections(prefixed, "PR-A01") == (
        check_docs._reference_id_sections(baseline, "PR-A01")
    )


def test_shared_condition_dispatch_is_unchanged_by_raw_html_prefix():
    """raw HTML block mask を共有 condition dispatch scanner へ戻す変異を殺す。"""
    text = """## 条件 dispatch

| key | 発火条件 | 読む節 |
|---|---|---|
| history | condition | `docs/provenance/audit.md`: `PR-A02` |
"""
    prefixed = "<x = >\n<x>\n" + text
    assert check_docs._condition_dispatch_table(prefixed, "条件 dispatch") == (
        check_docs._condition_dispatch_table(text, "条件 dispatch")
    )


def test_dispatch_inventory_current_mapping_has_no_findings():
    root = _build_min_repo()
    try:
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
        assert _dispatch_inventory_findings(result) == set()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_deleted_table_row_is_rejected():
    root = _build_min_repo()
    try:
        _rewrite_matching_lines(
            root,
            "docs/pegasus-runbook.md",
            lambda line: line.startswith("| `provenance` |"),
            lambda _line: "",
        )
        result = _assert_violation(root, "dispatch inventory drift")
        assert "TASKS_only=['provenance']" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_added_tasks_entry_is_rejected():
    root = _build_min_repo()
    try:
        rel = "tools/pegasus/dispatch_compute.py"
        source = _read(root, rel)
        _write(
            root,
            rel,
            source.replace(
                "}\n",
                '    "extra": _TaskSpec(child_script=("tools", "extra.py")),\n}\n',
                1,
            ),
        )
        result = _assert_violation(root, "dispatch inventory drift")
        assert "TASKS_only=['extra']" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_child_script_change_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                "`tools/run_tests.py`", "`tools/other_tests.py`", 1
            ),
        )
        result = _assert_violation(root, "dispatch inventory drift")
        assert "child_script={'tests':" in result.stdout
        assert "tools/other_tests.py" in result.stdout
        assert "tools/run_tests.py" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_missing_table_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                "| task | 子 script |", "| command | implementation |", 1
            ),
        )
        result = _assert_violation(root, "dispatch inventory drift")
        assert "exact task 表 header が 0 件" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_empty_table_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        text = _read(root, rel)
        text = re.sub(
            r"^\| `(?:tests|provenance)` \|.*\n",
            "",
            text,
            flags=re.MULTILINE,
        )
        _write(root, rel, text)
        result = _assert_violation(root, "dispatch inventory drift")
        assert "exact task 表が 0 行" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_missing_section_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        _write(
            root,
            rel,
            _read(root, rel).replace("### 7.0 ", "### 6.9 ", 1),
        )
        result = _assert_violation(root, "dispatch inventory drift")
        assert "`### 7.0` 節が 0 件" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_duplicate_task_row_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        duplicate = "| `tests` | `tools/run_tests.py` |\n"
        _write(
            root,
            rel,
            _read(root, rel).replace(duplicate, duplicate + duplicate, 1),
        )
        result = _assert_violation(root, "dispatch inventory drift")
        assert "task 行が重複 — ['tests']" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dispatch_inventory_ignores_table_outside_7_0_section():
    root = _build_min_repo()
    try:
        rel = "docs/pegasus-runbook.md"
        decoy = """## unrelated

| task | 子 script |
|---|---|
| `decoy` | `tools/decoy.py` |

"""
        _write(root, rel, decoy + _read(root, rel))
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
        assert _dispatch_inventory_findings(result) == set()
    finally:
        shutil.rmtree(root, ignore_errors=True)


_TEST_DEV_WAVE_LAYERS = {
    "L1": {
        *(('docs/dev-wave/core.md', section) for section in {
            'DW-C00', 'DW-STOP', 'DW-S01', 'DW-G01', 'DW-G02', 'DW-G03',
            'DW-G04', 'DW-G05', 'DW-S04', 'DW-S07', 'DW-S08', 'DW-S09',
            'DW-CTX',
        }),
        ('docs/dev-wave/mutation.md', 'DW-M01'),
        ('docs/dev-wave/operations.md', 'DW-O23'),
    },
    "L1.5": {
        *(('docs/dev-wave/workers.md', f'DW-S0{i}') for i in (2, 3)),
        *(('docs/dev-wave/workers.md', f'DW-S0{i}-{suffix}')
          for i in (5, 6) for suffix in ('A', 'B', 'C')),
        *(('docs/dev-wave/mutation.md', f'DW-M{i:02d}')
          for i in (2, 3, 4, 5, 6, 8)),
        *(('docs/dev-wave/operations.md', section)
          for section in ('DW-O01', 'DW-O02', 'DW-O05')),
    },
    "L2": {
        ('docs/dev-wave/core.md', 'DW-C01'),
        ('docs/dev-wave/mutation.md', 'DW-M07'),
        *(('docs/dev-wave/operations.md', section) for section in (
            'DW-O03', 'DW-O04', 'DW-O06', 'DW-O08', 'DW-O09', 'DW-O10',
            'DW-O11', 'DW-O12', 'DW-O13', 'DW-O14', 'DW-O16', 'DW-O17',
            'DW-O18', 'DW-O19', 'DW-O20', 'DW-O25', 'DW-O26', 'DW-O27', 'DW-O28',
        )),
    },
}
_OLD_DEV_WAVE_FILE_CAPS = {
    "docs/dev-wave/core.md": 9_600,
    "docs/dev-wave/workers.md": 5_000,
    "docs/dev-wave/mutation.md": 3_750,
    "docs/dev-wave/operations.md": 8_400,
}


def _test_reference_slices(root: str, rel: str) -> tuple[int, dict[str, str]]:
    text = _read(root, rel)
    headings = list(re.finditer(r"^##\s+([^\s—]+).*\n", text, re.MULTILINE))
    assert headings
    slices = {
        heading.group(1): text[
            heading.start():headings[index + 1].start()
            if index + 1 < len(headings) else len(text)
        ]
        for index, heading in enumerate(headings)
    }
    return len(text[:headings[0].start()].encode()), slices


def _test_layer_bytes(root: str) -> dict[str, int]:
    totals = {"L1": 0, "L1.5": 0, "L2": 0}
    for rel in _OLD_DEV_WAVE_FILE_CAPS:
        preamble, slices = _test_reference_slices(root, rel)
        present = []
        for layer, pairs in _TEST_DEV_WAVE_LAYERS.items():
            sections = [section for path, section in pairs if path == rel]
            if sections:
                present.append(layer)
                totals[layer] += sum(
                    len(slices[section].encode()) for section in sections
                )
        totals[next(layer for layer in ("L1", "L1.5") if layer in present)] += preamble
    return totals


def _grow_test_section(
    root: str,
    rel: str,
    section: str,
    add_bytes: int,
    *,
    multibyte: bool = False,
) -> None:
    text = _read(root, rel)
    match = re.search(
        rf"^## {re.escape(section)}(?:\s+—[^\n]*)?\n.*?(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None and add_bytes >= 0
    if add_bytes == 0:
        return
    payload = ("x" * (add_bytes - 1)) + "\n"
    if multibyte:
        assert add_bytes >= 4
        payload = "あ" + ("x" * (add_bytes - 4)) + "\n"
    insertion = text.index("\n", match.start(), match.end()) + 1
    _write(root, rel, text[:insertion] + payload + text[insertion:])


def _pad_test_operations_l2_to_bytes(root: str, target_bytes: int) -> None:
    """L1/L1.5 と O20 を動かさず、operations の L2 節だけで全体を埋める。"""

    rel = "docs/dev-wave/operations.md"
    candidates = sorted(
        section
        for path, section in _TEST_DEV_WAVE_LAYERS["L2"]
        if path == rel and section != "DW-O20"
    )
    remaining = target_bytes - len(_read(root, rel).encode())
    assert remaining >= 0
    for section in candidates:
        _, slices = _test_reference_slices(root, rel)
        section_bytes = len(slices[section].encode())
        addition = min(remaining, 1_000 - section_bytes)
        _grow_test_section(root, rel, section, addition)
        remaining -= addition
        if remaining == 0:
            break
    assert remaining == 0
    assert len(_read(root, rel).encode()) == target_bytes
    _, slices = _test_reference_slices(root, rel)
    assert all(len(slices[section].encode()) <= 1_000 for section in candidates)


def _grow_test_layer_to(root: str, layer: str, target: int) -> None:
    current = _test_layer_bytes(root)[layer]
    remaining = target - current
    assert remaining >= 0
    candidates = {
        "L1": (
            ("docs/dev-wave/core.md", "DW-C00"),
            ("docs/dev-wave/mutation.md", "DW-M01"),
            ("docs/dev-wave/operations.md", "DW-O23"),
        ),
        "L1.5": (
            ("docs/dev-wave/workers.md", "DW-S02"),
            ("docs/dev-wave/mutation.md", "DW-M02"),
            ("docs/dev-wave/operations.md", "DW-O01"),
        ),
    }[layer]
    for rel, section in candidates:
        file_bytes = len(_read(root, rel).encode())
        addition = min(remaining, _OLD_DEV_WAVE_FILE_CAPS[rel] - file_bytes)
        _grow_test_section(root, rel, section, addition)
        remaining -= addition
        if remaining == 0:
            break
    assert remaining == 0


@pytest.mark.parametrize("target_layer", ["l1", "l1_5", "l2_section"])
def test_dev_wave_layer_budget_rejects_plus_one(target_layer):
    root = _build_min_repo()
    try:
        if target_layer == "l1":
            _grow_test_layer_to(root, "L1", 10_626)
        elif target_layer == "l1_5":
            _grow_test_layer_to(root, "L1.5", 9_789)
        else:
            _, slices = _test_reference_slices(
                root, "docs/dev-wave/operations.md"
            )
            add_bytes = 1_001 - len(slices["DW-O04"].encode())
            _grow_test_section(
                root,
                "docs/dev-wave/operations.md",
                "DW-O04",
                add_bytes,
                multibyte=True,
            )

        layers = _test_layer_bytes(root)
        expected = {
            "l1": ("L1", 10_626, "L1 unique footprint 10626 bytes"),
            "l1_5": ("L1.5", 9_789, "L1.5 unique footprint 9789 bytes"),
            "l2_section": ("L2", None, "L2 節 DW-O04 が 1001 bytes"),
        }[target_layer]
        if expected[1] is not None:
            assert layers[expected[0]] == expected[1]
        assert layers["L1" if target_layer != "l1" else "L1.5"] < (
            10_625 if target_layer != "l1" else 9_788
        )
        for rel, old_cap in _OLD_DEV_WAVE_FILE_CAPS.items():
            assert len(_read(root, rel).encode()) <= old_cap
        assert sum(len(_read(root, rel).encode()) for rel in _OLD_DEV_WAVE_FILE_CAPS) <= 25_200
        if target_layer == "l2_section":
            _, slices = _test_reference_slices(
                root, "docs/dev-wave/operations.md"
            )
            assert len(slices["DW-O04"].encode()) == 1_001
            assert len(slices["DW-O04"]) <= 1_000
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1
        assert expected[2] in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


_DEV_WAVE_CONDITIONALITY_CASES = (
    "stage-u-to-c",
    "stage-marker-missing",
    "stage-unknown-mode",
    "condition-always",
)
_DEV_WAVE_BARE_PATH_CASES = (
    "stage-reference",
    "condition-reference",
    "self-reference",
)
_DEV_WAVE_SLICING_CASES = (
    "fence",
    "html-comment",
    "raw-html",
    "malformed-heading",
)
_DEV_WAVE_SHARED_EDGE_CASES = ("dw-ctx", "dw-o04")


def _flat_reference_pairs(text: str) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for line in text.splitlines():
        if line.startswith("|"):
            pairs.update(check_docs._dispatch_pairs_from_line(line)[0])
    return pairs


@pytest.mark.parametrize("case", _DEV_WAVE_CONDITIONALITY_CASES)
def test_dev_wave_dispatch_conditionality_retyping_is_rejected(case):
    root = _build_min_repo()
    try:
        rel = ".claude/commands/dev-wave.md"
        before = _read(root, rel)
        if case.startswith("stage-"):
            replacement = {
                "stage-u-to-c": "|C|",
                "stage-marker-missing": "||",
                "stage-unknown-mode": "|X|",
            }[case]
            _rewrite_matching_lines(
                root,
                rel,
                lambda line: line.startswith("| wave 開始 |U|"),
                lambda line: line.replace("|U|", replacement, 1),
            )
        else:
            trigger = check_docs.CONDITION_TRIGGER_CONTRACT["01"]
            _rewrite_matching_lines(
                root,
                rel,
                lambda line: line.startswith("| 01 |"),
                lambda line: line.replace(trigger, "常に", 1),
            )
        after = _read(root, rel)
        assert _flat_reference_pairs(after) == _flat_reference_pairs(before)
        _assert_violation(root, "dispatch")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    if case == "stage-marker-missing":
        for replacement in ("|U/C|", "|"):
            row_root = _build_min_repo()
            try:
                rel = ".claude/commands/dev-wave.md"
                _rewrite_matching_lines(
                    row_root,
                    rel,
                    lambda line: line.startswith("| wave 開始 |U|"),
                    lambda line: line.replace("|U|", replacement, 1),
                )
                _assert_violation(row_root, "dispatch 表の構造が不一致")
            finally:
                shutil.rmtree(row_root, ignore_errors=True)
        for old, new, needle in (
            (
                check_docs.DEV_WAVE_STAGE_DISPATCH_LEGEND,
                "種別は U=毎回、C=条件 dispatch 成立時。",
                "段 dispatch 凡例",
            ),
            (
                check_docs.DEV_WAVE_STAGE_DISPATCH_HEADER,
                "| 入る直前 | mode | 必ず読む節 |",
                "段 dispatch header",
            ),
        ):
            pin_root = _build_min_repo()
            try:
                rel = ".claude/commands/dev-wave.md"
                text = _read(pin_root, rel)
                assert text.count(old) == 1
                _write(pin_root, rel, text.replace(old, new, 1))
                _assert_violation(pin_root, needle)
            finally:
                shutil.rmtree(pin_root, ignore_errors=True)


def test_dev_wave_dispatch_condition_token_smuggling_is_diagnostic_sensitivity():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/dev-wave.md"
        trigger = check_docs.CONDITION_TRIGGER_CONTRACT["01"]
        _rewrite_matching_lines(
            root,
            rel,
            lambda line: line.startswith("| 01 |"),
            lambda line: line.replace(
                trigger,
                trigger + " `docs/dev-wave/operations.md`: `DW-O01`",
                1,
            ),
        )
        _assert_violation(
            root,
            ".claude/commands/dev-wave.md: diagnostic sensitivity — "
            "条件 dispatch '01' の条件セルに reference token="
            "['`DW-O01`', '`docs/dev-wave/operations.md`']",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_condition_dispatch_header_mismatch_is_dedicated():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        header = check_docs.DEV_WAVE_CONDITION_DISPATCH_HEADER
        assert text.count(header) == 1
        _write(root, rel, text.replace(header, "| # | 条件 | 参照 |", 1))

        result = _run_check(root)
        assert result.returncode == 1, result.stdout
        assert _violation_count(result) == 1, result.stdout
        assert "条件 dispatch header が exact 1 件でない" in result.stdout
        assert "条件 dispatch '#' が契約と不一致" not in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("case", _DEV_WAVE_BARE_PATH_CASES)
def test_dev_wave_dispatch_rejects_bare_path(case):
    root = _build_min_repo()
    try:
        rel = ".claude/commands/dev-wave.md"
        if case == "stage-reference":
            _rewrite_matching_lines(
                root,
                rel,
                lambda line: line.startswith("| wave 開始 |U|"),
                lambda line: line.removesuffix(" |\n")
                + "; `docs/dev-wave/operations.md` 全文 |\n",
            )
        elif case == "condition-reference":
            _rewrite_matching_lines(
                root,
                rel,
                lambda line: line.startswith("| 01 |"),
                lambda line: line.removesuffix(" |\n")
                + "; `docs/dev-wave/core.md` 全文 |\n",
            )
        else:
            text = _read(root, rel)
            exact = "`docs/skill-self-improvement.md` の全節"
            assert text.count(exact) == 1
            _write(root, rel, text.replace(exact, "`docs/skill-self-improvement.md` 全文", 1))
        _assert_violation(root, "節へ束縛されない path")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    ("line_prefix", "old", "new"),
    (
        (
            "| 段 9 |U|",
            "`docs/dev-wave/operations.md`: `DW-O23`",
            "`docs/dev-wave/operations.md` 全文: `DW-O23`",
        ),
        (
            "| 01 |",
            "`docs/dev-wave/operations.md`: `DW-O01`",
            "`docs/dev-wave/operations.md` 全文: `DW-O01`",
        ),
    ),
)
def test_dev_wave_dispatch_rejects_unchecked_text_between_path_and_section(
    line_prefix, old, new
):
    root = _build_min_repo()
    try:
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith(line_prefix) and old in line,
            lambda line: line.replace(old, new, 1),
        )
        result = _assert_violation(root, "参照 cell grammar が不一致")
        assert _violation_count(result) == 1, result.stdout
        assert "cell 全文が参照 grammar に fullmatch しない" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_dispatch_accepts_self_all_sections():
    root = _build_min_repo()
    try:
        text = _read(root, ".claude/commands/dev-wave.md")
        assert text.count("`docs/skill-self-improvement.md` の全節") == 1
        dispatch = check_docs._dispatch_tables(text)
        assert dispatch is not None
        assert check_docs._SELF_SECTIONS <= dispatch.stage_unconditional[
            "段 8 preflight"
        ]
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_dispatch_rejects_backtick_in_annotation():
    cell = (
        "`docs/dev-wave/operations.md`: `DW-O01`（F23/F24; "
        "`docs/dev-wave/core.md`: `DW-C00`）"
    )
    errors = check_docs._dispatch_reference_cell_errors(cell)
    assert "cell 全文が参照 grammar に fullmatch しない" in errors[-1]


def test_dev_wave_dispatch_rejects_unquoted_raw_path():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/dev-wave.md"
        _rewrite_matching_lines(
            root,
            rel,
            lambda line: line.startswith("| wave 開始 |U|"),
            lambda line: line.removesuffix(" |\n")
            + "; docs/dev-wave/operations.md 全文 |\n",
        )
        result = _assert_violation(root, "参照 cell grammar が不一致")
        assert _violation_count(result) == 1, result.stdout
        assert "unquoted=['docs/dev-wave/operations.md']" in result.stdout
        assert "cell 全文が参照 grammar に fullmatch しない" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_dispatch_rejects_all_sections_on_non_self_path():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/dev-wave.md"
        anchor = (
            "| 段 9 |U| `docs/dev-wave/operations.md`: `DW-O23` |\n"
        )
        old = "`docs/dev-wave/operations.md`: `DW-O23`"
        new = "`docs/dev-wave/operations.md` の全節: `DW-O23`"
        _replace_fragment_in_exact_line(root, rel, anchor, old, new)
        result = _assert_violation(root, "参照 cell grammar が不一致")
        assert _violation_count(result) == 1, result.stdout
        assert "exact fragment 以外に の全節がある" in result.stdout
        assert "cell 全文が参照 grammar に fullmatch しない" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _replace_fragment_in_exact_line(
    root: str,
    rel: str,
    anchor: str,
    old: str,
    new: str,
) -> None:
    before = _read(root, rel).splitlines(keepends=True)
    assert before.count(anchor) == 1
    assert anchor.count(old) == 1
    replacement = anchor.replace(old, new, 1)
    assert replacement != anchor

    anchor_index = before.index(anchor)
    after = [replacement if line == anchor else line for line in before]
    changed_lines = [
        index
        for index, (old_line, new_line) in enumerate(zip(before, after))
        if old_line != new_line
    ]
    assert changed_lines == [anchor_index]
    assert after[anchor_index] == replacement
    _write(root, rel, "".join(after))
    assert _read(root, rel).splitlines(keepends=True) == after


def _replace_stage_one_range(root: str, replacement: str) -> None:
    rel = ".claude/commands/dev-wave.md"
    anchor = (
        "| 段 1 |U| `docs/dev-wave/core.md`: `DW-G01`, `DW-G02`, "
        "`DW-G03`, `DW-G04`, `DW-G05`, `DW-S01` |\n"
    )
    old = "`DW-G01`, `DW-G02`, `DW-G03`, `DW-G04`, `DW-G05`"
    _replace_fragment_in_exact_line(root, rel, anchor, old, replacement)


def test_dev_wave_dispatch_rejects_range_marker_inside_annotation():
    root = _build_min_repo()
    try:
        _replace_stage_one_range(
            root, "`DW-G01`（説明〜補足）, `DW-G05`"
        )
        result = _assert_violation(root, "段 dispatch '段 1' の U edge が契約と不一致")
        assert "DW-G02" in result.stdout and "DW-G04" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_dispatch_rejects_ascii_tilde_inside_url():
    root = _build_min_repo()
    try:
        _replace_stage_one_range(
            root, "`DW-G01`（https://x/~u）, `DW-G05`"
        )
        result = _assert_violation(root, "段 dispatch '段 1' の U edge が契約と不一致")
        assert "DW-G02" in result.stdout and "DW-G04" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_dispatch_accepts_exact_range_delimiter():
    cell = "`docs/dev-wave/operations.md`: `DW-O01`〜`DW-O06`"
    pairs, paths = check_docs._dispatch_pairs_from_line(cell)
    assert paths == {"docs/dev-wave/operations.md"}
    assert pairs == {
        ("docs/dev-wave/operations.md", f"DW-O{i:02d}")
        for i in range(1, 7)
    }

    root = _build_min_repo()
    try:
        assert cell in _read(root, ".claude/commands/dev-wave.md")
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_dispatch_accepts_comma_delimited_section_references():
    """同一 path の `, ` 区切り複数節が typed edge へ展開される。"""

    cell = (
        "`docs/dev-wave/operations.md`: `DW-O18`, `DW-O26`, `DW-O27`"
    )
    assert check_docs._dispatch_reference_cell_errors(cell) == ()
    pairs, paths = check_docs._dispatch_pairs_from_line(cell)
    assert paths == {"docs/dev-wave/operations.md"}
    assert pairs == {
        ("docs/dev-wave/operations.md", "DW-O18"),
        ("docs/dev-wave/operations.md", "DW-O26"),
        ("docs/dev-wave/operations.md", "DW-O27"),
    }

    root = _build_min_repo()
    try:
        command = _read(root, ".claude/commands/dev-wave.md")
        row = next(
            line for line in command.splitlines()
            if line.startswith("| 18 |")
        )
        assert cell in row
        dispatch = check_docs._dispatch_tables(command)
        assert dispatch is not None and not dispatch.structure_errors
        assert dispatch.conditions["18"] == pairs
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("case", _DEV_WAVE_SLICING_CASES)
def test_dev_wave_layer_slicing_ignores_fenced_heading(case):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/core.md"
        text = _read(root, rel)
        heading = "## DW-C00 — synthetic\n\nbody"
        assert text.count(heading) == 1
        if case == "malformed-heading":
            _write(root, rel, text.replace(
                "## DW-C00 — synthetic", "## DW-C00—", 1
            ))
            result = _assert_violation(root, "可視 H2 DW-C00 と byte slice が1:1でない")
            assert _violation_count(result) == 1, result.stdout
            return
        injected = {
            "fence": "\n\n```text\n## DW-X99 — hidden\n```",
            "html-comment": "\n\n<!--\n## DW-X99 — hidden\n-->",
            "raw-html": "\n\n<div>\n## DW-X99 — hidden\n</div>\n",
        }[case]
        _, before_slices, _ = check_docs._visible_reference_slices(text)
        _write(root, rel, text.replace(heading, heading + injected, 1))
        _, after_slices, _ = check_docs._visible_reference_slices(
            _read(root, rel)
        )
        assert set(after_slices) == set(before_slices)
        assert len(after_slices["DW-C00"]) == 1
        assert (
            len(after_slices["DW-C00"][0].encode())
            - len(before_slices["DW-C00"][0].encode())
            == len(injected.encode())
        )
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_layer_coverage_rejects_anonymous_visible_h2_only():
    """1:1 malformed-heading とは別入力・別理由で coverage 比較だけを赤にする。"""

    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/core.md"
        text = _read(root, rel)
        marker = "## DW-G01 — synthetic"
        assert text.count(marker) == 1
        anonymous = "## — anonymous\n\nunclassified body\n\n"
        _write(root, rel, text.replace(marker, anonymous + marker, 1))
        result = _assert_violation(
            root, "分類済み節 + preamble が実 bytes を被覆しない"
        )
        assert _violation_count(result) == 1, result.stdout
        assert "可視 H2" not in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("case", _DEV_WAVE_SHARED_EDGE_CASES)
def test_dev_wave_shared_reference_edges_are_typed(case):
    root = _build_min_repo()
    try:
        dispatch = check_docs._dispatch_tables(
            _read(root, ".claude/commands/dev-wave.md")
        )
        assert dispatch is not None and not dispatch.structure_errors
        target = {
            "dw-ctx": ("docs/dev-wave/core.md", "DW-CTX"),
            "dw-o04": ("docs/dev-wave/operations.md", "DW-O04"),
        }[case]
        actual = {
            (owner, mode)
            for owner, mode, path, section in dispatch.edges
            if (path, section) == target
        }
        expected = {
            "dw-ctx": {("段 9", "U"), ("条件 21", "C"), ("条件 22", "C")},
            "dw-o04": {("段 5", "C"), ("段 6", "C"), ("条件 04", "C")},
        }[case]
        assert actual == expected
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_l2_accepts_dw_o20_plus_154_bytes():
    """O20 +154 後に旧 operations cap 8,400 bytes を跨いでも受理する。"""

    root = _build_min_repo()
    try:
        _, before = _test_reference_slices(root, "docs/dev-wave/operations.md")
        _grow_test_section(
            root,
            "docs/dev-wave/operations.md",
            "DW-O20",
            489 - len(before["DW-O20"].encode()),
        )
        _, before = _test_reference_slices(root, "docs/dev-wave/operations.md")
        assert len(before["DW-O20"].encode()) == 489
        legacy_cap = _OLD_DEV_WAVE_FILE_CAPS["docs/dev-wave/operations.md"]
        _pad_test_operations_l2_to_bytes(root, legacy_cap - 154 + 1)
        before_file_bytes = len(
            _read(root, "docs/dev-wave/operations.md").encode()
        )
        assert before_file_bytes == legacy_cap - 154 + 1
        _grow_test_section(
            root, "docs/dev-wave/operations.md", "DW-O20", 154
        )
        _, after = _test_reference_slices(root, "docs/dev-wave/operations.md")
        assert len(after["DW-O20"].encode()) == 643
        after_file_bytes = len(
            _read(root, "docs/dev-wave/operations.md").encode()
        )
        assert after_file_bytes == before_file_bytes + 154
        assert after_file_bytes > legacy_cap
        layers = _test_layer_bytes(root)
        assert layers["L1"] <= 10_625
        assert layers["L1.5"] <= 9_788
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_new_gate_case_registration_is_complete():
    """F42: 新しい parametrize 外延と M1〜M12 の KILL node 名を固定する。"""

    assert _DEV_WAVE_CONDITIONALITY_CASES == (
        "stage-u-to-c", "stage-marker-missing", "stage-unknown-mode", "condition-always",
    )
    assert _DEV_WAVE_BARE_PATH_CASES == (
        "stage-reference", "condition-reference", "self-reference",
    )
    assert _DEV_WAVE_SLICING_CASES == (
        "fence", "html-comment", "raw-html", "malformed-heading",
    )
    assert _DEV_WAVE_SHARED_EDGE_CASES == ("dw-ctx", "dw-o04")
    source = _read(_REPO, "orchestrator/tests/test_check_docs.py")
    for test_name in (
        "test_dev_wave_layer_budget_rejects_plus_one",
        "test_dev_wave_dispatch_conditionality_retyping_is_rejected",
        "test_dev_wave_condition_dispatch_header_mismatch_is_dedicated",
        "test_dev_wave_dispatch_rejects_bare_path",
        "test_dev_wave_dispatch_rejects_unquoted_raw_path",
        "test_dev_wave_dispatch_rejects_all_sections_on_non_self_path",
        "test_dev_wave_dispatch_rejects_range_marker_inside_annotation",
        "test_dev_wave_dispatch_rejects_ascii_tilde_inside_url",
        "test_dev_wave_dispatch_accepts_exact_range_delimiter",
        "test_dev_wave_layer_slicing_ignores_fenced_heading",
        "test_dev_wave_layer_coverage_rejects_anonymous_visible_h2_only",
        "test_dev_wave_shared_reference_edges_are_typed",
        "test_dev_wave_l2_accepts_dw_o20_plus_154_bytes",
        "test_cleanup_address_edge_rejects_split_lines",
        "test_cleanup_address_edge_rejects_id_adjacent_decoy",
        "test_cleanup_address_edge_rejects_non_code_span_path_decoy",
        "test_cleanup_address_edge_rejects_raw_html_block",
        "test_cleanup_address_edge_rejects_link_definition",
        "test_cleanup_address_edge_rejects_frontmatter_decoy",
        "test_cleanup_address_edge_accepts_rewording",
        "test_cleanup_address_edge_accepts_baseline",
    ):
        assert source.count(f"def {test_name}(") == 1


def test_tools_readme_is_enumerated_and_budgeted():
    assert "tools/README.md" in _enumerated_rels()
    assert check_docs.TOOLS_README_LIMITS == {
        "tools/README.md": check_docs.TextLimit(3_000),
    }


def test_tools_readme_missing_is_rejected():
    root = _build_min_repo()
    try:
        os.remove(os.path.join(root, "tools", "README.md"))
        result = _assert_violation(root, "tools/README.md")
        assert "LIVING_DOCS の列挙対象が不在" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_tools_readme_budget_overrun_is_rejected():
    root = _build_min_repo()
    try:
        _pad_to_bytes(root, "tools/README.md", 3_001)
        result = _assert_violation(
            root,
            "tools/README.md: 3001 bytes > 予算 3000 bytes",
        )
        assert _violation_count(result) == 1, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_family_contract_pins_exact_surface():
    assert check_docs.PROVENANCE_LIMITS == {
        "docs/ai-provenance.md": check_docs.TextLimit(6_300),
    }
    assert check_docs.PROVENANCE_REFERENCE_LIMITS == {
        "docs/provenance/correction.md": check_docs.TextLimit(1_600),
        "docs/provenance/audit.md": check_docs.TextLimit(1_600),
    }
    assert check_docs.PROVENANCE_FAMILY_BYTES == 9_000
    assert check_docs.REQUIRED_PROVENANCE_REFERENCE_SECTIONS == {
        "docs/provenance/correction.md": {
            "PR-C01", "PR-C02", "PR-C03",
        },
        "docs/provenance/audit.md": {
            "PR-A01", "PR-A02", "PR-A03",
        },
    }
    assert check_docs.PROVENANCE_DISPATCH_CONTRACT == {
        "correction": (
            "固定 target の forward correction を扱う",
            frozenset({
                ("docs/provenance/correction.md", "PR-C01"),
                ("docs/provenance/correction.md", "PR-C02"),
                ("docs/provenance/correction.md", "PR-C03"),
            }),
        ),
        "message-file": (
            "commit 前に message を検査する",
            frozenset({
                ("docs/provenance/audit.md", "PR-A01"),
            }),
        ),
        "history": (
            "commit 後・別 range の履歴を監査する",
            frozenset({
                ("docs/provenance/audit.md", "PR-A02"),
                ("docs/provenance/correction.md", "PR-C03"),
            }),
        ),
        "analysis": (
            "provenance を比較や改善判断に使う",
            frozenset({
                ("docs/provenance/audit.md", "PR-A03"),
            }),
        ),
    }
    assert check_docs.PROVENANCE_SHARED_DISPATCH_PAIRS == {
        ("docs/provenance/correction.md", "PR-C03"): frozenset({
            "correction", "history",
        }),
    }


def test_provenance_family_is_enumerated_and_not_dispatch_allowlisted():
    family = {
        "docs/ai-provenance.md",
        "docs/provenance/correction.md",
        "docs/provenance/audit.md",
    }
    assert family <= set(_enumerated_rels())
    assert not (
        set(check_docs.PROVENANCE_LIMITS)
        & check_docs.NORMATIVE_DISPATCH_ALLOWLIST
    )
    assert not (
        set(check_docs.PROVENANCE_REFERENCE_LIMITS)
        & check_docs.NORMATIVE_DISPATCH_ALLOWLIST
    )


_PROVENANCE_MEMBER_LIMITS = (
    ("docs/ai-provenance.md", 6_300),
    ("docs/provenance/correction.md", 1_600),
    ("docs/provenance/audit.md", 1_600),
)


def _pad_provenance_family(root: str, target: int) -> None:
    limits = dict(_PROVENANCE_MEMBER_LIMITS)
    current = sum(
        len(_read(root, rel).encode("utf-8")) for rel in limits
    )
    assert current <= target
    remaining = target - current
    for rel, limit in limits.items():
        size = len(_read(root, rel).encode("utf-8"))
        grow = min(remaining, limit - size)
        if grow:
            _pad_to_bytes(root, rel, size + grow)
            remaining -= grow
    assert remaining == 0
    sizes = {
        rel: len(_read(root, rel).encode("utf-8")) for rel in limits
    }
    assert sum(sizes.values()) == target
    assert all(sizes[rel] <= limit for rel, limit in limits.items())


def _assert_findings(root: str, *expected: str) -> subprocess.CompletedProcess:
    res = _run_check(root)
    assert res.returncode == 1, f"違反 fixture が赤にならなかった:\n{res.stdout}"
    assert _finding_set(res) == set(expected), res.stdout
    assert _violation_count(res) == len(expected), res.stdout
    return res


@pytest.mark.parametrize(("rel", "limit"), _PROVENANCE_MEMBER_LIMITS)
def test_provenance_member_limit_accepts_exact_boundary(rel, limit):
    root = _build_min_repo()
    try:
        _pad_to_bytes(root, rel, limit)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(("rel", "limit"), _PROVENANCE_MEMBER_LIMITS)
def test_provenance_member_limit_rejects_plus_one(rel, limit):
    root = _build_min_repo()
    try:
        _pad_to_bytes(root, rel, limit + 1)
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1
        assert (
            f"{rel}: {limit + 1} bytes > 予算 {limit} bytes" in res.stdout
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_family_accepts_exactly_9000_bytes():
    root = _build_min_repo()
    try:
        _pad_provenance_family(root, 9_000)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_family_rejects_9001_bytes():
    root = _build_min_repo()
    try:
        _pad_provenance_family(root, 9_001)
        _assert_findings(
            root,
            "docs/ai-provenance.md + docs/provenance/**: "
            "合計 9001 bytes > hard ceiling 9000 bytes",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_unregistered_reference_is_rejected():
    root = _build_min_repo()
    try:
        _write(root, "docs/provenance/extra.md", "# escaped\n")
        _assert_findings(
            root,
            "docs/provenance/extra.md: docs/provenance/** の予算未登録実体 — "
            "規範 detail を family 閉包外へ逃がしてはならない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_registered_provenance_reference_deletion_is_rejected():
    root = _build_min_repo()
    try:
        os.remove(os.path.join(root, "docs/provenance/audit.md"))
        _assert_findings(
            root,
            "docs/provenance/audit.md: 登録済み provenance reference が不在 — "
            "入口 dispatch が到達不能",
            "docs/ai-provenance.md:8: 実在しないパス参照: "
            "'docs/provenance/audit.md'",
            "docs/ai-provenance.md:9: 実在しないパス参照: "
            "'docs/provenance/audit.md'",
            "docs/ai-provenance.md:10: 実在しないパス参照: "
            "'docs/provenance/audit.md'",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_registered_provenance_reference_symlink_is_rejected():
    root = _build_min_repo()
    external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_provenance_")
    try:
        rel = "docs/provenance/audit.md"
        member = os.path.join(root, rel)
        external_member = os.path.join(external, "audit.md")
        _write(external, "audit.md", _read(root, rel))
        os.remove(member)
        os.symlink(external_member, member)
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        prefix = (
            "docs/provenance/audit.md: symlink または regular file 以外 — "
            "予算・interface 検査対象として受理しない "
            "(symlink を含む path は読まない: "
        )
        findings = _finding_set(res)
        normalized_findings = set()
        for finding in findings:
            if finding.startswith(prefix) and finding.endswith(")"):
                reported_path = finding.removeprefix(prefix).removesuffix(")")
                if os.path.isabs(reported_path):
                    finding = prefix + "<absolute path>)"
            normalized_findings.add(finding)
        assert normalized_findings == {
            "docs/provenance/audit.md: symlink または regular file 以外 — "
            "予算・interface 検査対象として受理しない "
            "(symlink を含む path は読まない: <absolute path>)"
        }, res.stdout
        assert _violation_count(res) == 1, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(external, ignore_errors=True)


@pytest.mark.parametrize("mutation", ["missing", "duplicate"])
def test_provenance_required_h2_multiplicity_is_rejected(mutation):
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        heading = "## PR-A02 — synthetic"
        assert text.count(heading) == 1
        if mutation == "missing":
            text = text.replace(heading, "### PR-A02 — synthetic", 1)
        else:
            text += f"\n{heading}\n\nbody\n"
        _write(root, rel, text)
        count = 0 if mutation == "missing" else 2
        _assert_findings(
            root,
            f"{rel}: H2 見出し PR-A02 が {count} 件 — "
            "provenance dispatch 先は一意でなければならない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_orphan_reference_h2_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        _write(root, rel, _read(root, rel) + "\n## PR-A99 — orphan\n\nbody\n")
        _assert_findings(
            root,
            f"{rel}: provenance dispatch 契約にない孤児 H2 — ['PR-A99']",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _dispatch_row(text: str, key: str) -> str:
    matches = [line for line in text.splitlines(keepends=True)
               if line.startswith(f"| {key} |")]
    assert len(matches) == 1, (key, matches)
    return matches[0]


def test_provenance_dispatch_row_deletion_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        _write(root, rel, text.replace(_dispatch_row(text, "history"), "", 1))
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の "
            "row count が不一致 — actual=0, expected=1",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_duplicate_row_is_rejected():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        row = _dispatch_row(text, "history")
        _write(root, rel, text + row)
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の "
            "row count が不一致 — actual=2, expected=1",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("replacement", ["", "常に監査する", "決して監査しない"])
def test_provenance_dispatch_condition_literal_change_is_rejected(replacement):
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        old = "commit 後・別 range の履歴を監査する"
        assert text.count(old) == 1
        row = _dispatch_row(text, "history")
        changed = row.replace(old, replacement, 1)
        _write(root, rel, text.replace(row, changed, 1))
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の発火条件が不一致 — "
            f"actual={[replacement]!r}, expected={[old]!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_conditions_cannot_be_swapped_between_keys():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        history = "commit 後・別 range の履歴を監査する"
        analysis = "provenance を比較や改善判断に使う"
        sentinel = "__SWAPPED_CONDITION__"
        changed = text.replace(history, sentinel, 1)
        changed = changed.replace(analysis, history, 1).replace(sentinel, analysis, 1)
        _write(root, rel, changed)
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'analysis' の発火条件が不一致 — "
            f"actual={[history]!r}, expected={[analysis]!r}",
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の発火条件が不一致 — "
            f"actual={[analysis]!r}, expected={[history]!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_missing_pair_is_rejected_independently():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        row = _dispatch_row(text, "history")
        removed = "; `docs/provenance/correction.md`: `PR-C03`"
        assert row.count(removed) == 1
        _write(root, rel, text.replace(row, row.replace(removed, "", 1), 1))
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の参照集合が不一致 — "
            "missing=[('docs/provenance/correction.md', 'PR-C03')], extra=[]",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_condition_token_smuggling_is_diagnostic_sensitivity():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        row = _dispatch_row(text, "history")
        replacement = (
            "| history | commit 後・別 range の履歴を監査する "
            "`docs/provenance/audit.md`: `PR-A02` | |\n"
        )
        _write(root, rel, text.replace(row, replacement, 1))
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の発火条件が不一致 — "
            "actual=['commit 後・別 range の履歴を監査する "
            "`docs/provenance/audit.md`: `PR-A02`'], "
            "expected=['commit 後・別 range の履歴を監査する']",
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の参照集合が不一致 — "
            "missing=[('docs/provenance/audit.md', 'PR-A02'), "
            "('docs/provenance/correction.md', 'PR-C03')], extra=[]",
            "docs/ai-provenance.md: diagnostic sensitivity — provenance 条件 "
            "dispatch 'history' の条件セルに reference token="
            "['`PR-A02`', '`docs/provenance/audit.md`']",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    ("mutation", "detail"),
    [
        ("header-missing", "header '| key | 発火条件 | 読む節 |' が 0 件"),
        ("header-hidden", "header '| key | 発火条件 | 読む節 |' が 0 件"),
        ("header-renamed", "header '| key | 発火条件 | 読む節 |' が 0 件"),
        ("header-duplicate", "header '| key | 発火条件 | 読む節 |' が 2 件"),
        ("separator-missing", "3列 separator が 0 件"),
        ("separator-duplicate", "3列 separator が 2 件"),
        ("separator-displaced", "separator が header 直後にない"),
        (
            "four-columns",
            "data row が3列・外周 delimiter 高々1個でない — "
            "leading=1, trailing=1, cells=4",
        ),
        (
            "two-columns",
            "data row が3列・外周 delimiter 高々1個でない — "
            "leading=1, trailing=1, cells=2",
        ),
        (
            "double-leading",
            "data row が3列・外周 delimiter 高々1個でない — "
            "leading=2, trailing=1, cells=4",
        ),
        (
            "double-trailing",
            "data row が3列・外周 delimiter 高々1個でない — "
            "leading=1, trailing=2, cells=4",
        ),
    ],
)
def test_provenance_dispatch_table_structure_is_exact(mutation, detail):
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        header = "| key | 発火条件 | 読む節 |"
        separator = "|---|---|---|"
        row = _dispatch_row(text, "history")
        if mutation == "header-missing":
            changed = text.replace(header + "\n", "", 1)
        elif mutation == "header-hidden":
            changed = text.replace(header, f"<!-- {header} -->", 1)
        elif mutation == "header-renamed":
            changed = text.replace(header, "| key | 発火条件 | 任意欄 |", 1)
        elif mutation == "header-duplicate":
            changed = text.replace(header, header + "\n" + header, 1)
        elif mutation == "separator-missing":
            changed = text.replace(separator + "\n", "", 1)
        elif mutation == "separator-duplicate":
            changed = text.replace(separator, separator + "\n" + separator, 1)
        elif mutation == "separator-displaced":
            changed = text.replace(
                header + "\n" + separator,
                header + "\n\n" + separator,
                1,
            )
        elif mutation == "four-columns":
            changed = text.replace(row, row.rstrip("\n")[:-1] + "| extra |\n", 1)
        elif mutation == "two-columns":
            condition = "commit 後・別 range の履歴を監査する"
            changed = text.replace(row, f"| history | {condition} |\n", 1)
        elif mutation == "double-leading":
            changed = text.replace(row, "|" + row, 1)
        else:
            changed = text.replace(row, row.rstrip("\n") + "|\n", 1)
        _write(root, rel, changed)
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 表の構造が不一致 — "
            f"{[detail]!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_data_row_outer_delimiters_are_optional():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        row = _dispatch_row(text, "history")
        changed = row.strip().removeprefix("|").removesuffix("|").strip() + "\n"
        _write(root, rel, text.replace(row, changed, 1))
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_registry_outside_path_is_diagnostic_sensitivity():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        row = _dispatch_row(text, "history")
        changed = row.replace(
            "docs/provenance/audit.md", "docs/dev-wave/core.md", 1
        )
        _write(root, rel, text.replace(row, changed, 1))
        _assert_findings(
            root,
            "docs/ai-provenance.md: provenance 条件 dispatch 'history' の参照集合が不一致 — "
            "missing=[('docs/provenance/audit.md', 'PR-A02')], "
            "extra=[('docs/dev-wave/core.md', 'PR-A02')]",
            "docs/ai-provenance.md: diagnostic sensitivity — provenance 条件 "
            "dispatch 'history' の第3列に registry 外 path=['docs/dev-wave/core.md']",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_html_commented_provenance_dispatch_table_is_not_visible():
    root = _build_min_repo()
    try:
        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        marker = "## 条件 dispatch\n"
        assert text.count(marker) == 1
        _write(root, rel, text.replace(marker, "<!--\n" + marker, 1) + "-->\n")
        _assert_findings(
            root,
            "docs/ai-provenance.md: 条件 dispatch 表を一意に抽出できない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_fenced_provenance_h2_is_not_visible():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        heading = "## PR-A01 — synthetic"
        assert text.count(heading) == 1
        _write(
            root,
            rel,
            text.replace(heading, f"```markdown\n{heading}\n```", 1),
        )
        _assert_findings(
            root,
            f"{rel}: H2 見出し PR-A01 が 0 件 — provenance dispatch 先は"
            "一意でなければならない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_inline_code_comment_delimiter_is_rejected_fail_closed():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        lineno = len(text.splitlines()) + 2
        _write(root, rel, text + "\n`<!--`\n## PR-A99 — visible\n`-->`\n")
        _assert_findings(
            root,
            f"{rel}: provenance Markdown の曖昧構文を受理しない — "
            f"{[f'line {lineno}: inline code 内の HTML comment delimiter']!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_unclosed_provenance_fence_is_rejected_fail_closed():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        lineno = len(text.splitlines()) + 2
        _write(root, rel, text + "\n```markdown\n## PR-A99 — masked\n")
        _assert_findings(
            root,
            f"{rel}: provenance Markdown の曖昧構文を受理しない — "
            f"{[f'line {lineno}: 未閉じ code fence']!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_mismatched_provenance_fence_is_rejected_fail_closed():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        opener = len(text.splitlines()) + 2
        closer = opener + 2
        _write(root, rel, text + "\n```markdown\n## PR-A99 — masked\n~~~\n")
        _assert_findings(
            root,
            f"{rel}: provenance Markdown の曖昧構文を受理しない — "
            f"{[f'line {closer}: 異種 fence closer', f'line {opener}: 未閉じ code fence']!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_fence_inside_html_comment_does_not_mask_following_h2():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        _write(
            root,
            rel,
            text + "\n<!--\n```markdown\n-->\n## PR-A99 — visible orphan\n",
        )
        _assert_findings(
            root,
            f"{rel}: provenance dispatch 契約にない孤児 H2 — ['PR-A99']",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_invalid_backtick_fence_info_string_is_rejected_fail_closed():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        text = _read(root, rel)
        lineno = len(text.splitlines()) + 2
        _write(root, rel, text + "\n```info`bad\n## PR-A99 — over-masked\n")
        _assert_findings(
            root,
            f"{rel}: provenance Markdown の曖昧構文を受理しない — "
            f"{[f'line {lineno}: 無効な backtick fence info string']!r}",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_references_inherit_land_helper_location_lint():
    root = _build_min_repo()
    try:
        rel = "docs/provenance/audit.md"
        _write(root, rel, _read(root, rel) + "\n`tools/dev_wave_land.py`\n")
        _assert_findings(
            root,
            f"{rel}: land helper path は DW-S09 / DW-O23 だけに置く",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _load_fixture_checker(root: str):
    module_name = f"_check_docs_fixture_{id(root)}"
    path = os.path.join(root, "tools", "check_docs.py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _run_loaded_checker(module) -> subprocess.CompletedProcess:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        returncode = module.main()
    return subprocess.CompletedProcess([], returncode, output.getvalue(), "")


class _ReadTextIdentityView:
    def __init__(self, source, *, ctime_ns):
        self.st_mode = source.st_mode
        self.st_mtime_ns = source.st_mtime_ns
        self.st_size = source.st_size
        self.st_ino = source.st_ino
        self.st_dev = source.st_dev
        self.st_ctime_ns = ctime_ns


def test_read_text_cache_uses_one_physical_open_per_main(tmp_path, monkeypatch):
    target = tmp_path / "shared.md"
    target.write_text("shared text\n", encoding="utf-8")
    monkeypatch.setattr(check_docs, "REPO", tmp_path)

    real_open = check_docs.Path.open
    physical_opens = 0

    def counting_open(path, *args, **kwargs):
        nonlocal physical_opens
        if path == target:
            physical_opens += 1
        return real_open(path, *args, **kwargs)

    observed = []
    findings = []

    def cache_probe(argv=None):
        observed.append(check_docs._safe_read_text(target, findings, "first"))
        observed.append(check_docs._safe_read_text(target, findings, "second"))
        return 0

    monkeypatch.setattr(check_docs.Path, "open", counting_open)
    monkeypatch.setattr(check_docs, "_main", cache_probe)

    assert check_docs.main([]) == 0
    assert observed == ["shared text\n", "shared text\n"]
    assert findings == []
    assert physical_opens == 1


def test_read_text_cache_uses_one_open_across_newline_modes(tmp_path, monkeypatch):
    target = tmp_path / "cross-mode.md"
    target.write_bytes(b"alpha\r\nbeta\r")
    monkeypatch.setattr(check_docs, "REPO", tmp_path)

    real_open = check_docs.Path.open
    physical_opens = 0

    def counting_open(path, *args, **kwargs):
        nonlocal physical_opens
        if path == target:
            physical_opens += 1
        return real_open(path, *args, **kwargs)

    observed = []
    findings = []

    def cross_mode_probe(argv=None):
        observed.append(
            check_docs._safe_read_text(target, findings, "raw", newline="")
        )
        observed.append(
            check_docs._safe_read_text(
                target, findings, "normalized", newline=None
            )
        )
        return 0

    monkeypatch.setattr(check_docs.Path, "open", counting_open)
    monkeypatch.setattr(check_docs, "_main", cross_mode_probe)

    assert check_docs.main([]) == 0
    assert observed == ["alpha\r\nbeta\r", "alpha\nbeta\n"]
    assert findings == []
    assert physical_opens == 1


def test_read_text_cache_keeps_newline_modes_distinct(tmp_path, monkeypatch):
    target = tmp_path / "newlines.md"
    target.write_bytes(b"alpha\r\nbeta\rgamma\n")
    monkeypatch.setattr(check_docs, "REPO", tmp_path)

    observed = []
    findings = []

    def newline_probe(argv=None):
        observed.append(
            check_docs._safe_read_text(
                target, findings, "raw", newline=""
            )
        )
        observed.append(
            check_docs._safe_read_text(
                target, findings, "normalized", newline=None
            )
        )
        return 0

    monkeypatch.setattr(check_docs, "_main", newline_probe)

    assert check_docs.main([]) == 0
    assert observed == [
        "alpha\r\nbeta\rgamma\n",
        "alpha\nbeta\ngamma\n",
    ]
    assert findings == []


def test_read_text_cache_replays_failure_for_each_caller(tmp_path, monkeypatch):
    target = tmp_path / "invalid.md"
    target.write_bytes(b"\xff")
    monkeypatch.setattr(check_docs, "REPO", tmp_path)

    findings = []

    def failure_probe(argv=None):
        assert check_docs._safe_read_text(target, findings, "first caller") is None
        assert check_docs._safe_read_text(target, findings, "second caller") is None
        return 0

    monkeypatch.setattr(check_docs, "_main", failure_probe)

    assert check_docs.main([]) == 0
    assert [finding.split(" (", 1)[0] for finding in findings] == [
        "first caller",
        "second caller",
    ]
    assert findings[0].removeprefix("first caller") == findings[1].removeprefix(
        "second caller"
    )


def test_read_text_cache_invalidates_revoked_read_permission(tmp_path, monkeypatch):
    target = tmp_path / "permission.md"
    target.write_text("secret\n", encoding="utf-8")
    initial = target.lstat()
    monkeypatch.setattr(check_docs, "REPO", tmp_path)

    real_lstat = check_docs.Path.lstat
    real_open = check_docs.Path.open

    def stable_ctime_lstat(path):
        current = real_lstat(path)
        if path == target:
            return _ReadTextIdentityView(current, ctime_ns=initial.st_ctime_ns)
        return current

    def permission_checked_open(path, *args, **kwargs):
        if path == target and not (path.lstat().st_mode & 0o444):
            raise PermissionError(13, "Permission denied", str(path))
        return real_open(path, *args, **kwargs)

    observed = []
    findings = []

    def permission_probe(argv=None):
        observed.append(check_docs._safe_read_text(target, findings, "before"))
        os.chmod(target, 0o000)
        try:
            observed.append(check_docs._safe_read_text(target, findings, "after"))
        finally:
            os.chmod(target, 0o644)
        return 0

    monkeypatch.setattr(check_docs.Path, "lstat", stable_ctime_lstat)
    monkeypatch.setattr(check_docs.Path, "open", permission_checked_open)
    monkeypatch.setattr(check_docs, "_main", permission_probe)

    assert check_docs.main([]) == 0
    assert observed == ["secret\n", None]
    assert len(findings) == 1
    assert findings[0].startswith("after (PermissionError: ")


def test_read_text_cache_invalidates_ctime_only_change(tmp_path, monkeypatch):
    target = tmp_path / "ctime.md"
    target.write_text("same\n", encoding="utf-8")
    initial = target.lstat()
    monkeypatch.setattr(check_docs, "REPO", tmp_path)

    real_lstat = check_docs.Path.lstat
    real_open = check_docs.Path.open
    physical_opens = 0
    use_changed_identity = False

    def ctime_only_lstat(path):
        current = real_lstat(path)
        if path == target and use_changed_identity:
            return _ReadTextIdentityView(
                current, ctime_ns=initial.st_ctime_ns + 1
            )
        return current

    def counting_open(path, *args, **kwargs):
        nonlocal physical_opens
        if path == target:
            physical_opens += 1
        return real_open(path, *args, **kwargs)

    observed = []
    findings = []

    def ctime_probe(argv=None):
        nonlocal use_changed_identity
        observed.append(check_docs._safe_read_text(target, findings, "before"))
        use_changed_identity = True
        changed = target.lstat()
        assert changed.st_mtime_ns == initial.st_mtime_ns
        assert changed.st_size == initial.st_size
        assert changed.st_ino == initial.st_ino
        assert changed.st_dev == initial.st_dev
        assert changed.st_mode == initial.st_mode
        assert changed.st_ctime_ns != initial.st_ctime_ns
        observed.append(check_docs._safe_read_text(target, findings, "after"))
        return 0

    monkeypatch.setattr(check_docs.Path, "lstat", ctime_only_lstat)
    monkeypatch.setattr(check_docs.Path, "open", counting_open)
    monkeypatch.setattr(check_docs, "_main", ctime_probe)

    assert check_docs.main([]) == 0
    assert observed == ["same\n", "same\n"]
    assert findings == []
    assert physical_opens == 2


def test_read_text_cache_invalidates_replaced_file_identity(tmp_path, monkeypatch):
    target = tmp_path / "replaceable.md"
    replacement = tmp_path / "replacement.md"
    target.write_text("old\n", encoding="utf-8")
    replacement.write_text("replacement content\n", encoding="utf-8")
    monkeypatch.setattr(check_docs, "REPO", tmp_path)

    observed = []
    findings = []

    def replacement_probe(argv=None):
        observed.append(check_docs._safe_read_text(target, findings, "before"))
        replacement.replace(target)
        observed.append(check_docs._safe_read_text(target, findings, "after"))
        return 0

    monkeypatch.setattr(check_docs, "_main", replacement_probe)

    assert check_docs.main([]) == 0
    assert observed == ["old\n", "replacement content\n"]
    assert findings == []


def test_read_text_cache_invalidates_inode_only_replacement(tmp_path, monkeypatch):
    target = tmp_path / "inode.md"
    replacement = tmp_path / "replacement.md"
    target.write_text("old\n", encoding="utf-8")
    replacement.write_text("new\n", encoding="utf-8")
    initial = target.lstat()
    os.utime(
        replacement,
        ns=(initial.st_atime_ns, initial.st_mtime_ns),
    )
    replacement_stat = replacement.lstat()
    assert replacement_stat.st_ino != initial.st_ino
    assert replacement_stat.st_size == initial.st_size
    assert replacement_stat.st_mtime_ns == initial.st_mtime_ns
    assert replacement_stat.st_dev == initial.st_dev
    assert replacement_stat.st_mode == initial.st_mode
    monkeypatch.setattr(check_docs, "REPO", tmp_path)

    real_lstat = check_docs.Path.lstat

    def stable_ctime_lstat(path):
        current = real_lstat(path)
        if path == target:
            return _ReadTextIdentityView(current, ctime_ns=initial.st_ctime_ns)
        return current

    observed = []
    findings = []

    def replacement_probe(argv=None):
        observed.append(check_docs._safe_read_text(target, findings, "before"))
        replacement.replace(target)
        observed.append(check_docs._safe_read_text(target, findings, "after"))
        return 0

    monkeypatch.setattr(check_docs.Path, "lstat", stable_ctime_lstat)
    monkeypatch.setattr(check_docs, "_main", replacement_probe)

    assert check_docs.main([]) == 0
    assert observed == ["old\n", "new\n"]
    assert findings == []


def test_read_text_cache_invalidates_mtime_only_change(tmp_path, monkeypatch):
    target = tmp_path / "mtime.md"
    target.write_text("same\n", encoding="utf-8")
    initial = target.lstat()
    monkeypatch.setattr(check_docs, "REPO", tmp_path)

    real_lstat = check_docs.Path.lstat
    real_open = check_docs.Path.open
    physical_opens = 0

    def stable_ctime_lstat(path):
        current = real_lstat(path)
        if path == target:
            return _ReadTextIdentityView(current, ctime_ns=initial.st_ctime_ns)
        return current

    def counting_open(path, *args, **kwargs):
        nonlocal physical_opens
        if path == target:
            physical_opens += 1
        return real_open(path, *args, **kwargs)

    observed = []
    findings = []

    def mtime_probe(argv=None):
        observed.append(check_docs._safe_read_text(target, findings, "before"))
        os.utime(
            target,
            ns=(initial.st_atime_ns, initial.st_mtime_ns + 2_000_000_000),
        )
        changed = real_lstat(target)
        assert changed.st_ino == initial.st_ino
        assert changed.st_size == initial.st_size
        assert changed.st_mtime_ns != initial.st_mtime_ns
        assert changed.st_dev == initial.st_dev
        assert changed.st_mode == initial.st_mode
        observed.append(check_docs._safe_read_text(target, findings, "after"))
        return 0

    monkeypatch.setattr(check_docs.Path, "lstat", stable_ctime_lstat)
    monkeypatch.setattr(check_docs.Path, "open", counting_open)
    monkeypatch.setattr(check_docs, "_main", mtime_probe)

    assert check_docs.main([]) == 0
    assert observed == ["same\n", "same\n"]
    assert findings == []
    assert physical_opens == 2


def test_provenance_registry_three_faces_asymmetry_is_rejected(monkeypatch):
    root = _build_min_repo()
    try:
        module = _load_fixture_checker(root)
        rel = "docs/provenance/extra.md"
        path = module.REPO / rel
        _write(root, rel, "# registered only in budget face\n")
        monkeypatch.setattr(
            module,
            "PROVENANCE_REFERENCE_LIMITS",
            {
                **module.PROVENANCE_REFERENCE_LIMITS,
                rel: module.TextLimit(1_600),
            },
        )
        monkeypatch.setattr(
            module, "LIVING_DOCS", [*module.LIVING_DOCS, path]
        )
        monkeypatch.setattr(
            module, "_ENUMERATED_DOCS", module._ENUMERATED_DOCS | {path}
        )
        res = _run_loaded_checker(module)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1, res.stdout
        assert "provenance registry 三面の path 集合が不一致" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_provenance_dispatch_pair_multiple_key_ownership_is_rejected(
    monkeypatch,
):
    root = _build_min_repo()
    try:
        module = _load_fixture_checker(root)
        contract = dict(module.PROVENANCE_DISPATCH_CONTRACT)
        condition, pairs = contract["history"]
        duplicate = ("docs/provenance/audit.md", "PR-A01")
        contract["history"] = (condition, pairs | {duplicate})
        monkeypatch.setattr(module, "PROVENANCE_DISPATCH_CONTRACT", contract)

        rel = "docs/ai-provenance.md"
        text = _read(root, rel)
        row = _dispatch_row(text, "history")
        changed = row.replace("`PR-A02`", "`PR-A01`, `PR-A02`", 1)
        _write(root, rel, text.replace(row, changed, 1))

        res = _run_loaded_checker(module)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1, res.stdout
        assert "provenance dispatch pair の key 所有が不一致" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _placeholder_findings(root: str) -> list[str]:
    module = _load_fixture_checker(root)
    findings: list[str] = []
    module._check_literal_placeholder_guard(findings)
    return findings


def _assert_placeholder_violation(root: str, *needles: str) -> list[str]:
    findings = _placeholder_findings(root)
    assert findings, "placeholder 違反 fixture が赤にならなかった"
    rendered = "\n".join(findings)
    for needle in needles:
        assert needle in rendered, f"{needle!r} が finding にない:\n{rendered}"
    return findings


def _assert_other_checkers_clean(root: str) -> None:
    module = _load_fixture_checker(root)
    module._check_literal_placeholder_guard = lambda findings: set()
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        rc = module.main()
    assert rc == 0, output.getvalue()


def test_placeholder_guard_each_literal_independently_fires():
    literals = (
        "<反映>",
        "<受入結果を反映>",
        "<受入全走結果を反映>",
    )
    for literal in literals:
        root = _build_min_repo()
        try:
            _write(
                root,
                "output/insights/independent.md",
                f"independent control: {literal}\n",
            )
            findings = _assert_placeholder_violation(
                root, "未許可のリテラル placeholder", repr(literal)
            )
            assert len(findings) == 1, findings
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_date_layout_preserves_old_targets_and_shallow_scope():
    root = _build_min_repo()
    try:
        module = _load_fixture_checker(root)
        old, _, _, _ = module._literal_placeholder_targets([])
        _write(root, "output/insights/2026-09-10/report.md", "# complete report\n")
        _write(root, "output/insights/2026-09-10/topic/verbatim.md", "<反映>\n")
        module = _load_fixture_checker(root)
        findings = []
        new, _, _, complete = module._literal_placeholder_targets(findings)
        assert complete and not findings, findings
        assert set(old) < set(new)
        assert {str(p.relative_to(module.REPO)) for p in set(new) - set(old)} == {
            "output/insights/2026-09-10/report.md"
        }
        assert _placeholder_findings(root) == []
        _write(root, "output/insights/2026-09-10/report.md", "<反映>\n")
        _assert_placeholder_violation(root, "2026-09-10/report.md", "未許可のリテラル placeholder")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_date_directory_rejects_symlink_and_non_directory():
    for kind in ("symlink", "file", "unreadable"):
        root = _build_min_repo()
        try:
            path = os.path.join(root, "output/insights/2026-09-10")
            if kind == "symlink":
                os.symlink("missing", path)
            elif kind == "unreadable":
                os.mkdir(path, 0o000)
            else:
                _write(root, "output/insights/2026-09-10", "file\n")
            _assert_placeholder_violation(root, "日付 directory の列挙失敗")
        finally:
            if kind == "unreadable":
                os.chmod(path, 0o700)
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_main_propagates_finding_to_rc():
    root = _build_min_repo()
    try:
        rel = "output/insights/2026-07-24_e2e-real-seal.md"
        _write(root, rel, _read(root, rel) + "main wiring control: <反映>\n")
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "check_docs: 1 件の違反" in res.stdout, res.stdout
        assert "未許可のリテラル placeholder" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_new_literal_is_violation_in_each_family():
    cases = (
        ("docs/worklog.md", "worklog control: <反映>\n"),
        (
            "docs/archive/worklog-phase3-0722-0724.md",
            "archive control: <受入結果を反映>\n",
        ),
        (
            "output/insights/2026-07-24_e2e-real-seal.md",
            "insight control: <受入全走結果を反映>\n",
        ),
    )
    for rel, addition in cases:
        root = _build_min_repo()
        try:
            _write(root, rel, _read(root, rel) + addition)
            findings = _assert_placeholder_violation(
                root, rel, "未許可のリテラル placeholder"
            )
            assert len(findings) == 1, findings
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_detects_new_family_member():
    cases = (
        (
            "docs/archive/worklog-new.md",
            "# new archive\n\n"
            "## 2025-12-30 (1) — new archive\n\n"
            "new archive member: <反映>\n\n"
            "### 次の一手\n"
            "1. legacy item\n",
        ),
        (
            "output/insights/new-insight.md",
            "new insight member: <反映>\n",
        ),
    )
    for rel, content in cases:
        root = _build_min_repo()
        try:
            _write(root, rel, content)
            if rel.startswith("docs/archive/"):
                readme_rel = "docs/archive/README.md"
                _write(
                    root,
                    readme_rel,
                    _read(root, readme_rel) + "- `worklog-new.md`\n",
                )
            _assert_other_checkers_clean(root)
            findings = _assert_placeholder_violation(
                root, rel, "未許可のリテラル placeholder"
            )
            assert len(findings) == 1, findings
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_registered_line_removal_is_violation():
    root = _build_min_repo()
    try:
        rel = "output/insights/2026-07-24_e2e-real-seal.md"
        _write(root, rel, _read(root, rel).replace(
            _PLACEHOLDER_DEBT_INSIGHT + "\n", "", 1
        ))
        findings = _assert_placeholder_violation(
            root,
            rel,
            "KNOWN_PLACEHOLDER_DEBTS",
            "expected=1, actual=0",
        )
        assert len(findings) == 1, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_registered_line_content_change_is_violation():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        changed = _PLACEHOLDER_DEBT_WORKLOG.replace("repo scan", "Repo scan", 1)
        _write(
            root,
            rel,
            _read(root, rel).replace(_PLACEHOLDER_DEBT_WORKLOG, changed, 1),
        )
        findings = _assert_placeholder_violation(
            root,
            rel,
            "未許可のリテラル placeholder",
            "KNOWN_PLACEHOLDER_DEBTS",
            "expected=1, actual=0",
        )
        assert len(findings) == 2, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_registered_line_duplication_is_violation():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        original = f"{heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
        duplicated = (
            f"{heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
            f"{_PLACEHOLDER_DEBT_WORKLOG}\n"
        )
        text = _read(root, rel)
        assert original in text
        _write(root, rel, text.replace(original, duplicated, 1))
        findings = _assert_placeholder_violation(
            root,
            "worklog-entry:4926160d0e41c9e972953e535dcce8cc1744eff78b13277cc91d722dc06129f2",
            "37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0",
            "expected=1, actual=2",
        )
        assert len(findings) == 1, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_same_file_record_replay_is_violation():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        source_heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        target_heading = (
            "## 2026-07-25 (4) — /rulings: 裁定待ち 5 件をユーザーが推奨どおり"
            "一括裁定 — official 解禁を承認 (D86 起票、計測なし)"
        )
        text = _read(root, rel)
        source = f"{source_heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
        target = f"{target_heading}\n\n"
        assert source in text and target in text
        text = text.replace(source, f"{source_heading}\n", 1)
        text = text.replace(
            target,
            f"{target_heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n",
            1,
        )
        _write(root, rel, text)
        findings = _assert_placeholder_violation(
            root,
            rel,
            "未許可のリテラル placeholder",
            "worklog-entry:4926160d0e41c9e972953e535dcce8cc1744eff78b13277cc91d722dc06129f2",
            "expected=1, actual=0",
        )
        assert len(findings) == 2, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_duplicate_worklog_h2_is_violation():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        text = _read(root, rel)
        assert text.count(heading) == 1
        _write(root, rel, text + f"\n{heading}\n")
        findings = _placeholder_findings(root)
        assert len(findings) == 1, findings
        rendered = findings[0]
        assert "worklog 族の H2 raw bytes が重複" in rendered
        assert heading in rendered
        assert rendered.count(rel) == 2, rendered
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        tab_heading = "##\t2026-07-30 (1) — tab-separated duplicate"
        _write(
            root,
            rel,
            _read(root, rel)
            + f"\n{tab_heading}\n\nbody\n\n{tab_heading}\n",
        )
        findings = _placeholder_findings(root)
        assert len(findings) == 1, findings
        rendered = findings[0]
        assert "worklog 族の H2 raw bytes が重複" in rendered
        assert repr(tab_heading) in rendered
        assert rendered.count(rel) == 2, rendered
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_h2_collision_replay_is_violation():
    root = _build_min_repo()
    try:
        source_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        replay_rel = "docs/archive/worklog-h2-collision.md"
        heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        source = _read(root, source_rel)
        registered = f"{heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
        assert registered in source
        _write(
            root,
            source_rel,
            source.replace(
                registered,
                f"{heading}\n",
                1,
            ),
        )
        _write(
            root,
            replay_rel,
            f"# collision replay\n\n{heading}\n\n"
            f"{_PLACEHOLDER_DEBT_WORKLOG}\n\n### 次の一手\n",
        )
        findings = _placeholder_findings(root)
        assert len(findings) == 1, findings
        rendered = findings[0]
        assert "worklog 族の H2 raw bytes が重複" in rendered
        assert source_rel in rendered and replay_rel in rendered
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        source_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        replay_rel = "docs/archive/worklog-tab-scope-replay.md"
        heading = (
            "## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 "
            "(test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)"
        )
        source = _read(root, source_rel)
        registered = f"{heading}\n\n{_PLACEHOLDER_DEBT_WORKLOG}\n"
        assert registered in source
        _write(
            root,
            source_rel,
            source.replace(registered, f"{heading}\n", 1),
        )
        tab_heading = heading.replace("## ", "##\t", 1)
        _write(
            root,
            replay_rel,
            f"# tab scope replay\n\n{tab_heading}\n\n"
            f"{_PLACEHOLDER_DEBT_WORKLOG}\n\n### 次の一手\n",
        )
        findings = _placeholder_findings(root)
        rendered = "\n".join(findings)
        assert len(findings) == 2, findings
        assert "未許可のリテラル placeholder" in rendered
        assert "expected=1, actual=0" in rendered
        assert "worklog 族の H2 raw bytes が重複" not in rendered
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_entry_rotation_keeps_ledger_green():
    registered_heading = (
        "## 2026-07-25 (4) — /rulings: 裁定待ち 5 件をユーザーが推奨どおり"
        "一括裁定 — official 解禁を承認 (D86 起票、計測なし)"
    )
    first_current_heading = "## 2026-08-01 (1) — first"
    original_first_heading = (
        "## 2026-07-24 (4) — 統合 E2E: 実 seal を official floor 経路に通す "
        "(D79(7) 部分閉鎖、branch worktree-dev-wave-e2e-real-seal、計測なし)"
    )

    def place_registered_entry_in_current(root: str) -> str:
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        worklog_rel = "docs/worklog.md"
        archive = _read(root, archive_rel)
        start = archive.index(registered_heading)
        entry = archive[start:]
        _write(root, archive_rel, archive[:start])

        assert entry.rstrip().endswith("### 次の一手")
        entry = entry.rstrip() + "\n1. [T-099] rotation handoff\n\n"
        worklog = _read(root, worklog_rel)
        marker = first_current_heading
        assert marker in worklog
        worklog = worklog.replace(
            first_current_heading,
            f"{first_current_heading}\n\n- [T-099] rotation sink",
            1,
        )
        _write(
            root,
            worklog_rel,
            worklog.replace(first_current_heading, entry + first_current_heading, 1),
        )
        baseline = _run_check(root)
        current_res = baseline
        assert current_res.returncode == 0, current_res.stdout
        return entry

    # H2 を現行 worklog に残し、登録行だけを後続 H2 へ移す対は赤。
    root = _build_min_repo()
    try:
        entry = place_registered_entry_in_current(root)
        worklog = _read(root, "docs/worklog.md")
        assert entry in worklog
        worklog = worklog.replace(
            _PLACEHOLDER_MENTION_WORKLOG_T094_A + "\n",
            "",
            1,
        )
        worklog = worklog.replace(
            first_current_heading,
            f"{first_current_heading}\n\n{_PLACEHOLDER_MENTION_WORKLOG_T094_A}",
            1,
        )
        _write(root, "docs/worklog.md", worklog)

        # baseline にない archive member と README 索引を作り、非空遷移も成立させる。
        new_name = "worklog-rotation-prelude.md"
        _write(
            root,
            f"docs/archive/{new_name}",
            "# rotation prelude\n\n"
            "## 2026-07-23 (1) — rotation prelude\n\n"
            "### 次の一手\n"
            "1. [T-098] archive boundary control\n",
        )
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        archive = _read(root, archive_rel)
        assert original_first_heading in archive
        _write(
            root,
            archive_rel,
            archive.replace(
                original_first_heading,
                f"{original_first_heading}\n\n- [T-098] archive boundary sink",
                1,
            ).replace(
                "## 2026-07-24 (5) — [T-086] PKG-2:",
                "### 次の一手\n\n## 2026-07-24 (5) — [T-086] PKG-2:",
                1,
            ),
        )
        _write(root, "docs/archive/README.md", _archive_readme(new_name))
        _assert_other_checkers_clean(root)
        replay_res = _run_check(root)
        assert replay_res.returncode == 1, replay_res.stdout
        assert "未許可のリテラル placeholder" in replay_res.stdout
        assert "expected=1, actual=0" in replay_res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # H2 + 本文の全体を新規 archive member へ移す対は緑。
    root = _build_min_repo()
    try:
        entry = place_registered_entry_in_current(root)
        worklog = _read(root, "docs/worklog.md")
        assert entry in worklog
        _write(root, "docs/worklog.md", worklog.replace(entry, "", 1))
        new_name = "worklog-rotation-new.md"
        _write(root, f"docs/archive/{new_name}", "# rotation\n\n" + entry)
        _write(root, "docs/archive/README.md", _archive_readme(new_name))
        rotated_res = _run_check(root)
        assert rotated_res.returncode == 0, rotated_res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_allowlist_is_path_bound():
    root = _build_min_repo()
    try:
        source = "output/insights/2026-07-24_e2e-real-seal.md"
        moved = "output/insights/moved.md"
        _write(root, source, _read(root, source).replace(
            _PLACEHOLDER_DEBT_INSIGHT + "\n", "", 1
        ))
        _write(root, moved, _PLACEHOLDER_DEBT_INSIGHT + "\n")
        findings = _assert_placeholder_violation(
            root,
            source,
            moved,
            "未許可のリテラル placeholder",
            "expected=1, actual=0",
        )
        assert len(findings) == 2, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_backticked_literal_is_still_detected():
    root = _build_min_repo()
    try:
        rel = "output/insights/markdown-context.md"
        _write(
            root,
            rel,
            "inline `<反映>` control\n"
            "```text\n"
            "<受入結果を反映>\n"
            "```\n",
        )
        findings = _assert_placeholder_violation(
            root, rel, "未許可のリテラル placeholder"
        )
        assert len(findings) == 2, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_verbatim_named_file_is_not_exempt():
    root = _build_min_repo()
    try:
        rel = "output/insights/new-verbatim.md"
        _write(root, rel, "verbatim suffix control: <反映>\n")
        findings = _assert_placeholder_violation(
            root, rel, "未許可のリテラル placeholder"
        )
        assert len(findings) == 1, findings
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_ledger_size_is_pinned():
    root = _build_min_repo()
    try:
        module = _load_fixture_checker(root)
        debts = sum(
            count
            for entries in module.KNOWN_PLACEHOLDER_DEBTS.values()
            for count in entries.values()
        )
        mentions = sum(
            count
            for entries in module.KNOWN_PLACEHOLDER_MENTIONS.values()
            for count in entries.values()
        )
        assert debts == 4
        assert mentions == 5
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_ledger_entries_are_pinned_exactly():
    expected = {
        (
            "KNOWN_PLACEHOLDER_DEBTS",
            "worklog-entry:4926160d0e41c9e972953e535dcce8cc1744eff78b13277cc91d722dc06129f2",
            "37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_DEBTS",
            "worklog-entry:0885598e3ddffd2a6a5c0424c3e6a65ba24f67048374cf3eefc064247e746eb7",
            "3beb84d709104086993083d461c6b511b63ffd595f2037c28f5c5ae91e046327",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_DEBTS",
            "worklog-entry:be893df535111cf91c64c141d38afa482dbca6f0a8a829a55b36ac72d8dc79bc",
            "37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_DEBTS",
            "insights-path:output/insights/2026-07-24_e2e-real-seal.md",
            "c022f2e9ee8cfaf2237eafa5c30e0c772a368c953e5ccf03a29233028bbe52fd",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "worklog-entry:1241aea6de50f3519f1cb497ff8b0fc07d4b4c2b76f35047d091bfb893aa685a",
            "abdbb38938a76268b5cf63c13309339f58f0cc996deaa13db39c3786e2f3b866",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "worklog-entry:825788c80a8f458dd12f5682450f134950c37fb0ea6ebbdaddfb26d9f9e95511",
            "80101b39632c395324f424bc9929db7a5c5b76c66b21d61e30afd52434f097ce",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "worklog-entry:825788c80a8f458dd12f5682450f134950c37fb0ea6ebbdaddfb26d9f9e95511",
            "9162d9fc17d08b52b54c4f4b1adb96a3b614ed4d944ac955de27bb0ea5b539e5",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "insights-path:output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md",
            "90d8e1f6a7f7229085d78f91ddc7bc91155bbe1ec39b44aaae2b2809daaaf5d9",
        ): 1,
        (
            "KNOWN_PLACEHOLDER_MENTIONS",
            "insights-path:output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md",
            "c66c4f6e14de10c369167108971c74fd0d1462b6a4489792efae907c5d02875c",
        ): 1,
    }
    actual = {}
    for ledger_name, ledger in (
        ("KNOWN_PLACEHOLDER_DEBTS", check_docs.KNOWN_PLACEHOLDER_DEBTS),
        ("KNOWN_PLACEHOLDER_MENTIONS", check_docs.KNOWN_PLACEHOLDER_MENTIONS),
    ):
        for scope, entries in ledger.items():
            for digest, count in entries.items():
                actual[(ledger_name, scope, digest)] = count
    assert actual == expected


def test_placeholder_guard_digest_line_boundary_contract():
    root = _build_min_repo()
    try:
        module = _load_fixture_checker(root)
        base = "digest プレースホルダ <反映>".encode("utf-8")
        lf_line = module._placeholder_logical_lines(
            (base + b"\n").decode("utf-8")
        )[0]
        crlf_line = module._placeholder_logical_lines(
            (base + b"\r\n").decode("utf-8")
        )[0]
        variants = (
            base + b" ",
            b"\xef\xbb\xbf" + base,
            "digest プレースホルダ <反映>".encode("utf-8"),
            base + b"\x0b" + "追記".encode("utf-8"),
        )
        baseline_digest = module._placeholder_line_digest(lf_line)
        assert module._placeholder_line_digest(crlf_line) == baseline_digest
        for variant in variants:
            logical = module._placeholder_logical_lines(
                variant.decode("utf-8")
            )
            assert len(logical) == 1
            assert module._placeholder_line_digest(logical[0]) != baseline_digest

        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        archive_bytes = _read(root, archive_rel).encode("utf-8")
        _write_bytes(root, archive_rel, archive_bytes.replace(b"\n", b"\r\n"))
        assert _placeholder_findings(root) == []
    finally:
        shutil.rmtree(root, ignore_errors=True)

    mutations = (
        _PLACEHOLDER_MENTION_WORKLOG_F36 + " ",
        "\ufeff" + _PLACEHOLDER_MENTION_WORKLOG_F36,
        _PLACEHOLDER_MENTION_WORKLOG_F36.replace(
            "プレースホルダ", "プレースホルダ", 1
        ),
        _PLACEHOLDER_MENTION_WORKLOG_F36 + "\v追記",
    )
    for changed in mutations:
        root = _build_min_repo()
        try:
            rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
            text = _read(root, rel)
            assert _PLACEHOLDER_MENTION_WORKLOG_F36 in text
            _write(
                root,
                rel,
                text.replace(_PLACEHOLDER_MENTION_WORKLOG_F36, changed, 1),
            )
            findings = _assert_placeholder_violation(
                root,
                "未許可のリテラル placeholder",
                "expected=1, actual=0",
            )
            assert len(findings) == 2, findings
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_missing_target_family_is_violation():
    cases = (
        ("output/insights", "output/insights: placeholder 検査の対象 directory が不在"),
        (
            "docs/archive/worklog-phase3-0722-0724.md",
            "docs/archive/worklog-*.md: placeholder 検査の対象族に実体がない",
        ),
    )
    for rel, expected in cases:
        root = _build_min_repo()
        try:
            path = os.path.join(root, rel)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            _assert_placeholder_violation(root, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        shutil.rmtree(os.path.join(root, "docs", "archive"))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert (
            "docs/archive: placeholder 検査の対象 directory が不在"
            in res.stdout
        ), res.stdout
        assert "docs/archive/README.md: ファイルが不在" in res.stdout, res.stdout
        assert "Traceback" not in res.stderr, res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_read_failures_are_aggregated_without_traceback():
    cases = ("worklog-directory", "archive-invalid-utf8")
    for case in cases:
        root = _build_min_repo()
        try:
            if case == "worklog-directory":
                path = os.path.join(root, "docs", "worklog.md")
                os.remove(path)
                os.mkdir(path)
                expected = (
                    "docs/worklog.md: placeholder 検査の列挙対象が regular file でない"
                )
            else:
                rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
                _write_bytes(root, rel, b"\xff")
                expected = f"{rel}: placeholder 検査の読取失敗"
            res = _run_check(root)
            assert res.returncode == 1, (case, res.stdout, res.stderr)
            assert re.search(
                r"^check_docs: \d+ 件の違反$", res.stdout, re.MULTILINE
            ), res.stdout
            assert expected in res.stdout, res.stdout
            assert res.stdout.count(expected) == 1, res.stdout
            assert "KNOWN_PLACEHOLDER_DEBTS の登録 digest" not in res.stdout
            assert "KNOWN_PLACEHOLDER_MENTIONS の登録 digest" not in res.stdout
            assert "Traceback" not in res.stdout, res.stdout
            assert "Traceback" not in res.stderr, res.stderr
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_unreadable_insight_does_not_mask_worklog_mismatch():
    root = _build_min_repo()
    try:
        rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        archive = _read(root, rel)
        registered = f"{_PLACEHOLDER_DEBT_WORKLOG}\n"
        assert archive.count(registered) == 2
        _write(
            root,
            rel,
            archive.replace(registered, registered * 2, 1),
        )
        _write_bytes(root, "output/insights/unrelated.md", b"\xff")
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "output/insights/unrelated.md: placeholder 検査の読取失敗" in res.stdout
        assert "insights-path scope の台帳照合を停止" in res.stdout
        assert "KNOWN_PLACEHOLDER_DEBTS の登録 digest" in res.stdout
        assert "expected=1, actual=2" in res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_safe_reader_dependency_failures_do_not_emit_derived_findings():
    # decisions.md: 正当な D1 参照を「実在しない D」と派生誤判定しない。
    root = _build_min_repo()
    try:
        _write(root, "README.md", "# living\n\nD1 を参照する。\n")
        _write_bytes(root, "docs/decisions.md", b"\xff")
        res = _run_check(root)
        prefix = "docs/decisions.md: D 見出し検査の読取失敗"
        assert res.returncode == 1, res.stdout
        assert res.stdout.count(prefix) == 1, res.stdout
        assert "実在しない D 参照" not in res.stdout, res.stdout
        assert "検査を停止" in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)
    # 通常経路では、実在しない D 参照の本来の finding が発火する。
    root = _build_min_repo()
    try:
        _write(root, "README.md", "# living\n\nD999 を参照する。\n")
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "実在しない D 参照: 'D999'" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # phase3.md: ledger だけが sink の T-001 を消失扱いしない。
    root = _build_min_repo()
    try:
        worklog = _read(root, "docs/worklog.md")
        _write(
            root,
            "docs/worklog.md",
            worklog.replace("- [T-001] consumed\n", "", 1),
        )
        _write_bytes(root, "docs/phase3.md", b"\xff")
        res = _run_check(root)
        prefix = "docs/phase3.md: living docs 検査の読取失敗"
        assert res.returncode == 1, res.stdout
        assert res.stdout.count(prefix) == 1, res.stdout
        assert "次の一手 ID [T-001]" not in res.stdout, res.stdout
        assert "検査を停止" in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # 通常の見送り台帳構造では、sink にない遷移の本来の finding が発火する。
    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/worklog.md",
            _CLEAN_WORKLOG.replace("[T-001] carry", "[T-777] carry", 1),
        )
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "次の一手 ID [T-777]" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # 見送り台帳の構造抽出失敗は空集合でなく未知状態として遷移検査を止める。
    root = _build_min_repo()
    try:
        _write(
            root,
            "docs/worklog.md",
            _CLEAN_WORKLOG.replace("[T-001] carry", "[T-777] carry", 1),
        )
        _write(
            root,
            "docs/phase3.md",
            _CLEAN_PHASE3.replace("## 見送り台帳 (synthetic)", "## broken ledger"),
        )
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "見送り台帳 sink の構造抽出失敗" in res.stdout, res.stdout
        assert "見送り台帳に依存する worklog 遷移検査を停止" in res.stdout
        assert "次の一手 ID [T-777]" not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # archive 1 件が不明なら、読めた非隣接 archive 同士を比較しない。
    root = _build_min_repo()
    try:
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        archive = _read(root, archive_rel)
        assert archive.rstrip().endswith("### 次の一手")
        _write(
            root,
            archive_rel,
            archive.rstrip() + "\n1. [T-777] unreadable middle sink\n",
        )
        unreadable_name = "worklog-archive-unreadable.md"
        later_name = "worklog-archive-later.md"
        _write_bytes(root, f"docs/archive/{unreadable_name}", b"\xff")
        _write(
            root,
            f"docs/archive/{later_name}",
            "# later archive\n\n"
            "## 2026-07-27 (1) — later archive\n\n"
            "### 次の一手\n",
        )
        _write(
            root,
            "docs/archive/README.md",
            _archive_readme(unreadable_name, later_name),
        )
        res = _run_check(root)
        prefix = (
            f"docs/archive/{unreadable_name}: "
            "placeholder 検査の読取失敗"
        )
        assert res.returncode == 1, res.stdout
        assert res.stdout.count(prefix) == 1, res.stdout
        assert "次の一手 ID [T-777]" not in res.stdout, res.stdout
        assert "検査を停止" in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # 通常の archive 構造では、archive 境界遷移の本来の finding が発火する。
    root = _build_min_repo()
    try:
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        later_name = "worklog-archive-structure-later.md"
        _write(
            root,
            archive_rel,
            _read(root, archive_rel).rstrip()
            + "\n1. [T-778] archive positive control\n",
        )
        _write(
            root,
            f"docs/archive/{later_name}",
            "# later archive\n\n"
            "## 2026-07-27 (1) — later archive\n\n"
            "### 次の一手\n",
        )
        _write(root, "docs/archive/README.md", _archive_readme(later_name))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "次の一手 ID [T-778]" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # archive entry の構造抽出失敗時は、読めた非隣接 archive を比較しない。
    root = _build_min_repo()
    try:
        archive_rel = f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
        malformed_name = "worklog-archive-structure-malformed.md"
        later_name = "worklog-archive-structure-later.md"
        _write(
            root,
            archive_rel,
            _read(root, archive_rel).rstrip()
            + "\n1. [T-778] archive positive control\n",
        )
        _write(
            root,
            f"docs/archive/{malformed_name}",
            "# readable but no worklog H2\n",
        )
        _write(
            root,
            f"docs/archive/{later_name}",
            "# later archive\n\n"
            "## 2026-07-27 (1) — later archive\n\n"
            "### 次の一手\n",
        )
        _write(
            root,
            "docs/archive/README.md",
            _archive_readme(malformed_name, later_name),
        )
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert "archive entry の構造抽出失敗" in res.stdout, res.stdout
        assert "archive 族全体に依存する順序・境界遷移検査を停止" in res.stdout
        assert "次の一手 ID [T-778]" not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_decision_heading_requires_allocator_canonical_dot():
    """check_docs と spool allocator が同じ dotted D 見出しだけを canonical とする。"""

    root = _build_min_repo()
    try:
        decisions = _read(root, "docs/decisions.md")
        _write(
            root,
            "docs/decisions.md",
            decisions.replace("## D1. placeholder", "## D1 placeholder", 1),
        )
        _assert_violation(root, "canonical D 見出しは `## D1.` で始める")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_r33_decision_heading_accepts_title_after_canonical_period():
    """R33 の section scan は実際の `D570. title` 見出しを受理する。"""

    assert check_docs.R33_DECISION_HEADING_RE.match(
        "D570. dev-wave docs 予算満杯時の運用"
    ) is not None


def test_r33_role_decision_pin_accepts_exact_pending_fragment():
    root = _build_min_repo()
    try:
        decisions = _read(root, "docs/decisions.md")
        _write(
            root,
            "docs/decisions.md",
            decisions.replace(_SYNTHETIC_R33_DECISION_SECTION, "", 1),
        )
        _write(
            root,
            "docs/spool/decisions/"
            "2026-08-20-dev-wave-t1142-n-pilot-admission-redesign-1.md",
            _SYNTHETIC_R33_PENDING_FRAGMENT,
        )
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_r33_source_contract_binds_entry_to_observation_roles_dictionary():
    root = _build_min_repo()
    try:
        rel = "orchestrator/campaign/s8b_holdout_admission.py"
        source = _read(root, rel)
        entry = (
            '    "n_pilot_r33": {\n'
            '        "generation_id": "n-pilot-r33",\n'
            '        "pilot_rounds": 33,\n'
            '        "allocation_count": 3,\n'
            '        "cell_count": 12,\n'
            '        "schedule_row_count": 396,\n'
            '        "decision_pin": "t1142-n-pilot-r33-admission-authority",\n'
            "    },\n"
        )
        assert source.count(entry) == 1
        source = source.replace(entry, "", 1)
        source += "\n_DEAD_R33_ROLE_CONTRACT = {\n" + entry + "}\n"
        _write(root, rel, source)
        _assert_violation(root, "R33 role contract entry は exact 1 件が必要")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_r33_source_contract_ignores_entry_in_docstring_within_observation_roles():
    root = _build_min_repo()
    try:
        rel = "orchestrator/campaign/s8b_holdout_admission.py"
        source = _read(root, rel)
        entry = (
            '    "n_pilot_r33": {\n'
            '        "generation_id": "n-pilot-r33",\n'
            '        "pilot_rounds": 33,\n'
            '        "allocation_count": 3,\n'
            '        "cell_count": 12,\n'
            '        "schedule_row_count": 396,\n'
            '        "decision_pin": "t1142-n-pilot-r33-admission-authority",\n'
            "    },\n"
        )
        assert source.count(entry) == 1
        decoy = '    "R33_decoy": """\n' + entry + '    """,\n'
        source = source.replace(entry, decoy, 1)
        _write(root, rel, source)
        _assert_violation(root, "R33 role contract entry は exact 1 件が必要")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_r33_source_contract_ignores_role_literal_in_docstring():
    root = _build_min_repo()
    try:
        rel = "orchestrator/campaign/s8b_holdout_admission.py"
        source = _read(root, rel)
        role_line = 'OBSERVATION_ROLE_N_PILOT_R33 = "n_pilot_r33"\n'
        assert source.count(role_line) == 1
        source = source.replace(role_line, "", 1)
        docstring = 'ROLE_DOC = """\n' + role_line + '"""\n'
        source = source.replace(
            "from __future__ import annotations\n",
            "from __future__ import annotations\n" + docstring,
            1,
        )
        _write(root, rel, source)
        _assert_violation(
            root,
            "R33 role literal は OBSERVATION_ROLE_N_PILOT_R33 の exact 1 件が必要",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_r33_decision_contract_rejects_ambiguous_r33_sections():
    root = _build_min_repo()
    try:
        decisions = _read(root, "docs/decisions.md")
        later_invalid = _SYNTHETIC_R33_DECISION_SECTION.replace(
            "## D570.", "## D571.", 1,
        ).replace("pilot_rounds=33", "pilot_rounds=32", 1)
        _write(root, "docs/decisions.md", decisions + "\n" + later_invalid)
        _assert_violation(root, "R33 decision section が曖昧")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    ("source_literal", "replacement"),
    [
        ('"generation_id": "n-pilot-r33"',
         '"generation_id": "n-pilot-r32"'),
        ('"generation_id": "n-pilot-r33",\n        "pilot_rounds": 33,',
         '"generation_id": "n-pilot-r33",\n        "pilot_rounds": 32,'),
        ('"allocation_count": 3,\n        "cell_count": 12,',
         '"allocation_count": 2,\n        "cell_count": 12,'),
    ],
    ids=["generation", "round", "allocation"],
)
def test_r33_role_contract_generation_round_allocation_mismatch_fails(
    source_literal: str,
    replacement: str,
):
    root = _build_min_repo()
    try:
        rel = "orchestrator/campaign/s8b_holdout_admission.py"
        source = _read(root, rel)
        assert source.count(source_literal) == 1
        _write(root, rel, source.replace(source_literal, replacement, 1))
        _assert_violation(root, "R33 role contract の role/generation/round/allocation/pin")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_r33_decision_contract_mismatch_fails():
    root = _build_min_repo()
    try:
        rel = "docs/decisions.md"
        decisions = _read(root, rel)
        _write(root, rel, decisions.replace("pilot_rounds=33", "pilot_rounds=32", 1))
        _assert_violation(root, "R33 role contract に対応する decision section がない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_r33_role_decision_pin_requires_canonical_or_pending_contract():
    root = _build_min_repo()
    try:
        rel = "docs/decisions.md"
        decisions = _read(root, rel)
        _write(
            root,
            rel,
            decisions.replace(_SYNTHETIC_R33_DECISION_SECTION, "", 1),
        )
        _assert_violation(root, "R33 role contract に対応する decision section がない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_safe_reader_rejects_worklog_symlink_and_fifo_without_hang():
    root = _build_min_repo()
    external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_")
    try:
        worklog = os.path.join(root, "docs", "worklog.md")
        external_rel = "external-worklog.md"
        _write(
            external,
            external_rel,
            "# external\n\n"
            "## EXTERNAL-SENTINEL\n\n"
            "external unauthorized: <受入結果を反映>\n",
        )
        os.remove(worklog)
        os.symlink(os.path.join(external, external_rel), worklog)
        res = _run_check(root, timeout=5)
        assert res.returncode == 1, res.stdout
        assert re.search(r"^check_docs: \d+ 件の違反$", res.stdout, re.MULTILINE)
        assert "docs/worklog.md" in res.stdout
        assert "次の一手の保存則を停止" in res.stdout
        assert "EXTERNAL-SENTINEL" not in res.stdout, res.stdout
        assert "未許可のリテラル placeholder" not in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(external, ignore_errors=True)

    root = _build_min_repo()
    try:
        worklog = os.path.join(root, "docs", "worklog.md")
        os.remove(worklog)
        os.mkfifo(worklog)
        res = _run_check(root, timeout=5)
        assert res.returncode == 1, res.stdout
        assert re.search(r"^check_docs: \d+ 件の違反$", res.stdout, re.MULTILINE)
        assert "docs/worklog.md" in res.stdout
        assert "regular file" in res.stdout
        assert "次の一手の保存則を停止" in res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # placeholder 列挙を経由しない decisions.md で safe-reader 単独の拒否を固定する。
    root = _build_min_repo()
    external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_")
    try:
        decisions = os.path.join(root, "docs", "decisions.md")
        _write(
            external,
            "external-decisions.md",
            "## D4242 EXTERNAL-SAFE-READER-SENTINEL\n"
            "## D4242 EXTERNAL-SAFE-READER-SENTINEL\n",
        )
        os.remove(decisions)
        os.symlink(
            os.path.join(external, "external-decisions.md"),
            decisions,
        )
        res = _run_check(root, timeout=5)
        assert res.returncode == 1, res.stdout
        assert "docs/decisions.md: D 見出し検査の読取失敗" in res.stdout
        assert "symlink を含む path は読まない" in res.stdout
        assert "D4242 の見出しが重複" not in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(external, ignore_errors=True)

    root = _build_min_repo()
    try:
        decisions = os.path.join(root, "docs", "decisions.md")
        os.remove(decisions)
        os.mkfifo(decisions)
        res = _run_check(root, timeout=5)
        assert res.returncode == 1, res.stdout
        assert "docs/decisions.md: D 見出し検査の読取失敗" in res.stdout
        assert "regular file でないため読まない" in res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_placeholder_guard_rejects_symlinked_target_directories():
    cases = (
        (
            "docs/archive",
            _PLACEHOLDER_ARCHIVE_NAME,
            "",
            "docs/archive: placeholder 検査の対象 directory が symlink",
        ),
        (
            "output/insights",
            "2026-07-24_e2e-real-seal.md",
            _PLACEHOLDER_DEBT_INSIGHT + "\n",
            "output/insights: placeholder 検査の対象 directory が symlink",
        ),
    )
    for rel, member, content, expected in cases:
        root = _build_min_repo()
        external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_")
        try:
            if rel == "docs/archive":
                content = _read(
                    root, f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}"
                )
                _write(
                    external,
                    "README.md",
                    "# EXTERNAL-ARCHIVE-README-SENTINEL\n\n"
                    "## 現在の収容物\n",
                )
            _write(external, member, content)
            external_marker = (
                "worklog-external-unapproved.md"
                if rel == "docs/archive"
                else "external-unapproved.md"
            )
            _write(
                external,
                external_marker,
                "# external\n\n## EXTERNAL-DIRECTORY-SENTINEL\n\n"
                "external unauthorized: <受入結果を反映>\n",
            )
            path = os.path.join(root, rel)
            shutil.rmtree(path)
            os.symlink(external, path)
            findings = _assert_placeholder_violation(root, expected)
            assert findings
            res = _run_check(root, timeout=5)
            assert res.returncode == 1, res.stdout
            assert expected in res.stdout, res.stdout
            assert external_marker not in res.stdout, res.stdout
            assert "EXTERNAL-DIRECTORY-SENTINEL" not in res.stdout, res.stdout
            assert "EXTERNAL-ARCHIVE-README-SENTINEL" not in res.stdout, res.stdout
            assert "未許可のリテラル placeholder" not in res.stdout, res.stdout
            assert "Traceback" not in res.stdout + res.stderr
        finally:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(external, ignore_errors=True)


def test_placeholder_guard_rejects_symlinked_and_non_regular_members():
    cases = (
        (
            f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}",
            "archive-symlink",
        ),
        (
            "output/insights/2026-07-24_e2e-real-seal.md",
            "insight-symlink",
        ),
        (
            f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}",
            "archive-directory",
        ),
        (
            "output/insights/2026-07-24_e2e-real-seal.md",
            "insight-directory",
        ),
        (
            f"docs/archive/{_PLACEHOLDER_ARCHIVE_NAME}",
            "archive-fifo",
        ),
        (
            "output/insights/2026-07-24_e2e-real-seal.md",
            "insight-fifo",
        ),
    )
    for rel, case in cases:
        root = _build_min_repo()
        external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_")
        try:
            content = _read(root, rel)
            path = os.path.join(root, rel)
            os.remove(path)
            if case.endswith("symlink"):
                target = os.path.join(external, "registered.md")
                _write(
                    external,
                    "registered.md",
                    content + "\nexternal unauthorized: <受入結果を反映>\n",
                )
                os.symlink(target, path)
            elif case.endswith("fifo"):
                os.mkfifo(path)
            else:
                os.mkdir(path)
            findings = _assert_placeholder_violation(
                root,
                rel,
                "placeholder 検査の対象 member が regular file でない",
            )
            assert findings
            res = _run_check(root, timeout=5)
            assert res.returncode == 1, res.stdout
            assert rel in res.stdout, res.stdout
            assert (
                "placeholder 検査の対象 member が regular file でない"
                in res.stdout
            ), res.stdout
            assert "未許可のリテラル placeholder" not in res.stdout, res.stdout
            assert "Traceback" not in res.stdout + res.stderr
        finally:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(external, ignore_errors=True)


def test_placeholder_guard_non_exact_literals_are_not_detected():
    """exact 3 文字列は確定裁定であり、意味的に同じ別表記・HTML entity・
    予測値の先書きは本 gate の射程外である (裁定パッケージ [T-100])。
    """

    root = _build_min_repo()
    try:
        _write(
            root,
            "output/insights/non-exact.md",
            "<結果を反映>\n"
            "<反映済み>\n"
            "&lt;反映&gt;\n"
            "受入結果を反映\n"
            "検査は 123 passed と予測する\n",
        )
        assert _placeholder_findings(root) == []
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _read(root: str, rel: str) -> str:
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return f.read()


def _pad_to_bytes(root: str, rel: str, target: int) -> None:
    text = _read(root, rel)
    current = len(text.encode("utf-8"))
    assert current <= target
    _write(root, rel, text + ("\n" * (target - current)))


def _rewrite_matching_lines(
    root: str,
    rel: str,
    predicate,
    rewrite,
    expected: int = 1,
) -> None:
    lines = _read(root, rel).splitlines(keepends=True)
    matched = sum(1 for line in lines if predicate(line))
    assert matched == expected, (rel, matched, expected)
    _write(
        root,
        rel,
        "".join(
            rewrite(line) if predicate(line) else line
            for line in lines
        ),
    )


def _insert_before_unique_marker(root: str, rel: str, marker: str, addition: str) -> None:
    text = _read(root, rel)
    assert text.count(marker) == 1, (rel, marker, text.count(marker))
    _write(root, rel, text.replace(marker, addition + marker, 1))


def _set_condition_18_trigger_and_contract(root: str, replacement: str) -> None:
    """合成入口と合成 checker の条件18 trigger を同じ単点へ変異する。"""

    current = "親のテスト・受入前と赤処理前"
    _rewrite_matching_lines(
        root,
        ".claude/commands/dev-wave.md",
        lambda line: line.startswith("| 18 |"),
        lambda line: line.replace(current, replacement, 1),
    )
    checker_rel = "tools/check_docs.py"
    checker_text = _read(root, checker_rel)
    old_assignment = f'    "18": "{current}",'
    new_assignment = f'    "18": "{replacement}",'
    assert checker_text.count(old_assignment) == 1
    _write(
        root,
        checker_rel,
        checker_text.replace(old_assignment, new_assignment, 1),
    )


def _mutate_command_guard(root: str, case: str) -> None:
    if case == "command_byte_over":
        _pad_to_bytes(
            root,
            ".claude/commands/rulings.md",
            check_docs.COMMAND_LIMITS[
                ".claude/commands/rulings.md"
            ].max_bytes + 1,
        )
    elif case == "self_byte_over":
        _pad_to_bytes(
            root,
            "docs/skill-self-improvement.md",
            check_docs.SELF_LIMITS[
                "docs/skill-self-improvement.md"
            ].max_bytes + 1,
        )
    elif case == "long_line":
        rel = ".claude/commands/rulings.md"
        _write(root, rel, _read(root, rel) + ("x" * 181) + "\n")
    elif case == "unregistered_command":
        _write(root, ".claude/commands/extra.md", "# extra\n")
    elif case == "registered_command_deleted":
        os.remove(os.path.join(root, ".claude/commands/rulings.md"))
    elif case == "arguments_missing":
        rel = ".claude/commands/rulings.md"
        _write(root, rel, _read(root, rel).replace("$ARGUMENTS", "arguments"))
    elif case == "frontmatter_key_changed":
        rel = ".claude/commands/rulings.md"
        _write(root, rel, _read(root, rel).replace(
            "argument-hint:", "argument-hint-renamed:", 1
        ))
    elif case == "frontmatter_duplicate":
        rel = ".claude/commands/rulings.md"
        _write(root, rel, _read(root, rel).replace(
            "description: synthetic rulings",
            "description: synthetic rulings\ndescription: duplicate",
            1,
        ))
    elif case == "frontmatter_malformed":
        rel = ".claude/commands/rulings.md"
        _write(root, rel, _read(root, rel).replace("---", "not-frontmatter", 1))
    elif case == "disable_value_changed":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel).replace(
            "disable-model-invocation: true",
            "disable-model-invocation: false",
            1,
        ))
    elif case == "command_startup_wave_pre_form":
        rel = ".claude/commands/dev-wave.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                _SYNTHETIC_DEV_WAVE_COMMAND_START_SECTION,
                _PRE_WAVE_DEV_WAVE_COMMAND_START_SECTION,
                1,
            ),
        )
    elif case == "command_startup_routing_blockquoted":
        rel = ".claude/commands/dev-wave.md"
        current = (
            "- wave 開始時に `docs/skill-self-improvement.md` の"
            "発火 gate・routing・dev-wave を読み、\n"
            "  専用 handoff に「dev-wave 改善候補」節を作る。\n"
        )
        blockquoted = (
            "> - wave 開始時に `docs/skill-self-improvement.md` の"
            "発火 gate・routing・dev-wave を読み、\n"
            ">   専用 handoff に「dev-wave 改善候補」節を作る。\n"
        )
        assert _read(root, rel).count(current) == 1
        _write(root, rel, _read(root, rel).replace(current, blockquoted, 1))
    elif case == "stage6-relocated":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        stage6_lines = _SYNTHETIC_STAGE6_WAITER_ITEM.splitlines(keepends=True)
        relocated = (
            stage6_lines[1]
            + stage6_lines[0]
        )
        assert text.count(_SYNTHETIC_STAGE6_WAITER_ITEM) == 1
        _write(
            root,
            rel,
            text.replace(_SYNTHETIC_STAGE6_WAITER_ITEM, relocated, 1),
        )
    elif case == "stage9-deleted":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        stage9_heading = _SYNTHETIC_STAGE9_WAITER_ITEM.splitlines(keepends=True)[0]
        assert text.count(_SYNTHETIC_STAGE9_WAITER_ITEM) == 1
        _write(
            root,
            rel,
            text.replace(_SYNTHETIC_STAGE9_WAITER_ITEM, stage9_heading, 1),
        )
    elif case == "dw-c00-fenced":
        rel = "docs/dev-wave/core.md"
        text = _read(root, rel)
        fenced = "```text\n" + _SYNTHETIC_DW_C00_WAITER_LINE + "```\n"
        assert text.count(_SYNTHETIC_DW_C00_WAITER_LINE) == 1
        _write(
            root,
            rel,
            text.replace(_SYNTHETIC_DW_C00_WAITER_LINE, fenced, 1),
        )
    elif case == "dw-o01-wrong-pid-source":
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        assert text.count(_SYNTHETIC_DW_O01_WAITER_LINE) == 1
        _write(
            root,
            rel,
            text.replace("`--pid-file`", "`--pid`", 1),
        )
    elif case == "target-symlinked":
        path = os.path.join(root, "tools", "dev_wave_wait.py")
        os.remove(path)
        os.symlink("dev_wave_land.py", path)
    elif case == "decoy-optional":
        rel = ".claude/commands/dev-wave.md"
        _insert_before_unique_marker(
            root,
            rel,
            "## 段 dispatch",
            "参考例であり急ぐ場合は手動投入してよい。\n\n",
        )
    elif case == "decoy-negated":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        negated = (
            "6. **レビュー・fix (codex 並列):** 敵対レビュー 2 本、fix、変異 matrix、受入再走を行う。\n"
            "   受入投入は `tools/dev_wave_wait.py acceptance --lease-optional` を使わない。\n"
        )
        assert text.count(_SYNTHETIC_STAGE6_WAITER_ITEM) == 1
        _write(
            root,
            rel,
            text.replace(_SYNTHETIC_STAGE6_WAITER_ITEM, negated, 1),
        )
    elif case == "decoy-lease-optional-omitted":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        omitted = (
            "6. **レビュー・fix (codex 並列):** 敵対レビュー 2 本、fix、変異 matrix、受入再走を行う。\n"
            "   受入投入は `tools/dev_wave_wait.py acceptance` を使う。\n"
        )
        assert text.count(_SYNTHETIC_STAGE6_WAITER_ITEM) == 1
        _write(
            root,
            rel,
            text.replace(_SYNTHETIC_STAGE6_WAITER_ITEM, omitted, 1),
        )
    elif case == "decoy-lease-optional-typo":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        typo = (
            "6. **レビュー・fix (codex 並列):** 敵対レビュー 2 本、fix、変異 matrix、受入再走を行う。\n"
            "   受入投入は `tools/dev_wave_wait.py acceptance --lease-optonal` を使う。\n"
        )
        assert text.count(_SYNTHETIC_STAGE6_WAITER_ITEM) == 1
        _write(
            root,
            rel,
            text.replace(_SYNTHETIC_STAGE6_WAITER_ITEM, typo, 1),
        )
    elif case == "decoy-blockquoted":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        stage6_lines = _SYNTHETIC_STAGE6_WAITER_ITEM.splitlines(keepends=True)
        blockquoted = stage6_lines[0] + "".join(
            "> " + line for line in stage6_lines[1:]
        )
        assert text.count(_SYNTHETIC_STAGE6_WAITER_ITEM) == 1
        _write(
            root,
            rel,
            text.replace(_SYNTHETIC_STAGE6_WAITER_ITEM, blockquoted, 1),
        )
    elif case == "pre-wave-form":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        pre_wave = (
            "6. **レビュー・fix (codex 並列):** 敵対レビュー 2 本、fix、変異 matrix、受入再走を行う。\n"
            "   受入直前に runbook の受入 lease を `claim` し、`acquired` のときだけ投入する。\n"
        )
        assert text.count(_SYNTHETIC_STAGE6_WAITER_ITEM) == 1
        _write(
            root,
            rel,
            text.replace(_SYNTHETIC_STAGE6_WAITER_ITEM, pre_wave, 1),
        )
    elif case == "reference_section_deleted":
        rel = "docs/dev-wave/mutation.md"
        _write(root, rel, _read(root, rel).replace(
            "## DW-M05 — synthetic", "### removed DW-M05", 1
        ))
    elif case == "reference_section_duplicated":
        rel = "docs/dev-wave/mutation.md"
        _write(root, rel, _read(root, rel) + "\n## DW-M05 — duplicate\n")
    elif case == "stage2_operations_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 2 preflight |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: "",
        )
    elif case == "stage2_o03_readded":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 2 preflight |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: line.replace(
                "`DW-O02`, `DW-O05`", "`DW-O02`, `DW-O03`, `DW-O05`", 1
            ),
        )
    elif case == "stage3_o03_readded":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 3 preflight |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: line.replace(
                "`DW-O02`, `DW-O05`", "`DW-O02`, `DW-O03`, `DW-O05`", 1
            ),
        )
    elif case == "stage3_o13_readded":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 3 preflight |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: line.replace("`DW-O05`", "`DW-O05`, `DW-O13`", 1),
        )
    elif case == "stage6_m07_readded":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 6 |")
            and "`docs/dev-wave/mutation.md`" in line,
            lambda line: line.replace(
                "`DW-M06`, `DW-M08`", "`DW-M06`, `DW-M07`, `DW-M08`", 1
            ),
        )
    elif case == "stage6_s05_inheritance_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 6 |")
            and "`DW-S05-A`" in line,
            lambda line: "",
        )
    elif case == "stage6_all_operations_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 6 |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: "",
        )
    elif case == "stage6_o25_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 6 |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: line.replace(", `DW-O25`", "", 1),
        )
    elif case == "stage8_operations_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 8 preflight |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: "",
        )
    elif case == "stage8_self_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 8 preflight |")
            and "`docs/skill-self-improvement.md`" in line,
            lambda line: "",
        )
    elif case == "stage9_land_operation_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 段 9 |")
            and "`docs/dev-wave/operations.md`" in line,
            lambda line: "",
        )
    elif case == "condition_o13_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 13 |"),
            lambda line: "",
        )
    elif case == "condition_18_o18_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 18 |"),
            lambda line: line.replace("`DW-O18`, ", "", 1),
        )
    elif case == "condition_18_o26_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 18 |"),
            lambda line: line.replace(", `DW-O26`", "", 1),
        )
    elif case == "condition_18_trigger_broadened":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 18 |"),
            lambda line: line.replace(
                check_docs.CONDITION_TRIGGER_CONTRACT["18"],
                "親のテスト・受入と赤処理",
                1,
            ),
        )
    elif case == "condition_18_run_point_deleted":
        _set_condition_18_trigger_and_contract(root, "親の赤処理前")
    elif case == "condition_18_red_point_deleted":
        _set_condition_18_trigger_and_contract(root, "親のテスト・受入前")
    elif case == "condition_all_operations_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: any(
                line.startswith(f"| {key} |")
                for key in _OPERATION_CONDITION_KEYS
            ),
            lambda line: "",
            expected=len(_OPERATION_CONDITION_KEYS),
        )
    elif case == "condition_supervisor_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 22 |"),
            lambda line: "",
        )
    elif case == "condition_land_operation_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 23 |"),
            lambda line: "",
        )
    elif case == "condition_waiter_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 24 |"),
            lambda line: "",
        )
    elif case == "condition_25_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 25 |"),
            lambda line: "",
        )
    elif case == "condition_25_trigger_broadened":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 25 |"),
            lambda line: line.replace(
                "main を進める land を起動する直前",
                "local main を取り込む直前",
                1,
            ),
        )
    elif case == "condition_26_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 26 |"),
            lambda line: "",
        )
    elif case == "condition_26_trigger_broadened":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 26 |"),
            lambda line: line.replace(
                "起動/待機/検査/submodule/取込/fix前",
                "起動/待機/検査/submodule/取込/fix前後",
                1,
            ),
        )
    elif case == "condition_26_target_changed":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 26 |"),
            lambda line: line.replace("`DW-C01`", "`DW-C00`", 1),
        )
    elif case == "condition_27_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 27 |"),
            lambda line: "",
        )
    elif case == "condition_27_trigger_broadened":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 27 |"),
            lambda line: line.replace(
                "land 成功後の自己撤去直前",
                "land 前後",
                1,
            ),
        )
    elif case == "condition_27_target_changed":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 27 |"),
            lambda line: line.replace("`DW-O28`", "`DW-O27`", 1),
        )
    elif case == "self_heading_deleted":
        rel = "docs/skill-self-improvement.md"
        _write(root, rel, _read(root, rel).replace(
            "## 発火 gate\n", "", 1
        ))
    elif case == "self_h3_deleted":
        rel = "docs/skill-self-improvement.md"
        _write(root, rel, _read(root, rel).replace(
            "### cleanup-branches\n", "", 1
        ))
    elif case == "self_next_tasks_h3_deleted":
        rel = "docs/skill-self-improvement.md"
        _write(root, rel, _read(root, rel).replace(
            "### next-tasks\n", "", 1
        ))
    elif case == "self_long_line":
        rel = "docs/skill-self-improvement.md"
        _write(root, rel, _read(root, rel) + ("x" * 101) + "\n")
    elif case == "self_reference_deleted":
        rel = ".claude/commands/rulings.md"
        _write(root, rel, _read(root, rel).replace(
            "docs/skill-self-improvement.md", "self contract omitted", 1
        ))
    elif case == "self_l2_admission_wave_pre_form":
        rel = "docs/skill-self-improvement.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                _SYNTHETIC_SELF_ROUTING_SECTION,
                _PRE_WAVE_SELF_ROUTING_SECTION,
                1,
            ),
        )
    elif case == "reference_orphan_h2":
        rel = "docs/dev-wave/operations.md"
        _insert_before_unique_marker(
            root,
            rel,
            "## DW-O25 —",
            "## DW-X99 — orphan\n\nbody\n\n",
        )
    elif case == "dispatch_heading_duplicated":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel) + "\n## 段 dispatch\n\n")
    elif case == "dispatch_heading_missing":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel).replace(
            "## 条件 dispatch", "## 条件 dispatch omitted", 1
        ))
    elif case == "d2_rollback_body_deleted":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        changed = re.sub(
            r"条件には最遅読了段がある。.*?旧成果物を流用してはならない。\n\n",
            "",
            text,
            count=1,
            flags=re.DOTALL,
        )
        assert changed != text
        _write(root, rel, changed)
    elif case == "d4_inheritance_body_deleted":
        rel = ".claude/commands/dev-wave.md"
        text = _read(root, rel)
        changed = re.sub(
            r"段 6 で fix を codex へ再投する子は、.*?"
            r"fix 操作の直前に読む。\n\n",
            "",
            text,
            count=1,
            flags=re.DOTALL,
        )
        assert changed != text
        _write(root, rel, changed)
    elif case == "codex_command_contract_deleted":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel).replace(
            "Codex `role=author`", "Claude `role=author`", 1,
        ))
    elif case == "codex_core_contract_deleted":
        rel = "docs/dev-wave/core.md"
        _write(root, rel, _read(root, rel).replace(
            "親は直接編集しない", "親も直接編集できる", 1,
        ))
    elif case == "codex_worker_contract_deleted":
        rel = "docs/dev-wave/workers.md"
        _write(root, rel, _read(root, rel).replace(
            "親が直接直さない", "親が直接直す", 1,
        ))
    elif case == "s09_land_route_deleted":
        rel = "docs/dev-wave/core.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                check_docs.DEV_WAVE_LAND_UNIQUE_ROUTE_LITERAL,
                "land route omitted",
                1,
            ),
        )
    elif case == "s09_acceptance_order_deleted":
        rel = "docs/dev-wave/core.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                _S09_ACCEPTANCE_ORDER_LITERAL,
                "acceptance order omitted",
                1,
            ),
        )
    elif case == "core_land_helper_outside_s09":
        rel = "docs/dev-wave/core.md"
        _write(root, rel, _read(root, rel) + "\ntools/dev_wave_land.py\n")
    elif case == "o23_land_helper_deleted":
        rel = "docs/dev-wave/operations.md"
        sections = check_docs._reference_id_sections(_read(root, rel), "DW-O23")
        assert len(sections) == 1
        _write(
            root,
            rel,
            _read(root, rel).replace(
                sections[0],
                sections[0].replace("`tools/dev_wave_land.py`", "helper omitted", 1),
                1,
            ),
        )
    elif case == "operations_land_helper_outside_o23":
        rel = "docs/dev-wave/operations.md"
        _insert_before_unique_marker(
            root,
            rel,
            "## DW-O23 —",
            "tools/dev_wave_land.py\n\n",
        )
    elif case == "o25_contract_weakened":
        rel = "docs/dev-wave/operations.md"
        current = "480 秒以内の rc=0 を必須とする"
        assert _read(root, rel).count(current) == 1
        _write(
            root,
            rel,
            _read(root, rel).replace(current, "赤でも警告に留める", 1),
        )
    elif case == "o25_before_o01":
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        assert text.count(_SYNTHETIC_DW_O25_SECTION) == 1
        text = text.replace(
            "\n\n" + _SYNTHETIC_DW_O25_SECTION.rstrip("\n"),
            "",
            1,
        )
        insertion = text.index("## DW-O01 ")
        _write(
            root,
            rel,
            text[:insertion] + _SYNTHETIC_DW_O25_SECTION + text[insertion:],
        )
    elif case == "o26_section_deleted":
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        _, section_slices = check_docs._h2_section_slices(text)
        sections = section_slices["DW-O26 — 焦点走の consumer test 拡張"]
        assert len(sections) == 1
        _write(
            root,
            rel,
            text.replace(sections[0], "", 1),
        )
    elif case == "o26_heading_only":
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        _, section_slices = check_docs._h2_section_slices(text)
        sections = section_slices["DW-O26 — 焦点走の consumer test 拡張"]
        assert len(sections) == 1
        section = sections[0]
        heading = section.splitlines()[0] + "\n"
        _write(root, rel, text.replace(section, heading, 1))
    elif case == "o26_contract_weakened":
        rel = "docs/dev-wave/operations.md"
        current = "静的レビューが見落とした破れを"
        assert _read(root, rel).count(current) == 1
        _write(
            root,
            rel,
            _read(root, rel).replace(
                current, "静的レビューが見落とした差分を", 1
            ),
        )
    elif case == "o28_section_deleted":
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        _, section_slices = check_docs._h2_section_slices(text)
        sections = section_slices["DW-O28 — land 後の自己撤去"]
        assert len(sections) == 1
        _write(root, rel, text.replace(sections[0], "", 1))
    elif case == "o28_heading_only":
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        _, section_slices = check_docs._h2_section_slices(text)
        sections = section_slices["DW-O28 — land 後の自己撤去"]
        assert len(sections) == 1
        section = sections[0]
        heading = section.splitlines()[0] + "\n"
        _write(root, rel, text.replace(section, heading, 1))
    elif case == "o28_contract_weakened":
        rel = "docs/dev-wave/operations.md"
        current = "他へ引き渡さない"
        assert _read(root, rel).count(current) == 1
        _write(
            root,
            rel,
            _read(root, rel).replace(current, "他へ引き渡してよい", 1),
        )
    elif case == "codex_skill_deleted":
        os.remove(os.path.join(
            root, ".agents", "skills", "dev-wave", "SKILL.md"
        ))
    elif case == "codex_skill_extra_file":
        _write(root, ".agents/skills/dev-wave/README.md", "# extra\n")
    elif case == "codex_skill_name_changed":
        rel = ".agents/skills/dev-wave/SKILL.md"
        _write(root, rel, _read(root, rel).replace(
            "name: dev-wave", "name: dev-wave-renamed", 1,
        ))
    elif case == "codex_skill_adapter_deleted":
        rel = ".agents/skills/dev-wave/SKILL.md"
        literal = "docs/dev-wave/workers.md"
        assert _read(root, rel).count(literal) == 1
        _write(root, rel, _read(root, rel).replace(
            literal, "common dispatcher omitted", 1,
        ))
    elif case == "codex_skill_natural_language_stop_contract_deleted":
        rel = ".agents/skills/dev-wave/SKILL.md"
        literal = check_docs.CODEX_DEV_WAVE_NATURAL_LANGUAGE_STOP_LITERAL
        assert _read(root, rel).count(literal) == 1
        _write(root, rel, _read(root, rel).replace(
            literal, "natural-language stop contract omitted", 1,
        ))
    elif case == "codex_skill_protected_path_authoring_contract_deleted":
        rel = ".agents/skills/dev-wave/SKILL.md"
        literal = check_docs.CODEX_DEV_WAVE_PROTECTED_PATH_AUTHORING_LITERAL
        assert _read(root, rel).count(literal) == 1
        _write(root, rel, _read(root, rel).replace(
            literal, "protected-path authoring contract omitted", 1,
        ))
    elif case == "codex_startup_wave_pre_form":
        rel = ".agents/skills/dev-wave/SKILL.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                _SYNTHETIC_CODEX_DEV_WAVE_START_SECTION,
                _PRE_WAVE_CODEX_DEV_WAVE_START_SECTION,
                1,
            ),
        )
    elif case == "codex_startup_routing_moved":
        rel = ".agents/skills/dev-wave/SKILL.md"
        item = (
            "4. `docs/skill-self-improvement.md` の発火 gate・routing・"
            "dev-wave 終端を読み、専用 handoff に\n"
            "   `dev-wave 改善候補` 節を作る。\n"
        )
        text = _read(root, rel)
        assert text.count(item) == 1
        text = text.replace(item, "", 1)
        marker = "## Codex 向けに適合する\n\n"
        assert text.count(marker) == 1
        _write(root, rel, text.replace(marker, marker + item + "\n", 1))
    elif case == "codex_skill_stage9_land_literal_deleted":
        rel = ".agents/skills/dev-wave/SKILL.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                check_docs.CODEX_DEV_WAVE_STAGE9_LAND_LITERAL,
                "Stage 9 Codex land contract omitted.",
                1,
            ),
        )
    elif case == "single_dispatch_agents_marker_deleted":
        rel = "AGENTS.md"
        text = _read(root, rel)
        assert text.count(_SYNTHETIC_SINGLE_DISPATCH_DECLARATION) == 1
        _write(
            root,
            rel,
            text.replace(
                _SYNTHETIC_SINGLE_DISPATCH_DECLARATION,
                "single dispatch declaration omitted",
                1,
            ),
        )
    elif case == "single_dispatch_agents_projection_deleted":
        rel = "AGENTS.md"
        text = _read(root, rel)
        original = f"{_SYNTHETIC_SINGLE_DISPATCH_PROJECTION_HEADING}\n"
        assert text.count(original) == 1
        _write(root, rel, text.replace(original, "projection omitted\n", 1))
    elif case == "single_dispatch_agents_projection_path_deleted":
        rel = "AGENTS.md"
        text = _read(root, rel)
        original = "/tmp/synthetic-required.md"
        assert text.count(original) == 1
        _write(root, rel, text.replace(original, "synthetic-required.md", 1))
    elif case == "single_dispatch_agents_projection_path_placeholder_only":
        rel = "AGENTS.md"
        text = _read(root, rel)
        original = "/tmp/synthetic-required.md"
        assert text.count(original) == 1
        _write(root, rel, text.replace(original, "絶対パス", 1))
    elif case == "single_dispatch_agents_projection_stop_deleted":
        rel = "AGENTS.md"
        text = _read(root, rel)
        original = "読めなければ即停止"
        assert text.count(original) == 1
        _write(root, rel, text.replace(original, "読めなければ停止", 1))
    elif case in {
        "single_dispatch_agents_comment_decoy",
        "single_dispatch_agents_fence_decoy",
        "single_dispatch_agents_blockquote_decoy",
        "single_dispatch_agents_indented_code_decoy",
    }:
        rel = "AGENTS.md"
        text = _read(root, rel)
        original = f"`{_SYNTHETIC_SINGLE_DISPATCH_DECLARATION}`\n"
        assert text.count(original) == 1
        replacement = {
            "single_dispatch_agents_comment_decoy": (
                f"<!-- {_SYNTHETIC_SINGLE_DISPATCH_DECLARATION} -->\n"
            ),
            "single_dispatch_agents_fence_decoy": (
                f"```text\n{_SYNTHETIC_SINGLE_DISPATCH_DECLARATION}\n```\n"
            ),
            "single_dispatch_agents_blockquote_decoy": (
                f"> {_SYNTHETIC_SINGLE_DISPATCH_DECLARATION}\n"
            ),
            "single_dispatch_agents_indented_code_decoy": (
                f"    `{_SYNTHETIC_SINGLE_DISPATCH_DECLARATION}`\n"
            ),
        }[case]
        _write(root, rel, text.replace(original, replacement, 1))
    elif case == "single_dispatch_agents_marker_duplicated":
        rel = "AGENTS.md"
        text = _read(root, rel)
        original = f"`{_SYNTHETIC_SINGLE_DISPATCH_DECLARATION}`\n"
        assert text.count(original) == 1
        _write(root, rel, text.replace(original, original + original, 1))
    elif case == "single_dispatch_agents_stage_mismatch":
        rel = "tools/dev_wave_codex.py"
        text = _read(root, rel)
        assert text == _SYNTHETIC_SINGLE_DISPATCH_LAUNCHER_STAGES
        _write(
            root,
            rel,
            text.replace('"focus"', '"mismatch"', 1),
        )
    elif case == "single_dispatch_launcher_stage_unreadable":
        _write(root, "tools/dev_wave_codex.py", "# malformed synthetic launcher\n")
    elif case == "single_dispatch_operations_marker_deleted":
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        assert text.count(_SYNTHETIC_SINGLE_DISPATCH_OPERATIONS_REFERENCE) == 1
        _write(
            root,
            rel,
            text.replace(
                _SYNTHETIC_SINGLE_DISPATCH_OPERATIONS_REFERENCE,
                "single dispatch reference omitted",
                1,
            ),
        )
    elif case in {
        "single_dispatch_operations_comment_decoy",
        "single_dispatch_operations_fence_decoy",
        "single_dispatch_operations_blockquote_decoy",
    }:
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        original = f"{_SYNTHETIC_SINGLE_DISPATCH_OPERATIONS_REFERENCE}\n"
        assert text.count(original) == 1
        replacement = {
            "single_dispatch_operations_comment_decoy": (
                f"<!-- {_SYNTHETIC_SINGLE_DISPATCH_OPERATIONS_REFERENCE} -->\n"
            ),
            "single_dispatch_operations_fence_decoy": (
                f"```text\n{_SYNTHETIC_SINGLE_DISPATCH_OPERATIONS_REFERENCE}\n```\n"
            ),
            "single_dispatch_operations_blockquote_decoy": (
                f"> {_SYNTHETIC_SINGLE_DISPATCH_OPERATIONS_REFERENCE}\n"
            ),
        }[case]
        _write(root, rel, text.replace(original, replacement, 1))
    elif case == "codex_skill_openai_changed":
        rel = ".agents/skills/dev-wave/agents/openai.yaml"
        _write(root, rel, _read(root, rel).replace(
            "display_name: \"Dev Wave\"",
            "display_name: \"Changed\"",
            1,
        ))
    elif case == "codex_skill_land_helper_duplicated":
        rel = ".agents/skills/dev-wave/SKILL.md"
        _write(root, rel, _read(root, rel) + "\ntools/dev_wave_land.py\n")
    elif case == "command_land_helper_duplicated":
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel) + "\ntools/dev_wave_land.py\n")
    elif case == "command_alternate_land_helper":
        rel = ".claude/commands/dev-wave.md"
        _write(
            root, rel,
            _read(root, rel)
            + "\n```sh\n$ python3 tools/alternate_land.py --main main\n```\n",
        )
    elif case == "skill_alternate_land_helper":
        rel = ".agents/skills/dev-wave/SKILL.md"
        _write(
            root, rel,
            _read(root, rel)
            + "\n```sh\n$ python3 tools/alternate_land.py --main main\n```\n",
        )
    elif case == "command_direct_main_ff":
        rel = ".claude/commands/dev-wave.md"
        _write(
            root, rel,
            _read(root, rel) + "\n```sh\n$ git merge --ff-only deadbeef\n```\n",
        )
    elif case == "skill_direct_main_ff":
        rel = ".agents/skills/dev-wave/SKILL.md"
        _write(
            root, rel,
            _read(root, rel) + "\n```sh\n$ git merge --ff-only deadbeef\n```\n",
        )
    elif case == "codex_rulings_skill_deleted":
        os.remove(os.path.join(
            root, ".agents", "skills", "rulings", "SKILL.md"
        ))
    elif case == "codex_rulings_skill_extra_file":
        _write(root, ".agents/skills/rulings/README.md", "# extra\n")
    elif case == "codex_rulings_skill_name_changed":
        rel = ".agents/skills/rulings/SKILL.md"
        _write(root, rel, _read(root, rel).replace(
            "name: rulings", "name: rulings-renamed", 1,
        ))
    elif case == "codex_rulings_skill_adapter_deleted":
        rel = ".agents/skills/rulings/SKILL.md"
        literal = check_docs.CODEX_RULINGS_SKILL_LITERALS[0]
        _write(root, rel, _read(root, rel).replace(
            literal, "repository entry omitted", 1,
        ))
    elif case == "codex_rulings_skill_openai_changed":
        rel = ".agents/skills/rulings/agents/openai.yaml"
        _write(root, rel, _read(root, rel).replace(
            "display_name: \"Rulings\"",
            "display_name: \"Changed\"",
            1,
        ))
    elif case == "codex_next_tasks_skill_byte_over":
        _pad_to_bytes(root, ".agents/skills/next-tasks/SKILL.md", 5_733)
    elif case == "codex_next_tasks_skill_openai_changed":
        rel = ".agents/skills/next-tasks/agents/openai.yaml"
        _write(root, rel, _read(root, rel).replace(
            'display_name: "Next Tasks"', 'display_name: "Changed"', 1,
        ))
    elif case == "codex_next_tasks_skill_adapter_deleted":
        rel = ".agents/skills/next-tasks/SKILL.md"
        _write(root, rel, _read(root, rel).replace("AGENTS.md\n", "", 1))
    elif case == "codex_next_tasks_skill_extra_file":
        _write(root, ".agents/skills/next-tasks/README.md", "# extra\n")
    elif case == "fifth_reference":
        _write(root, "docs/dev-wave/extra.md", "# extra\n")
    elif case == "nested_reference":
        _write(root, "docs/dev-wave/appendix/extra.md", "# extra\n")
    elif case == "non_md_reference":
        _write(root, "docs/dev-wave/extra.txt", "extra\n")
    elif case == "invalid_utf8":
        path = os.path.join(root, "docs/dev-wave/core.md")
        with open(path, "wb") as f:
            f.write(b"\xff")
    elif case == "symlink":
        path = os.path.join(root, "docs/dev-wave/core.md")
        os.remove(path)
        os.symlink("workers.md", path)
    elif case == "non_regular":
        path = os.path.join(root, "docs/dev-wave/mutation.md")
        os.remove(path)
        os.mkfifo(path)
    elif case == "registered_reference_deleted":
        os.remove(os.path.join(root, "docs/dev-wave/operations.md"))
    elif case == "dispatch_allowlist":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| wave 開始 |"),
            lambda line: line.removesuffix(" |\n")
            + "; `docs/failures.md` |\n",
        )
    else:
        raise AssertionError(f"unknown case: {case}")


_COMMAND_GUARD_CASES = [
    "self_next_tasks_h3_deleted",
    "codex_next_tasks_skill_byte_over",
    "codex_next_tasks_skill_openai_changed",
    "codex_next_tasks_skill_adapter_deleted",
    "codex_next_tasks_skill_extra_file",
    "command_byte_over",
    "self_byte_over",
    "long_line",
    "unregistered_command",
    "registered_command_deleted",
    "arguments_missing",
    "frontmatter_key_changed",
    "frontmatter_duplicate",
    "frontmatter_malformed",
    "disable_value_changed",
    "command_startup_wave_pre_form",
    "command_startup_routing_blockquoted",
    "stage6-relocated",
    "stage9-deleted",
    "dw-c00-fenced",
    "dw-o01-wrong-pid-source",
    "target-symlinked",
    "decoy-optional",
    "decoy-negated",
    "decoy-lease-optional-omitted",
    "decoy-lease-optional-typo",
    "decoy-blockquoted",
    "pre-wave-form",
    "reference_section_deleted",
    "reference_section_duplicated",
    "stage2_operations_deleted",
    "stage2_o03_readded",
    "stage3_o03_readded",
    "stage3_o13_readded",
    "stage6_m07_readded",
    "stage6_s05_inheritance_deleted",
    "stage6_all_operations_deleted",
    "stage6_o25_deleted",
    "stage8_operations_deleted",
    "stage8_self_deleted",
    "stage9_land_operation_deleted",
    "condition_o13_deleted",
    "condition_18_o18_deleted",
    "condition_18_o26_deleted",
    "condition_18_trigger_broadened",
    "condition_18_run_point_deleted",
    "condition_18_red_point_deleted",
    "condition_all_operations_deleted",
    "condition_supervisor_deleted",
    "condition_land_operation_deleted",
    "condition_waiter_deleted",
    "condition_25_deleted",
    "condition_25_trigger_broadened",
    "condition_26_deleted",
    "condition_26_trigger_broadened",
    "condition_26_target_changed",
    "condition_27_deleted",
    "condition_27_trigger_broadened",
    "condition_27_target_changed",
    "self_heading_deleted",
    "self_h3_deleted",
    "self_long_line",
    "self_reference_deleted",
    "self_l2_admission_wave_pre_form",
    "reference_orphan_h2",
    "dispatch_heading_duplicated",
    "dispatch_heading_missing",
    "d2_rollback_body_deleted",
    "d4_inheritance_body_deleted",
    "codex_command_contract_deleted",
    "codex_core_contract_deleted",
    "codex_worker_contract_deleted",
    "s09_land_route_deleted",
    "s09_acceptance_order_deleted",
    "core_land_helper_outside_s09",
    "o23_land_helper_deleted",
    "operations_land_helper_outside_o23",
    "o25_contract_weakened",
    "o25_before_o01",
    "o26_section_deleted",
    "o26_heading_only",
    "o26_contract_weakened",
    "o28_section_deleted",
    "o28_heading_only",
    "o28_contract_weakened",
    "codex_skill_deleted",
    "codex_skill_extra_file",
    "codex_skill_name_changed",
    "codex_skill_adapter_deleted",
    "codex_skill_natural_language_stop_contract_deleted",
    "codex_skill_protected_path_authoring_contract_deleted",
    "codex_startup_wave_pre_form",
    "codex_startup_routing_moved",
    "codex_skill_stage9_land_literal_deleted",
    "single_dispatch_agents_marker_deleted",
    "single_dispatch_agents_projection_deleted",
    "single_dispatch_agents_projection_path_deleted",
    "single_dispatch_agents_projection_path_placeholder_only",
    "single_dispatch_agents_projection_stop_deleted",
    "single_dispatch_agents_comment_decoy",
    "single_dispatch_agents_fence_decoy",
    "single_dispatch_agents_blockquote_decoy",
    "single_dispatch_agents_indented_code_decoy",
    "single_dispatch_agents_marker_duplicated",
    "single_dispatch_agents_stage_mismatch",
    "single_dispatch_launcher_stage_unreadable",
    "single_dispatch_operations_marker_deleted",
    "single_dispatch_operations_comment_decoy",
    "single_dispatch_operations_fence_decoy",
    "single_dispatch_operations_blockquote_decoy",
    "codex_skill_openai_changed",
    "codex_skill_land_helper_duplicated",
    "command_land_helper_duplicated",
    "command_alternate_land_helper",
    "skill_alternate_land_helper",
    "command_direct_main_ff",
    "skill_direct_main_ff",
    "codex_rulings_skill_deleted",
    "codex_rulings_skill_extra_file",
    "codex_rulings_skill_name_changed",
    "codex_rulings_skill_adapter_deleted",
    "codex_rulings_skill_openai_changed",
    "fifth_reference",
    "nested_reference",
    "non_md_reference",
    "invalid_utf8",
    "symlink",
    "non_regular",
    "registered_reference_deleted",
    "dispatch_allowlist",
]

_COMMAND_GUARD_NEEDLES = {
    "self_next_tasks_h3_deleted": "H3 見出し 'next-tasks' が 0 件",
    "codex_next_tasks_skill_byte_over": "5733 bytes > 予算 5732 bytes",
    "codex_next_tasks_skill_openai_changed": "生成済み Skill interface 契約と不一致",
    "codex_next_tasks_skill_adapter_deleted": "Codex adapter 契約がない",
    "codex_next_tasks_skill_extra_file": "Codex next-tasks Skill の予算未登録実体",
    "command_byte_over": "bytes > 予算",
    "self_byte_over": "bytes > 予算",
    "long_line": "最長行予算",
    "unregistered_command": "command byte予算が未登録",
    "registered_command_deleted": "予算登録済み command が不在",
    "arguments_missing": "$ARGUMENTS が 0 件",
    "frontmatter_key_changed": "frontmatter key 集合が契約と不一致",
    "frontmatter_duplicate": "frontmatter key 重複",
    "frontmatter_malformed": "frontmatter を一意に解析できない",
    "disable_value_changed": "disable-model-invocation は 'true' 必須",
    "command_startup_wave_pre_form": "可視 H2 節 '入力と開始' の節全体",
    "command_startup_routing_blockquoted": "可視 H2 節 '入力と開始' の節全体",
    "stage6-relocated": "9 段状態機械の項 6 に waiter consumer",
    "stage9-deleted": "9 段状態機械の項 9 に waiter consumer",
    "dw-c00-fenced": "DW-C00 に waiter consumer normative line",
    "dw-o01-wrong-pid-source": "DW-O01 に waiter consumer normative line",
    "target-symlinked": "canonical target が symlink でない regular file",
    "decoy-optional": "normative line と同じ節に義務を打ち消す語がある",
    "decoy-negated": "9 段状態機械の項 6 に waiter consumer",
    "decoy-lease-optional-omitted": "9 段状態機械の項 6 に waiter consumer",
    "decoy-lease-optional-typo": "9 段状態機械の項 6 に waiter consumer",
    "decoy-blockquoted": "9 段状態機械の項 6 に waiter consumer",
    "pre-wave-form": "9 段状態機械の項 6 に waiter consumer",
    "reference_section_deleted": "H2 見出し DW-M05 が 0 件",
    "reference_section_duplicated": "H2 見出し DW-M05 が 2 件",
    "stage2_operations_deleted": "段 dispatch '段 2 preflight' の U edge が契約と不一致",
    "stage2_o03_readded": "段 dispatch '段 2 preflight' の U edge が契約と不一致",
    "stage3_o03_readded": "段 dispatch '段 3 preflight' の U edge が契約と不一致",
    "stage3_o13_readded": "段 dispatch '段 3 preflight' の U edge が契約と不一致",
    "stage6_m07_readded": "段 dispatch '段 6' の U edge が契約と不一致",
    "stage6_s05_inheritance_deleted": "段 dispatch '段 6' の U edge が契約と不一致",
    "stage6_all_operations_deleted": "段 dispatch '段 6' の C edge が契約と不一致",
    "stage6_o25_deleted": "段 dispatch '段 6' の C edge が契約と不一致",
    "stage8_operations_deleted": "段 dispatch '段 8 preflight' の C edge が契約と不一致",
    "stage8_self_deleted": "段 dispatch '段 8 preflight' の U edge が契約と不一致",
    "stage9_land_operation_deleted": "段 dispatch '段 9' の U edge が契約と不一致",
    "condition_o13_deleted": "条件 dispatch '13' が契約と不一致",
    "condition_18_o18_deleted": "条件 dispatch '18' が契約と不一致",
    "condition_18_o26_deleted": "条件 dispatch '18' が契約と不一致",
    "condition_18_trigger_broadened": "条件 dispatch '18' が契約と不一致",
    "condition_18_run_point_deleted": (
        "条件 dispatch '18' の trigger に テスト・受入前と赤処理前が必要"
    ),
    "condition_18_red_point_deleted": (
        "条件 dispatch '18' の trigger に テスト・受入前と赤処理前が必要"
    ),
    "condition_all_operations_deleted": "条件 dispatch '01' が契約と不一致",
    "condition_supervisor_deleted": "条件 dispatch '22' が契約と不一致",
    "condition_land_operation_deleted": "条件 dispatch '23' が契約と不一致",
    "condition_waiter_deleted": "条件 dispatch '24' が契約と不一致",
    "condition_25_deleted": "条件 dispatch '25' が契約と不一致",
    "condition_25_trigger_broadened": "条件 dispatch '25' が契約と不一致",
    "condition_26_deleted": "条件 dispatch '26' が契約と不一致",
    "condition_26_trigger_broadened": "条件 dispatch '26' が契約と不一致",
    "condition_26_target_changed": "条件 dispatch '26' が契約と不一致",
    "condition_27_deleted": "条件 dispatch '27' が契約と不一致",
    "condition_27_trigger_broadened": "条件 dispatch '27' が契約と不一致",
    "condition_27_target_changed": "条件 dispatch '27' が契約と不一致",
    "self_heading_deleted": "H2 見出し '発火 gate' が 0 件",
    "self_h3_deleted": "H3 見出し 'cleanup-branches' が 0 件",
    "self_long_line": "最長行予算",
    "self_reference_deleted": "docs/skill-self-improvement.md への到達性がない",
    "self_l2_admission_wave_pre_form": "可視 H2 節 'routing' の節全体",
    "reference_orphan_h2": "dispatch 契約にない孤児 H2",
    "dispatch_heading_duplicated": "段/条件 dispatch 表を一意に抽出できない",
    "dispatch_heading_missing": "段/条件 dispatch 表を一意に抽出できない",
    "d2_rollback_body_deleted": "D2 巻き戻し構造",
    "d4_inheritance_body_deleted": "D4 fix 子の段5全文継承",
    "codex_command_contract_deleted": "Codex-first 実装境界",
    "codex_core_contract_deleted": "Codex-first 実装契約がない",
    "codex_worker_contract_deleted": "Codex-first 実装契約がない",
    "s09_land_route_deleted": "DW-S09 の helper 唯一経路 literal",
    "s09_acceptance_order_deleted": "DW-S09 の acceptance/O23 順序 literal",
    "core_land_helper_outside_s09": "path-section外=1",
    "o23_land_helper_deleted": "land helper path は全体で exact 1 件",
    "operations_land_helper_outside_o23": "land helper path は全体で exact 1 件",
    "o25_contract_weakened": "可視 H2 節 'DW-O25 — ff-only land の全史 provenance 関門' の節全体",
    "o25_before_o01": "DW-O25 は DW-O23 より後に置く",
    "o26_section_deleted": "H2 見出し DW-O26 が 0 件",
    "o26_heading_only": "可視 H2 節 'DW-O26 — 焦点走の consumer test 拡張' の節全体",
    "o26_contract_weakened": "可視 H2 節 'DW-O26 — 焦点走の consumer test 拡張' の節全体",
    "o28_section_deleted": "H2 見出し DW-O28 が 0 件",
    "o28_heading_only": "可視 H2 節 'DW-O28 — land 後の自己撤去' の節全体",
    "o28_contract_weakened": "可視 H2 節 'DW-O28 — land 後の自己撤去' の節全体",
    "codex_skill_deleted": "Codex dev-wave Skill の必須 file が不在",
    "codex_skill_extra_file": "Codex dev-wave Skill の予算未登録実体",
    "codex_skill_name_changed": "name は 'dev-wave' 必須",
    "codex_skill_adapter_deleted": "Codex adapter 契約がない",
    "codex_skill_natural_language_stop_contract_deleted": (
        "自然文の依頼を一般タスクとして"
    ),
    "codex_skill_protected_path_authoring_contract_deleted": (
        "`apply_patch` tool を直接呼び"
    ),
    "codex_startup_wave_pre_form": "可視 H2 節 '開始する' の節全体",
    "codex_startup_routing_moved": "可視 H2 節 '開始する' の節全体",
    "codex_skill_stage9_land_literal_deleted": "exact adapter literal が 0 件",
    "single_dispatch_agents_marker_deleted": (
        "AGENTS.md: 単独段 dispatch の宣言テンプレート"
    ),
    "single_dispatch_agents_projection_deleted": (
        "AGENTS.md: 宣言テンプレート直後の「必読事項の射影:」見出し行"
    ),
    "single_dispatch_agents_projection_path_deleted": (
        "AGENTS.md: 宣言テンプレート直後の射影節本文に絶対パスらしき記述と"
        "「読めなければ即停止」の両方がない"
    ),
    "single_dispatch_agents_projection_path_placeholder_only": (
        "AGENTS.md: 宣言テンプレート直後の射影節本文に絶対パスらしき記述と"
        "「読めなければ即停止」の両方がない"
    ),
    "single_dispatch_agents_projection_stop_deleted": (
        "AGENTS.md: 宣言テンプレート直後の射影節本文に絶対パスらしき記述と"
        "「読めなければ即停止」の両方がない"
    ),
    "single_dispatch_agents_comment_decoy": (
        "AGENTS.md: 単独段 dispatch の宣言テンプレート"
    ),
    "single_dispatch_agents_fence_decoy": (
        "AGENTS.md: 単独段 dispatch の宣言テンプレート"
    ),
    "single_dispatch_agents_blockquote_decoy": (
        "AGENTS.md: 単独段 dispatch の宣言テンプレート"
    ),
    "single_dispatch_agents_indented_code_decoy": (
        "AGENTS.md: 単独段 dispatch の宣言テンプレート"
    ),
    "single_dispatch_agents_marker_duplicated": (
        "AGENTS.md: 単独段 dispatch の宣言テンプレート"
    ),
    "single_dispatch_agents_stage_mismatch": (
        "AGENTS.md: 単独段 dispatch の stage 語彙"
    ),
    "single_dispatch_launcher_stage_unreadable": (
        "AGENTS.md: tools/dev_wave_codex.py の STAGES を解析できない"
    ),
    "single_dispatch_operations_marker_deleted": (
        "docs/dev-wave/operations.md: DW-O02 に AGENTS.md の単独段例外"
    ),
    "single_dispatch_operations_comment_decoy": (
        "docs/dev-wave/operations.md: DW-O02 に AGENTS.md の単独段例外"
    ),
    "single_dispatch_operations_fence_decoy": (
        "docs/dev-wave/operations.md: DW-O02 に AGENTS.md の単独段例外"
    ),
    "single_dispatch_operations_blockquote_decoy": (
        "docs/dev-wave/operations.md: DW-O02 に AGENTS.md の単独段例外"
    ),
    "codex_skill_openai_changed": "生成済み Skill interface 契約と不一致",
    "codex_skill_land_helper_duplicated": "共通 dispatcher の leaf path を重複 pin",
    "command_land_helper_duplicated": "land helper path は DW-S09 / DW-O23 だけ",
    "command_alternate_land_helper": "alternate land helper command",
    "skill_alternate_land_helper": "alternate land helper command",
    "command_direct_main_ff": "direct git merge --ff-only main mutation",
    "skill_direct_main_ff": "direct git merge --ff-only main mutation",
    "codex_rulings_skill_deleted": "Codex rulings Skill の必須 file が不在",
    "codex_rulings_skill_extra_file": "Codex rulings Skill の予算未登録実体",
    "codex_rulings_skill_name_changed": "name は 'rulings' 必須",
    "codex_rulings_skill_adapter_deleted": "Codex adapter 契約がない",
    "codex_rulings_skill_openai_changed": "生成済み Skill interface 契約と不一致",
    "fifth_reference": "docs/dev-wave/** の層予算registry未登録実体",
    "nested_reference": "docs/dev-wave/** の層予算registry未登録実体",
    "non_md_reference": "docs/dev-wave/** の層予算registry未登録実体",
    "invalid_utf8": "invalid UTF-8",
    "symlink": "symlink または regular file 以外",
    "non_regular": "symlink または regular file 以外",
    "registered_reference_deleted": "登録済み dev-wave reference が不在",
    "dispatch_allowlist": "規範 dispatch の参照先が allowlist 外",
}
_COMMAND_GUARD_EXPECTED_COUNTS = {
    case: 1 for case in _COMMAND_GUARD_CASES
}
_COMMAND_GUARD_EXPECTED_COUNTS["condition_all_operations_deleted"] = (
    len(_OPERATION_CONDITION_KEYS) + 1
)
_COMMAND_GUARD_EXPECTED_COUNTS.update({
    "condition_26_deleted": 2,
    "condition_26_target_changed": 2,
    "condition_27_deleted": 2,
    "condition_27_target_changed": 2,
})
_COMMAND_GUARD_EXPECTED_COUNTS.update({
    "condition_18_o26_deleted": 2,
    "condition_18_trigger_broadened": 2,
    "dispatch_allowlist": 2,
    "codex_startup_wave_pre_form": 2,
    "o26_section_deleted": 2,
    "o28_section_deleted": 2,
})


def test_dev_wave_waiter_consumer_pins_accept_current_docs_contract():
    """現行 docs の4 consumer と canonical target が正例になる。"""

    findings: list[str] = []
    check_docs._check_dev_wave_waiter_consumer_pins(
        (check_docs.REPO / ".claude/commands/dev-wave.md").read_text(),
        (check_docs.REPO / "docs/dev-wave/core.md").read_text(),
        (check_docs.REPO / "docs/dev-wave/operations.md").read_text(),
        findings,
    )
    assert findings == []


def test_single_dispatch_structure_contract_accepts_handwritten_fixture():
    """単独段 marker の正例と launcher stage 語彙の cross-check を固定する。"""

    assert check_docs.DEV_WAVE_SINGLE_DISPATCH_STAGE_CHOICES == (
        "plan", "consult", "author", "review", "fix", "focus",
    )
    assert check_docs.DEV_WAVE_SINGLE_DISPATCH_DECLARATION_LITERAL == (
        _SYNTHETIC_SINGLE_DISPATCH_DECLARATION
    )
    assert check_docs.DEV_WAVE_SINGLE_DISPATCH_PROJECTION_HEADING == (
        _SYNTHETIC_SINGLE_DISPATCH_PROJECTION_HEADING
    )
    assert check_docs.DEV_WAVE_SINGLE_DISPATCH_OPERATIONS_REFERENCE_LITERAL == (
        _SYNTHETIC_SINGLE_DISPATCH_OPERATIONS_REFERENCE
    )
    assert check_docs._launcher_stage_choices() == (
        "plan", "consult", "author", "review", "fix", "focus",
    )

    root = _build_min_repo()
    try:
        baseline = _run_check(root)
        assert baseline.returncode == 0, baseline.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_single_dispatch_indented_code_block_decoy_is_ignored():
    """4スペース以上の indented code block の marker は可視本文に数えない。"""

    root = _build_min_repo()
    try:
        rel = "AGENTS.md"
        text = _read(root, rel)
        original = f"`{_SYNTHETIC_SINGLE_DISPATCH_DECLARATION}`\n"
        assert text.count(original) == 1
        decoy = f"    `{_SYNTHETIC_SINGLE_DISPATCH_DECLARATION}`\n"
        _write(root, rel, text.replace(original, original + decoy, 1))
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_single_dispatch_tab_indented_code_block_decoy_is_ignored():
    """タブ1個の indented code block の marker は可視本文に数えない。"""

    root = _build_min_repo()
    try:
        rel = "AGENTS.md"
        text = _read(root, rel)
        original = f"`{_SYNTHETIC_SINGLE_DISPATCH_DECLARATION}`\n"
        assert text.count(original) == 1
        decoy = f"\t`{_SYNTHETIC_SINGLE_DISPATCH_DECLARATION}`\n"
        _write(root, rel, text.replace(original, original + decoy, 1))
        result = _run_check(root)
        assert result.returncode == 0, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_command_guard_case_registration_is_complete():
    """条件 24〜27、L2 再追加、新節 pin と guard 登録表を固定する。"""

    case_keys = set(_COMMAND_GUARD_CASES)
    assert {
        "self_next_tasks_h3_deleted",
        "codex_next_tasks_skill_byte_over",
        "codex_next_tasks_skill_openai_changed",
        "codex_next_tasks_skill_adapter_deleted",
        "codex_next_tasks_skill_extra_file",
    } <= case_keys
    assert "condition_waiter_deleted" in case_keys
    assert {
        "condition_25_deleted",
        "condition_25_trigger_broadened",
        "condition_26_deleted",
        "condition_26_trigger_broadened",
        "condition_26_target_changed",
        "condition_27_deleted",
        "condition_27_trigger_broadened",
        "condition_27_target_changed",
        "stage2_o03_readded",
        "stage3_o03_readded",
        "stage3_o13_readded",
        "stage6_m07_readded",
        "stage6_o25_deleted",
        "o25_contract_weakened",
        "o25_before_o01",
        "command_startup_wave_pre_form",
        "command_startup_routing_blockquoted",
        "codex_startup_wave_pre_form",
        "codex_startup_routing_moved",
        "single_dispatch_agents_marker_deleted",
        "single_dispatch_agents_projection_deleted",
        "single_dispatch_agents_projection_path_deleted",
        "single_dispatch_agents_projection_path_placeholder_only",
        "single_dispatch_agents_projection_stop_deleted",
        "single_dispatch_agents_comment_decoy",
        "single_dispatch_agents_fence_decoy",
        "single_dispatch_agents_blockquote_decoy",
        "single_dispatch_agents_indented_code_decoy",
        "single_dispatch_agents_marker_duplicated",
        "single_dispatch_agents_stage_mismatch",
        "single_dispatch_launcher_stage_unreadable",
        "single_dispatch_operations_marker_deleted",
        "single_dispatch_operations_comment_decoy",
        "single_dispatch_operations_fence_decoy",
        "single_dispatch_operations_blockquote_decoy",
        "self_l2_admission_wave_pre_form",
        "stage6-relocated",
        "stage9-deleted",
        "dw-c00-fenced",
        "dw-o01-wrong-pid-source",
        "condition_18_o18_deleted",
        "condition_18_o26_deleted",
        "condition_18_trigger_broadened",
        "condition_18_run_point_deleted",
        "condition_18_red_point_deleted",
        "o26_section_deleted",
        "o26_heading_only",
        "o26_contract_weakened",
        "o28_section_deleted",
        "o28_heading_only",
        "o28_contract_weakened",
        "target-symlinked",
        "decoy-optional",
        "decoy-negated",
        "decoy-lease-optional-omitted",
        "decoy-lease-optional-typo",
        "decoy-blockquoted",
        "pre-wave-form",
    } <= case_keys
    assert (
        case_keys
        == set(_COMMAND_GUARD_NEEDLES)
        == set(_COMMAND_GUARD_EXPECTED_COUNTS)
    )
    with open(__file__, encoding="utf-8") as source_file:
        source = source_file.read()
    for test_name in (
        "test_condition_18_contract_pins_exact_two_points_and_targets",
        "test_condition_18_resolves_in_separate_red_context",
        "test_condition_25_contract_pins_exact_trigger_and_target",
        "test_condition_26_contract_pins_exact_trigger_and_target",
        "test_condition_27_contract_pins_exact_trigger_and_target",
        "test_dev_wave_dispatch_accepts_comma_delimited_section_references",
        "test_dw_o18_exact_section_pin_accepts_synthetic_fixture",
        "test_dw_o26_exact_section_pin_accepts_synthetic_fixture",
        "test_dw_o28_exact_section_pin_accepts_synthetic_fixture",
        "test_non_attributable_landing_contract_mutations_have_one_finding",
        "test_non_attributable_landing_general_terms_are_accepted",
        "test_normative_exact_section_contract_is_handwritten_and_complete",
        "test_normative_exact_section_pins_reject_raw_html_inside_pinned_sections",
        "test_dev_wave_operation_order_rejects_titleless_reorder_and_missing_target",
        "test_dw_o20_points_to_dw_c01_and_drops_legacy_submodule_command",
        "test_dw_c01_is_immediately_before_dw_stop",
        "test_normative_exact_section_pins_accept_real_repo",
        "test_dev_wave_waiter_consumer_pins_accept_current_docs_contract",
    ):
        assert source.count(f"def {test_name}(") == 1


def test_operation_contract_pins_exact_section_set():
    """operations 契約の外延と配線を literal で固定する (O15 削除後の 20 節 + O26/O27/O28)。

    checker とテスト fixture は同じ `_OPERATION_NUMBERS` から導出される (F9 型の
    自己整合面)。fixture の literal range 表記が単純な縮小・拡大を先に赤くし、
    本 pin は誤配線と外延の完全性を固定する — 二つの独立面の役割分担であり、
    どちらも単独の oracle ではない。
    """
    operations = "docs/dev-wave/operations.md"
    expected = {
        "DW-O01", "DW-O02", "DW-O03", "DW-O04", "DW-O05", "DW-O06",
        "DW-O08", "DW-O09", "DW-O10", "DW-O11", "DW-O12", "DW-O13",
        "DW-O14", "DW-O16", "DW-O17", "DW-O18", "DW-O19", "DW-O20",
        "DW-O23", "DW-O25",
    }
    assert set(_SYNTHETIC_OPERATION_SECTION_IDS) == expected
    assert set(_SYNTHETIC_REGISTERED_OPERATION_SECTION_IDS) == (
        expected | {"DW-O26", "DW-O27", "DW-O28"}
    )
    assert check_docs.REQUIRED_REFERENCE_SECTIONS[operations] == (
        expected | {"DW-O26", "DW-O27", "DW-O28"}
    )
    assert check_docs._ALL_OPERATIONS == frozenset(
        (operations, section) for section in expected
    )
    for section in sorted(expected):
        key = section.removeprefix("DW-O")
        operations_pairs = {
            pair
            for pair in check_docs.CONDITION_DISPATCH_CONTRACT[key]
            if pair[0] == operations
        }
        expected_pairs = {(operations, section)}
        if section == "DW-O18":
            expected_pairs.add((operations, "DW-O26"))
            expected_pairs.add((operations, "DW-O27"))
        assert operations_pairs == expected_pairs, (
            f"条件 {key} の operations 配線が {section} 単独でない"
        )
    assert check_docs.CONDITION_DISPATCH_CONTRACT["18"] == {
        (operations, "DW-O18"),
        (operations, "DW-O26"),
        (operations, "DW-O27"),
    }
    assert check_docs.CONDITION_DISPATCH_CONTRACT["27"] == {
        (operations, "DW-O28"),
    }
    assert not {"26", "27"} & set(_OPERATION_CONDITION_KEYS)
    assert check_docs.CONDITION_DISPATCH_CONTRACT["15"] == {
        ("docs/dev-wave/mutation.md", "DW-M07")
    }
    assert _OPERATION_CONDITION_KEYS == sorted(
        section.removeprefix("DW-O") for section in expected
    )
    for stage in ("段 5", "段 6"):
        assert check_docs._ALL_OPERATIONS <= (
            check_docs.STAGE_DISPATCH_CONTRACT[stage]
        ), f"{stage} が operations 全節を消費していない"
    assert (
        "docs/dev-wave/operations.md", "DW-O23"
    ) in check_docs.STAGE_DISPATCH_CONTRACT["段 9"]
    assert check_docs.DEV_WAVE_LAND_HELPER == "tools/dev_wave_land.py"
    assert check_docs.DEV_WAVE_LAND_UNIQUE_ROUTE_LITERAL == (
        "`tools/dev_wave_land.py` は local main を変更する唯一の通常 land 経路"
    )
    assert check_docs.DEV_WAVE_S09_ACCEPTANCE_ORDER_LITERAL == (
        _S09_ACCEPTANCE_ORDER_LITERAL
    )
    assert check_docs.CODEX_DEV_WAVE_STAGE9_LAND_LITERAL == (
        "段 9 は dispatcher が指定する共通 land 契約だけに従い、"
        "Codex 固有の取り込み手順を重ねない。"
    )


def test_condition_24_contract_pins_exact_target():
    """条件 24 の参照先と operations 非所属だけを固定する。"""

    assert check_docs.CONDITION_DISPATCH_CONTRACT["24"] == {
        ("docs/dev-wave/core.md", "DW-C00")
    }
    assert "24" not in _OPERATION_CONDITION_KEYS


def test_condition_18_contract_pins_exact_two_points_and_targets():
    """条件18の契約、独立2点 oracle、手書き row、3参照節を固定する。"""

    assert check_docs.CONDITION_TRIGGER_CONTRACT["18"] == (
        "親のテスト・受入前と赤処理前"
    )
    assert check_docs.CONDITION_18_RUN_POINT_LITERAL == "テスト・受入前"
    assert check_docs.CONDITION_18_RED_POINT_LITERAL == "赤処理前"
    assert _SYNTHETIC_CONDITION_18_ROW == (
        "| 18 | 親のテスト・受入前と赤処理前 | "
        "`docs/dev-wave/operations.md`: `DW-O18`, `DW-O26`, `DW-O27` |"
    )
    assert check_docs.CONDITION_DISPATCH_CONTRACT["18"] == {
        ("docs/dev-wave/operations.md", "DW-O18"),
        ("docs/dev-wave/operations.md", "DW-O26"),
        ("docs/dev-wave/operations.md", "DW-O27"),
    }
    assert [
        key
        for key, trigger in check_docs.CONDITION_TRIGGER_CONTRACT.items()
        if "赤処理" in trigger
    ] == ["18"]


def test_condition_18_resolves_in_separate_red_context():
    """投入終了後の別 process が入口を再読し、赤処理の条件18を解決する。"""

    inner_budget = 2 * (
        _CONDITION_CONTEXT_ARTIFACT_TIMEOUT_SECONDS
        + 2 * _CONDITION_CONTEXT_PROCESS_TIMEOUT_SECONDS
        + 4 * _CONDITION_CONTEXT_REAP_TIMEOUT_SECONDS
    )
    assert (
        inner_budget + _CONDITION_CONTEXT_EXIT_MARGIN_SECONDS
        < _CONDITION_CONTEXT_TEST_LIMIT_SECONDS
    )
    expected_sections = ("DW-O18", "DW-O26", "DW-O27")

    def assert_red_resolution(result: dict) -> None:
        resolved = result["red"]["resolved"].get("18")
        assert resolved is not None
        assert tuple(resolved) == expected_sections

    root = _build_min_repo()
    try:
        positive = _run_condition_18_separate_contexts(
            root, "condition-18-positive-red.json"
        )
        assert positive["submission"]["pid"] != positive["red"]["pid"]
        assert (
            positive["sequence"]["submission_ended"]
            <= positive["sequence"]["red_started"]
        )
        assert tuple(positive["submission"]["resolved"]["18"]) == expected_sections
        assert positive["submission"]["resolved_value_types"]["18"] == "tuple"
        assert positive["red"]["resolved_value_types"]["18"] == "tuple"
        assert_red_resolution(positive)

        _set_condition_18_trigger_and_contract(root, "親のテスト・受入前")
        negative = _run_condition_18_separate_contexts(
            root, "condition-18-negative-red.json"
        )
        assert negative["submission"]["pid"] != negative["red"]["pid"]
        assert (
            negative["sequence"]["submission_ended"]
            <= negative["sequence"]["red_started"]
        )
        assert tuple(negative["submission"]["resolved"]["18"]) == expected_sections
        assert negative["submission"]["resolved_value_types"]["18"] == "tuple"
        assert negative["red"]["resolved"] == {}
        assert negative["red"]["resolved_value_types"] == {}
        with pytest.raises(AssertionError):
            assert_red_resolution(negative)

        for result in (positive, negative):
            assert result["red"]["stdin"] == ""
            assert result["red"]["argv"] == [result["artifact_path"], root]
            assert result["red_command"][3:] == [result["artifact_path"], root]
            submission_resolution = json.dumps(
                result["submission"]["resolved"],
                ensure_ascii=False,
                sort_keys=True,
            )
            assert all(
                submission_resolution not in argument
                for argument in result["red_command"]
            )
            assert submission_resolution not in json.dumps(
                result["red"]["environment"],
                ensure_ascii=False,
                sort_keys=True,
            )
            assert submission_resolution not in json.dumps(
                result["red_environment"],
                ensure_ascii=False,
                sort_keys=True,
            )
            assert json.loads(_read(
                root, os.path.basename(result["artifact_path"])
            )) == {"acceptance": "red"}
        print(
            "CONDITION_18_CONTEXT_TIMINGS "
            + json.dumps(
                [positive["elapsed"], negative["elapsed"]],
                sort_keys=True,
            )
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_condition_25_contract_pins_exact_trigger_and_target():
    """fixture から独立した literal で条件 25 の trigger/target を固定する。"""

    assert check_docs.CONDITION_TRIGGER_CONTRACT["25"] == (
        "main を進める land を起動する直前"
    )
    assert check_docs.CONDITION_DISPATCH_CONTRACT["25"] == {
        ("docs/dev-wave/operations.md", "DW-O25")
    }
    assert "25" in _OPERATION_CONDITION_KEYS


def test_condition_26_contract_pins_exact_trigger_and_target():
    """fixture から独立した literal で条件 26 の trigger/target を固定する。"""

    assert check_docs.CONDITION_TRIGGER_CONTRACT["26"] == (
        "起動/待機/検査/submodule/取込/fix前"
    )
    assert check_docs.CONDITION_DISPATCH_CONTRACT["26"] == {
        ("docs/dev-wave/core.md", "DW-C01")
    }
    assert "26" not in _OPERATION_CONDITION_KEYS


def test_condition_27_contract_pins_exact_trigger_and_target():
    """fixture から独立した literal で条件 27 の trigger/target を固定する。"""

    assert check_docs.CONDITION_TRIGGER_CONTRACT["27"] == (
        "land 成功後の自己撤去直前"
    )
    assert check_docs.CONDITION_DISPATCH_CONTRACT["27"] == {
        ("docs/dev-wave/operations.md", "DW-O28")
    }
    assert "27" not in _OPERATION_CONDITION_KEYS


def _replace_workers_section_literal(text, section_id, replacement):
    match = re.search(
        rf"^## {re.escape(section_id)}(?:\s+—[^\n]*)?\s*$\n.*?(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    section = match.group(0)
    literal = {
        "DW-S02": check_docs.DEV_WAVE_DW_S02_REASONING_XHIGH_LITERAL,
        "DW-S03": check_docs.DEV_WAVE_DW_S03_REASONING_XHIGH_LITERAL,
        "DW-S05-A": "`reasoning=ultra`",
        "DW-S06-A": check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_LITERAL,
        "DW-S06-C": check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_LITERAL,
    }[section_id]
    changed_section = section.replace(literal, replacement, 1)
    assert changed_section != section
    return text[:match.start()] + changed_section + text[match.end():]


def _replace_workers_section_sentence(text, section_id, replacement):
    match = re.search(
        rf"^## {re.escape(section_id)}(?:\s+—[^\n]*)?\s*$\n.*?(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    section = match.group(0)
    sentence = {
        "DW-S05-A": check_docs.DEV_WAVE_DW_S05_A_REASONING_XHIGH_SENTENCE,
        "DW-S06-A": check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_SENTENCE,
        "DW-S06-C": check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_SENTENCE,
    }[section_id]
    assert section.count(sentence) == 1
    changed_section = section.replace(sentence, replacement, 1)
    assert changed_section != section
    return text[:match.start()] + changed_section + text[match.end():]


def _mutated_workers_text(root, section_id, replacement):
    target = os.path.join(root, "workers.md")
    shutil.copyfile(
        os.path.join(_REPO, "docs", "dev-wave", "workers.md"),
        target,
    )
    with open(target, encoding="utf-8") as stream:
        text = stream.read()
    _write(
        root,
        "workers.md",
        _replace_workers_section_literal(text, section_id, replacement),
    )
    return _read(root, "workers.md")


def _reasoning_effort_pin_findings(workers_text):
    findings = []
    check_docs._check_dev_wave_reasoning_effort_pins(workers_text, findings)
    return findings


def _wrap_workers_section(text, section_id, before, after):
    match = re.search(
        rf"^## {re.escape(section_id)}(?:\s+—[^\n]*)?\s*$\n.*?(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    return (
        text[:match.start()]
        + before
        + match.group(0)
        + after
        + text[match.end():]
    )


def _append_reference_section_text(text, section_id, addition):
    match = re.search(
        rf"^## {re.escape(section_id)}(?:\s+—[^\n]*)?\s*$\n.*?(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    return text[:match.end()] + addition + text[match.end():]


def test_dev_wave_reasoning_effort_pins_accept_current_workers_contract():
    workers = os.path.join(_REPO, "docs", "dev-wave", "workers.md")
    with open(workers, encoding="utf-8") as stream:
        assert _reasoning_effort_pin_findings(stream.read()) == []


def test_dev_wave_reasoning_effort_pins_accept_s06_b_inherited_without_literal():
    workers = os.path.join(_REPO, "docs", "dev-wave", "workers.md")
    with open(workers, encoding="utf-8") as stream:
        text = stream.read()
    visible = check_docs._visible_markdown_text(text)
    sections = check_docs._reference_id_sections(visible, "DW-S06-B")
    assert len(sections) == 1
    assert [
        match.group("value")
        for match in check_docs.DEV_WAVE_REASONING_EFFORT_RE.finditer(sections[0])
    ] == []
    assert _reasoning_effort_pin_findings(text) == []


def test_dev_wave_reasoning_effort_pin_rejects_dw_s02_high():
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, "DW-S02", "`reasoning=high`")
        assert _reasoning_effort_pin_findings(text) == [
            check_docs.DEV_WAVE_DW_S02_REASONING_XHIGH_FINDING
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_dw_s03_high():
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, "DW-S03", "`reasoning=high`")
        assert _reasoning_effort_pin_findings(text) == [
            check_docs.DEV_WAVE_DW_S03_REASONING_XHIGH_FINDING
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_missing_dw_s02_value():
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, "DW-S02", "")
        assert _reasoning_effort_pin_findings(text) == [
            check_docs.DEV_WAVE_DW_S02_REASONING_XHIGH_FINDING
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_missing_dw_s03_value():
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, "DW-S03", "")
        assert _reasoning_effort_pin_findings(text) == [
            check_docs.DEV_WAVE_DW_S03_REASONING_XHIGH_FINDING
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_high():
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, "DW-S06-A", "`reasoning=high`")
        assert _reasoning_effort_pin_findings(text) == [
            check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_missing_dw_s06_a_value():
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, "DW-S06-A", "")
        assert _reasoning_effort_pin_findings(text) == [
            check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_dw_s06_c_high():
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, "DW-S06-C", "`reasoning=high`")
        assert _reasoning_effort_pin_findings(text) == [
            check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_FINDING
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_dw_s05_a_high():
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, "DW-S05-A", "`reasoning=high`")
        assert _reasoning_effort_pin_findings(text) == [
            check_docs.DEV_WAVE_DW_S05_A_REASONING_XHIGH_FINDING
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("section_id, finding", [
    ("DW-S02", check_docs.DEV_WAVE_DW_S02_REASONING_XHIGH_FINDING),
    ("DW-S03", check_docs.DEV_WAVE_DW_S03_REASONING_XHIGH_FINDING),
    ("DW-S05-A", check_docs.DEV_WAVE_DW_S05_A_REASONING_XHIGH_FINDING),
    ("DW-S06-A", check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING),
    ("DW-S06-C", check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_FINDING),
], ids=["DW-S02", "DW-S03", "DW-S05-A", "DW-S06-A", "DW-S06-C"])
def test_dev_wave_reasoning_effort_pin_rejects_previous_medium(section_id, finding):
    root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
    try:
        text = _mutated_workers_text(root, section_id, "`reasoning=medium`")
        assert _reasoning_effort_pin_findings(text) == [finding]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _assert_reasoning_effort_decoys_rejected(section_id, finding):
    replacements = (
        "`reasoning=high` <!-- `reasoning=ultra` -->",
        "`reasoning=high`\n\n```\n`reasoning=ultra`\n```\ncontinuation",
        "`reasoning=high`\n\n> `reasoning=ultra`\n\ncontinuation",
        "`reasoning=ultra` and `reasoning=high`",
        "`reasoning=ultra` and `reasoning=ultra`",
    )
    for replacement in replacements:
        root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
        try:
            text = _mutated_workers_text(root, section_id, replacement)
            assert _reasoning_effort_pin_findings(text) == [finding]
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_dw_s02_decoys_and_duplicates():
    _assert_reasoning_effort_decoys_rejected(
        "DW-S02",
        check_docs.DEV_WAVE_DW_S02_REASONING_XHIGH_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_rejects_dw_s03_decoys_and_duplicates():
    _assert_reasoning_effort_decoys_rejected(
        "DW-S03",
        check_docs.DEV_WAVE_DW_S03_REASONING_XHIGH_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_decoys_and_duplicates():
    finding = check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING
    replacements = (
        "`reasoning=high` <!-- `reasoning=ultra` -->",
        "`reasoning=high`\n\n```\n`reasoning=ultra`\n```\ncontinuation",
        "`reasoning=ultra` and `reasoning=high`",
        "`reasoning=ultra` and `reasoning=ultra`",
    )
    for replacement in replacements:
        root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
        try:
            text = _mutated_workers_text(root, "DW-S06-A", replacement)
            assert _reasoning_effort_pin_findings(text) == [finding]
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_dw_s05_a_decoys_and_duplicates():
    _assert_reasoning_effort_decoys_rejected(
        "DW-S05-A",
        check_docs.DEV_WAVE_DW_S05_A_REASONING_XHIGH_FINDING,
    )


def _assert_reasoning_effort_real_keys_and_quotes_rejected(section_id, finding):
    replacements = (
        '`model_reasoning_effort="high"`（例: `reasoning=ultra`）',
        '`model_reasoning_effort="high"`',
        "`model_reasoning_effort='high'`",
        '`reasoning_effort=high` and `reasoning=ultra`',
        '`reasoning=ultra`\n\n> `reasoning=high`\n\ncontinuation',
        '`model_reasoning_effort="high"` <!-- `reasoning=ultra` -->',
    )
    for replacement in replacements:
        root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
        try:
            text = _mutated_workers_text(root, section_id, replacement)
            assert _reasoning_effort_pin_findings(text) == [finding]
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_dw_s02_real_keys_and_quotes():
    _assert_reasoning_effort_real_keys_and_quotes_rejected(
        "DW-S02",
        check_docs.DEV_WAVE_DW_S02_REASONING_XHIGH_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_rejects_dw_s03_real_keys_and_quotes():
    _assert_reasoning_effort_real_keys_and_quotes_rejected(
        "DW-S03",
        check_docs.DEV_WAVE_DW_S03_REASONING_XHIGH_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_real_keys_and_quotes():
    finding = check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING
    replacements = (
        "`reasoning_effort=high`",
        '`model_reasoning_effort="high"`',
        "`model_reasoning_effort='high'`",
        '`reasoning_effort="ultra"` and `reasoning=high`',
        '`model_reasoning_effort="ultra"` <!-- `reasoning=high` -->',
    )
    for replacement in replacements:
        root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
        try:
            text = _mutated_workers_text(root, "DW-S06-A", replacement)
            assert _reasoning_effort_pin_findings(text) == [finding]
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_ambiguous_values():
    finding = check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING
    for replacement, invalid_value in (
        ("`reasoning=high/max`", "high/max"),
        ("`reasoning=high.max`", "high.max"),
        ("`reasoning=high:max`", "high:max"),
        ('`reasoning=high"`', 'high"'),
    ):
        assert [
            match.group("value")
            for match in check_docs.DEV_WAVE_REASONING_EFFORT_RE.finditer(
                replacement
            )
        ] == [invalid_value]
        root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
        try:
            text = _mutated_workers_text(root, "DW-S06-A", replacement)
            assert _reasoning_effort_pin_findings(text) == [finding]
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pins_ignore_comment_and_fence_examples():
    cases = (
        ("DW-S02", "high"),
        ("DW-S03", "high"),
        ("DW-S06-A", "high"),
        ("DW-S06-C", "high"),
    )
    for section_id, decoy in cases:
        additions = (
            f'\n<!-- `model_reasoning_effort="{decoy}"` -->\n',
            (
                f'\n```\n`reasoning_effort={decoy}`\n```\n'
            ),
            (
                f'\n`pre_model_reasoning_effort={decoy}` and '
                f'`reasoning_effort_extra={decoy}`\n'
            ),
        )
        for addition in additions:
            root = tempfile.mkdtemp(prefix="izanagi_reasoning_pin_")
            try:
                workers = os.path.join(_REPO, "docs", "dev-wave", "workers.md")
                with open(workers, encoding="utf-8") as stream:
                    text = _append_reference_section_text(
                        stream.read(), section_id, addition
                    )
                assert _reasoning_effort_pin_findings(text) == []
            finally:
                shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_rejects_hidden_whole_s06_sections():
    workers = os.path.join(_REPO, "docs", "dev-wave", "workers.md")
    with open(workers, encoding="utf-8") as stream:
        text = stream.read()
    cases = (
        ("DW-S06-A", check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING),
        ("DW-S06-C", check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_FINDING),
    )
    wrappers = (
        ("```\n", "```\n"),
        ("<!--\n", "-->\n"),
        ("<x>\n", ""),
    )
    for section_id, finding in cases:
        for before, after in wrappers:
            hidden = _wrap_workers_section(text, section_id, before, after)
            assert _reasoning_effort_pin_findings(hidden) == [finding]


def _assert_reasoning_effort_production_path_rejects(section_id, finding):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        _write(
            root,
            rel,
            _replace_workers_section_literal(
                _read(root, rel),
                section_id,
                "`reasoning=high`",
            ),
        )
        res = _run_check(root)
        assert res.returncode != 0, res.stdout
        assert finding in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s02_high():
    _assert_reasoning_effort_production_path_rejects(
        "DW-S02",
        check_docs.DEV_WAVE_DW_S02_REASONING_XHIGH_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s03_high():
    _assert_reasoning_effort_production_path_rejects(
        "DW-S03",
        check_docs.DEV_WAVE_DW_S03_REASONING_XHIGH_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_high_exact(
):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        _write(
            root,
            rel,
            _replace_workers_section_literal(
                _read(root, rel),
                "DW-S06-A",
                "`reasoning=high`",
            ),
        )
        res = _run_check(root)
        assert res.returncode != 0, res.stdout
        assert _finding_set(res) == {
            check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_c_high_exact(
):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        _write(
            root,
            rel,
            _replace_workers_section_literal(
                _read(root, rel),
                "DW-S06-C",
                "`reasoning=high`",
            ),
        )
        res = _run_check(root)
        assert res.returncode != 0, res.stdout
        assert _finding_set(res) == {
            check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_FINDING
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s05_a_high_exact(
):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        _write(
            root,
            rel,
            _replace_workers_section_literal(
                _read(root, rel),
                "DW-S05-A",
                "`reasoning=high`",
            ),
        )
        res = _run_check(root)
        assert res.returncode != 0, res.stdout
        assert _finding_set(res) == {
            check_docs.DEV_WAVE_DW_S05_A_REASONING_XHIGH_FINDING
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s05_a_decoys_exact(
):
    finding = check_docs.DEV_WAVE_DW_S05_A_REASONING_XHIGH_FINDING
    for replacement in (
        "参考リンク: [例: `reasoning=high`](https://e.invalid/example)",
        "参考値: outer=`reasoning=high`",
    ):
        root = _build_min_repo()
        try:
            rel = "docs/dev-wave/workers.md"
            _write(
                root,
                rel,
                _replace_workers_section_literal(
                    _read(root, rel),
                    "DW-S05-A",
                    replacement,
                ),
            )
            res = _run_check(root)
            assert res.returncode != 0, res.stdout
            assert _finding_set(res) == {finding}
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_rejects_s06_decoys_exact(
):
    finding = check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING
    for replacement in (
        "参考リンク: [例: `reasoning=high`](https://e.invalid/example)",
        "参考値: outer=`reasoning=high`",
    ):
        root = _build_min_repo()
        try:
            rel = "docs/dev-wave/workers.md"
            _write(
                root,
                rel,
                _replace_workers_section_literal(
                    _read(root, rel),
                    "DW-S06-A",
                    replacement,
                ),
            )
            res = _run_check(root)
            assert res.returncode != 0, res.stdout
            assert _finding_set(res) == {finding}
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_requires_independent_s06_lines_exact(
):
    cases = (
        ("DW-S06-A", check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING),
        ("DW-S06-C", check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_FINDING),
    )
    for section_id, finding in cases:
        sentence = {
            "DW-S06-A": check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_SENTENCE,
            "DW-S06-C": check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_SENTENCE,
        }[section_id]
        replacements = (
            f"> {sentence}",
            f"- {sentence}",
            f"* {sentence}",
            f"+ {sentence}",
            f"1. {sentence}",
            f"# {sentence}",
            f"参考（旧規範）: {sentence}",
            f"例: {sentence}",
            f"  {sentence}",
            f"{sentence} 参考",
            f"{sentence} ",
            f"{sentence}\n{sentence}",
        )
        for replacement in replacements:
            root = _build_min_repo()
            try:
                rel = "docs/dev-wave/workers.md"
                _write(
                    root,
                    rel,
                    _replace_workers_section_sentence(
                        _read(root, rel),
                        section_id,
                        replacement,
                    ),
                )
                res = _run_check(root)
                assert res.returncode != 0, res.stdout
                assert _finding_set(res) == {finding}
            finally:
                shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_rejects_unicode_line_separators_exact(
):
    cases = (
        ("DW-S06-A", check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING),
        ("DW-S06-C", check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_FINDING),
    )
    separators = ("\u2028", "\u2029", "\v", "\f", "\u0085")
    for section_id, finding in cases:
        sentence = {
            "DW-S06-A": check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_SENTENCE,
            "DW-S06-C": check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_SENTENCE,
        }[section_id]
        for separator in separators:
            root = _build_min_repo()
            try:
                rel = "docs/dev-wave/workers.md"
                _write(
                    root,
                    rel,
                    _replace_workers_section_sentence(
                        _read(root, rel),
                        section_id,
                        f"参考（旧規範）:{separator}{sentence}",
                    ),
                )
                res = _run_check(root)
                assert res.returncode != 0, res.stdout
                assert _finding_set(res) == {finding}
            finally:
                shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_accepts_crlf_document_exact(
):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        workers = _read(root, rel)
        assert "\r" not in workers
        _write_bytes(root, rel, workers.replace("\n", "\r\n").encode("utf-8"))
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert _finding_set(res) == set()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _assert_s06_extra_visible_effort_rejected(section_id, finding):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        _write(
            root,
            rel,
            _append_reference_section_text(
                _read(root, rel),
                section_id,
                "\n`reasoning=ultra`\n",
            ),
        )
        res = _run_check(root)
        assert res.returncode != 0, res.stdout
        assert _finding_set(res) == {finding}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_extra_visible_effort_exact(
):
    _assert_s06_extra_visible_effort_rejected(
        "DW-S06-A",
        check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_c_extra_visible_effort_exact(
):
    _assert_s06_extra_visible_effort_rejected(
        "DW-S06-C",
        check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_ambiguous_value_exact(
):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        _write(
            root,
            rel,
            _replace_workers_section_sentence(
                _read(root, rel),
                "DW-S06-A",
                "`reasoning=high/xhigh`",
            ),
        )
        res = _run_check(root)
        assert res.returncode != 0, res.stdout
        assert _finding_set(res) == {
            check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_accepts_url_and_path_references_exact():
    assert [
        match.group("value")
        for match in check_docs.DEV_WAVE_REASONING_EFFORT_RE.finditer(
            "`reasoning=high` and `reasoning=xhigh`"
        )
    ] == ["high", "xhigh"]
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        text = _append_reference_section_text(
            _read(root, rel),
            "DW-S06-A",
            "\nhttps://e.invalid/?reasoning=日本語\n"
            "/path/reasoning=/tmp\n"
            "note.reasoning=💥\n",
        )
        _write(root, rel, text)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert _finding_set(res) == set()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_rejects_hidden_s06_a_exact(
):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        baseline = _read(root, rel)
        expected = {
            check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING,
            (
                "docs/dev-wave/workers.md: H2 見出し DW-S06-A が 0 件 — "
                "dispatch先は一意でなければならない"
            ),
        }
        for before, after in (
            ("```\n", "```\n"),
            ("<!--\n", "-->\n"),
            ("<x>\n", ""),
        ):
            _write(
                root,
                rel,
                _wrap_workers_section(baseline, "DW-S06-A", before, after),
            )
            res = _run_check(root)
            assert res.returncode != 0, res.stdout
            assert _finding_set(res) == expected
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_o16_value_exact(
):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        _write(
            root,
            rel,
            _append_reference_section_text(
                _read(root, rel),
                "DW-O16",
                "\n`reasoning=xhigh`\n",
            ),
        )
        res = _run_check(root)
        assert res.returncode != 0, res.stdout
        assert _finding_set(res) == {
            check_docs.DEV_WAVE_DW_O16_REASONING_EFFORT_FINDING
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _assert_reasoning_effort_real_key_production_path_rejects(
    section_id,
    finding,
):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        _write(
            root,
            rel,
            _replace_workers_section_literal(
                _read(root, rel),
                section_id,
                '`model_reasoning_effort="high"`（例: `reasoning=ultra`）',
            ),
        )
        res = _run_check(root)
        assert res.returncode != 0, res.stdout
        assert finding in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s02_real_key():
    _assert_reasoning_effort_real_key_production_path_rejects(
        "DW-S02",
        check_docs.DEV_WAVE_DW_S02_REASONING_XHIGH_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s03_real_key():
    _assert_reasoning_effort_real_key_production_path_rejects(
        "DW-S03",
        check_docs.DEV_WAVE_DW_S03_REASONING_XHIGH_FINDING,
    )


def test_dev_wave_reasoning_effort_pin_findings_are_time_invariant():
    assert check_docs.DEV_WAVE_DW_S02_REASONING_XHIGH_FINDING == (
        "docs/dev-wave/workers.md: DW-S02 の `reasoning=ultra` は"
        "現行 adoption pin と不一致 — "
        "変更には採用裁定 (A/B 証拠またはユーザー裁定) と pin の同時更新が必要"
    )
    assert check_docs.DEV_WAVE_DW_S03_REASONING_XHIGH_FINDING == (
        "docs/dev-wave/workers.md: DW-S03 の `reasoning=ultra` は"
        "現行 adoption pin と不一致 — "
        "変更には採用裁定 (A/B 証拠またはユーザー裁定) と pin の同時更新が必要"
    )
    assert check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_FINDING == (
        "docs/dev-wave/workers.md: DW-S06-A の `reasoning=ultra` は段 6 敵対レビューの"
        "現行 adoption pin と不一致 — 変更には採用裁定と pin の同時更新が必要"
    )
    assert check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_FINDING == (
        "docs/dev-wave/workers.md: DW-S06-C の `reasoning=ultra` は段 6 焦点再レビューの"
        "現行 adoption pin と不一致 — 変更には採用裁定と pin の同時更新が必要"
    )
    assert check_docs.DEV_WAVE_DW_S06_A_REASONING_XHIGH_SENTENCE == (
        "実装 wave は異なるレンズの敵対レビューを `reasoning=ultra` で必ず 2 本並列で行う。"
    )
    assert check_docs.DEV_WAVE_DW_S06_C_REASONING_XHIGH_SENTENCE == (
        "並列 fix の統合後、焦点再レビューは全体へ `reasoning=ultra` で 1 本でよい。"
    )


def _append_reference_section_body(text, section_id, addition):
    match = re.search(
        rf"^## {re.escape(section_id)}(?:\s+—[^\n]*)?\s*$\n.*?(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    section = match.group(0).rstrip()
    changed_section = section + "\n\n" + addition + "\n\n"
    return text[:match.start()] + changed_section + text[match.end():]


def _replace_reference_section_literal(text, section_id, old, new):
    match = re.search(
        rf"^## {re.escape(section_id)}(?:\s+—[^\n]*)?\s*$\n.*?(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    section = match.group(0)
    changed_section = section.replace(old, new, 1)
    assert changed_section != section
    return text[:match.start()] + changed_section + text[match.end():]


def _assert_model_slug_production_path_rejects(
    rel,
    section_id,
    addition,
    finding,
):
    root = _build_min_repo()
    try:
        _write(
            root,
            rel,
            _append_reference_section_body(
                _read(root, rel),
                section_id,
                addition,
            ),
        )
        _assert_findings(root, finding)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_model_pin_production_path_rejects_dw_s03_backticked_slug():
    _assert_model_slug_production_path_rejects(
        "docs/dev-wave/workers.md",
        "DW-S03",
        "`gpt-5.6-sol`",
        check_docs.DEV_WAVE_WORKERS_MODEL_SLUG_ABSENCE_FINDING,
    )


def test_dev_wave_model_pin_production_path_rejects_dw_s03_bare_model_decoy():
    _assert_model_slug_production_path_rejects(
        "docs/dev-wave/workers.md",
        "DW-S03",
        "-m gpt-5.6-sol",
        check_docs.DEV_WAVE_WORKERS_MODEL_SLUG_ABSENCE_FINDING,
    )


def test_dev_wave_model_pin_production_path_rejects_dw_s02_slug():
    _assert_model_slug_production_path_rejects(
        "docs/dev-wave/workers.md",
        "DW-S02",
        "--model=gpt-5.6-luna",
        check_docs.DEV_WAVE_WORKERS_MODEL_SLUG_ABSENCE_FINDING,
    )


def test_dev_wave_model_pin_production_path_rejects_dw_o01_concrete_model():
    _assert_model_slug_production_path_rejects(
        "docs/dev-wave/operations.md",
        "DW-O01",
        "-m gpt-5.6-sol",
        check_docs.DEV_WAVE_DW_O01_MODEL_AUTHORITY_FINDING,
    )


def test_dev_wave_model_pin_rejects_dw_o01_authority_drift():
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        changed = text.replace("gpt-6-astra", "gpt-5.6-terra", 1)
        assert changed != text
        _write(root, rel, changed)
        _assert_findings(
            root,
            check_docs.DEV_WAVE_DW_O01_MODEL_AUTHORITY_FINDING,
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_model_pin_rejects_dw_o01_authority_in_html_comment():
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        literal = check_docs.DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL
        changed = text.replace(literal, f"<!-- {literal} -->", 1)
        assert changed != text
        _write(root, rel, changed)
        _assert_findings(
            root,
            check_docs.DEV_WAVE_DW_O01_MODEL_AUTHORITY_FINDING,
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_model_pin_rejects_duplicate_dw_o01_authority():
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        literal = check_docs.DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL
        changed = text.replace(literal, f"{literal}\n\n{literal}", 1)
        assert changed != text
        _write(root, rel, changed)
        _assert_findings(
            root,
            check_docs.DEV_WAVE_DW_O01_MODEL_AUTHORITY_FINDING,
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_model_pin_rejects_slug_in_dw_o01_heading():
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        changed = text.replace(
            "## DW-O01 — synthetic",
            "## DW-O01 — synthetic gpt-5.6-sol",
            1,
        )
        assert changed != text
        _write(root, rel, changed)
        _assert_findings(
            root,
            check_docs.DEV_WAVE_DW_O01_MODEL_AUTHORITY_FINDING,
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_model_pin_rejects_missing_dw_o01_model_placeholder():
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        _write(
            root,
            rel,
            _replace_reference_section_literal(
                _read(root, rel),
                "DW-O01",
                check_docs.DEV_WAVE_DW_O01_DISPATCH_ROUTE_LITERAL,
                "--model-from-dispatcher",
            ),
        )
        _assert_findings(
            root,
            check_docs.DEV_WAVE_DW_O01_MODEL_PLACEHOLDER_FINDING,
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    "replacement",
    (
        lambda line: f"> {line}",
        lambda line: f"- {line}",
        lambda line: f"<div>\n{line}\n</div>\n",
        lambda line: f"この route では起動しない: {line}",
    ),
)
def test_dev_wave_dispatch_route_requires_visible_top_level_full_match(
    replacement,
):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        route = check_docs.DEV_WAVE_DW_O01_DISPATCH_ROUTE_LITERAL
        changed = text.replace(route, replacement(route), 1)
        assert changed != text
        _write(root, rel, changed)
        _assert_findings(
            root,
            check_docs.DEV_WAVE_DW_O01_MODEL_PLACEHOLDER_FINDING,
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("separator", ("\u2028", "\u2029"))
def test_dev_wave_dispatch_route_rejects_separator_in_normative_candidate(
    separator,
):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        route = check_docs.DEV_WAVE_DW_O01_DISPATCH_ROUTE_LITERAL
        changed_route = route.replace(" --stage", f"{separator}--stage", 1)
        assert changed_route != route
        _write(root, rel, text.replace(route, changed_route, 1))
        _assert_findings(
            root,
            check_docs.DEV_WAVE_DW_O01_MODEL_PLACEHOLDER_FINDING,
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


_ROUTE_SEPARATOR_NON_CANDIDATE_CASES = (
    "fence",
    "html_comment",
    "raw_html",
    "visible_prose",
    "non_target_section",
)


@pytest.mark.parametrize("separator", ("\u2028", "\u2029"))
@pytest.mark.parametrize("case", _ROUTE_SEPARATOR_NON_CANDIDATE_CASES)
def test_dev_wave_dispatch_route_accepts_separator_outside_candidate(
    case,
    separator,
):
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        route = check_docs.DEV_WAVE_DW_O01_DISPATCH_ROUTE_LITERAL
        decoy = f"補足{separator}説明"
        if case == "fence":
            payload = f"```text\n{decoy}\n```"
        elif case == "html_comment":
            payload = f"<!-- {decoy} -->"
        elif case == "raw_html":
            payload = f"<div>\n{decoy}\n</div>\n"
        elif case == "visible_prose":
            payload = f"非規範の補足: {decoy}"
        elif case == "non_target_section":
            marker = "## DW-O02 — synthetic\n\n"
            assert marker in text
            changed = text.replace(marker, f"{marker}{decoy}\n\n", 1)
            payload = None
        else:  # pragma: no cover - registration meta-test が閉じる
            raise AssertionError(case)
        if payload is not None:
            changed = text.replace(route, f"{payload}\n{route}", 1)
        assert changed != text
        _write(root, rel, changed)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert _finding_set(res) == set()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_route_separator_non_candidate_registration_is_complete():
    assert set(_ROUTE_SEPARATOR_NON_CANDIDATE_CASES) == {
        "fence",
        "html_comment",
        "raw_html",
        "visible_prose",
        "non_target_section",
    }


def test_dev_wave_model_pin_rejects_slug_in_dw_s05_a():
    _assert_model_slug_production_path_rejects(
        "docs/dev-wave/workers.md",
        "DW-S05-A",
        "gpt-5.6-luna",
        check_docs.DEV_WAVE_WORKERS_MODEL_SLUG_ABSENCE_FINDING,
    )


def test_dev_wave_model_pin_rejects_slug_in_dw_s03_heading():
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/workers.md"
        text = _read(root, rel)
        changed = text.replace(
            "## DW-S03 — synthetic",
            "## DW-S03 — synthetic gpt-5.6-sol",
            1,
        )
        assert changed != text
        _write(root, rel, changed)
        _assert_findings(
            root,
            check_docs.DEV_WAVE_WORKERS_MODEL_SLUG_ABSENCE_FINDING,
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_model_pin_rejects_other_model_family_outside_dw_o01():
    _assert_model_slug_production_path_rejects(
        "docs/dev-wave/operations.md",
        "DW-O05",
        "gpt-5.4-mini",
        check_docs.DEV_WAVE_OPERATIONS_OUTSIDE_DW_O01_MODEL_SLUG_ABSENCE_FINDING,
    )


def test_dev_wave_model_pin_rejects_slug_in_command():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/dev-wave.md"
        _write(root, rel, _read(root, rel) + "\ngpt-5.6-sol\n")
        _assert_findings(
            root,
            check_docs.DEV_WAVE_COMMAND_MODEL_SLUG_ABSENCE_FINDING,
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_model_pin_rejects_duplicate_dw_o01_section():
    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        _insert_before_unique_marker(
            root,
            rel,
            "## DW-O25 —",
            "## DW-O01 — duplicate\n\nbody\n\n",
        )
        # DW-O01 重複は model pin と既存 H2 一意性の冗長 gate である。
        _assert_findings(
            root,
            check_docs.DEV_WAVE_DW_O01_SECTION_CARDINALITY_FINDING,
            f"{rel}: H2 見出し DW-O01 が 2 件 — "
            "dispatch先は一意でなければならない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_model_pins_accept_min_repo_contract():
    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "違反なし" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_model_pins_accept_current_docs_contract():
    res = subprocess.run(
        [sys.executable, os.path.join(_REPO, "tools", "check_docs.py")],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"実 repo で違反が出た:\n{res.stdout}\n{res.stderr}"
    assert "違反なし" in res.stdout, res.stdout


def test_dev_wave_model_pin_contract_is_time_invariant():
    assert check_docs.DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL == (
        "`<model>`: 全段 `gpt-6-astra` (段 3 の 2 本も同じ)。"
    )
    assert check_docs.DEV_WAVE_MODEL_SLUG_RE.findall(
        "`gpt-5.6-sol` -m gpt-5.6-sol --model=gpt-5.6-luna\n"
        "gpt-5.6-terra gpt-5.4-mini gpt-6-next\n"
        "descriptions: gpt-5.6-* gpt-6-*"
    ) == [
        "gpt-5.6-sol",
        "gpt-5.6-sol",
        "gpt-5.6-luna",
        "gpt-5.6-terra",
        "gpt-5.4-mini",
        "gpt-6-next",
    ]
    assert check_docs.DEV_WAVE_DW_O01_DISPATCH_ROUTE_LITERAL == (
        "`tools/dev_wave_codex.py --stage <stage> [--lane <lane>] -o <出力>.md` "
        "で起動（他の引数は `--help`）。model は全段、effort は段 5 / 6 "
        "が docs 権威から導出。caller 指定は不可。"
    )


def test_codex_dev_wave_skill_contract_pins_exact_surface():
    """checker と合成 fixture の同時縮小で adapter 義務が消えないよう外延を固定する。"""

    assert check_docs.CODEX_DEV_WAVE_SKILL_FILES == {
        ".agents/skills/dev-wave/SKILL.md",
        ".agents/skills/dev-wave/agents/openai.yaml",
    }
    assert check_docs.CODEX_DEV_WAVE_SKILL_LITERALS == (
        ".claude/commands/dev-wave.md",
        "4. `docs/skill-self-improvement.md` の発火 gate・routing・dev-wave "
        "終端を読み、専用 handoff に\n"
        "   `dev-wave 改善候補` 節を作る。",
        "docs/dev-wave/workers.md",
        "docs/dev-wave/operations.md",
        "本 Skill は明示起動専用であり、自然文の依頼を一般タスクとして\n"
        "  処理せず、`$dev-wave <対象>` の明示起動を案内して止まる。",
        "防護パス文字列を含む prompt・commit message は、Bash heredoc や不透明な command substitution で\n"
        "  作らない。Codex では Bash の中からではなく `apply_patch` tool を直接呼び、新規 file は\n"
        "  `*** Add File:` patch で作る。commit message はその file を `git commit -F <file>` へ渡す。",
        "manager は実装面を直接編集しない",
        "codex exec",
        "collaboration child",
        ".codex/role-adapters/*.json",
        "hooks/README.md",
        "supervised manifest",
        "段 1〜9",
        "local main",
    )
    assert check_docs.CODEX_DEV_WAVE_DESCRIPTION == (
        _SYNTHETIC_DEV_WAVE_DESCRIPTION
    )
    assert check_docs.CODEX_DEV_WAVE_OPENAI_YAML == (
        _SYNTHETIC_DEV_WAVE_OPENAI_YAML
    )


def test_normative_exact_section_contract_is_handwritten_and_complete():
    """production 定数と合成 fixture の共謀的縮小を独立 literal で拒否する。"""

    assert check_docs.DEV_WAVE_COMMAND_START_SECTION_LITERAL == (
        _SYNTHETIC_DEV_WAVE_COMMAND_START_SECTION
    )
    assert check_docs.CODEX_DEV_WAVE_START_SECTION_LITERAL == (
        _SYNTHETIC_CODEX_DEV_WAVE_START_SECTION
    )
    assert check_docs.DEV_WAVE_SELF_ROUTING_SECTION_LITERAL == (
        _SYNTHETIC_SELF_ROUTING_SECTION
    )
    assert check_docs.DEV_WAVE_DW_O25_SECTION_LITERAL == (
        _SYNTHETIC_DW_O25_SECTION
    )
    assert check_docs.DEV_WAVE_DW_O18_SECTION_LITERAL == (
        _SYNTHETIC_DW_O18_SECTION
    )
    assert check_docs.DEV_WAVE_DW_O26_SECTION_LITERAL == (
        _SYNTHETIC_DW_O26_SECTION
    )
    assert check_docs.DEV_WAVE_DW_O28_SECTION_LITERAL == (
        _SYNTHETIC_DW_O28_SECTION
    )
    assert check_docs.DEV_WAVE_DW_C01_SECTION_LITERAL == (
        _SYNTHETIC_DW_C01_SECTION
    )
    assert len(_SYNTHETIC_DW_O18_SECTION.encode("utf-8")) == 995
    assert len(_SYNTHETIC_DW_O25_SECTION.encode("utf-8")) == 648
    assert len(_SYNTHETIC_DW_O26_SECTION.encode("utf-8")) == 998
    assert len(_SYNTHETIC_DW_O28_SECTION.encode("utf-8")) == 996
    assert len(_SYNTHETIC_DW_C01_SECTION.encode("utf-8")) == 994
    assert len("- Web検索は必要な段だけ明示して使う。\n".encode("utf-8")) == 54
    assert check_docs.DEV_WAVE_EXACT_VISIBLE_SECTIONS == {
        (".claude/commands/dev-wave.md", "入力と開始"):
            _SYNTHETIC_DEV_WAVE_COMMAND_START_SECTION,
        ("docs/skill-self-improvement.md", "routing"):
            _SYNTHETIC_SELF_ROUTING_SECTION,
        (
            "docs/dev-wave/operations.md",
            "DW-O18 — テスト cwd と非帰属赤の着地",
        ): _SYNTHETIC_DW_O18_SECTION,
        (
            "docs/dev-wave/operations.md",
            "DW-O25 — ff-only land の全史 provenance 関門",
        ): _SYNTHETIC_DW_O25_SECTION,
        (
            "docs/dev-wave/operations.md",
            "DW-O26 — 焦点走の consumer test 拡張",
        ): _SYNTHETIC_DW_O26_SECTION,
        (
            "docs/dev-wave/operations.md",
            "DW-O28 — land 後の自己撤去",
        ): _SYNTHETIC_DW_O28_SECTION,
        (
            "docs/dev-wave/core.md",
            "DW-C01 — 実測で是正した作法",
        ): _SYNTHETIC_DW_C01_SECTION + "\n",
    }
    assert len(check_docs.DEV_WAVE_EXACT_VISIBLE_SECTIONS[
        ("docs/dev-wave/core.md", "DW-C01 — 実測で是正した作法")
    ].encode("utf-8")) == 995


def test_dw_o18_exact_section_pin_accepts_synthetic_fixture():
    """DW-O18/DW-O26 の独立全文 literal を持つ baseline 正例を固定する。"""

    root = _build_min_repo()
    try:
        operations = _read(root, "docs/dev-wave/operations.md")
        assert operations.count(_SYNTHETIC_DW_O18_SECTION) == 1
        assert operations.count(_SYNTHETIC_DW_O26_SECTION) == 1
        result = _run_check(root)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "違反なし" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dw_o26_exact_section_pin_accepts_synthetic_fixture():
    """DW-O26 の全文・見出しが exact pin と一致する正例を固定する。"""

    root = _build_min_repo()
    try:
        operations = _read(root, "docs/dev-wave/operations.md")
        assert operations.count(_SYNTHETIC_DW_O26_SECTION) == 1
        result = _run_check(root)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "違反なし" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    "case",
    (
        "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8",
        "M10", "M11", "M12",
    ),
)
def test_non_attributable_landing_contract_mutations_have_one_finding(case):
    """段 4 の M1〜M8・M10〜M12 は対応する単一理由だけで拒否する。"""

    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel)
        o18_finding = (
            f"{rel}: 可視 H2 節 'DW-O18 — テスト cwd と非帰属赤の着地' の"
            "節全体が exact 契約と不一致 — sections=1"
        )
        o26_finding = (
            f"{rel}: 可視 H2 節 'DW-O26 — 焦点走の consumer test 拡張' の"
            "節全体が exact 契約と不一致 — sections=1"
        )
        if case == "M1":
            needle = "非帰属赤の着地5分超禁止、悩まない(D690)。"
            assert text.count(needle) == 1
            changed = text.replace(
                needle,
                "5分を目安にする。",
                1,
            )
            expected = o18_finding
        elif case == "M2":
            needle = "真に決定的な不安定testはその1件のpin更新を個別に諮り、"
            assert text.count(needle) == 1
            changed = text.replace(needle, "", 1)
            expected = o18_finding
        elif case == "M3":
            needle = "受理は`child-green`だけ、"
            assert text.count(needle) == 1
            changed = text.replace(
                needle,
                "",
                1,
            )
            expected = o18_finding
        elif case == "M4":
            needle = "判定不能・原因未理解は除外せず共に停止。"
            assert text.count(needle) == 1
            changed = text.replace(needle, "", 1)
            expected = o18_finding
        elif case == "M5":
            changed = _append_reference_section_body(
                text,
                "DW-O16",
                "non-attributable-only",
            )
            expected = (
                check_docs.DEV_WAVE_OPERATIONS_NON_ATTRIBUTABLE_ONLY_ABSENCE_FINDING
            )
        elif case == "M6":
            changed = _append_reference_section_body(
                text,
                "DW-O16",
                "tools/check_acceptance_reds.py",
            )
            expected = (
                check_docs.DEV_WAVE_OPERATIONS_ACCEPTANCE_REDS_TOOL_ABSENCE_FINDING
            )
        elif case == "M7":
            changed = text.replace(
                "## DW-O18 — テスト cwd と非帰属赤の着地",
                "## DW-O18 — テスト cwd と非帰属赤の処理",
                1,
            )
            expected = o18_finding.replace("sections=1", "sections=0")
        elif case == "M8":
            changed = text.replace(
                "変更 test file は受入前に単独走で確認する。",
                "",
                1,
            )
            expected = o26_finding
        elif case == "M10":
            needle = "N走完全一致はflakeでも非帰属の証拠でもない。"
            assert text.count(needle) == 1
            changed = text.replace(needle, "", 1)
            expected = o18_finding
        elif case == "M11":
            needle = "停止条件外は治すか上記の制限内で投げ直しwaveを止めない。"
            assert text.count(needle) == 1
            changed = text.replace(needle, "", 1)
            expected = o18_finding
        elif case == "M12":
            needle = "未確立赤も偽赤。"
            assert text.count(needle) == 1
            changed = text.replace(needle, "", 1)
            expected = o18_finding
        else:  # pragma: no cover - parameter 集合を上で固定する
            raise AssertionError(case)
        assert changed != text
        _write(root, rel, changed)
        result = _run_check(root)
        assert result.returncode == 1, result.stdout + result.stderr
        assert _finding_set(result) == {expected}, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_non_attributable_landing_general_terms_are_accepted():
    """M9: 一般語だけの追記を禁止語として過検出しない。"""

    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        text = _append_reference_section_body(
            _read(root, rel),
            "DW-O16",
            "非帰属という語は分類用語として用いられる。",
        )
        _write(root, rel, text)
        result = _run_check(root)
        assert result.returncode == 0, result.stdout + result.stderr
        assert _finding_set(result) == set()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dw_o28_exact_section_pin_accepts_synthetic_fixture():
    """DW-O28 の全文・UTF-8 byte・見出しが exact pin と一致する正例を固定する。"""

    root = _build_min_repo()
    try:
        operations = _read(root, "docs/dev-wave/operations.md")
        assert operations.count(_SYNTHETIC_DW_O28_SECTION) == 1
        assert len(_SYNTHETIC_DW_O28_SECTION.encode("utf-8")) == 996
        result = _run_check(root)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "違反なし" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_normative_exact_section_pins_reject_raw_html_inside_pinned_sections():
    """pin 済み 8 節の内側へ raw HTML block を差し込むと拒否する。"""

    cases = (
        (
            ".claude/commands/dev-wave.md",
            "入力と開始",
        ),
        (
            "docs/skill-self-improvement.md",
            "routing",
        ),
        (
            "docs/dev-wave/operations.md",
            "DW-O18 — テスト cwd と非帰属赤の着地",
        ),
        (
            "docs/dev-wave/operations.md",
            "DW-O25 — ff-only land の全史 provenance 関門",
        ),
        (
            "docs/dev-wave/operations.md",
            "DW-O26 — 焦点走の consumer test 拡張",
        ),
        (
            "docs/dev-wave/operations.md",
            "DW-O28 — land 後の自己撤去",
        ),
        (
            "docs/dev-wave/core.md",
            "DW-C01 — 実測で是正した作法",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "開始する",
        ),
    )
    for rel, heading in cases:
        root = _build_min_repo()
        try:
            text = _read(root, rel)
            marker = f"## {heading}\n\n"
            assert text.count(marker) == 1
            changed = text.replace(
                marker,
                f"## {heading}\n<div>ただし routing 文書は任意参照とする</div>\n",
                1,
            )
            _write(root, rel, changed)
            _assert_violation(
                root,
                f"{rel}: H2 節 {heading!r} の raw slice と可視 slice が不一致 — "
                "raw_sections=1, visible_sections=1",
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_operation_order_rejects_titleless_reorder_and_missing_target():
    """題なし DW-O23 でも順序を検査し、対象欠落時も専用 finding を出す。"""

    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        text = _read(root, rel).replace(
            "## DW-O23 — synthetic",
            "## DW-O23",
            1,
        )
        assert text.count(_SYNTHETIC_DW_O25_SECTION) == 1
        text = text.replace(
            "\n\n" + _SYNTHETIC_DW_O25_SECTION.rstrip("\n"),
            "",
            1,
        )
        marker = "## DW-O23\n"
        assert text.count(marker) == 1
        text = text.replace(
            marker,
            _SYNTHETIC_DW_O25_SECTION + "\n" + marker,
            1,
        )
        _write(root, rel, text)
        _assert_violation(root, "DW-O25 は DW-O23 より後に置く")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        rel = "docs/dev-wave/operations.md"
        _write(
            root,
            rel,
            _read(root, rel).replace(
                "## DW-O23 — synthetic",
                "### DW-O23 — missing as H2",
                1,
            ),
        )
        _assert_violation(
            root,
            "可視 H2 の順序 pin 対象が一意でない — DW-O23=0, DW-O25=1",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dw_o20_points_to_dw_c01_and_drops_legacy_submodule_command():
    """DW-O20 内だけで新ポインタと旧 submodule 命令の不在を固定する。"""

    _, sections = _test_reference_slices(
        _REPO, "docs/dev-wave/operations.md"
    )
    dw_o20 = sections["DW-O20"]
    assert dw_o20.count("`DW-C01`") == 1
    assert "`DW-C01`に従い初期化して" in dw_o20
    assert "`git submodule update --init`" not in dw_o20


def test_dw_c01_is_immediately_before_dw_stop():
    """既存 core slice を動かさず C01 を DW-STOP の直前へ置く。"""

    text = _read(_REPO, "docs/dev-wave/core.md")
    section_ids = re.findall(r"^##\s+([^\s—]+)", text, re.MULTILINE)
    assert section_ids.count("DW-C01") == 1
    assert section_ids.count("DW-STOP") == 1
    c01_index = section_ids.index("DW-C01")
    assert section_ids[c01_index + 1] == "DW-STOP"


def test_normative_exact_section_pins_accept_real_repo():
    """新 pin が過剰拒否に変異したとき実 repo 正例で必ず落ちる。"""

    res = subprocess.run(
        [sys.executable, os.path.join(_REPO, "tools", "check_docs.py")],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"実 repo で過剰拒否した:\n{res.stdout}\n{res.stderr}"
    assert "違反なし" in res.stdout, res.stdout


def test_codex_rulings_skill_contract_pins_exact_surface():
    """checker と合成 fixture の同時縮小で adapter 義務が消えないよう外延を固定する。"""

    assert check_docs.CODEX_RULINGS_SKILL_FILES == {
        ".agents/skills/rulings/SKILL.md",
        ".agents/skills/rulings/agents/openai.yaml",
    }
    assert check_docs.CODEX_RULINGS_SKILL_LITERALS == (
        "AGENTS.md",
        "CLAUDE.md",
        ".claude/commands/rulings.md",
        "$ARGUMENTS",
        "$rulings",
        "docs/worklog.md",
        "docs/skill-self-improvement.md",
        "hooks/README.md",
        "クラス 1",
        "クラス 2",
        "それ以外ではファイルを編集しない",
        "push と remote branch 操作は人間に残す",
    )
    assert check_docs.CODEX_RULINGS_OPENAI_YAML == (
        'interface:\n'
        '  display_name: "Rulings"\n'
        '  short_description: "Izanagi の裁定待ちを索引・詳説して判断を補佐"\n'
        '  default_prompt: "Use $rulings to list and explain the Izanagi '
        'decisions awaiting my ruling."\n'
    )


def test_codex_next_tasks_skill_contract_pins_exact_surface():
    """checker と合成 fixture の同時変更に対し独立 literal で契約を固定する。"""

    assert check_docs.CODEX_NEXT_TASKS_SKILL_FILES == {
        ".agents/skills/next-tasks/SKILL.md",
        ".agents/skills/next-tasks/agents/openai.yaml",
    }
    assert check_docs.CODEX_NEXT_TASKS_SKILL_LIMITS == {
        ".agents/skills/next-tasks/SKILL.md": check_docs.TextLimit(5_732, 400),
        ".agents/skills/next-tasks/agents/openai.yaml": check_docs.TextLimit(300, 160),
    }
    assert check_docs.CODEX_NEXT_TASKS_SKILL_LITERALS == (
        "AGENTS.md",
        "CLAUDE.md",
        ".claude/commands/next-tasks.md",
        "$1",
        "$next-tasks",
        "$dev-wave",
        "docs/pegasus-runbook.md",
        "docs/skill-self-improvement.md",
        "hooks/README.md",
        "クラス 1",
        "クラス 2",
        "D2051",
        "next_tasks_consult.sh claude",
        "実測せずに外さない",
        "CONSULT-MODE",
        "3 巡目へ進めず",
        "件数合わせで除外候補を復活させない",
        "自己改善の終端条件を含める",
        "丸付き数字は使わない",
        "それ以外ではファイルを編集しない",
        "push と remote branch 操作は人間に残す",
        "環境に API キーを置かない",
        "API key や代替 provider を新設して呼び出す経路は作らない",
    )
    assert check_docs.CODEX_NEXT_TASKS_OPENAI_YAML == (
        'interface:\n'
        '  display_name: "Next Tasks"\n'
        '  short_description: "今すぐ投げられる dev-wave タスク候補を提案"\n'
        '  default_prompt: "Use $next-tasks to propose two dev-wave tasks that can start now."\n'
    )
    assert check_docs.REQUIRED_SELF_HEADINGS[3] == {
        "dev-wave", "cleanup-branches", "rulings", "next-tasks",
    }


def test_codex_cleanup_branches_skill_contract_pins_exact_surface():
    """checker と test fixture の whole-file pin を独立 literal で固定する。"""

    assert check_docs.CODEX_CLEANUP_BRANCHES_SKILL_FILES == {
        ".agents/skills/cleanup-branches/SKILL.md",
        ".agents/skills/cleanup-branches/agents/openai.yaml",
    }
    assert check_docs.CODEX_CLEANUP_BRANCHES_SKILL_LIMITS == {
        ".agents/skills/cleanup-branches/SKILL.md":
            check_docs.TextLimit(3_100, 210),
        ".agents/skills/cleanup-branches/agents/openai.yaml":
            check_docs.TextLimit(300, 110),
    }
    assert check_docs.CODEX_CLEANUP_BRANCHES_DESCRIPTION == (
        _SYNTHETIC_CLEANUP_DESCRIPTION
    )
    assert check_docs.CODEX_CLEANUP_BRANCHES_OPENAI_YAML == (
        _SYNTHETIC_CLEANUP_OPENAI_YAML
    )
    assert check_docs.CODEX_CLEANUP_BRANCHES_SKILL_SHA256 == (
        _EXPECTED_CLEANUP_SKILL_SHA256
    )
    assert check_docs.CLEANUP_COMMAND_SHA256 == (
        _EXPECTED_CLEANUP_COMMAND_SHA256
    )
    assert hashlib.sha256(
        _SYNTHETIC_CLEANUP_SKILL.encode("utf-8")
    ).hexdigest() == _EXPECTED_CLEANUP_SKILL_SHA256
    assert hashlib.sha256(
        _SYNTHETIC_CLEANUP_COMMAND.encode("utf-8")
    ).hexdigest() == _EXPECTED_CLEANUP_COMMAND_SHA256


def test_cleanup_command_budget_is_pinned_and_enforced():
    rel = ".claude/commands/cleanup-branches.md"
    assert check_docs.COMMAND_LIMITS[rel] == check_docs.TextLimit(9_064, 110)
    assert len(_SYNTHETIC_CLEANUP_COMMAND.encode("utf-8")) == 9_061

    root = _build_min_repo()
    try:
        original = _read(root, rel)
        assert len(original.encode("utf-8")) == 9_061
        oversized = original + "\n" + "x" * 3
        assert len(oversized.encode("utf-8")) == 9_065
        _write(root, rel, oversized)

        res = _run_check(root)

        assert res.returncode == 1, res.stdout
        assert (
            f"{rel}: 9065 bytes > 予算 9064 bytes" in res.stdout
        ), res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_command_docs_guard_rejects_symlinked_commands_directory():
    root = _build_min_repo()
    external = tempfile.mkdtemp(prefix="izanagi_checkdocs_external_commands_")
    try:
        command_dir = os.path.join(root, ".claude", "commands")
        shutil.copytree(command_dir, external, dirs_exist_ok=True)
        _write(
            external,
            "EXTERNAL-COMMAND-SENTINEL.md",
            "# EXTERNAL-COMMAND-SENTINEL\n",
        )
        shutil.rmtree(command_dir)
        os.symlink(external, command_dir)
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert re.search(
            r"^check_docs: \d+ 件の違反$", res.stdout, re.MULTILINE
        ), res.stdout
        assert ".claude/commands: command directory が symlink" in res.stdout
        assert "EXTERNAL-COMMAND-SENTINEL" not in res.stdout, res.stdout
        assert "Traceback" not in res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(external, ignore_errors=True)


@pytest.mark.parametrize("case", _COMMAND_GUARD_CASES)
def test_command_docs_guard_positive_controls(case):
    """各 finding 分岐は baseline からケース別の期待件数だけ増える。"""

    root = _build_min_repo()
    try:
        baseline = _run_check(root)
        assert baseline.returncode == 0, baseline.stdout
        _mutate_command_guard(root, case)
        res = _run_check(root)
        assert res.returncode == 1, (
            f"{case}: positive control が赤にならなかった:\n{res.stdout}\n{res.stderr}"
        )
        assert _violation_count(res) == _COMMAND_GUARD_EXPECTED_COUNTS[case], (
            f"{case}: baseline との差分件数が期待値と違う:\n{res.stdout}"
        )
        assert _COMMAND_GUARD_NEEDLES[case] in res.stdout, (
            f"{case}: 対応する finding 分岐が発火していない:\n{res.stdout}"
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _assert_cleanup_digest_violation(root: str, rel: str) -> None:
    res = _run_check(root)
    assert res.returncode == 1, res.stdout
    assert _violation_count(res) == 1, res.stdout
    assert f"{rel}: whole-file SHA-256 が契約と不一致" in res.stdout


def test_cleanup_skill_one_byte_change_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".agents/skills/cleanup-branches/SKILL.md"
        original = _read(root, rel)
        changed = original.replace("cleanup dispatcher", "cleanvp dispatcher", 1)
        assert len(changed.encode("utf-8")) == len(original.encode("utf-8"))
        assert sum(a != b for a, b in zip(
            changed.encode("utf-8"), original.encode("utf-8")
        )) == 1
        _write(root, rel, changed)
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_command_one_byte_change_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        original = _read(root, rel)
        source = "commit graph"
        assert original.count(source) == 1
        changed = original.replace(source, "commit graqh", 1)
        assert len(changed.encode("utf-8")) == len(original.encode("utf-8"))
        assert sum(a != b for a, b in zip(
            changed.encode("utf-8"), original.encode("utf-8")
        )) == 1
        _write(root, rel, changed)
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_skill_additional_h2_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".agents/skills/cleanup-branches/SKILL.md"
        _write(root, rel, _read(root, rel) + "\n## destructive override\n")
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_command_closing_hash_h2_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        original = _read(root, rel)
        changed = original.replace(
            "## 4. 事後検査", "## 4. 事後検査 ##", 1
        )
        _write(root, rel, _make_cleanup_command_mutation_budget_neutral(
            original, changed
        ))
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_command_leading_space_h2_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        _write(root, rel, _read(root, rel).replace(
            "## 4. 事後検査", " ## 4. 事後検査", 1
        ))
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_command_setext_h2_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        original = _read(root, rel)
        changed = original.replace(
            "## 4. 事後検査", "4. 事後検査\n------------", 1
        )
        _write(root, rel, _make_cleanup_command_mutation_budget_neutral(
            original, changed
        ))
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_command_invalid_backtick_info_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        original = _read(root, rel)
        changed = original + "\n```x`x\n## x\n```\n"
        _write(root, rel, _make_cleanup_command_mutation_budget_neutral(
            original, changed
        ))
        _assert_cleanup_digest_violation(root, rel)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_metadata_policy_block_is_required():
    root = _build_min_repo()
    try:
        rel = ".agents/skills/dev-wave/agents/openai.yaml"
        policy = "\npolicy:\n  allow_implicit_invocation: false\n"
        original = _read(root, rel)
        assert original.count(policy) == 1
        _write(root, rel, original.replace(policy, "", 1))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1, res.stdout
        assert "生成済み Skill interface 契約と不一致" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_explicit_trigger_description_is_required():
    root = _build_min_repo()
    try:
        rel = ".agents/skills/dev-wave/SKILL.md"
        current = f"description: {_SYNTHETIC_DEV_WAVE_DESCRIPTION}"
        old = f"description: {_PRE_WAVE_CODEX_DEV_WAVE_DESCRIPTION}"
        original = _read(root, rel)
        assert original.count(current) == 1
        _write(root, rel, original.replace(current, old, 1))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1, res.stdout
        assert "description が explicit trigger 契約と不一致" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dev_wave_description_guard_wiring_evaporation_characterization():
    """配線を削ると緑になる現況を characterization する。

    実効的な防壁は `test_dev_wave_explicit_trigger_description_is_required` である。
    """

    root = _build_min_repo()
    try:
        skill_rel = ".agents/skills/dev-wave/SKILL.md"
        current = f"description: {_SYNTHETIC_DEV_WAVE_DESCRIPTION}"
        old = f"description: {_PRE_WAVE_CODEX_DEV_WAVE_DESCRIPTION}"
        skill = _read(root, skill_rel)
        assert skill.count(current) == 1
        _write(root, skill_rel, skill.replace(current, old, 1))

        checker_rel = "tools/check_docs.py"
        checker = _read(root, checker_rel)
        wiring = (
            "        expected_description=CODEX_DEV_WAVE_DESCRIPTION,\n"
        )
        assert checker.count(wiring) == 1
        _write(root, checker_rel, checker.replace(wiring, "", 1))

        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "description が explicit trigger 契約と不一致" not in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_metadata_policy_block_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".agents/skills/cleanup-branches/agents/openai.yaml"
        original = _read(root, rel)
        assert "\npolicy:\n" not in original
        _write(
            root,
            rel,
            original + "\npolicy:\n  allow_implicit_invocation: false\n",
        )
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1, res.stdout
        assert "生成済み Skill interface 契約と不一致" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _rebind_synthetic_cleanup_command_digest(root: str) -> None:
    rel = ".claude/commands/cleanup-branches.md"
    digest = hashlib.sha256(_read(root, rel).encode("utf-8")).hexdigest()
    assert digest != check_docs.CLEANUP_COMMAND_SHA256
    checker_rel = "tools/check_docs.py"
    checker = _read(root, checker_rel)
    old = (
        "CLEANUP_COMMAND_SHA256 = (\n"
        f'    "{check_docs.CLEANUP_COMMAND_SHA256}"\n'
        ")"
    )
    assert checker.count(old) == 1
    _write(root, checker_rel, checker.replace(
        old,
        "CLEANUP_COMMAND_SHA256 = (\n"
        f'    "{digest}"\n'
        ")",
        1,
    ))


def _make_cleanup_command_mutation_budget_neutral(
    original: str,
    mutated: str,
) -> str:
    """変異の byte 純増分を、検査対象外の別箇所から取り除く。"""

    original_size = len(original.encode("utf-8"))
    added_bytes = len(mutated.encode("utf-8")) - original_size
    slack = "discard_changes: true"
    assert added_bytes > 0, "cleanup command mutation must add bytes"
    assert original.count(slack) == 1, "cleanup command slack must be unique"
    assert mutated.count(slack) == 1, "mutation must not touch cleanup command slack"
    assert added_bytes < len(slack), "insufficient cleanup command mutation slack"

    balanced = mutated.replace(slack, slack[:-added_bytes], 1)
    assert len(balanced.encode("utf-8")) == original_size
    return balanced


def _assert_cleanup_address_edge_violation(root: str) -> None:
    rel = ".claude/commands/cleanup-branches.md"
    res = _assert_violation(
        root,
        f"{rel}: F26 と `docs/failures.md` が同一可視行に共起しない",
    )
    assert _violation_count(res) == 1, res.stdout
    assert f"{rel}: whole-file SHA-256 が契約と不一致" not in res.stdout


def test_cleanup_checker_invocation_line_is_required():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        invocation = (
            "削除の直前に対象ごと `python3 "
            "tools/check_worktree_occupancy.py <worktree>`。rc0 のみ進み、\n"
            "rc1=占有/rc2=判定不能は停止。"
        )
        original = _read(root, rel)
        assert original.count(invocation) == 1
        _write(root, rel, original.replace(invocation, "", 1))
        _rebind_synthetic_cleanup_command_digest(root)

        res = _run_check(root)

        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1, res.stdout
        assert "worktree 占有 checker の必須可視 literal が無い" in res.stdout
        assert f"{rel}: whole-file SHA-256 が契約と不一致" not in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _assert_cleanup_checker_contract_violation(root: str) -> None:
    rel = ".claude/commands/cleanup-branches.md"
    res = _run_check(root)
    assert res.returncode == 1, res.stdout
    assert _violation_count(res) == 1, res.stdout
    assert "worktree 占有 checker の必須可視 literal が無い" in res.stdout
    assert f"{rel}: whole-file SHA-256 が契約と不一致" not in res.stdout


def test_cleanup_checker_rc_rules_are_required_with_invocation():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        contract = (
            "削除の直前に対象ごと `python3 "
            "tools/check_worktree_occupancy.py <worktree>`。rc0 のみ進み、\n"
            "rc1=占有/rc2=判定不能は停止。"
        )
        replacement = (
            "削除の直前に対象ごと `python3 "
            "tools/check_worktree_occupancy.py <worktree>`。\n"
        )
        original = _read(root, rel)
        assert original.count(contract) == 1
        _write(root, rel, original.replace(contract, replacement, 1))
        _rebind_synthetic_cleanup_command_digest(root)

        _assert_cleanup_checker_contract_violation(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_checker_negated_invocation_is_rejected():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        contract = (
            "削除の直前に対象ごと `python3 "
            "tools/check_worktree_occupancy.py <worktree>`。rc0 のみ進み、\n"
            "rc1=占有/rc2=判定不能は停止。"
        )
        negation = (
            "この command では `tools/check_worktree_occupancy.py` を実行しない。"
            "\nrc0 は無視する。"
        )
        original = _read(root, rel)
        assert original.count(contract) == 1
        _write(root, rel, original.replace(contract, negation, 1))
        _rebind_synthetic_cleanup_command_digest(root)

        _assert_cleanup_checker_contract_violation(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_checker_literals_scattered_across_sections_are_rejected():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        contract = (
            "削除の直前に対象ごと `python3 "
            "tools/check_worktree_occupancy.py <worktree>`。rc0 のみ進み、\n"
            "rc1=占有/rc2=判定不能は停止。"
        )
        section_two = "## 2. 残す対象と退避 (残す対象以外は退避して消す)\n"
        original = _read(root, rel)
        assert original.count(contract) == 1
        assert original.count(section_two) == 1
        changed = original.replace(
            contract,
            "rc0 のみ進み、\nrc1=占有/rc2=判定不能は停止。",
            1,
        ).replace(
            section_two,
            section_two + "\n`tools/check_worktree_occupancy.py`\n",
            1,
        )
        _write(root, rel, changed)
        _rebind_synthetic_cleanup_command_digest(root)

        _assert_cleanup_checker_contract_violation(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_address_edge_rejects_split_lines():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        changed = _read(root, rel).replace(
            "正本は `docs/failures.md` F26。",
            "正本は F26。\n`docs/failures.md`",
            1,
        )
        _write(root, rel, changed)
        _rebind_synthetic_cleanup_command_digest(root)
        _assert_cleanup_address_edge_violation(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_address_edge_rejects_id_adjacent_decoy():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        original = _read(root, rel)
        changed = original.replace(
            "正本は `docs/failures.md` F26。",
            "旧 `docs/failures.md` の F260 は無効。",
            1,
        )
        _write(root, rel, _make_cleanup_command_mutation_budget_neutral(
            original, changed
        ))
        _rebind_synthetic_cleanup_command_digest(root)
        _assert_cleanup_address_edge_violation(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_address_edge_rejects_non_code_span_path_decoy():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        original = _read(root, rel)
        changed = original.replace(
            "正本は `docs/failures.md` F26。",
            "正本は docs/failures.md の F26。",
            1,
        )
        _write(root, rel, _make_cleanup_command_mutation_budget_neutral(
            original, changed
        ))
        _rebind_synthetic_cleanup_command_digest(root)
        _assert_cleanup_address_edge_violation(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_address_edge_rejects_raw_html_block():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        original = _read(root, rel)
        changed = original.replace(
            "正本は `docs/failures.md` F26。",
            "",
            1,
        )
        changed += "\n<div hidden>F26 (`docs/failures.md`)</div>\n"
        _write(root, rel, _make_cleanup_command_mutation_budget_neutral(
            original, changed
        ))
        _rebind_synthetic_cleanup_command_digest(root)
        _assert_cleanup_address_edge_violation(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_address_edge_rejects_link_definition():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        original = _read(root, rel)
        changed = original.replace(
            "正本は `docs/failures.md` F26。",
            "",
            1,
        )
        changed += "\n[F26]: https://invalid.example/docs/failures.md\n"
        _write(root, rel, _make_cleanup_command_mutation_budget_neutral(
            original, changed
        ))
        _rebind_synthetic_cleanup_command_digest(root)
        _assert_cleanup_address_edge_violation(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_address_edge_rejects_frontmatter_decoy():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        original = _read(root, rel)
        description = (
            "description: 古い・取込済みの branch と worktree を退避してから掃除する "
            "(submodule 罠対応、push 系はユーザー引き渡し)"
        )
        edge = "正本は `docs/failures.md` F26。"
        assert original.count(description) == 1
        assert original.count(edge) == 1
        changed = original.replace(
            description,
            "description: F26 `docs/failures.md`",
            1,
        ).replace(
            edge,
            "",
            1,
        )
        _write(root, rel, changed)
        _rebind_synthetic_cleanup_command_digest(root)
        _assert_cleanup_address_edge_violation(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_address_edge_accepts_rewording():
    root = _build_min_repo()
    try:
        rel = ".claude/commands/cleanup-branches.md"
        original = _read(root, rel)
        source = "正本は `docs/failures.md` F26。"
        assert original.count(source) == 1
        changed = original.replace(
            source,
            "F26 (`docs/failures.md`) が正本。",
            1,
        )
        _write(root, rel, _make_cleanup_command_mutation_budget_neutral(
            original, changed
        ))
        _rebind_synthetic_cleanup_command_digest(root)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_address_edge_accepts_baseline():
    """この baseline は、後続本文で消化済みの backlog ID が sink になる正例も兼ねる。"""
    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_land_route_guard_does_not_overmatch_ordinary_prose():
    root = _build_min_repo()
    try:
        additions = {
            ".claude/commands/dev-wave.md": (
                "\n通常の説明では `tools/alternate_land.py` や "
                "`python ./tools/alternate_land.py`、"
                "`git -C <main> merge deadbeef --ff-only` "
                "という文字列を引用できる。\n"
            ),
            ".agents/skills/dev-wave/SKILL.md": (
                "\n通常の説明として alternate land helper と "
                "`python3 tools/alternate_land.py`、"
                "`git merge --no-edit deadbeef --ff-only` "
                "を論じても実行経路ではない。\n"
            ),
        }
        for rel, prose in additions.items():
            _write(root, rel, _read(root, rel) + prose)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_land_route_guard_rejects_command_syntax_variants_independently():
    cases = (
        (
            ".claude/commands/dev-wave.md",
            "python tools/alternate_land.py --main main",
            "alternate land helper command",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "$ python3 ./tools/alternate_land.py --main main",
            "alternate land helper command",
        ),
        (
            ".claude/commands/dev-wave.md",
            "$ python ./tools/second_land.py --main main",
            "alternate land helper command",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "python3 tools/second_land.py --main main",
            "alternate land helper command",
        ),
        (
            ".claude/commands/dev-wave.md",
            "git merge deadbeef --ff-only",
            "direct git merge --ff-only main mutation",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "$ git -C <main> merge deadbeef --ff-only",
            "direct git merge --ff-only main mutation",
        ),
        (
            ".claude/commands/dev-wave.md",
            "git -C /tmp/main merge --no-edit --ff-only deadbeef",
            "direct git merge --ff-only main mutation",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "$ git merge --no-edit deadbeef --ff-only",
            "direct git merge --ff-only main mutation",
        ),
        (
            ".claude/commands/dev-wave.md",
            "python3 -u tools/alternate_land.py",
            "alternate land helper command",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "python -B -W ignore ./tools/alternate_land.py",
            "alternate land helper command",
        ),
        (
            ".claude/commands/dev-wave.md",
            "git --no-pager -C main merge --ff-only T",
            "direct git merge --ff-only main mutation",
        ),
        (
            ".agents/skills/dev-wave/SKILL.md",
            "git -c advice.detachedHead=false -C main merge T --ff-only",
            "direct git merge --ff-only main mutation",
        ),
    )
    for rel, command, needle in cases:
        root = _build_min_repo()
        try:
            _write(root, rel, _read(root, rel) + f"\n```sh\n{command}\n```\n")
            res = _run_check(root)
            assert res.returncode == 1, (
                f"{rel}: variant was accepted: {command!r}\n{res.stdout}"
            )
            assert needle in res.stdout, (command, res.stdout)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_land_route_guard_allows_non_land_and_non_ff_commands():
    root = _build_min_repo()
    try:
        additions = {
            ".claude/commands/dev-wave.md": (
                "\n```sh\n"
                "python3 -u tools/alternate_plan.py\n"
                "git --no-pager -C main merge T\n"
                "```\n"
            ),
            ".agents/skills/dev-wave/SKILL.md": (
                "\n```sh\n"
                "python -B -W ignore ./tools/report.py\n"
                "git -c advice.detachedHead=false merge --no-ff T\n"
                "```\n"
            ),
        }
        for rel, commands in additions.items():
            _write(root, rel, _read(root, rel) + commands)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== positive control: 列挙対象を 1 個消すと違反が出る (F9 の核心) =====

def test_missing_enumerated_doc_is_violation():
    root = _build_min_repo()
    try:
        rels = _enumerated_rels()
        assert rels, "列挙対象が空 — _ENUMERATED_DOCS の抽出に失敗している"
        governed = {
            *check_docs.DEV_WAVE_REFERENCE_FILES,
            *check_docs.SELF_LIMITS,
            *check_docs.PROVENANCE_LIMITS,
        }
        candidates = [rel for rel in rels if rel not in governed]
        assert candidates, "command guard 外の LIVING_DOCS 対象がない"
        victim = candidates[len(candidates) // 2]
        os.remove(os.path.join(root, victim))
        res = _run_check(root)
        assert res.returncode == 1, f"列挙対象不在なのに fail しなかった:\n{res.stdout}"
        assert "列挙対象が不在" in res.stdout, res.stdout
        assert victim in res.stdout, f"消した {victim} が finding に出ていない:\n{res.stdout}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_missing_enumerated_doc_only_fires_own_finding():
    # 不在検査だけが増える (他の検査を巻き添えにしない) ことを固定 — baseline との差分は 1 件。
    root = _build_min_repo()
    try:
        rels = _enumerated_rels()
        victim = rels[0]
        os.remove(os.path.join(root, victim))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert _violation_count(res) == 1, (
            f"不在検査以外も発火している:\n{res.stdout}"
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== T-143: RuleOps living doc の独立 literal pin / 行番号参照 positive control =====

def test_ruleops_doc_is_literal_pinned_as_enumerated_living_doc():
    assert "docs/ruleops.md" in _enumerated_rels()


def test_ruleops_line_reference_is_own_violation():
    root = _build_min_repo()
    try:
        baseline = _run_check(root)
        assert baseline.returncode == 0, baseline.stdout
        _write(
            root,
            os.path.join("docs", "ruleops.md"),
            "# synthetic RuleOps\n\n`ruleops.md:12` を参照する。\n",
        )
        result = _run_check(root)
        assert result.returncode == 1, result.stdout
        assert _violation_count(result) == 1, result.stdout
        assert "docs の行番号参照 (腐敗する)" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== V19a: output の生きた README を検査網へ固定 =====

def test_output_readmes_are_enumerated_and_valid_fixture_is_clean():
    expected = {"output/README.md", "output/task-runs/README.md"}
    assert expected <= set(_enumerated_rels())
    root = _build_min_repo()
    try:
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
        assert "違反なし" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_broken_reference_in_task_runs_readme_is_positive_control():
    """対象を列挙しただけの恒真化を防ぎ、本文 lint が実際に発火することを固定。"""

    root = _build_min_repo()
    try:
        victim = "output/task-runs/README.md"
        _write(root, victim, "# task-runs\n\n壊れた参照: tools/definitely-missing.py\n")
        res = _run_check(root)
        assert res.returncode == 1, f"壊れた参照が赤にならなかった:\n{res.stdout}"
        assert victim in res.stdout, res.stdout
        assert "実在しないパス参照" in res.stdout, res.stdout
        assert "tools/definitely-missing.py" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_missing_task_runs_readme_is_violation():
    root = _build_min_repo()
    try:
        victim = "output/task-runs/README.md"
        os.remove(os.path.join(root, victim))
        res = _run_check(root)
        assert res.returncode == 1, res.stdout
        assert victim in res.stdout, res.stdout
        assert "列挙対象が不在" in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== backlog guard: fail-closed の全構造分岐 =====

def test_backlog_guard_missing_worklog_is_violation():
    root = _build_min_repo()
    try:
        os.remove(os.path.join(root, "docs", "worklog.md"))
        _assert_violation(root, "docs/worklog.md: ファイルが不在")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_missing_phase3_is_violation():
    root = _build_min_repo()
    try:
        os.remove(os.path.join(root, "docs", "phase3.md"))
        _assert_violation(root, "docs/phase3.md: ファイルが不在")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_rotation_heading_must_be_unique():
    fixtures = {
        "zero": _CLEAN_WORKLOG.replace("## ローテーション\n", ""),
        "multiple": _CLEAN_WORKLOG.replace(
            "## ローテーション\n", "## ローテーション\n\n## ローテーション (duplicate)\n", 1
        ),
    }
    for name, worklog in fixtures.items():
        root = _build_min_repo()
        try:
            _write_backlog_docs(root, worklog_text=worklog)
            expected = "`## ローテーション` が 0 件" if name == "zero" else "`## ローテーション` が 2 件"
            _assert_violation(root, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_entry_title_must_fullmatch():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "## 2026-08-02 (2) — second", "## 補助見出し (entry ではない)"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "worklog entry title に full-match しない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_zero_entries_is_violation():
    root = _build_min_repo()
    try:
        _write_backlog_docs(root, worklog_text="# worklog\n\n## ローテーション\n")
        _assert_violation(root, "worklog エントリが 0 件")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_next_action_section_must_be_unique():
    fixtures = {
        "zero": _CLEAN_WORKLOG.replace("### 次の一手\n1. [T-001] carry\n", "本文だけ。\n", 1),
        "multiple": _CLEAN_WORKLOG.replace(
            "### 次の一手\n1. [T-001] carry\n",
            "### 次の一手\n1. [T-001] carry\n\n### 次の一手 (duplicate)\n1. [T-003] duplicate\n",
            1,
        ),
    }
    for name, worklog in fixtures.items():
        root = _build_min_repo()
        try:
            _write_backlog_docs(root, worklog_text=worklog)
            count = "0 件" if name == "zero" else "2 件"
            _assert_violation(root, "`### 次の一手`", count, "source を一意に抽出できない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_deferred_ledger_section_must_be_unique():
    fixtures = {
        "zero": _CLEAN_PHASE3.replace("## 見送り台帳 (synthetic)", "## 別の台帳"),
        "multiple": _CLEAN_PHASE3.replace(
            "### 裁定・完了記録",
            "## 見送り台帳 (duplicate)\n\n- duplicate\n\n### 裁定・完了記録",
        ),
    }
    for name, phase3 in fixtures.items():
        root = _build_min_repo()
        try:
            _write_backlog_docs(root, phase3_text=phase3)
            count = "0 件" if name == "zero" else "2 件"
            _assert_violation(root, "`## 見送り台帳`", count, "sink を一意に抽出できない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_completion_record_section_must_be_unique():
    fixtures = {
        "zero": _CLEAN_PHASE3.replace("### 裁定・完了記録", "### 別の記録"),
        "multiple": _CLEAN_PHASE3.replace(
            "## 残存リスク",
            "### 裁定・完了記録 (duplicate)\n\n- duplicate\n\n## 残存リスク",
        ),
    }
    for name, phase3 in fixtures.items():
        root = _build_min_repo()
        try:
            _write_backlog_docs(root, phase3_text=phase3)
            count = "0 件" if name == "zero" else "2 件"
            _assert_violation(root, "`### 裁定・完了記録`", count, "終端を一意に抽出できない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_completion_record_must_follow_ledger():
    root = _build_min_repo()
    try:
        phase3 = """# phase

### 裁定・完了記録

- completed

## 見送り台帳

- [T-900] deferred
"""
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "`### 裁定・完了記録` が `## 見送り台帳` より後にない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_zero_entries_with_valid_ids_is_violation():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("[T-001]", "legacy", 2).replace("[T-002]", "legacy")
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "有効 ID を持つエントリが 1 件もない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_item_requires_id():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("1. [T-002] continue", "1. missing ID")
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "末尾エントリ", "項目先頭に有効な [T-NNN] ID がない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_next_action_rejects_duplicate_ids():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "1. [T-002] continue", "1. [T-002] first\n2. [T-002] duplicate"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "`### 次の一手` 内で ID [T-002] が重複")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_bearing_middle_entry_requires_ids_on_all_items():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — second

- [T-001] consumed

### 次の一手
1. missing ID

## 2026-08-03 (3) — third

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(
            root,
            "エントリ '2026-08-02 (2) — second'",
            "項目先頭に有効な [T-NNN] ID がない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_bearing_middle_entry_rejects_duplicate_ids():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — second

- [T-001] consumed

### 次の一手
1. [T-002] first
2. [T-002] duplicate

## 2026-08-03 (3) — third

- [T-002] consumed

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(
            root,
            "エントリ '2026-08-02 (2) — second'",
            "`### 次の一手` 内で ID [T-002] が重複",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ledger_rejects_invalid_id_format():
    root = _build_min_repo()
    try:
        phase3 = _CLEAN_PHASE3.replace("[T-900]", "[T-01]")
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "見送り台帳の項目先頭 ID '[T-01]' が不正形式")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ledger_rejects_duplicate_ids():
    root = _build_min_repo()
    try:
        phase3 = _CLEAN_PHASE3.replace(
            "- [T-900] deferred item", "- [T-900] first\n- [T-900] duplicate"
        )
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "見送り台帳の ID [T-900] が重複")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ledger_live_item_requires_id():
    root = _build_min_repo()
    try:
        phase3 = _CLEAN_PHASE3.replace("- [T-900] deferred item", "- deferred item")
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "見送り台帳の生存項目先頭に有効な [T-NNN] ID がない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ledger_struck_item_rejects_id():
    root = _build_min_repo()
    try:
        phase3 = _CLEAN_PHASE3.replace(
            "### 裁定・完了記録",
            "- ~~[T-901] retired item~~\n\n### 裁定・完了記録",
        )
        _write_backlog_docs(root, phase3_text=phase3)
        _assert_violation(root, "見送り台帳の取り消し線項目に ID '[T-901]' がある")
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== backlog guard: 保存則の正例 =====

def test_backlog_guard_carried_id_in_next_action_is_clean():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "- [T-001] consumed\n\n### 次の一手\n1. [T-002] continue",
            "本文。\n\n### 次の一手\n1. [T-001] continue",
        )
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_only_item_is_source_and_sink():
    """ID 単独 source も D70 の対象とし、次 entry での脱落を具体 finding にする。"""

    id_only_source = _CLEAN_WORKLOG.replace("1. [T-001] carry", "- [T-001]")
    root = _build_min_repo()
    try:
        id_only_sink = id_only_source.replace("- [T-001] consumed", "- [T-001]")
        _write_backlog_docs(root, worklog_text=id_only_sink)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = _build_min_repo()
    try:
        dropped = id_only_source.replace("- [T-001] consumed", "本文。")
        _write_backlog_docs(root, worklog_text=dropped)
        _assert_violation(
            root,
            "次の一手 ID [T-001]",
            "後続エントリ",
            "見送り台帳にもない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_deferred_id_in_ledger_is_clean():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed\n\n", "本文。\n\n")
        phase3 = _CLEAN_PHASE3.replace("[T-900]", "[T-001]")
        _write_backlog_docs(root, worklog_text=worklog, phase3_text=phase3)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_pre_id_transition_is_not_applicable():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("1. [T-001] carry", "1. legacy item").replace(
            "- [T-001] consumed\n\n", "本文。\n\n"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_source_is_only_next_action_in_three_entry_chain():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — second

- [T-001] consumed

### 次の一手
1. [T-002] carry

## 2026-08-03 (3) — third

- [T-002] consumed

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_four_digit_id_is_clean():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("[T-002]", "[T-1000]")
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ===== backlog guard: 保存則の負例 =====

def test_backlog_guard_dropped_id_is_violation():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed\n\n", "本文。\n\n")
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "次の一手 ID [T-001]", "後続エントリ")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_prose_and_html_comment_do_not_satisfy_sink():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "- [T-001] consumed",
            "本文で [T-001] に言及する。\n\n<!-- [T-001] はここにあるだけ -->",
        )
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "次の一手 ID [T-001]", "後続エントリ")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_fences_and_multiline_comment_do_not_satisfy_sink():
    hidden_sinks = {
        "backtick fence": "```text\n- [T-001] dummy\n```",
        "tilde fence": "~~~text\n- [T-001] dummy\n~~~",
        "HTML comment": "<!--\n- [T-001] dummy\n-->",
    }
    for name, hidden_sink in hidden_sinks.items():
        root = _build_min_repo()
        try:
            worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed", hidden_sink)
            _write_backlog_docs(root, worklog_text=worklog)
            _assert_violation(root, "次の一手 ID [T-001]", "後続エントリ")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_hidden_ledger_items_do_not_satisfy_sink():
    hidden_sinks = {
        "backtick fence": "```text\n- [T-001] dummy\n```",
        "tilde fence": "~~~text\n- [T-001] dummy\n~~~",
        "HTML comment": "<!--\n- [T-001] dummy\n-->",
    }
    for name, hidden_sink in hidden_sinks.items():
        root = _build_min_repo()
        try:
            worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed\n\n", "本文。\n\n")
            phase3 = _CLEAN_PHASE3.replace(
                "- [T-900] deferred item",
                f"- [T-900] deferred item\n\n{hidden_sink}",
            )
            _write_backlog_docs(root, worklog_text=worklog, phase3_text=phase3)
            _assert_violation(root, "次の一手 ID [T-001]", "見送り台帳にもない")
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_hidden_ledger_items_are_not_live_items():
    hidden_items = {
        "backtick fence": "```text\n- missing ID\n```",
        "tilde fence": "~~~text\n- missing ID\n~~~",
        "HTML comment": "<!--\n- missing ID\n-->",
    }
    for name, hidden_item in hidden_items.items():
        root = _build_min_repo()
        try:
            phase3 = _CLEAN_PHASE3.replace(
                "- [T-900] deferred item",
                f"- [T-900] deferred item\n\n{hidden_item}",
            )
            _write_backlog_docs(root, phase3_text=phase3)
            res = _run_check(root)
            assert res.returncode == 0, f"{name}:\n{res.stdout}"
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_rejects_redundant_zero_padding():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("[T-002]", "[T-0001]")
        _write_backlog_docs(root, worklog_text=worklog)
        _assert_violation(root, "項目先頭 ID '[T-0001]' が不正形式")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_completion_record_does_not_satisfy_sink():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("- [T-001] consumed\n\n", "本文。\n\n")
        phase3 = _CLEAN_PHASE3.replace("- completed item", "- [T-001] completed item")
        _write_backlog_docs(root, worklog_text=worklog, phase3_text=phase3)
        _assert_violation(root, "次の一手 ID [T-001]", "見送り台帳にもない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_all_adjacent_transitions():
    root = _build_min_repo()
    try:
        worklog = """# worklog

## ローテーション

## 2026-08-01 (1) — first

### 次の一手
1. [T-001] dropped in middle

## 2026-08-02 (2) — second

- [T-900] unrelated

### 次の一手
1. [T-002] carried

## 2026-08-03 (3) — third

- [T-002] consumed

### 次の一手
1. [T-003] latest
"""
        _write_backlog_docs(root, worklog_text=worklog)
        res = _assert_violation(root, "次の一手 ID [T-001]")
        assert "次の一手 ID [T-002]" not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_latest_archive_rotation_boundary():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-08-02 (2) — current first

### 次の一手
1. [T-002] current
"""
        archive_name = "worklog-synthetic-latest.md"
        archive = """# archive

## 2026-08-01 (1) — archive last

### 次の一手
1. [T-001] lost at rotation
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", archive_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(archive_name),
        )
        _assert_violation(root, archive_name, "次の一手 ID [T-001]", "current first")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_archive_internal_transitions():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-08-03 (3) — current

- [T-002] consumed

### 次の一手
1. [T-003] current
"""
        archive_name = "worklog-synthetic.md"
        archive = """# archive

## 2026-08-01 (1) — archive first

### 次の一手
1. [T-001] lost inside archive

## 2026-08-02 (2) — archive second

### 次の一手
1. [T-002] carried to current
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", archive_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(archive_name),
        )
        _assert_violation(root, archive_name, "次の一手 ID [T-001]", "archive second")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_id_bearing_archive_entry_requires_ids_on_all_items():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-08-03 (3) — current

### 次の一手
1. [T-003] current
"""
        archive_name = "worklog-synthetic.md"
        archive = """# archive

## 2026-08-01 (1) — archive first

### 次の一手
1. [T-001] carry

## 2026-08-02 (2) — archive second

- [T-001] consumed

### 次の一手
1. missing ID
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", archive_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(archive_name),
        )
        _assert_violation(
            root,
            archive_name,
            "エントリ '2026-08-02 (2) — archive second'",
            "項目先頭に有効な [T-NNN] ID がない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_checks_boundaries_between_all_archives():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-08-03 (3) — current

- [T-002] consumed

### 次の一手
1. [T-003] current
"""
        first_name = "worklog-first.md"
        second_name = "worklog-second.md"
        first = """# first archive

## 2026-08-01 (1) — first archive last

### 次の一手
1. [T-001] lost between archives
"""
        second = """# second archive

## 2026-08-02 (2) — second archive first

### 次の一手
1. [T-002] carried to current
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", first_name), first)
        _write(root, os.path.join("docs", "archive", second_name), second)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(first_name, second_name),
        )
        _assert_violation(root, first_name, "次の一手 ID [T-001]", "second archive first")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_archive_is_selected_by_entry_date():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-09-02 (2) — current

### 次の一手
1. [T-002] current
"""
        older_name = "worklog-zz-older.md"
        newer_name = "worklog-aa-newer.md"
        older = """# older

## 2025-12-31 (1) — older

### 次の一手
1. legacy item
"""
        newer = """# newer

## 2026-09-01 (1) — newer

### 次の一手
1. [T-001] lost from chronologically latest archive
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", older_name), older)
        _write(root, os.path.join("docs", "archive", newer_name), newer)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(older_name, newer_name),
        )
        res = _assert_violation(root, newer_name, "次の一手 ID [T-001]")
        assert older_name not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_same_day_archives_use_entry_ordinal_not_filename():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-09-02 (3) — current

- [T-002] consumed

### 次の一手
1. [T-003] current
"""
        early_name = "worklog-z-early.md"
        late_name = "worklog-a-late.md"
        early = """# early

## 2026-09-01 (1) — early

### 次の一手
1. [T-001] carry across archive boundary
"""
        late = """# late

## 2026-09-01 (2) — late

- [T-001] consumed

### 次の一手
1. [T-002] carry to current
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", early_name), early)
        _write(root, os.path.join("docs", "archive", late_name), late)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(late_name, early_name),
        )
        res = _run_check(root)
        assert res.returncode == 0, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_ambiguous_same_day_archive_order_is_violation():
    root = _build_min_repo()
    try:
        current = """# current

## ローテーション

## 2026-09-02 (2) — current

- [T-001] consumed

### 次の一手
1. [T-002] current
"""
        first_name = "worklog-a.md"
        second_name = "worklog-z.md"
        archive = """# archive

## 2026-09-01 (1) — same ordinal

### 次の一手
1. [T-001] carry
"""
        _write_backlog_docs(root, worklog_text=current)
        _write(root, os.path.join("docs", "archive", first_name), archive)
        _write(root, os.path.join("docs", "archive", second_name), archive)
        _write(
            root,
            os.path.join("docs", "archive", "README.md"),
            _archive_readme(first_name, second_name),
        )
        _assert_violation(
            root,
            "archive worklog の順序を一意に決定できない",
            first_name,
            second_name,
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_latest_archive_structure_is_fail_closed():
    fixtures = {
        "zero entries": ("# archive\n", "日付付き worklog entry が 0 件"),
        "invalid H2": (
            "# archive\n\n## 9999-12-31 malformed entry\n",
            "entry title に full-match しない",
        ),
        "zero next": (
            "# archive\n\n## 2026-08-01 (1) — last\n\n本文。\n",
            "`### 次の一手` が 0 件",
        ),
        "multiple next": (
            "# archive\n\n## 2026-08-01 (1) — last\n\n"
            "### 次の一手\n1. [T-001] first\n\n"
            "### 次の一手 (duplicate)\n1. [T-002] second\n",
            "`### 次の一手` が 2 件",
        ),
    }
    for name, (archive, expected) in fixtures.items():
        root = _build_min_repo()
        try:
            archive_name = "worklog-synthetic-latest.md"
            _write(root, os.path.join("docs", "archive", archive_name), archive)
            _write(
                root,
                os.path.join("docs", "archive", "README.md"),
                _archive_readme(archive_name),
            )
            _assert_violation(root, archive_name, expected)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def _direct_carry_source(
    module,
    source_entry: int,
    items: tuple[str, ...],
    *,
    h2: str | None = None,
    path: str = "docs/worklog.md",
):
    raw_h2 = h2 or f"## 2026-08-01 ({source_entry}) — direct carry source"
    section_body = "".join(f"- {item}\n" for item in items)
    whole_text = f"{raw_h2}\n\n### 次の一手\n{section_body}"
    return module._CarrySource(
        path,
        whole_text,
        source_entry,
        raw_h2,
        section_body,
        whole_text.index(section_body),
    )


def test_backlog_guard_carry_same_id_mismatch_is_positive_control():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "1. [T-002] continue", "- [T-002] (1)"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        res = _assert_violation(
            root,
            "[T-002]",
            "entry (1) の次の一手に同じ ID がない",
            "参照先 H2 docs/worklog.md:",
            "参照先の次の一手に同じ ID を置くか、carry を正しい参照先へ直す",
        )
        assert "docs/worklog.md:" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_known_carry_id_mismatches_are_clean():
    root = _build_min_repo()
    try:
        _enable_known_carry_mismatch_fixture(root)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "carry 同一 ID 不一致" not in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_carry_mismatch_ledger_entries_are_pinned_exactly():
    assert check_docs.KNOWN_CARRY_ID_MISMATCHES == {
        "6bc0dfb4679d3be38c2a97c7c81c595b62a2b033800e5b27d7f9a63b75c3814b": {
            "34209a9f738fe90a9f3cd57531c3ef900085884b79fc6c1dd833fdf3c46ee45c": 1,
            "f46fe17fc7831678f44471bf5c7c460be6bd65bac6a7e5a47cd0535c150a54a6": 1,
            "f5e03b5bb559682274a1731a73e6d4dca0208c7846fabe312cad1834bc74c14e": 1,
            "5e4a6cb7d118a27df5b710ca20351ea9e5e45ef764ed559b597dc9931140b666": 1,
        },
    }
    assert check_docs.EXPECTED_KNOWN_CARRY_ID_MISMATCHES == 4
    assert check_docs.MIN_EXPECTED_CARRY_REFERENCE_COUNT == 404_326
    assert hashlib.sha256(_KNOWN_CARRY_SOURCE_H2.encode()).hexdigest() in (
        check_docs.KNOWN_CARRY_ID_MISMATCHES
    )


def test_backlog_guard_known_carry_list_marker_rewrite_is_violation():
    root = _build_min_repo()
    try:
        _enable_known_carry_mismatch_fixture(root)
        rel = f"docs/archive/{_KNOWN_CARRY_ID_MISMATCH_ARCHIVE_NAME}"
        text = _read(root, rel)
        original = "- [T-208] 変わらず ((73) 参照)"
        rewritten = "1. [T-208] 変わらず ((73) 参照)"
        _write(root, rel, _replace_once(text, original, rewritten))
        res = _assert_violation(
            root,
            "[T-208]",
            "entry (73) の次の一手に同じ ID がない",
            "expected=1, actual=0",
        )
        assert "carry 同一 ID 不一致" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_carry_item_digest_covers_marker_and_continuation():
    raw_h2 = "## 2026-08-01 (2) — folded carry source"
    section_body = "- [T-002] (1)\n  folded detail\n- [T-003] (1)\n"
    whole_text = f"{raw_h2}\n\n### 次の一手\n{section_body}"
    source = check_docs._CarrySource(
        "docs/worklog.md",
        whole_text,
        2,
        raw_h2,
        section_body,
        whole_text.index(section_body),
    )
    references = list(check_docs._iter_carry_references((source,)))
    assert [reference.item_digest for reference in references] == [
        hashlib.sha256(b"- [T-002] (1)\n  folded detail").hexdigest(),
        hashlib.sha256(b"- [T-003] (1)").hexdigest(),
    ]


def test_backlog_guard_carry_mismatch_ledger_total_is_enforced():
    root = _build_min_repo()
    try:
        _enable_known_carry_mismatch_fixture(root)
        module = _load_fixture_checker(root)
        module.EXPECTED_KNOWN_CARRY_ID_MISMATCHES = 5
        res = _run_loaded_checker(module)
        assert res.returncode == 1, res.stdout
        assert (
            "登録 occurrence 総数が不一致 — expected=5, actual=4"
            in res.stdout
        )
        assert len(_finding_set(res)) == 1, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_registered_carry_mismatch_removal_is_violation():
    root = _build_min_repo()
    try:
        _enable_known_carry_mismatch_fixture(root)
        rel = f"docs/archive/{_KNOWN_CARRY_ID_MISMATCH_ARCHIVE_NAME}"
        text = _read(root, rel)
        removed = "- [T-211] 変わらず ((73) 参照)\n"
        assert text.count(removed) == 1
        _write(root, rel, text.replace(removed, "", 1))
        module = _load_fixture_checker(root)
        module.MIN_EXPECTED_CARRY_REFERENCE_COUNT = 0
        res = _run_loaded_checker(module)
        assert res.returncode == 1, res.stdout
        assert "expected=1, actual=0" in res.stdout
        assert "凍結 archive を編集せず、復元するか裁定へ返す" in res.stdout
        assert "5e4a6cb7d118a27d" in res.stdout
        assert len(_finding_set(res)) == 1, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_same_target_and_id_from_new_source_is_violation(
    monkeypatch,
):
    known_item = "[T-208] 変わらず ((73) 参照)"
    source_digest = hashlib.sha256(_KNOWN_CARRY_SOURCE_H2.encode()).hexdigest()
    item_digest = hashlib.sha256(f"- {known_item}".encode()).hexdigest()
    monkeypatch.setattr(
        check_docs,
        "KNOWN_CARRY_ID_MISMATCHES",
        {source_digest: {item_digest: 1}},
    )
    monkeypatch.setattr(check_docs, "EXPECTED_KNOWN_CARRY_ID_MISMATCHES", 1)
    monkeypatch.setattr(check_docs, "MIN_EXPECTED_CARRY_REFERENCE_COUNT", 2)
    sources = (
        _direct_carry_source(
            check_docs,
            77,
            (known_item,),
            h2=_KNOWN_CARRY_SOURCE_H2,
            path=f"docs/archive/{_KNOWN_CARRY_ID_MISMATCH_ARCHIVE_NAME}",
        ),
        _direct_carry_source(
            check_docs,
            78,
            (known_item,),
            h2="## 2026-08-01 (78) — new source",
        ),
    )
    findings: list[str] = []
    check_docs._validate_entry_universe(
        {73: ["target.md:1"], 77: ["known.md:1"], 78: ["new.md:1"]},
        {73: {"[T-193]"}, 77: set(), 78: set()},
        sources,
        findings,
        numbered_archive_input_complete=True,
    )
    assert any(
        finding.startswith("docs/worklog.md:4: [T-208]")
        and "entry (73) の次の一手に同じ ID がない" in finding
        for finding in findings
    )
    assert any("参照先の次の一手に同じ ID を置くか" in finding
               for finding in findings)
    assert not any("expected=1, actual=0" in finding for finding in findings)
    assert not any("母数" in finding for finding in findings)
    assert not any("candidate" in finding for finding in findings)


@pytest.mark.parametrize(
    "invalid_item",
    (
        pytest.param("[T-999] (073)", id="leading-zero"),
        pytest.param("[T-999] (73 )", id="trailing-space"),
        pytest.param(
            "[T-999] 変わらず ( (73) 参照)",
            id="legacy-inner-space",
        ),
    ),
)
def test_backlog_guard_carry_candidate_parse_break_is_positive_control(
    invalid_item: str,
):
    root = _build_min_repo()
    try:
        _enable_known_carry_mismatch_fixture(root)
        worklog = _CLEAN_WORKLOG.replace(
            "1. [T-001] carry", "1. [T-999] carry"
        ).replace(
            "1. [T-002] continue", f"- {invalid_item}"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        res = _assert_violation(
            root,
            "carry 風 candidate",
            "厳密 carry 文法に一致しない",
            "candidate=5, parsed=4",
            "正例: `- [T-1219] (953)`",
        )
        assert _violation_count(res) == 1, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("suffix", ("(D837)", "(Python 3)"))
def test_backlog_guard_non_carry_parenthetical_item_is_clean(suffix: str):
    root = _build_min_repo()
    try:
        item = f"[T-500] {suffix}"
        worklog = _CLEAN_WORKLOG.replace(
            "1. [T-001] carry", f"1. {item}"
        ).replace("1. [T-002] continue", f"- {item}")
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "carry 風 candidate" not in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_carry_reference_population_floor_rejects_shrink(
    monkeypatch,
):
    monkeypatch.setattr(check_docs, "KNOWN_CARRY_ID_MISMATCHES", {})
    monkeypatch.setattr(check_docs, "EXPECTED_KNOWN_CARRY_ID_MISMATCHES", 0)
    monkeypatch.setattr(check_docs, "MIN_EXPECTED_CARRY_REFERENCE_COUNT", 2)
    source = _direct_carry_source(check_docs, 2, ("[T-002] (1)",))
    findings: list[str] = []
    check_docs._validate_entry_universe(
        {1: ["target.md:1"], 2: ["source.md:1"]},
        {1: {"[T-002]"}, 2: set()},
        (source,),
        findings,
        numbered_archive_input_complete=True,
    )
    assert findings == [
        "carry 参照母数が粗い下限を下回る — minimum=2, actual=1"
    ]


def test_backlog_guard_entry_universe_and_index_must_match(monkeypatch):
    monkeypatch.setattr(check_docs, "KNOWN_CARRY_ID_MISMATCHES", {})
    monkeypatch.setattr(check_docs, "EXPECTED_KNOWN_CARRY_ID_MISMATCHES", 0)
    monkeypatch.setattr(check_docs, "MIN_EXPECTED_CARRY_REFERENCE_COUNT", 0)
    findings: list[str] = []
    check_docs._validate_entry_universe(
        {1: ["target.md:1"]},
        {},
        (),
        findings,
        numbered_archive_input_complete=True,
    )
    assert any("universe にあるが次の一手索引 key が不在" in f for f in findings)
    assert any("universe / index 集合不一致" in f for f in findings)


@pytest.mark.parametrize(
    (
        "kind",
        "target_value",
        "category_label",
        "detail",
        "absent_labels",
        "absent_details",
    ),
    (
        pytest.param(
            "missing",
            "missing",
            "索引 key 不在",
            "key 不在",
            ("索引値 None", "索引値空集合"),
            ("値 None (section 抽出対象外)", "空集合 (次の一手が空)"),
            id="index-key-missing",
        ),
        pytest.param(
            "none",
            None,
            "索引値 None",
            "値 None (section 抽出対象外)",
            ("索引 key 不在", "索引値空集合"),
            ("key 不在", "空集合 (次の一手が空)"),
            id="index-value-none",
        ),
        pytest.param(
            "empty",
            set(),
            "索引値空集合",
            "空集合 (次の一手が空)",
            ("索引 key 不在", "索引値 None"),
            ("key 不在", "値 None (section 抽出対象外)"),
            id="index-value-empty",
        ),
    ),
)
def test_backlog_guard_carry_target_index_states_are_distinct(
    monkeypatch,
    kind,
    target_value,
    category_label,
    detail,
    absent_labels,
    absent_details,
):
    monkeypatch.setattr(check_docs, "KNOWN_CARRY_ID_MISMATCHES", {})
    monkeypatch.setattr(check_docs, "EXPECTED_KNOWN_CARRY_ID_MISMATCHES", 0)
    monkeypatch.setattr(check_docs, "MIN_EXPECTED_CARRY_REFERENCE_COUNT", 1)
    source = _direct_carry_source(check_docs, 2, ("[T-002] (1)",))
    index = {2: set()}
    if kind != "missing":
        index[1] = target_value
    findings: list[str] = []
    check_docs._validate_entry_universe(
        {1: ["target.md:1"], 2: ["source.md:1"]},
        index,
        (source,),
        findings,
        numbered_archive_input_complete=True,
    )
    assert any(category_label in finding for finding in findings), findings
    assert any(
        finding.startswith("docs/worklog.md:4: [T-002]")
        and "entry (1)" in finding
        and detail in finding
        for finding in findings
    ), findings
    for forbidden in (*absent_labels, *absent_details):
        assert not any(forbidden in finding for finding in findings), findings


def test_backlog_guard_incomplete_numbered_archive_stops_carry_validation(
    monkeypatch,
):
    monkeypatch.setattr(
        check_docs,
        "KNOWN_CARRY_ID_MISMATCHES",
        {"source": {"item": 1}},
    )
    monkeypatch.setattr(check_docs, "EXPECTED_KNOWN_CARRY_ID_MISMATCHES", 9)
    monkeypatch.setattr(check_docs, "MIN_EXPECTED_CARRY_REFERENCE_COUNT", 9)
    source = _direct_carry_source(check_docs, 2, ("[T-002] (1)",))
    findings: list[str] = []
    check_docs._validate_entry_universe(
        {1: ["target.md:1"], 2: ["source.md:1"]},
        {1: set(), 2: set()},
        (source,),
        findings,
        numbered_archive_input_complete=False,
    )
    assert findings == [
        "docs/archive: 番号付き archive 入力が不完全 — "
        "carry 参照先の実在検査を停止"
    ]


def test_backlog_guard_fold_shape_carry_chain_is_clean():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "1. [T-001] carry", "1. [T-002] carry"
        ).replace("1. [T-002] continue", "- [T-002] (1)")
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_carry_references_are_streamed(monkeypatch):
    sources = (
        _direct_carry_source(
            check_docs,
            10,
            ("[T-1219] (953)", "[T-1220] (954)"),
        ),
        _direct_carry_source(
            check_docs,
            11,
            ("[T-193] 変わらず ((73) 参照)",),
        ),
    )
    source_consumed: list[int] = []
    item_consumed: list[str] = []

    def source_generator():
        for source in sources:
            source_consumed.append(source.source_entry)
            yield source

    original_top_level_items = check_docs._top_level_items

    def item_generator(body: str):
        for item in original_top_level_items(body):
            item_consumed.append(item[0])
            yield item

    monkeypatch.setattr(check_docs, "_top_level_items", item_generator)
    scan = check_docs._CarryScanStats()
    references = check_docs._iter_carry_references(source_generator(), scan)
    assert iter(references) is references
    assert source_consumed == []
    assert item_consumed == []
    first = next(references)
    assert first.task_id == "[T-1219]"
    assert scan.candidate_count == scan.parsed_count == 1
    assert source_consumed == [10]
    assert item_consumed == ["[T-1219] (953)"]
    actual = [first, *references]
    assert [item.source_entry for item in actual] == [10, 10, 11]
    assert [item.task_id for item in actual] == [
        "[T-1219]",
        "[T-1220]",
        "[T-193]",
    ]
    assert [item.target_entry for item in actual] == [953, 954, 73]
    assert [item.line for item in actual] == [4, 5, 4]
    assert scan.candidate_count == scan.parsed_count == 3
    assert source_consumed == [10, 11]


def test_backlog_guard_carry_findings_are_sampled_without_early_stop(
    monkeypatch,
):
    monkeypatch.setattr(check_docs, "KNOWN_CARRY_ID_MISMATCHES", {})
    monkeypatch.setattr(check_docs, "EXPECTED_KNOWN_CARRY_ID_MISMATCHES", 0)
    monkeypatch.setattr(check_docs, "MIN_EXPECTED_CARRY_REFERENCE_COUNT", 25)
    items = tuple(f"[T-{number:03d}] (1)" for number in range(300, 325))
    source = _direct_carry_source(check_docs, 2, items)
    findings: list[str] = []
    check_docs._validate_entry_universe(
        {1: ["target.md:1"], 2: ["source.md:1"]},
        {1: {"[T-001]"}, 2: set()},
        (source,),
        findings,
        numbered_archive_input_complete=True,
    )
    mismatch_details = [
        finding for finding in findings
        if "参照先 entry (1) の次の一手に同じ ID がない" in finding
    ]
    assert len(mismatch_details) == 20
    assert "carry 同一 ID 不一致: 他 5 件を抑止" in findings
    assert (
        "carry 同一 ID 不一致: 上記の 5 件は target 数でなく "
        "carry occurrence 数"
    ) in findings
    assert not any("母数" in finding for finding in findings)


@pytest.mark.parametrize(
    ("kind", "category", "detail"),
    (
        pytest.param(
            "missing",
            "参照先不在",
            "全域番号 universe に実在しない",
            id="target-missing",
        ),
        pytest.param(
            "key",
            "索引 key 不在",
            "次の一手索引が key 不在",
            id="index-key-missing",
        ),
        pytest.param(
            "none",
            "索引値 None",
            "値 None (section 抽出対象外)",
            id="index-value-none",
        ),
        pytest.param(
            "empty",
            "索引値空集合",
            "空集合 (次の一手が空)",
            id="index-value-empty",
        ),
    ),
)
def test_backlog_guard_carry_index_failures_count_every_occurrence(
    monkeypatch,
    kind: str,
    category: str,
    detail: str,
):
    monkeypatch.setattr(check_docs, "KNOWN_CARRY_ID_MISMATCHES", {})
    monkeypatch.setattr(check_docs, "EXPECTED_KNOWN_CARRY_ID_MISMATCHES", 0)
    monkeypatch.setattr(check_docs, "MIN_EXPECTED_CARRY_REFERENCE_COUNT", 25)
    source = _direct_carry_source(
        check_docs,
        2,
        tuple("[T-300] (1)" for _ in range(25)),
    )
    locations = {2: ["source.md:1"]}
    index: dict[int, set[str] | None] = {2: set()}
    if kind != "missing":
        locations[1] = ["target.md:1"]
    if kind == "none":
        index[1] = None
    elif kind == "empty":
        index[1] = set()
    findings: list[str] = []
    check_docs._validate_entry_universe(
        locations,
        index,
        (source,),
        findings,
        numbered_archive_input_complete=True,
    )
    samples = [finding for finding in findings if detail in finding]
    assert len(samples) == 20, findings
    assert f"carry {category}: 他 5 件を抑止" in findings
    assert (
        f"carry {category}: 上記の 5 件は target 数でなく "
        "carry occurrence 数"
    ) in findings
    assert not any("母数" in finding for finding in findings)


@pytest.mark.parametrize(
    "carry_item",
    (
        "- [T-002] (1)",
        "- [T-002] 変わらず ((1) 参照)",
        "- [T-002] **継続**: 変わらず ((1) 参照)。末尾注記",
    ),
)
def test_backlog_guard_carry_reference_existing_in_current_is_clean(carry_item: str):
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "1. [T-001] carry", "1. [T-002] carry"
        ).replace("1. [T-002] continue", carry_item)
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    "carry_item",
    (
        "- [T-002] (999)",
        "- [T-002] 変わらず ((999) 参照)",
        "- [T-002] **継続**: 変わらず ((999) 参照)。末尾注記",
    ),
)
def test_backlog_guard_dangling_carry_reference_is_violation(carry_item: str):
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace("1. [T-002] continue", carry_item)
        _write_backlog_docs(root, worklog_text=worklog)
        res = _assert_violation(root, "[T-002]", "(999)", "宙吊り参照")
        assert "docs/worklog.md:" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_new_carry_syntax_in_prose_is_not_a_reference():
    root = _build_min_repo()
    try:
        worklog = _CLEAN_WORKLOG.replace(
            "1. [T-002] continue",
            "- [T-002] prose mentions [T-003] (999) without carrying it",
        )
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "宙吊り参照" not in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_archive_filename_entry_range_two_token_boundaries():
    """2 token 形では entry 位置を優先し、旧日付範囲名は維持する。"""

    numbered = {
        "worklog-phase3-0826-1000.md": (1000, 1000),
        "worklog-phase3-0826-1001.md": (1001, 1001),
        "worklog-phase3-0826-1031.md": (1031, 1031),
        "worklog-phase3-0826-1032.md": (1032, 1032),
        "worklog-phase3-0826-1100.md": (1100, 1100),
        "worklog-phase3-0826-1101.md": (1101, 1101),
        # MMDD の日部は月と独立に 31 を通すため、暦にない 11/31 も両義になる。
        "worklog-phase3-0826-1131.md": (1131, 1131),
        "worklog-phase3-0826-1201.md": (1201, 1201),
        "worklog-phase3-0826-1231.md": (1231, 1231),
        "worklog-phase3-0826-1300.md": (1300, 1300),
    }
    unnumbered = (
        "worklog-phase3-0722-0724.md",
        "worklog-phase3-0730-0731.md",
        "worklog-phase3-0719.md",
        "worklog-phase1-2.md",
    )

    for name, entry_range in numbered.items():
        path = check_docs.REPO / "docs/archive" / name
        claim = check_docs._archive_filename_entry_range(path)
        assert (claim.classification, claim.entry_range) == (
            "numbered",
            entry_range,
        ), name
    for name in unnumbered:
        path = check_docs.REPO / "docs/archive" / name
        claim = check_docs._archive_filename_entry_range(path)
        assert (claim.classification, claim.entry_range) == (
            "unnumbered",
            None,
        ), name


def test_backlog_guard_numbered_archive_entry_is_carry_target():
    root = _build_min_repo()
    try:
        name = "worklog-phase3-0730-1000.md"
        archive = _archive_with_entries(("2026-07-30", "1000")).replace(
            "### 次の一手\n",
            "### 次の一手\n- [T-001] carry target\n",
            1,
        )
        _write(root, f"docs/archive/{name}", archive)
        _write_archive_index(
            root,
            _numbered_archive_claim_line(name, "2026-07-30", 1000),
        )
        worklog = _CLEAN_WORKLOG.replace(
            "1. [T-002] continue", "- [T-001] (1000)"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_two_token_entry_1001_is_carry_target():
    root = _build_min_repo()
    try:
        name = "worklog-phase3-0730-1001.md"
        archive = _archive_with_entries(("2026-07-30", "1001")).replace(
            "### 次の一手\n",
            "### 次の一手\n- [T-001] carry target\n",
            1,
        )
        _write(root, f"docs/archive/{name}", archive)
        _write_archive_index(
            root,
            _numbered_archive_claim_line(name, "2026-07-30", 1001),
        )
        worklog = _CLEAN_WORKLOG.replace(
            "1. [T-002] continue", "- [T-001] (1001)"
        )
        _write_backlog_docs(root, worklog_text=worklog)
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    "name",
    (
        "worklog-phase3-0730.md",
        "worklog-phase1-2.md",
        "worklog-synthetic.md",
    ),
)
def test_backlog_guard_unnumbered_archive_carry_is_out_of_scope(name: str):
    root = _build_min_repo()
    try:
        archive = """# unnumbered archive

## 2026-07-30 (10) — carry source

### 次の一手
- [T-050] (999)

## 2026-07-31 (11) — carry sink

- [T-050] consumed

### 次の一手
"""
        _write(root, f"docs/archive/{name}", archive)
        _write_archive_index(root, f"- `{name}`\n")
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "宙吊り参照" not in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_archive_non_phase_numeric_token_filename_is_malformed():
    root = _build_min_repo()
    try:
        name = "worklog-broken-106-110.md"
        _write(
            root,
            f"docs/archive/{name}",
            _archive_with_entries(
                *(("2026-07-30", str(number)) for number in range(106, 111))
            ),
        )
        _write_archive_index(root, f"- `{name}`\n")
        _assert_violation(root, name, "malformed filename")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_backlog_guard_duplicate_global_entry_number_is_violation():
    root = _build_min_repo()
    try:
        name = "worklog-phase3-0730-1.md"
        _write(root, f"docs/archive/{name}", _archive_with_entries(("2026-07-30", "1")))
        _write_archive_index(
            root,
            _numbered_archive_claim_line(name, "2026-07-30", 1),
        )
        res = _assert_violation(root, "全域 entry 番号 (1) が複数箇所に実在")
        assert "docs/worklog.md:" in res.stdout
        assert f"docs/archive/{name}:" in res.stdout
        assert "宙吊り参照" not in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_archive_claims_accept_single_and_cross_date_ranges():
    root = _build_min_repo()
    try:
        single = "worklog-phase4-0729-1000.md"
        ranged = "worklog-phase4-0730-1001-0731-1003.md"
        _write(root, f"docs/archive/{single}", _archive_with_entries(("2026-07-29", "1000")))
        _write(
            root,
            f"docs/archive/{ranged}",
            _archive_with_entries(
                ("2026-07-30", "1001"),
                ("2026-07-30", "1002"),
                ("2026-07-31", "1003"),
            ),
        )
        _write_archive_index(
            root,
            _numbered_archive_claim_line(single, "2026-07-29", 1000),
            _numbered_archive_claim_line(
                ranged,
                "2026-07-30",
                1001,
                1003,
                end_date="07-31",
                continuation="folded range annotation",
            ),
        )
        res = _run_check(root)
        assert res.returncode == 0, res.stdout + res.stderr
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_archive_filename_and_readme_reject_interior_gap():
    root = _build_min_repo()
    try:
        name = "worklog-phase3-0730-10-12.md"
        _write(
            root,
            f"docs/archive/{name}",
            _archive_with_entries(("2026-07-30", "10"), ("2026-07-30", "12")),
        )
        _write_archive_index(
            root,
            _numbered_archive_claim_line(name, "2026-07-30", 10, 12),
        )
        res = _assert_violation(root, "欠番=11")
        assert f"docs/archive/{name}: filename が名乗る" in res.stdout
        assert f"docs/archive/README.md:" in res.stdout
        assert f"{name} が名乗る" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_archive_readme_range_must_match_actual_set():
    root = _build_min_repo()
    try:
        name = "worklog-phase3-0730-10-12.md"
        _write(
            root,
            f"docs/archive/{name}",
            _archive_with_entries(
                ("2026-07-30", "10"),
                ("2026-07-30", "11"),
                ("2026-07-30", "12"),
            ),
        )
        _write_archive_index(
            root,
            _numbered_archive_claim_line(name, "2026-07-30", 10, 11),
        )
        res = _assert_violation(root, f"{name} が名乗る", "範囲外=12")
        assert f"docs/archive/{name}: filename が名乗る" not in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("listing", ("missing", "bare"))
def test_numbered_archive_readme_requires_range_syntax(listing: str):
    root = _build_min_repo()
    try:
        name = "worklog-phase3-0730-10.md"
        _write(root, f"docs/archive/{name}", _archive_with_entries(("2026-07-30", "10")))
        lines = () if listing == "missing" else (f"- `{name}`\n",)
        _write_archive_index(root, *lines)
        res = _assert_violation(
            root,
            name,
            "正規な「現在の収容物」行が 0 件",
        )
        if listing == "bare":
            assert "entry 範囲を抽出できない" in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    ("name", "entries", "readme_line"),
    (
        (
            "worklog-phase3-0730-106-110-copy.md",
            tuple(str(number) for number in range(106, 111)),
            None,
        ),
        (
            "worklog-phase3-106-110.md",
            tuple(str(number) for number in range(106, 111)),
            None,
        ),
        (
            "worklog-phase10-0730-10-999-12.md",
            ("10", "11", "12"),
            _numbered_archive_claim_line(
                "worklog-phase10-0730-10-999-12.md", "2026-07-30", 10, 12
            ),
        ),
        (
            "worklog-phase3-0730-0731-0732.md",
            ("10",),
            None,
        ),
    ),
)
def test_archive_malformed_filename_is_violation(
    name: str,
    entries: tuple[str, ...],
    readme_line: str | None,
):
    root = _build_min_repo()
    try:
        _write(
            root,
            f"docs/archive/{name}",
            _archive_with_entries(
                *(("2026-07-30", number) for number in entries)
            ),
        )
        _write_archive_index(root, readme_line or f"- `{name}`\n")
        _assert_violation(root, name, "malformed filename")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_archive_readme_items_are_streamed_as_logical_items():
    items = check_docs._archive_readme_items(
        "preface\n- first\n  continuation\n- second\ntrailing prose\n",
        7,
    )
    assert iter(items) is items
    assert next(items) == ("- first continuation", 15)
    assert next(items) == ("- second", 38)
    with pytest.raises(StopIteration):
        next(items)


def test_numbered_archive_rejects_entry_without_global_number():
    root = _build_min_repo()
    try:
        name = "worklog-phase3-0730-10.md"
        _write(
            root,
            f"docs/archive/{name}",
            _archive_with_entries(
                ("2026-07-30", "10"),
                extra_h2="2026-07-30 (続き) — synthetic continuation",
            ),
        )
        _write_archive_index(
            root,
            _numbered_archive_claim_line(name, "2026-07-30", 10),
        )
        res = _assert_violation(root, "番号付き archive 内の H2", "全域 entry 番号がない")
        assert "entry 範囲 (10)〜(10) と実体 entry 集合が不一致" not in res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_spool_fold_rotation_output_passes_real_check_docs():
    root = _build_min_repo()
    module_name = "_t329_spool_fold_integration"
    try:
        worklog = _read(root, "docs/worklog.md").replace(
            "### 次の一手\n1. [T-001] carry",
            ("rotation filler " * 7500) + "\n\n### 次の一手\n1. [T-001] carry",
            1,
        )
        _write_backlog_docs(root, worklog_text=worklog)
        subprocess.run(["git", "-C", root, "init", "-q"], check=True)
        subprocess.run(["git", "-C", root, "config", "user.name", "Fixture"], check=True)
        subprocess.run(
            ["git", "-C", root, "config", "user.email", "fixture@example.invalid"],
            check=True,
        )
        subprocess.run(["git", "-C", root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", root, "commit", "-qm", "base"], check=True)
        _write(
            root,
            "docs/spool/worklog/2026-08-03-t329-1.md",
            "---\n"
            "schema: izanagi-spool-v1\n"
            "ledger: worklog\n"
            "authored: 2026-08-03\n"
            "wave: t329\n"
            "seq: 1\n"
            "title: rotation integration\n"
            "---\n"
            "## 本文\n\n- rotation integration\n\n"
            "## 次の一手差分\n\n### carry\n\n- [T-002]\n",
        )
        subprocess.run(["git", "-C", root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", root, "commit", "-qm", "fragment"], check=True)

        source = os.path.join(root, "tools", "spool_fold.py")
        spec = importlib.util.spec_from_file_location(module_name, source)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        plan = module.plan_fold(root, fold_date="2026-08-03")
        assert plan.rotation_path is not None
        module.apply_fold(root, plan)

        res = _run_check(root, "--expect-active-transaction", plan.transaction_id)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "違反なし" in res.stdout
    finally:
        sys.modules.pop(module_name, None)
        shutil.rmtree(root, ignore_errors=True)


def test_spool_fold_rotation_ordinal_1001_is_numbered_archive():
    root = _build_min_repo()
    module_name = "_t1732_spool_fold_ordinal_1001_integration"
    try:
        worklog = _read(root, "docs/worklog.md")
        worklog = worklog.replace("(1) — first", "(1001) — first", 1)
        worklog = worklog.replace("(2) — second", "(1002) — second", 1)
        worklog = worklog.replace(
            "### 次の一手\n1. [T-001] carry",
            ("rotation filler " * 7500) + "\n\n### 次の一手\n1. [T-001] carry",
            1,
        )
        _write_backlog_docs(root, worklog_text=worklog)
        subprocess.run(["git", "-C", root, "init", "-q"], check=True)
        subprocess.run(["git", "-C", root, "config", "user.name", "Fixture"], check=True)
        subprocess.run(
            ["git", "-C", root, "config", "user.email", "fixture@example.invalid"],
            check=True,
        )
        subprocess.run(["git", "-C", root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", root, "commit", "-qm", "base"], check=True)
        _write(
            root,
            "docs/spool/worklog/2026-08-03-t1732-1.md",
            "---\n"
            "schema: izanagi-spool-v1\n"
            "ledger: worklog\n"
            "authored: 2026-08-03\n"
            "wave: t1732\n"
            "seq: 1\n"
            "title: ordinal 1001 rotation integration\n"
            "---\n"
            "## 本文\n\n- ordinal 1001 rotation integration\n\n"
            "## 次の一手差分\n\n### carry\n\n- [T-002]\n",
        )
        subprocess.run(["git", "-C", root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", root, "commit", "-qm", "fragment"], check=True)

        source = os.path.join(root, "tools", "spool_fold.py")
        spec = importlib.util.spec_from_file_location(module_name, source)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        plan = module.plan_fold(root, fold_date="2026-08-03")
        expected = "docs/archive/worklog-phase3-0801-1001.md"
        assert plan.rotation_path == expected
        claim = check_docs._archive_filename_entry_range(
            check_docs.REPO / plan.rotation_path
        )
        assert (claim.classification, claim.entry_range) == (
            "numbered",
            (1001, 1001),
        )
        module.apply_fold(root, plan)

        res = _run_check(root, "--expect-active-transaction", plan.transaction_id)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "違反なし" in res.stdout
    finally:
        sys.modules.pop(module_name, None)
        shutil.rmtree(root, ignore_errors=True)


def test_real_repo_clean():
    res = subprocess.run(
        [sys.executable, os.path.join(_REPO, "tools", "check_docs.py")],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"実 repo で違反が出た:\n{res.stdout}\n{res.stderr}"
    assert "違反なし" in res.stdout, res.stdout
    assert _admission_findings(res) == []


# ===== handoff 48h stale + schema 検査 (S2, dev-wave 段5 U2, 段4裁定 B4) =====
# 48h stale 判定と handoff schema (4 行ヘッダ書式・状態語彙・基準コミット形) は所有者を
# 判別できないため非阻害の warning とする (rc に算入しない)。「状態:」行の欠落だけは
# 自己修復可能な finding のまま残す (択一 4)。既存被覆はゼロだったため以下は全て純増。


def _well_formed_handoff_text(
    *,
    state: str = "作業中",
    base: str | None = None,
    purpose: str = "テスト目的",
    updated: str = "2026-08-01",
) -> str:
    """4 行ヘッダ契約 (# タイトル + 直後 4 行。書式検査は check_docs.py の非阻害 warning が唯一の経路) を満たす最小 handoff。"""
    if base is None:
        base = "a" * 40
    return (
        "# synthetic handoff\n"
        f"- 目的: {purpose}\n"
        f"- 状態: {state}\n"
        f"- 最終更新: {updated}\n"
        f"- 基準コミット: {base}\n"
        "\n"
        "## 本文\n"
        "trivial body\n"
    )


def _write_handoff(
    root: str, name: str, text: str, *, age_hours: float | None = None
) -> str:
    rel = os.path.join("docs", "handoff", name)
    _write(root, rel, text)
    path = os.path.join(root, rel)
    if age_hours is not None:
        ts = time.time() - age_hours * 3600
        os.utime(path, (ts, ts))
    return path


def _assert_warning_not_finding(root: str, *needles: str) -> subprocess.CompletedProcess:
    res = _run_check(root)
    assert res.returncode == 0, f"警告のはずが rc!=0 になった:\n{res.stdout}\n{res.stderr}"
    assert "違反なし" in res.stdout, f"warning のはずが finding 扱いになった:\n{res.stdout}"
    for needle in needles:
        assert needle in res.stdout, f"{needle!r} が警告出力にない:\n{res.stdout}"
    return res


def _assert_no_warnings(root: str) -> subprocess.CompletedProcess:
    res = _run_check(root)
    assert res.returncode == 0, f"rc!=0:\n{res.stdout}\n{res.stderr}"
    assert "違反なし" in res.stdout, res.stdout
    assert "件の警告" not in res.stdout, f"警告が出てはいけないのに出た:\n{res.stdout}"
    return res


def test_stale_active_handoff_does_not_make_check_docs_red():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-stale.md",
            _well_formed_handoff_text(state="作業中"),
            age_hours=49,
        )
        _assert_warning_not_finding(
            root,
            "2026-07-01-stale.md",
            "状態が稼働中のまま 48h 以上未更新",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_fresh_active_handoff_emits_no_stale_warning():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-fresh.md",
            _well_formed_handoff_text(state="作業中"),
            age_hours=47,
        )
        res = _assert_no_warnings(root)
        assert "48h" not in res.stdout, res.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_handoff_without_status_header_is_still_a_finding():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-nostatus.md",
            "# broken handoff\n\nno header fields at all.\n",
        )
        _assert_violation(root, "ヘッダ定型 (状態:) がない")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_unknown_state_value_is_a_warning_not_a_finding():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-unknownstate.md",
            _well_formed_handoff_text(state="完了"),
        )
        _assert_warning_not_finding(
            root,
            "既知の 3 値 (作業中/計測中/中断) のいずれでもない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_malformed_four_line_header_is_a_warning_not_a_finding():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-malformed.md",
            "# malformed header handoff\n"
            "\n"
            "- 状態: 作業中\n"
            "- 最終更新: 2026-08-01\n"
            "- 基準コミット: " + "a" * 40 + "\n",
        )
        _assert_warning_not_finding(
            root,
            "4 行ヘッダ",
            "書式が",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_short_base_commit_is_a_warning_not_a_finding():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-shortsha.md",
            _well_formed_handoff_text(base="abc1234"),
        )
        _assert_warning_not_finding(
            root,
            "40 桁または 64 桁の hex ではない",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_repo_with_only_a_well_formed_handoff_has_zero_warnings():
    root = _build_min_repo()
    try:
        _write_handoff(
            root,
            "2026-07-01-wellformed.md",
            _well_formed_handoff_text(),
        )
        _assert_no_warnings(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        if fn is test_command_docs_guard_positive_controls:
            calls = [(case, (case,)) for case in _COMMAND_GUARD_CASES]
        elif fn is test_speed_transition_sink_uses_whole_entry_body:
            calls = [
                (f"{boundary}-{sink_has_body_id}", (boundary, sink_has_body_id))
                for boundary in ("current", "archive_pair", "archive_current")
                for sink_has_body_id in (True, False)
            ]
        else:
            calls = [(fn.__name__, ())]
        for label, args in calls:
            display = (
                f"{fn.__name__}[{label}]"
                if args else fn.__name__
            )
            try:
                fn(*args)
                print(f"PASS {display}")
                passed += 1
            except AssertionError as e:
                print(f"FAIL {display}: {e}")
                failed += 1
            except Exception as e:  # noqa: BLE001
                print(f"ERROR {display}: {type(e).__name__}: {e}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


# check_docs speed changes: the reference bodies below are verbatim from
# 4f412c67bcd7ff9cca1e78ce9bd1dd7a15d46037:tools/check_docs.py.
def _speed_reference_raw_slice(body: str, item_offset: int) -> str:
    """list marker から継続物理行の終端までの raw slice を返す。"""

    assert 0 <= item_offset < len(body)
    line_end = item_offset
    while line_end < len(body) and body[line_end] not in "\r\n":
        line_end += 1
    raw_end = line_end
    cursor = line_end
    while cursor < len(body):
        if body[cursor] == "\r":
            cursor += 1
            if cursor < len(body) and body[cursor] == "\n":
                cursor += 1
        elif body[cursor] == "\n":
            cursor += 1
        continuation_end = cursor
        while (
            continuation_end < len(body)
            and body[continuation_end] not in "\r\n"
        ):
            continuation_end += 1
        continuation = body[cursor:continuation_end]
        if not continuation.startswith((" ", "\t")):
            break
        raw_end = continuation_end
        cursor = continuation_end
    return body[item_offset:raw_end]


def _speed_reference_visible_lines(text: str) -> list[tuple[str, int, str]]:
    """code fence / HTML comment 外の可視行と offset・改行を返す。"""

    FENCE_OPEN_RE = check_docs.FENCE_OPEN_RE
    _mask_html_comments = check_docs._mask_html_comments
    lines: list[tuple[str, int, str]] = []
    in_comment = False
    fence: tuple[str, int] | None = None
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        newline = raw_line[len(line):]
        if fence is not None:
            marker_char, marker_len = fence
            stripped = line.lstrip(" \t")
            indent = len(line) - len(stripped)
            if indent <= 3 and re.fullmatch(
                rf"{re.escape(marker_char)}{{{marker_len},}}[ \t]*", stripped
            ):
                fence = None
            lines.append(("", offset, newline))
            offset += len(raw_line)
            continue

        # fence opener の info string 内にある `<!--` は comment 開始ではない。
        # comment 継続中でない行は opener を先に判定する。
        if not in_comment:
            fence_match = FENCE_OPEN_RE.fullmatch(line)
            if fence_match is not None:
                marker = fence_match.group("marker")
                fence = (marker[0], len(marker))
                lines.append(("", offset, newline))
                offset += len(raw_line)
                continue

        visible, in_comment = _mask_html_comments(line, in_comment)
        fence_match = FENCE_OPEN_RE.fullmatch(visible)
        if fence_match is not None:
            marker = fence_match.group("marker")
            fence = (marker[0], len(marker))
            lines.append(("", offset, newline))
            offset += len(raw_line)
            continue

        lines.append((visible, offset, newline))
        offset += len(raw_line)
    return lines


def test_speed_line_number_matches_count_boundaries():
    from itertools import product

    for length in range(8):
        for chars in product("a\n\r", repeat=length):
            body = "".join(chars)
            for offset in range(-length - 2, length + 3):
                assert check_docs._line_number(body, offset) == body.count("\n", 0, offset) + 1


def test_speed_raw_slice_matches_reference_exhaustively():
    from itertools import product

    alphabet = "-x \t\r\n"
    for length in range(1, 7):
        for chars in product(alphabet, repeat=length):
            body = "".join(chars)
            for offset in range(-1, length + 1):
                try:
                    expected = _speed_reference_raw_slice(body, offset)
                except AssertionError:
                    with pytest.raises(AssertionError):
                        check_docs._top_level_item_raw_slice(body, offset)
                else:
                    assert check_docs._top_level_item_raw_slice(body, offset) == expected
    with pytest.raises(AssertionError):
        check_docs._top_level_item_raw_slice("", 0)


def test_speed_visible_lines_matches_reference():
    cases = (
        "", "plain", "plain\r", "plain\r\nnext\n", "<!-- start\ninside\nend -->visible\n",
        "before <!-- hidden --> after\n", "<!-- unclosed\rinside\r\nend -->\n",
        "``` info <!-- ignored\ninside\n```\nafter\n",
        "<!-- hidden\n```\n-->\n``` info <!-- ignored\n```\n",
        "~~~<!-- opener\r\ninside\r\n~~~\r\n",
        "x\r\n<!-- a -->\ry\n<!-- b\r\nc -->z",
    )
    for body in cases:
        assert check_docs._visible_markdown_lines(body) == _speed_reference_visible_lines(body)


@pytest.mark.parametrize("boundary", ("current", "archive_pair", "archive_current"))
@pytest.mark.parametrize("sink_has_body_id", (True, False))
def test_speed_transition_sink_uses_whole_entry_body(boundary, sink_has_body_id):
    root = _build_min_repo()
    try:
        sink_item = "- [T-001] consumed\n\n" if sink_has_body_id else "本文。\n\n"
        if boundary == "current":
            current = (
                "# current\n\n## ローテーション\n\n"
                "## 2026-09-01 (1) — source\n\n"
                "### 次の一手\n1. [T-001] carried\n\n"
                "## 2026-09-02 (2) — sink\n\n"
                + sink_item + "### 次の一手\n1. [T-002] latest\n"
            )
            _write_backlog_docs(root, worklog_text=current)
        else:
            current = (
                "# current\n\n## ローテーション\n\n"
                "## 2026-09-03 (3) — current\n\n"
                + (sink_item if boundary == "archive_current" else "- [T-002] consumed\n\n")
                + "### 次の一手\n1. [T-003] latest\n"
            )
            first_name = "worklog-first.md"
            first = (
                "# first\n\n## 2026-09-01 (1) — first\n\n"
                "### 次の一手\n1. [T-001] carried\n"
            )
            _write_backlog_docs(root, worklog_text=current)
            _write(root, f"docs/archive/{first_name}", first)
            names = [first_name]
            if boundary == "archive_pair":
                second_name = "worklog-second.md"
                second = (
                    "# second\n\n## 2026-09-02 (2) — second\n\n"
                    + sink_item + "### 次の一手\n1. [T-002] carried\n"
                )
                _write(root, f"docs/archive/{second_name}", second)
                names.append(second_name)
            _write(root, "docs/archive/README.md", _archive_readme(*names))
        result = _run_check(root)
        if sink_has_body_id:
            assert result.returncode == 0, result.stdout
            assert "違反なし" in result.stdout, result.stdout
        else:
            assert result.returncode == 1, result.stdout
            assert "次の一手 ID [T-001]" in result.stdout, result.stdout
            assert "見送り台帳にもない" in result.stdout, result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_speed_archive_order_uses_last_entry_of_left_archive():
    root = _build_min_repo()
    try:
        current = (
            "# current\n\n## ローテーション\n\n"
            "## 2026-09-04 (4) — current\n\n"
            "- [T-002] consumed\n\n### 次の一手\n1. [T-003] latest\n"
        )
        first = (
            "# first\n\n## 2026-09-01 (1) — early\n\n"
            "### 次の一手\n\n"
            "## 2026-09-03 (3) — late\n\n"
            "### 次の一手\n1. [T-001] carried\n"
        )
        second = (
            "# second\n\n## 2026-09-02 (2) — middle\n\n"
            "- [T-001] consumed\n\n"
            "### 次の一手\n1. [T-002] carried\n"
        )
        names = ("worklog-first.md", "worklog-second.md")
        _write_backlog_docs(root, worklog_text=current)
        for name, content in zip(names, (first, second)):
            _write(root, f"docs/archive/{name}", content)
        _write(root, "docs/archive/README.md", _archive_readme(*names))
        result = _run_check(root)
        assert result.returncode == 1, result.stdout
        assert "archive worklog の順序を一意に決定できない" in result.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)

from orchestrator.tests.growth_test_holds import enforce_held_functions  # noqa: E402
enforce_held_functions(globals(), __file__, plain_runner="manual")


if __name__ == "__main__":
    sys.exit(_run())
