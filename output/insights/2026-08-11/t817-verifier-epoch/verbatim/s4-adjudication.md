# 段 4 裁定 — [T-817] verifier-policy epoch / witness なし COMMIT の再評価

裁定者 = 親 (wave manager)。入力 = 段 1 実測 (`s1/brief.md`)、段 2 プラン (`s2/plan.md`)、
段 3 敵対レンズ A (`s3/consult-a2.md`, NO-GO)、レンズ B (`s3/consult-b.md`, NO-GO)。
base = main `276ab6cc` (段 1〜3 の根拠 5 ファイルは `11978dcb..276ab6cc` で 1 行も動いていない)。

## 結論

**本 wave は実装しない (実装差分ゼロ)。** 段 5・6 を飛ばし `4→7→8→9` とする。
承認済み裁定 [T-817] (a) 条件付きを親が不採用にするのではなく、**裁定時点で未見だった新事実 4 件を
添えてユーザー再裁定へ戻す** (DW-S04)。加えてユーザーが本 wave の起動時に設定した停止条件
「識別子の設計が衝突したら止めて報告」に該当する衝突を 1 件検出した。

## 所見の real / refuted と採否

| # | レンズ | 所見 | 判定 | 親の裏取り |
|---|---|---|---|---|
| A1 | A | detached receipt は same-run を証明しない (BLOCKER) | **real・採用** | 現行 producer は WAL と stdout の双方へ同一 execution nonce を書かない (`pipeline.py:349-362`)。`trace_bin` は 16 桁の表示用 prefix で identity 検査に使うなと実装自身が明記 (`buildcache.py:37`) |
| A2 | A | 実 corpus では positive 枝に到達不能 (synthetic 専用) | **real・採用** | 段 1 実測 M2/M3 と一致。git 全史でも `output/campaigns` 配下に stdout 系 path は 0 件 |
| A3/B1 | 両方 | 三重 gate を迂回する生きた consumer が残る | **real・採用 (独立 2 例 = DW-G03 成立)** | `p2_2_report._ranked` は committed + median のみで winner を選び certified を見ない。`critic/digest.load_workload` も committed のみで throughput 降順。**いずれも実読で確認** |
| A4 | A | epoch SHA が実際の gate 実装に束縛されない | **real・採用** | enforcement closure は exact 8 path 固定 (`campaign_lock.py:29-38`)。新設 JSON も selector も入らない |
| A5 | A | 記録の形による epoch 判定は payload 偽造に弱い | **real・採用 (親 (P3) を修正)** | `wal._validate_attempt_topology` は verify_done を attempt へ結合しない |
| A6/B6 | 両方 | 凍結 bytes 不変でも「現行の成功証拠」としての読まれ方は変わらない / freeze 検証は再構築する | **real・採用 (親 M5 を訂正)** | `test_s1_known_axes_freeze.py:85` が実 repo に対し `build_document()` を走らせる。**凍結 producer は「走らせない」のではなくテストが実際に再構築している** |
| A7 | A | N1 の「571 件」は単位を混同 | **real・採用 (親 N1 を訂正)** | 除外の単位は verify 記録ではなく **committed attempt**。commit 459 件、うち P2-2 = 24 件 |
| B2 | B | 「不在 = 歴史保存」は identity 全体では成立しない | **real・採用 (親 (P2) を修正)** | 歴史 lock には `build_admission` も無く、`canonical_preimage` はそれを例外で拒否する (M8 と整合) |
| B3 | B | resume/recovery が epoch-less record を追記しうる | **real・採用** | `ensure_resumable_wal` → `repair_truncated_tail` / `recover_interrupted_attempts`、`wal.replay` は orphan abort を append しうる |
| B5 | B | `verifier_policy_sha256` は**実装済み**で namespace が衝突する | **real・採用 (段 2 プランの前提が誤り)** | `reflux_origin_ledger.py:245` が `AuthorityManifest.verifier_policy_sha256` を持ち、`:257` の exact key 集合、`:423,455,490,1854` で identity 導出に使う。**実読で確認** |
| B4 | B | artifact admission の positive 枝が実装可能な形でない (P2-2 は legacy overlay に不在) | **real・採用** | `legacy_admission_overlay_v1.json` の記載は 3 campaign で P2-2 を含まない |
| B7 | B | S8b は独立 identity 層で role 名 pin を path 検索では拾えない | **real・scope 外 → 裁定パッケージ** | F30 型。本 wave の scope 外 |
| B8 | B | guided は witness/receipt 無しの `certified` を書く | **real・scope 外 → 裁定パッケージ** | `guided.py:126-141` |

