## 総括

判定は **land 不可** です.

全 8 件の内訳は `closed 5 / partial 3 / regressed 0` です. A の completeness 防壁, Human oracle の独立性, B の env 判定一致には残存穴があります.

今回 pytest は実行していません. `54 passed / 6 skipped / rc=0` と変異 `6/6 KILLED` は親の実測事実として採用し, 以下は静的レビュー結果です.

## 所見ごとの対応表

| 元所見 | 判定 | fix 後の根拠と理由 |
|---|---|---|
| A BLOCKER 1: 未知 layer の過剰保証 | **partial** | Human 全文比較と top-level/layer key の exact 化は有効です: [test_hold_inventory.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:51), [test_hold_inventory.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:203). ただし nested `what` と `reason` の key/value は exact pin されず, `_expected_human()` も inventory から値を受け取ります: [test_hold_inventory.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:158). 新しい過剰保証を `reason` 等へ入れる変異が生存します. |
| A MAJOR 1: release と実条件の非結合 | **closed** | production/test release の全 field, 全 bypass surface, Pegasus allowlist が literal と相互関係で固定されています: [test_hold_inventory.py:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:78), [test_hold_inventory.py:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:93), [test_hold_inventory.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:151). |
| A MAJOR 2: Human の値, 帰属, 順序 | **partial** | renderer だけの label, 順序, 欠落は exact 比較で捕捉します: [hold_inventory.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:170), [test_hold_inventory.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:203). 一方, expected helper は renderer と同じ loop/branch を再実装し, ruling, reason, 一部 status を実 inventory からコピーします: [test_hold_inventory.py:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:164). semantic oracle としては独立していません. |
| B BLOCKER 1: plain runner coverage 違反 | **closed** | `_run()` と `__main__` が追加されています: [test_hold_inventory.py:305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:305). 親実測にも `test_plain_runner_coverage` が含まれています. |
| B MAJOR 2: script 起動時 import failure | **closed** | import 前に repo root bootstrap が入りました: [hold_inventory.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:15). script/module 両 entrypoint の subprocess 契約もあります: [test_hold_inventory.py:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:258). |
| B MAJOR 3: bypass surface 不完全 | **closed, inventory scope 内** | 指摘された `--noconftest`, `--confcutdir`, direct call, `PYTEST_ADDOPTS` が追加され, status の runner assumption も明記されています: [hold_inventory.py:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:104), [hold_inventory.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:117), [hold_inventory.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:150). 実 bypass の拒否は未実装ですが, inventory はそれを unresolved と正しく開示しています. |
| B MAJOR 4: conftest との判定 drift | **partial** | conftest の実判定との直接照合は追加されました: [test_hold_inventory.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:237). ただし `unset`, exact token, invalid だけで, conftest が独立分岐として扱う empty string がありません: [conftest.py:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/conftest.py:277), [hold_inventory.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:71). |
| B MINOR 1: 無効な `git diff --check` 証拠 | **closed** | これはコード欠陥ではなく検査証拠の欠陥です. fix 子は untracked file を扱える `git diff --no-index --check` の結果を記録しました: [s6-fix.md:35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-freeze-hold-residual/s6-fix.md:35). |

## BLOCKER 1: nested field から completeness 過剰保証を再導入できる

根拠:

- top-level と layer の key は exact ですが, `what` の key set と `reason` の内容は固定されていません: [test_hold_inventory.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:40), [test_hold_inventory.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:54).
- Human expected は mutated inventory の `reason` と `what` をそのまま利用します: [test_hold_inventory.py:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:164).
- renderer も `reason` をそのまま出力します: [hold_inventory.py:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:189).

例えば production `reason` に `"coverage": "includes registered and unregistered hold categories"` を追加する 1-site 変異は, 現在の blacklist に一致せず, Human expected と JSON expected の両方が同じ値へ追随します.

成果物影響: `completeness=registered-layers-only` と矛盾する保証を Human/JSON の双方へ載せても受理されます.

推奨対応: `what` と `reason` を含む全 nested object の key set と canonical 値を独立に固定してください. 自由 prose を許す場合は, completeness claim を格納できない型付き field へ制限する必要があります.

