# [T-2252] 自己整合しない較正を層 3 の within-run 床値に使わない (D1537 の実装)

wave: `dev-wave-t2252-self-inconsistent-floor` / branch:
`worktree-dev-wave-t2252-self-inconsistent-floor`
実装 commit `64c4d0cb0`。

本 README は実施記録と裁定の一次資料。設計判断の正本は `docs/decisions.md`、経緯の正本は
`docs/worklog.md` の該当エントリ。裁定 D1537 の一次資料は
`output/insights/2026-09-02_t2136-within-run-floor-protocol/README.md` (裁定 1)。

## 何を閉じたか

有効な v2 lock authority の契約が pin する較正の (path, sha256) が、裁定で確定した自己整合しない
較正の exact identity 集合 (pegasus g1 `calibration-753f535a8d024727.json` の 1 件) に完全一致する
campaign では、層 3 が within-run の候補形成を行わない。pin 由来も直下 record 由来も候補にしない
(系列単位の除外)。between-run、直下 record の一致判定、`genome-absent-legacy-record` の表示は不変。

除外は `_validated_pin_path` の path / directory / 通常 file / SHA-256 検査の**後**に行う。
SHA 不一致等の `Layer3ReportError` と `pin-file-missing` の診断は不変で、pin file が無くても契約の
ref が宣言集合に入れば除外する。within-run の search 詳細の `contract_pin` に
`within_run_exclusion = "self-inconsistent-calibration"` を 1 つ足す。`status` 値は増やさない。

宣言は `orchestrator/campaign/layer3_report.py` の module 定数
`SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS` (consumer-local)。層 3 は effective-clock の自己比較を
実行しない。`orchestrator/tests/test_env_contract.py` の既知例外集合は独立 oracle として据え置き、
`test_layer3_report.py` 側で宣言集合が「登録簿の required 世代のうち実 bytes で自己比較に落ちる集合」と
等しいことを実述語で検査する。

## 何を閉じていないか

- 健全な世代 (pegasus g2) の活性化は人間手番 (D437)。本 wave は行わない。発効後に生産される
  g2-pinned campaign は g2 の値を採る。既存の g1-pinned campaign は発効後も一致なしのまま (authority 不変)。
- D1538 (genome 不在 record の内容 hash 許可リスト) は別項で、本 wave は触っていない。
- g2 正例のテストは `_calibration_floors` の直接呼び出しであり、activation 全鎖の証明ではない。

## 段 3 / 段 6 が覆したもの

| 段 | 所見 | 結果 |
|---|---|---|
| 3 (sol) | pin の path 1 本だけの除外は、同 bytes の直下 copy が別名で置かれた場合に一致が戻る。「重複エラー」から「直下 1 件の新規一致」へ転じる受理拡大も起きる | 除外を系列単位へ変更 |
| 3 (sol / luna) | 較正検証 leaf への共有 frozenset は新しい例外台帳で、材料レポートの generator hash に束縛されず、silo ladder / T-126 の identity 閉包も動かす | 宣言を `layer3_report.py` へ、`test_env_contract.py` は据え置き |
| 3 (両方) | brief (P2) の「bytes 検証を呼ばずに除外」は fail-closed を隠す | 検証を先に完遂 |
| 3 (luna) | 新 status 値は裁定が要求せず発効後に語義が古くなる | status 値を足さず理由 key 1 つ |
| 3 (refuted) | 宣言参照は「却下された再検査の関門」ではない / 自己比較 audit は恒真でない / テストは空実装で緑にならない | 変更なし |
| 6 (B) | 新 fixture 2 つが genome 不在 record で D1538 と逆向きの gate | canonical genome を追加 |
| 6 (B) | 改訂 registered-glob テストが再帰走査への退行を検出できない | `scanned_files == 1` を追加 |

## 成果物影響

- repo 内の層 3 レポート 7 件はすべて隣接 lock が authority なし (v1) で linux-baremetal。
  noise_floor の値は変わらない。再生成しない。dossier・T2136 変異台帳の g1 値の写しも再発行しない。
- 今後生産される pegasus g1 authority の campaign の層 3 レポートは within-run が None になる
  (現存する実 campaign にこの条件のものは 0 件)。
- `layer3_report.py` の bytes が変わるので、全新規 report の `meta.generator.sha256` が変わる。
- certified 選択・受理集合・campaign lock・環境契約・activation record は変わらない。

## 検査の実測

| 検査 | 結果 |
|---|---|
| 焦点走 1 (`test_layer3_report.py` 単独、計算ノード dispatch 975799) | 209 passed / rc=0 |
| 焦点走 2 (変更 test file + consumer test 8 file、dispatch 975828) | 1172 passed / rc=0 |
| 変異 probe (実装 commit `64c4d0cb0` 束縛、全件 SURVIVED 期待で観測 node を収集) | baseline PASSED / 負例 8 件すべて赤 node を出し (MISMATCH = 期待 SURVIVED に対する観測)、等価変異 M9 SURVIVED |
| 変異本走 (main 取り込み merge commit `f1e166da8` 束縛) | baseline PASSED / KILLED 8 / SURVIVED 1 (M9 等価変異、期待どおり) / MISMATCH 0 / 期待 node 9 件完全一致 |
| AI provenance 全史監査 (merge commit `f541e725b` 時点、計算ノード dispatch 976050) | 8,089 件、新規違反なし (rc=0) |
| 受入全走 | land の受領証を正本とする |

## 成果物

- `verbatim/` — 子 8 本の逐語 (plan 1、consult 2、author 1、review 2、fix 1、focus 1) と親の裁定
  (`s4-ruling.md`、`s6-fix-ruling.md`)、親 brief。codex 出力の行末空白は `git diff --check` に掛かるため
  可視文字不変の最小正規化 (行末空白の除去) を当て、原文 sha256・byte 数・除去位置と復元法を
  `verbatim/NORMALIZATION.json` に記録した (7 file、復元結果が原文 hash と一致することを検算済み)
- `mutation-spec-probe.json` — 変異 9 点の事前登録 (全件 SURVIVED 期待の probe)
- `mutation-probe-attempt1.json` — probe 台帳 (観測 node 収集用)
- `mutation-spec-final.json` — 期待 node を probe の観測から機械生成した本走 spec
- `mutation-ledger.json` — main 取り込み merge commit `f1e166da8` 束縛の本走台帳

## 変異の期待 node (本走で観測と完全一致)

| ID | 変異 | 殺した node (test_layer3_report.py) |
|---|---|---|
| M1 | 除外条件を恒偽にする | g1 負例 5 件 (registered-glob 改訂、直下 copy、系列単位、nested validated、pin-missing) |
| M2 | 宣言集合を空にする | M1 の 5 件 + 宣言の実在束縛 |
| M3 | 宣言集合に g2 を足す (過剰拒否) | 健全 g2 正例 + 宣言の実在束縛 |
| M4 | 除外を pin 由来 path だけに戻す | 直下 copy、系列単位、pin-missing |
| M5 | 除外を between_run にも適用する (過剰拒否) | 系列単位 (between_run 維持の assert) |
| M6 | 除外を bytes 検証の前に置き検証を飛ばす | SHA 不一致 fail-closed + g1 負例 4 件 (status が validated にならない) |
| M7 | pin-missing のとき除外しない | pin-missing 負例 |
| M8 | 理由 key を書かない | 理由 key を assert する 4 件 |
| M9 | 等価変異 (frozenset の literal 構文だけ変える) | 生存 (harness の SURVIVED 検出の正例) |
