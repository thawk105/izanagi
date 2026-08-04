# [T-407] 段 1 brief — ruleops inventory が非 UTF-8 blob で全体を拒否する

基準: worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob`、
HEAD `b1b1a12` (local main と同一)。受入は repo root から `python3 tools/run_tests.py`
(login ノードでは site_policy が Pegasus gen_S 計算ノードへ同期 dispatch する)。

## 実測した前提 (親が本 wave で確認済み)

- `python3 tools/ruleops.py inventory --repo .` は rc=2 / reason `non-utf8` で停止する。
  対象は `output/insights/2026-08-03_t361-t362-cluster-probes/.../ *.probe.raw` の 4 件
  (各 32 bytes の乱数、導入 commit `9b0f044`)。
- `ruleops.py check` は rc=0 (ledger は候補 0 件)。**受入の RuleOps preflight は緑**であり、
  影響は `test_real_checkout_independent_maximum_package_and_runner_preflight` 1 件に閉じる。
- scope は `_TEST_PATH_RE` (`orchestrator/tests/test_*.py`) と `_INSIGHT_PATH_RE`
  (`output/insights/.+`)。`docs/paper-story/**` と `output/campaigns/**` の PNG も非 UTF-8 だが
  scope 外なので従来から通っていた。
- `build_inventory` の `raw.decode("utf-8","strict")` (tools/ruleops.py:665-668) は
  **復号結果を捨てる純粋な門番**である。後続の `_markers` は bytes で処理し、
  `.json`/`.md` の非 UTF-8 は `_strict_json` の RuleOpsError を握って `(None, None)` を返す。
- 既存被覆: 非 UTF-8 の fail-closed テストは **ledger 経路のみ** (test_ruleops.py:389、
  `check --ledger`)。**inventory scope の非 UTF-8 blob を突くテストは存在しない** →
  本 wave の新規テストの純増検出力はここに限る。
- 4 件の bytes は同じ evidence tree の `tracking-receipt.json` / `source-tree-inventory.json` /
  `preflight.json` が sha256 で pin 済み (`b8bbe51c…` を照合)。producer は
  `output/insights/.../driver/run_probes.py` の `_write_probe` (`secrets.token_bytes(32)`)。

## scope と provisional 裁定 (すべて攻撃対象)

- **(P1) 択一は (A) ツール側を直すを採る。** (B) evidence の保存形式変更は、commit 済み bytes を
  書き換えると自己 pin を壊し (F29 型)、producer だけ直しても現在の赤は消えないため不採用。
- **(P2 = 確定済みユーザー裁定、2026-08-04 再裁定) 非 UTF-8 の scoped blob は `items` から
  読み飛ばし、読み飛ばした件数を出力の根に出す。**
  経緯: worklog (152) に既存裁定「(a) 読み飛ばす。同ツールは規約文書の検査が目的であり、
  測定の生出力は元々対象外」があり、これは wave 開始後に並行セッションが land したため
  段 1 時点で未見だった。親が提示した A1 (binary として載せる) は一度承認されたが、
  記録済み裁定との食い違いを親が発見して停止し、ユーザーが「記録どおり読み飛ばす + 件数を出す」を
  確定した。A1 と「件数なしの読み飛ばし」は不採用。
  **本項は攻撃対象から外す** — 代案への差し戻しは `DW-S04` に従い、裁定時点で未見の新事実が
  出た場合だけユーザー再裁定へ戻す。実装の穴・受理集合・被覆への攻撃は従来どおり行う。
- **(P5) 出力の根に新しい key を 1 つ足すため `INVENTORY_SCHEMA` を `ruleops-inventory/v2` へ上げる。**
  同じ版名が 2 つの形を指す状態を作らないため。両レンズが repo 内に v1 を pin する consumer と
  保存済み inventory JSON が無いことを独立に確認済み。攻撃対象。
- **(P6) 読み飛ばし件数の key 名は `skipped_non_utf8` (整数) とする。** path 列は出さない
  (裁定の「読み飛ばす」に対し最小)。攻撃対象。
- **(P3) 修復は `build_inventory` に限定する** (`DW-G03` の局所修復既定)。`inspect` (ruleops.py:1010)、
  ledger、receipt の strict decode は現状維持。同型欠陥の独立 2 例目は未確認。
- **(P4) 新規テストは「三軸 matrix」とする** (段 3 の両レンズが独立に must-fix とした)。
  content (非 UTF-8 / UTF-8) × suffix (`.py` / `.md` / `.json` / `.raw`) × scope-kind
  (direct test / insight) を同一 test 群で固定し、UTF-8 control の `artifact_format`
  (`python` / `markdown` / `json` / `other`) も併せて固定する。これで
  「suffix 特例」「insight 限定」「全件読み飛ばし」「件数が実際の読み飛ばし数と無関係」の
  誤実装を殺す。加えて `inspect` の非 UTF-8 fail-closed 負例を 1 本置く。
  fixture は `tmp_path` 上に自前で作り、実 repo の probe evidence に依存しない
  (親 directory の `mkdir` を忘れないこと — レンズ A が段 2 プランの実行不能箇所として指摘)。

## scope 外と裁定した real 所見 (実装せず起票する)

- **[T-409 候補] 当該 real-repo test が D63 の canonical group から外れている。**
  `test_ruleops.py:1709` は `@pytest.mark.xdist_group(name="real_repo")` を直接付けているが、
  D63 決定 (1) は「decorator 不使用・`conftest.py` の正本リストで管理・単一 `xdist_group("real-repo")`」
  を契約とする。group 名も `real_repo` ≠ `real-repo` で別 group になり、実 submodule を patch する
  writer との排他が効いていない。収集監査 meta-test は非 canonical node の positional arg しか
  拒否せず kwargs 形を見逃す。**本 wave の赤は決定的でこの欠陥に起因しない**ため実装しないが、
  受入全走の緑を「並行干渉に対して頑健」とは主張できない。同 test は D63 決定 (4) の
  `--untracked-files=all` 共有 helper も使っていない。
- **[T-410 候補] 許可 rc の Git stderr が非 UTF-8 でも検査されない** (`ruleops.py:359` 付近)。
  非ゼロ rc の分岐でしか strict decode せず、rc=0 や `grep` の rc=1 では任意 bytes を捨てる。
- **[T-411 候補] direct test candidate の target 本文を `validate_candidate_ledger` が decode しない**
  (`ruleops.py:2051` 付近)。insight candidate とは非対称で、`inspect` が拒否する target を
  `check` が構造上受理しうる。
- **[T-412 候補] mutation receipt の非 UTF-8 負例テストが無い。** 既存 ledger 負例は
  `_strict_json` の共通入口しか固定せず、`_receipt_document` だけ緩める変異を殺せない。

## 段 3 レンズが実測した事実 (旧設計 A1 への review で得たが、対象非依存なので継承する)

- HEAD `b1b1a12` の scoped tracked regular blob 1,659 件 / 40,345,708 bytes を strict 走査し、
  非 UTF-8 は 4 件のみ。tracked PNG 9 件 (`docs/paper-story` 3、`output/campaigns` 6、`output/env`) は
  全て scope 外。
- `artifact_format` を値として読む repo 内 consumer は `_markers` だけ。closed enum consumer、
  保存済み inventory JSON、JSON Schema はいずれも 0 件。
- 受入 preflight (`run_tests.py:540`) は `check` だけを呼び、`build_inventory` は call graph に無い。
- 凍結証拠 4 件の sha256 pin は実在し実バイトと一致するが、**commit 後に再検証する repo 内
  consumer は存在しない** (producer 実行中の照合のみ)。
- 同型欠陥 (「scope 内に想定外 bytes が来ると列挙全体が止まる」) の独立 2 例目は見つからなかった。
  `s8b_holdout_freeze.py:257-351` は逆に非 UTF-8 を text から外し `skipped_binary_count` を出す
  **先例**であり、本 wave の新設計と同型。

## 不変条件 (破ったら停止)

1. ledger / receipt / `inspect` の非 UTF-8 fail-closed を緩めない。
2. inventory の item key 集合 (test:53-55) を変えない。root key 集合は `skipped_non_utf8` の
   追加**だけ**変える (`_INVENTORY_ROOT_KEYS` の更新は必要な schema 変更であり、テスト弱体化ではない)。
3. 凍結証拠 (`*.probe.raw` と その sha256 pin) の bytes に触れない。ファイル削除もしない。
4. D99 決定 (1)(2) の性質 (read-only、HEAD 固定、対象 2 族) を変えない。
5. `human_approved:false` 固定と「成功は削除安全を主張しない」を変えない。

## 成果物影響 (DW-G05)

放置した場合: certified 選択・レポート・台帳の値と受理集合は不変 (D99「研究状態への影響」)。
変わるのは**受入全走が恒常的に 1 件赤になり、以後の wave が「全緑」を回帰判定に使えなくなる**こと。
赤の常在は新規回帰を隠す。実装した場合の変化は 2 つ — (i) `ruleops inventory` の受理集合
(非 UTF-8 blob を含む repo を拒否→受理)、(ii) inventory 出力の形 (根に `skipped_non_utf8`、
schema 版 v1→v2)。人間レビュー用の一覧からは非 UTF-8 成果物が消えるが、件数として残る。

## 分割方針

実装面 (ruleops.py + test_ruleops.py) は Codex `role=author` 1 本。親は brief・裁定・統合・
全走・記録・commit・land と docs 本文 (`docs/ruleops.md`) のみ。
段 2 プラン 1 本、段 3 敵対レンズ 2 本、段 6 レビュー 2 本。
**軽量版は採らない** — 択一が割れ (P1/P2)、ツールの受理集合と出力の形が変わるため (`DW-C00`)。
**段 2・3 は再裁定により旧設計 (A1) 前提の成果物を破棄して再実行する** (旧 plan・旧 review を
実装の根拠に流用しない。対象非依存の実測事実だけを上記へ継承した)。