## MAJOR 1: empty env の drift が未検出

現在の conftest と inventory はどちらも empty string を held とします. しかし照合 test は env 削除, exact token, invalid nonempty の 3 ケースだけです: [test_hold_inventory.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:237).

`_test_effective_status()` の条件を `value is None` だけへ弱体化すると, empty string だけが `invalid-opt-in-rejected` になり, 現在の焦点 test は検出しません.

成果物影響: empty env で conftest は held と判定する一方, inventory は invalid と報告し, 実状態との不一致が再発します.

推奨対応: `None`, `""`, exact token, invalid nonempty の 4 ケースを parameterize し, 各ケースで conftest と inventory の双方を照合してください. 最終的には public な副作用なし classifier を共有する方が堅牢です.

## MAJOR 2: ruling, reason, configured status の semantic oracle がない

次の値は Human expected が実 inventory からコピーする一方, inventory test が canonical source または literal と比較していません.

- production/test layer の `ruling` と `reason`: [hold_inventory.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:53), [hold_inventory.py:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:93).
- production の `configured_status`: [hold_inventory.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:62).
- test の canonical ruling は source にあります: [growth_test_holds.py:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/growth_test_holds.py:13).

例えば test layer の ruling を `"wrong-ruling"` へ変える, または production の configured status だけを `"active"` にする変異は生存します.

成果物影響: 誤った裁定主体や理由, または `configured_status=active` と `effective_status=held` の矛盾を成果物として受理します.

推奨対応: layer level の ruling/reason/status を canonical source と独立 literal の双方へ結合し, `production.configured_status == production.effective_status` も明示してください.

## M5 の検出力判定

M5 で Human 側が発火しなかった理由は指摘どおりです. `_expected_human()` が mutated inventory の `bypass_surface` を使うため, inventory からの削除には追随します.

ただし M5 単体については **検出力の移動** であり, 受理集合の低下ではありません.

- inventory から `plain-python-runner` を削ると exact surface set が発火します: [test_hold_inventory.py:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:93).
- renderer だけから表示を削ると Human 全文比較が発火します: [test_hold_inventory.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:207).

従って M5 の期待 node 数が減ったこと自体は所見にしません. 一方, exact surface test が pin していない ruling/reason 等では同じ追随が実際の検出力低下になるため, 上の MAJOR 2 としています.

## bootstrap と private import

Repo root bootstrap は, root が未登録の場合だけ `sys.path[0]` へ追加します: [hold_inventory.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:15). standalone process では必要な変更であり, module/pytest 起動で root が既に存在すれば順序を変えません. 理論上は後続 import の shadowing 面を増やしますが, 現在の成果物影響は示せません. **nit / backlog** とし, must-fix にはしません.

Private `_growth_holds_opted_in()` の import は refactor に脆いですが, rename 時は collection error となるため silent green ではありません. private 関数使用そのものも **backlog** です. ただし empty string 欠落は silent drift を許すため MAJOR 1 です.

## 変異 6 件で捕まらない残存穴

| 追加破壊 | 現在の予想 | scope |
|---|---|---|
| nested `reason` または `what` へ未知 layer の過剰保証を追加 | SURVIVES | scope 内, BLOCKER 1 |
| inventory の empty env 分岐だけを invalid へ変更 | SURVIVES | scope 内, MAJOR 1 |
| layer ruling/reason を誤値へ変更 | SURVIVES | scope 内, MAJOR 2 |
| production configured status だけを active へ変更 | SURVIVES | scope 内, MAJOR 2 |
| repository の別箇所へ第 3 の hold layer を新設し inventory 登録を忘れる | inventory test は 2 layer のまま green | 現契約では scope 外 |
| `--noconftest`, unsafe `--confcutdir`, direct call を実際に使う | inventory は開示するが実行を阻止しない | enforcement は scope 外 |

裁定パッケージ候補は 2 件です.

1. `registered-layers-only` snapshot を維持するか, 全 hold producer の中央 registry と登録強制へ昇格するか.
2. T-930 を disclosure-only のまま残すか, `tools/run_tests.py` と Pegasus transport で conftest suppression を fail-closed に拒否するか.