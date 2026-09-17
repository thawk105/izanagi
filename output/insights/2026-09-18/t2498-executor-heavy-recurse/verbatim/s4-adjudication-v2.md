# 段 4 裁定 v2 (段 6 レビュー後の追補) — [T-2498]

`s4-adjudication.md` (v1) は有効。本追補は段 6 の敵対レビュー 2 本 (A = 受理集合の後退と過剰拒否、B = 残る素通しと
検出力) の所見を裁定し、fix の仕様と変異事前登録を更新する。

## 1. 所見の裁定

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| A1 | `-m cProfile` を 1,100 層重ねた入力で Python の再帰が `RecursionError` になり、`main()` の例外経路 (防護 path を含まない入力は rc 0) が後続 segment の `pytest -q` を検査せず許可する。親が再現 (1,100 層: 新版 EXC、300 層: DENY、旧版は両方 DENY)。 | **real / must-fix** | fix A2 (guard_bash.py) + fix B2 (test) |
| A2 | script 形 (`-m cProfile -- -m pytest`、`-m cProfile /tmp/safe.py -mpytest`、`-m cProfile -- -W pytest`) が合成後の既存 residual 判定 (`-m` の anywhere 走査) で新たに拒否される。直接形 (`python3 -- -m pytest`、`python3 /tmp/safe.py -mpytest`) は旧版でも拒否。 | **real / must-fix (期待値の固定)** | 実装は変えない。契約を「内側 segment は直接形と同じ判定 (baseline の保守性を含む) を受ける」と明文化し、fix B2 で `decide(wrapped).ok == decide(direct).ok` の一致 test を足す。D428 の記録を「27 件中 26 件が重量 module 形、1 件 (`-- -m pytest`) は直接形も拒否される script 形」へ訂正する。旧版は直接形 DENY / 包み形 ALLOW で、包み形だけが穴だった。 |
| A3/A4 | 通常深さでの既存拒否層の素通り、ALLOW 正例の破壊、round-trip 不一致、targets 変化、列挙追加 | refuted | 記録のみ |
| B1 | 綴り差 14 形はすべて再帰が届く | refuted | 記録のみ |
| B2 | 内側の `-h` / `--co` が非実行と扱われない | real / backlog | 既存 `_pytest_nonexecuting` の境界で直接形も同じ。scope 外 (変更禁止面)。裁定パッケージへ |
| B3 | M1 / M2 / M4 は複数関数が赤、M4 は過剰拒否 + 2 重 wrapper 素通しの 2 理由 | real / nit | 期待 node は完全集合で登録 (DW-M08)。M4 は「2 理由」と台帳に明記し、単独変異の証拠に数えない |
| B4 | M8 (再帰位置を sanctioned 早期許可の後へ) は非等価だが新規 6 関数では未検出。識別入力 `python3 -m cProfile tools/run_tests.py -m pytest -q` (現物 D / M8 A) | real / nit → 採用 | fix B2 で識別入力の test を足し、M8 を KILLED 期待へ |
| B5 | M6 は既存 test と冗長、M7 は既存 test が守る | real / nit | KILLED 期待は維持、新規検出力に数えない (memory の規律) |

## 2. fix A2 の仕様 (guard_bash.py、第 2 worktree の impl branch 1f0594712 の上)

- executor 層の処理を Python 再帰から**反復**へ変える。`_heavy_segment_violation` に keyword 引数
  (例 `peel_executors: bool = True`) を足し、既定 True の呼び出し (`_heavy_command_violation` からの入口) だけが
  層を剥く。剥いた各層の合成 segment には `_heavy_segment_violation(inner_seg, repo_root, depth + 1,
  peel_executors=False)` を当てる (その層の全 gate = provenance / 出力先 / admission / residual / sanctioned /
  pytest 等を受けるが、更に剥かない)。loop は合成 segment を `_heavy_head_and_args` で再解釈して次の層へ進む。
- 停止性: 各層の args は前層の正規形 args の真の suffix (executor module token と program token を必ず消費する)
  なので、正規形 token 数が厳密に減り有限回で止まる。Python の stack は層数によらず深さ 1。docstring に書く。
- 深さ上限は設けない (深い軽量 command を過剰拒否しない)。1,100 層の入力で例外を起こさず、後続 segment の
  検査へ到達すること。
- 合成規則 (module: `[raw_head, "-m", value, *rest]`、script: `[raw_head, value, *rest]`、`-` 始まりは `--` 補完)、
  `_script_executor_program` / `_script_executor_arguments`、multi-target 除外、`_PYTHON_MODULE_RE` 検査、
  再帰位置 (shell block 直後、sanctioned 早期許可の前) は v1 のまま。