refuted はゼロ。親の (P1)(P2)(P3)(P4) はいずれも**部分的に誤り**と裁定する。

## 承認済み裁定の前提を覆した新事実 (ユーザー再裁定へ返す根拠)

- **N1'** (訂正版) ログ残存率 = **0/24** (P2-2 の committed attempt 基準) / **0/459** (全 commit 基準)。
  裁定が (a) を (b) より優先した理由「検証すれば通る記録まで捨てない」の対象集合は**空**。
- **N3** そもそも **same-run 束縛が存在しない**。WAL と stdout に共通の execution nonce が無く、
  binary の識別子も表示用 prefix しか記録されていない。よって「ログが残っていれば突き合わせる」
  機構は、**残っていたとしても健全に作れない**。作れば「別 run の counter を正証拠にする」経路を
  自作することになり、規律 2 に反する。裁定文が想定した「再実行なしで突き合わせ可能」は成立しない。
- **N4** 「現行 certified 選択」の実体は replay/guided ではない。旧 certified / 旧 fitness を読んで
  順位・winner・certified 集合を作る**生きた consumer が 8 経路以上**ある
  (`p2_2_report`、`critic/digest`、`s1_report`、`s1_known_axes_freeze`、`layer3_report`、
  `s8b_oracle_report`、`s8b_oracle_judge`、`search_baselines`)。replay/guided だけに gate を置くと、
  レポートは旧 winner を出し続け、**成果物間で受理集合が食い違う**。裁定が想定した作業量と面が違う。
- **N5** 識別子の衝突: `verifier_policy_sha256` は実装済み (Reflux authority)。
  並走 [T-804] は `spec_sha256` を manifest schema へ伝播中。build admission には `policy_sha256` が
  実在する。**ユーザーが設定した「識別子の設計が衝突したら止めて報告」に該当する。**

## 実装しない理由 (規律に基づく)

1. **再評価の半分は健全に作れない (N3)。** 突き合わせ機構を作ることは、same-run を証明できない
   証拠を正証拠に昇格させる経路を新設することであり、**規律 2 (正しさゲートを緩める変異を許さない)**
   に真正面から反する。しかも実 corpus では 1 件も発火しない = **恒真な保証** (CLAUDE.md 監査節が
   名指しする失敗型)。
2. **除外の半分は、裁定された面では意味を持たない (N4)。** replay/guided だけを止めても
   `p2_2_report` と `critic/digest` が旧 winner を再発行する (独立 2 レンズが別々に発見 = DW-G03)。
   部分実装は「謳うだけで効かない gate」を 1 個増やすだけで、成果物間の不整合を作る。
3. **epoch だけを先に入れる案も採らない。** 消費側が誰も見ない identity key は装飾であり (A4)、
   さらに歴史保存の意味論 (B2) と resume 経路 (B3) の穴が未解決。名前空間も未確定 (N5)。

## scope 外の real 所見 (裁定パッケージへ)

B7 (S8b の独立 identity 層と role 名 pin)、B8 (guided の certified WAL の位置づけ)、
および N4 が挙げた 8 consumer の扱い。

## 変異事前登録

**免除。** 実装差分ゼロの「実装しない」裁定のため、変異 matrix は DW-S04 の免除に該当する。

## 受入の要否

実装差分ゼロ・docs のみ。受入全走の要否は段 7 で証拠付きで判定し worklog へ記録する
(`record-acceptance-exemption-evidence` の規律)。
