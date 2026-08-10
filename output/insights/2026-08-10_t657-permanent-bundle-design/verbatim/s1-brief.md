# 段 1 brief — [T-657] R3 恒久機構合流の設計 wave

## scope

較正 (環境契約の活性化) と凍結 (ratified freeze の世代) の**世代交代を 1 つの束として解決する恒久
機構**の第 1 設計段パッケージを起票する。**実装差分ゼロの docs-only wave** である。

## 確定済みユーザー裁定 (2026-08-10 §58、および §54 由来)

- **R3 を採る。** pegasus 第 2 世代は `registered-inactive` (登録済み・無効) のまま維持し、恒久機構の
  設計・裁定・実装が済んでから活性化を起票し直す。R1 は現行コードが機械的に拒否する未解決課題、
  R2 は中間 commit が単独で赤になるため不採用。
- **封印 (S1 / S2) と保証境界 (G-a / G-b / G-c)、副作用境界は先送り。** 本 wave では裁定しない。
  恒久設計は「どちらに裁定されても設計が成立する」形で書き、未裁定であることを明記する。
- **旧 branch `worktree-dev-wave-t657-t660-g2-activation` は main へ merge しない。** 必要な内容は
  再導出する。
- **floor protocol 復元はユーザー確認のみの手番。** repo への書き戻しは不要
  (`output/insights/2026-08-10_t657-restore-redesign/restore-floor-protocol.md` §4)。

## brief 前の実測 (DW-S01。承認済み裁定の前提の再確認)

| # | 事実 | 取得元 |
|---|---|---|
| M1 | freeze の承認 commit A は「approval record と active pointer の**追加ちょうど 2 件**」でなければ拒否される。G ≠ A、非 merge、`AI-Agent: none` 逐語も同時に要求 | `orchestrator/campaign/s8b_ratified_freeze.py` の `_verify_pairing` / `_assert_user_commit` |
| M2 | 環境活性化の有効 head は **Python literal** `_ACTIVATION_HEAD_SERIAL: int = 1` と `_ACTIVATION_HEAD_STATE_SHA256` である。serial 前進は必ず source 編集 commit を伴う | `orchestrator/campaign/env_contract.py` |
| M3 | freeze 側の pointer 連鎖と `resolve_active_generation` は**実装済み**だが、世代 record の**現物は 0 件** (`output/s8b-freeze/` は floor_protocol / holdout_freeze / selector_predictions / selector-runs のみ) | 実ファイル列挙 |
| M4 | 環境と凍結を束ねる実装は**存在しない** (`active_bundle` / `bundle_resolver` / `active-bundle` の grep が code で 0 件) | `grep -rln --include=*.py` |
| M5 | 旧 branch は main の ancestor でなく 14 commit 先行。floor protocol は G1 のまま (`HEAD:output/s8b-freeze/floor_protocol.json` = `3acd995ae3d45f012040c5a23a089a64328201aa`、sha256 = `261cec1c…e74aac`) | `git rev-list --count` / `git rev-parse` / `sha256sum` |

**M1 ∧ M2 ⇒ 「1 commit で一体活性化」は現行機構で機械的に不成立。** これが R1 を未解決課題にした構造で
あり、恒久設計が解かねばならない中心課題である (設計パッケージ §5-5 の再実測。一次資料と一致)。

## 不変条件

- 実装差分ゼロ。凍結成果物の bytes を変えない (M5 の 2 値が wave 終了時も同一であること)。
- `registered-inactive` を壊さない。本 wave は activation record も literal も触らない。
- 先送り 3 件 (封印・保証境界・副作用境界) を親が一存で決めない。設計は択一を**開いたまま**書く。
- 旧 branch の内容は再導出のみ。cherry-pick も merge もしない。
- 「実装済み」と「使える成果物がある」を混同しない (M3)。

## 成果物の形

1. `docs/calibration-freeze-bundle-design.md` (新設、design 族 = 段完了で凍結) — 恒久機構の設計本体。
2. `docs/README.md` の地図へ 1 行登録。
3. spool fragment (worklog / decisions) — 番号は placeholder、採番は land の fold。
4. 次の一手: [T-657] を「設計起票済み・裁定待ち」へ更新し、後続 (裁定 → 実装 wave 群) を新 T で起票。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 正本置き場は**新設ファイル**とし、`freeze-permanent-design.md` (R1..R16 承認済み) は改訂
  しない。較正合流は freeze 族の上位に載る新層だから。
- **(P2)** 恒久機構の骨格は「(a) 環境活性化 head を literal から record 由来へ移し、(b) 承認を
  **bundle digest** (凍結世代 + 環境活性化候補の組) に対して行い、(c) A commit の許容 diff 集合を
  再定義する」方向。
- **(P3)** 段階分割は設計パッケージ §9 を継承し、R3 の「登録済み・無効のまま維持」を段 0 の不変条件
  として明記する。段 4 以降の完了判定は先送り 3 件の裁定に依存するため「未定義」と書く。

## 成果物影響 (DW-G05)

本 wave は certified 選択・レポート・台帳の**どの値も変えない** (実装差分ゼロ、受理集合不変)。
起票しない場合の影響は「pegasus 第 2 世代が無効のまま固定され、floor 実測が第 1 世代の較正で続き、
較正の世代交代が恒久的に着手不能なまま残る」ことである。

## gate 判定

- `DW-G01` 生死実験先行: 本 wave は機構を実装しないため非該当。M1/M2 の実測が最安の生死確認に当たる。
- `DW-G04` 条件付き機能: 実装しない。設計メモに留める。
- `DW-O09`: docs のみでも成立するため実施済み (M3/M5 の pin 閉包確認)。bytes は変えない。

## 分割方針

- 段 2: codex plan 1 本 (read-only, max)。設計の骨格と consumer 面を file:line で起草。
- 段 3: 敵対 2 本。**レンズ A** = 恒久機構の成立性 (現行コードが機械的に拒否する形を作っていないか、
  M1/M2 の一般化が過剰でないか)。**レンズ B** = 先送りの漏れと「実装したふり」層 (設計が
  producer 側だけで consumer を残していないか、先送りしたはずの裁定を暗黙に決めていないか)。
- 段 5: docs-only のため親が執筆 (実装子なし)。
- 段 6: 敵対レビュー 2 本を**書き上がった設計文書**に対して行う。
- 受入: docs のみのため免除可否を worklog へ証拠付きで記録する。