- 表への追加なし。`_script_executor_targets` の返り値不変。既存の受理を増やさず、v1 §2 の ALLOW 行を 1 件も DENY にしない。
- 実測 (decide 直呼び): v1 §2 全行、A1 の 4 入力 (`"python3 " + "-m cProfile " * 1100 + "-m json.tool ; pytest -q"` → DENY、
  `… * 1100 + "-m pytest -q"` → DENY、`… * 1100 + "-m json.tool /tmp/a.json"` → ALLOW、300 層 → DENY)、
  A2 の一致対 (下記 B2 の対) を報告する。

## 3. fix B2 の仕様 (test_hooks.py、wave worktree)

既存 6 関数 (`test_bash_login_executor_recursion_*`) の直後に 3 関数を足す。既存テストの期待値は変えない。

1. `test_bash_login_executor_recursion_deep_nesting_has_no_stack_limit`:
   `"python3 " + "-m cProfile " * 1100 + "-m json.tool ; pytest -q"` → DENY (例外なし、理由に `pytest`)、
   `"python3 " + "-m cProfile " * 1100 + "-m pytest -q"` → DENY、
   `"python3 " + "-m cProfile " * 1100 + "-m json.tool /tmp/a.json"` → ALLOW (深い軽量形を過剰拒否しない)。
   site="PEGASUS_LOGIN"。現行 (fix A2 前) では 1 本目・2 本目が `RecursionError` で赤になるのが正しい。
2. `test_bash_login_executor_recursion_precedes_sanctioned_allow`:
   `python3 -m cProfile tools/run_tests.py -m pytest -q`、`python3 -m profile -o /tmp/p tools/run_tests.py -m pytest -q`
   → DENY (LOGIN)。M8 (再帰を sanctioned 早期許可の後へ移す) の専属 killer。
3. `test_bash_login_executor_recursion_matches_direct_form`:
   次の (包み形, 直接形) の対で `GB.decide(wrapped, site="PEGASUS_LOGIN")[0] == GB.decide(direct, site="PEGASUS_LOGIN")[0]`
   を assert する (値そのものは pin しない — baseline の保守性が将来緩めば両方が一緒に動く):
   (`python3 -m cProfile -- -m pytest`, `python3 -- -m pytest`)、
   (`python3 -m cProfile /tmp/safe.py -mpytest`, `python3 /tmp/safe.py -mpytest`)、
   (`python3 -m cProfile -- -W pytest`, `python3 -- -W pytest`)、
   (`python3 -m cProfile /tmp/safe.py`, `python3 /tmp/safe.py`)、
   (`python3 -m cProfile -m pytest --collect-only`, `python3 -m pytest --collect-only`)、
   (`python3 -m cProfile -m json.tool /tmp/a.json`, `python3 -m json.tool /tmp/a.json`)、
   (`python3 -m cProfile -m pytest -q`, `python3 -m pytest -q`)。
   失敗 message に両者の判定と理由を出す。

## 4. 変異事前登録 v2 (anchor は fix A2 後に確定)

| id | category | 位置 | 期待 |
|---|---|---|---|
| M0 | positive (等価) | docstring のみ | SURVIVED |
| M1 | negative | 層を剥く入口の恒偽化 | KILLED (負例 3 関数 + deep + precedes) |
| M2 | negative | module 形を None に落とす | KILLED |
| M3 | negative | coverage run 経路を落とす | KILLED |
| M4 | positive (2 理由: 過剰拒否 + 2 重 wrapper 素通し) | 合成 segment から `*rest` を落とす | KILLED (単独証拠に数えない) |
| M5 | negative | script 形を None に落とす | KILLED |
| M6 | positive (既存 test と冗長) | `_PYTHON_MODULE_RE` 検査を外す | KILLED (新規検出力に数えない) |
| M7 | positive (既存 test が守る) | multi-target 除外を外す | KILLED (新規検出力に数えない) |
| M8 | negative | 層剥き block を sanctioned 早期許可の後へ移す | **KILLED** (B2 の precedes 関数) |
| M9 | negative | loop を 1 層で打ち切る (2 層目以降を剥かない) | KILLED (module_denied の 2 重 wrapper、deep 関数) |

## 5. 親の検査 (fix 後)

再 merge → 焦点走 (5 file、launcher は計算ノード) → D428 反転検査 (corpus に両レビューの追加形 + 深い生成 case を足し、
例外は fail-closed で数える) → 焦点再レビュー 1 本 (DW-O16、closed / partial / regressed 表) → 変異 probe → 本走 →
README → 段 7。
