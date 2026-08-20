# [T-222] 段4 裁定

対象: `tools/pegasus/dispatch_compute.py:924-946` の `_accounting_present` に、accounting footer の
`Group Name` を policy account (`DEFAULT_PROJECT` = `"SFC"`) へ exact 束縛する検査を追加する。

## 段3 所見の裁定

段3 は2レンズ (`s3-lens-a-accuracy.md`: 正確性・実データ整合、`s3-lens-b-scope.md`: 波及範囲・
scope の完全性) を並列実行した。

| # | 所見 (レンズ) | 判定 | 採否 | scope | 対応 |
|---|---|---|---|---|---|
| 1 | 新regexがCRLFを消費できない (A#1) | real (だが既存 `_NQSV_REQUEST_ID_RE` 等と同型の既存弱点。今回の変更が悪化させるものではない) | 不採用 (今 wave) | scope外 | 対応しない。理由: 既存4フィールドも同じ弱点を共有しており、本 wave が導入した退行ではない。全 `_NQSV_*_RE` を横断して CRLF 耐性を足す族一般化は DW-G03 (独立2例) の対象になりうるが本 ID の scope ではない。nit として記録するに留める |
| 2 | `DEFAULT_PROJECT` 以外の project 経路が実在するか (A#2) | refuted (`dispatch()` に project 引数なし、CLI/環境変数上書きなし) | — | — | brief (P1) の provisional 裁定 (module 定数を直接参照) を確定裁定にする |
| 3 | Group Name の実データ出現順序が未検証、tail 切り詰めとの相互作用 (A#3) | real→**親が一次資料で検証済み** | 採用 (テスト追加のみ) | scope内 | `output/insights/2026-07-30_pegasus-compute-node-dispatch/probe-874129-accounting.txt` (実 probe 874129.nqsv の生ログ) を読んだ。実際の順序は `Request ID → Request Name → Queue → Number of Jobs → User Name → Group Name → Created/Started/Ended Request Time → Elapse` であり、`Group Name` は `Started Request Time` より前に出現する。プランの fixture 配置 (Request ID の直後、Started の前) は実データと整合している。追加対応として、`test_scheduler_logs_are_tail_bounded_with_explicit_omission` 系統に Group Name が tail 保持域に残ることを確認するケースを1件足す (安価で検出力が増す) |
| 4 | `findall` 全件一致という設計の是非、重複/混在行への防御 (A#4) | real (正しい fail-closed 設計と確認) | 採用 (テスト追加) | scope内 | 追加対応として、Group Name 重複行・`SFC`+`OTHER` 混在行のケースを既存 parametrize (`test_accounting_requires_matching_request_id_and_all_nqsv_fields` 系統) に足す |
| 5 | scope 完全性: `silo_ladder_rung1.py` / `floor_liveness.py` / `collect_receipt.py` / `t503_restore_durability_probe.py` に同型の未検証経路 (B#1) | real | **不採用 (scope外、独立 backlog 候補として親からユーザーへ返す)** | scope外 | 詳細は下記「scope 外 real 所見」節 |
| 6 | resume 側の独立経路が main に実在するか (B#2) | refuted (brief の主張どおり、dispatch_compute.py 内に resume/monitor 相当の独立関数は無い) | — | — | brief の記述を確定事実として扱う |
| 7 | 既存テストの網羅性 (B#3) | refuted (`_Scheduler(` 使用63件中61件が `accounting=True` 既定で fixture 更新だけで足りる。直接契約テストは既知の2件のみ) | — | — | プランの scope (fixture 更新 + 既存2契約テスト拡張) で under-registration なしと確定 |
| 8 | `check_acceptance_reds.py` 等 receipt consumer が schema v2 のまま新しい意味 (Group Name 検証済み) を暗黙に受け取る (B#4) | real (だが破壊的ではない。旧 `True` が新たに偽陽性になることはなく、判定は厳格化のみ) | 不採用 (今 wave) | scope外 | 受理集合を緩める変更ではないため機能上のリスクなし。schema version 更新は別途の docs-only backlog 候補とし、本 wave の must-fix にしない (DW-G05: 成果物影響を1行で書けない nit) |

## scope 外 real 所見 (裁定パッケージ、ユーザーへ返す)

lens B (`s3-lens-b-scope.md` 項目1) が、`_accounting_present` とは独立に accounting evidence を
検証する経路を4箇所発見した。いずれも Group Name を検証していない同型の欠落を持つ。

- `orchestrator/campaign/silo_ladder_rung1.py:153,3531,3702,4644` — Request ID/Started/Ended/Elapse を
  独自 regex で再検証する完全な重複経路。policy は同じく `SFC` (`tools/pegasus/policy.json:23`)
- `orchestrator/campaign/floor_liveness.py:30,186,407` — 4 marker の単純存在検査で
  `accounting_present=True` を生成
- `tools/pegasus/collect_receipt.py:27,67,151` — scheduler stderr accounting summary を独自 parse し
  別キー `scheduler_accounting_present` を生成
- `tools/pegasus/probes/t503_restore_durability_probe.py:296,308` — Request ID と scheduler terminal
  accounting を独自検証

**推奨:** 独立した producer 4箇所に同型欠陥が再現しており DW-G03 (族一般化には独立2例) の閾値を
満たす。ただし本 ID ([T-222]) はユーザー起票時点で `dispatch_compute.py:924-946` 単体に明示的に
scope を絞られており (worklog `docs/archive/worklog-phase3-0801-80.md:50-53`)、4ファイルへの
横断対応は「小さく閉じたタスク」という起票時の性質と矛盾する。**本 wave は scope を広げず、
上記4箇所は新規 backlog 候補としてユーザーへ返す。** (実装しない場合の成果物影響: 各経路の
policy account 検証は本 wave の後も Group Name 不一致を見逃したまま — ただし main 経路で
実際に Group Name が `SFC` 以外になった実例は無く、理論的ギャップに留まる。)

## plan v2 (段5 実装子への確定指示)

段2プラン (`s2-plan.md`) の1〜4を採用し、次を追加する。

1. `tools/pegasus/dispatch_compute.py:141` 付近に `_NQSV_GROUP_NAME_RE` を追加
   (`re.compile(r"(?m)^[ \t]*Group Name:[ \t]*(\S+)[ \t]*$")`)。
2. `_accounting_present` (`:924-946`) へ `_NQSV_GROUP_NAME_RE.findall(tail) != [DEFAULT_PROJECT]`
   なら `False` を返す分岐を、Request ID 検査の直後・既存4フィールド検査の前に追加する
   (docstring も「submit ID・policy account・必須 field の連言」に更新)。
3. `orchestrator/tests/test_pegasus_dispatch_compute.py`:
   - `_Scheduler._finish` (`:96-103`) の fake footer に `Group Name:             SFC` を
     Request ID の直後・Started Request Time の前に追加 (実データ順序と整合、上表#3で検証済み)。
   - `test_accounting_accepts_measured_nqsv_shape_only_when_id_matches` (`:2242-2250`) の正例 tail にも
     同じ行を追加 (プラン#4で指摘済み、これを欠くと正例テストが赤になる)。
   - `test_accounting_requires_matching_request_id_and_all_nqsv_fields` (`:2206-2239` 付近) の
     parametrize に、最低次の4ケースを追加する: (a) Group Name が `OTHER` (不一致)、
     (b) Group Name 行が欠落、(c) Group Name 行が重複 (`SFC` 2回)、(d) `SFC` と `OTHER` の混在。
     既存ケース (Request ID 不一致・フィールド欠落) には正しい `Group Name: SFC` 行を足し、
     独立した理由を保つ (プランの指摘どおり)。
   - 追加 (推奨、コスト低): `test_scheduler_logs_are_tail_bounded_with_explicit_omission` 系統に、
     tail 保持域内に `Group Name` 行が残ることを確認する1ケースを足す。
4. 呼び出し側 (`:1935`, `:1944-1946`) は変更しない。

## 変異事前登録 (DW-M01、段6 で使う)

DW-M01 により、受理集合を縮小する本 wave では承認外の過剰拒否を検出する正例も登録する (M4)。

- M1: `_NQSV_GROUP_NAME_RE.findall(tail) != [DEFAULT_PROJECT]` の分岐を丸ごと削除 (常に通す) →
  既存2契約テスト+新規不一致/欠落ケースで KILLED を期待 (under-rejection/bypass の検出)
- M2: 比較を `!=` から `not in` 相当 (部分一致、`DEFAULT_PROJECT not in group_names`) へ弱める →
  新規の混在行ケース (`SFC`+`OTHER`) と重複ケース (`SFC`+`SFC`) の両方で KILLED を期待
  (段6敵対レビュー b#5 で訂正: 当初「混在行だけ」と記録したのは不正確。`"SFC" not in ["SFC","SFC"]`
  も False になるため重複ケースも同じ変異で新たに通ってしまう。検出力自体は変わらず、
  記録の説明を補正した)
- M3: 期待値を `DEFAULT_PROJECT` から別の定数・空文字へ差し替え → 正例テスト (id一致) で
  KILLED を期待 (単一理由: 正しい `SFC` が拒否される)
- M4: 比較演算子を `!=` から `==` へ反転 (over-rejection 検出用の正例変異、DW-M01 必須) →
  正例テスト (`test_accounting_accepts_measured_nqsv_shape_only_when_id_matches`) が真っ先に
  KILLED することを期待。有効な `SFC` job を誤って reject する側の欠陥を、無効な job を誤って
  accept する側の欠陥と同時に検出する

各変異は `_accounting_present` 内の1行 (Group Name 検査分岐) だけを変更し、他4フィールドの検査
条件には触れない。前後に同じ入力を拒否する層は無い (呼び出し側 :1935, :1944-1946 は bool を
そのまま使うだけで独自の Group Name 検査を持たない、段3 lens B #2/#3 で確認済み)。

## 受理集合の変化 (DW-G05)

- 実装前: Group Name が `SFC` 以外、または欠落した job でも、他4フィールドが揃っていれば
  accounting evidence 受理 (`_accounting_present` = True)。
- 実装後: 上記に加え Group Name が exact に `SFC` であることが必須。不一致・欠落・重複は reject。
  reject された job は `marker_valid` が True なら `DispatchError("result/log/accounting-grace-expired")`
  (`dispatch_compute.py:1983`) へ、False なら既存の F47 latch 経路へ落ちる (呼び出し側の分岐は
  変更しない)。受理集合を狭める方向のみであり、緩める変更はない (規律2 と整合)。

## 段6 敵対レビュー所見の裁定

段5実装後の実 diff に対し、異なる2レンズ (`s6-review-a-accuracy.md`: 正確性・退行、
`s6-review-b-integrity.md`: 完全性・副作用・権限境界) で敵対レビューを行った。blocker 級の
指摘はゼロ。real (非blocker) が2件。

| # | 所見 (レンズ) | 判定 | 対応 |
|---|---|---|---|
| 1 | Group Name 分岐の挿入位置が「Request ID 検査の直後」の字義どおりだと、ID値の一致検査 (`observed != expected`) より前にある (A#2) | real (非blocker) | **不採用・nit**。全条件は副作用のない純粋な連言 (AND) であり、分岐の順序を変えても最終的な bool 結果・受理集合は完全に同一 (親が確認)。成果物影響を1行で書けない (DW-G05) ため、コード変更はしない |
| 2 | `test_scheduler_logs_are_tail_bounded_with_explicit_omission` に足した `assert "Group Name:" in stderr["tail"]` は、現行の fixture 順序 (`Request ID` が `Group Name` より前) では `Request ID:` assertion に対し恒真 (tautology) — 独立した検出力を持たない (A#5、B#5 が M2 の記録不整合として関連指摘) | real (非blocker) | **不採用・nit (再考のうえ fix 子への投入を見送り)**。当初は fix 子での1行削除を検討したが、`DW-S06-B` の fix 子契約は「既存テストの期待値を変更しない…反転・緩和・skip・削除を禁じ」を無条件の文言で要求しており、この assertion が本 wave 内で段5が追加した新しいものであっても、fix 子への「削除」指示は文言上の禁止に触れるおそれがある。恒真であっても偽陽性・偽陰性を生まず (誤って reject/accept される job は無い)、成果物 (certified 選択・受理集合・台帳) への影響を1行で書けないため `DW-G05` の nit 基準を満たす。追加の fix サイクルは起動せず、次にこのテストへ触る wave への backlog として記録するに留める |

M2 の変異登録の説明不整合 (B#5) は上の「変異事前登録」節を直接補正済み (検出力自体に変更なし)。

両所見とも must-fix ではないため、段6 の fix サイクルは起動しない。実装は段5 の diff (`impl-diff-dispatch-compute.patch`, `impl-diff-test-file.patch`) を確定形とし、変異 matrix・受入へ進む。
