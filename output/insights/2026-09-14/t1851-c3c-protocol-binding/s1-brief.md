# 段 1 brief — [T-1851] / [T-1946] / [T-2107] 単位 C3c (resolved protocol 束縛の修正)

branch `worktree-dev-wave-t1851-c3c-protocol-binding`、base `f5423e2fff3adb164731963ca33e82ed08d08c4d`
(= 着手直前の local main、clean、submodule 3 件再帰初期化済み、開始 gate rc=0)。

## 研究前進

official 床値が 1 度も採れていない唯一の code blocker を外す。放置すると freeze v2 の floor/budget が
埋まらず oracle gate は 2 件拒否を返し続ける (C3b `ruling-package.md` 裁定 1 の成果物影響)。
**完了判定:** 公開 production 経路のテストで (i) resolver が versioned protocol を選ぶ構成で
launch certificate が通る正例、(ii) resolved protocol の bytes を変えた負例が同じ強度で拒否される、
(iii) 既存の legacy-resolution 構成が従来どおり通る、の 3 つを実走で示す。
**本 wave は official 床値の投入を行わない** (依頼の明示)。実値域の供給は後続の測定 wave。

## 生死確認 (DW-G01) — 済み

2026-09-09 に sanctioned 経路で official campaign `988501.nqsv` を実投入し、停止点と入力実値を実測済み
(`output/insights/2026-09-09/t1851-unit-c3b-floor-range/README.md`)。新しい probe や driver は作らない。

## 確定済みユーザー裁定

- **D1936 項 11:** 案 a を採る。resolved protocol の canonical hash を legacy 固定 path へ比較する
  取り違えを直す。裁定 2 の二重比較も同じ面として扱うが、**hold 機構全体の効力を証明したとは書かない。**
  legacy の再封印・hold の射程拡大・全解除は採らない。
- **D1936 項 12:** 同一凍結世代の再走機構は拡張しない (`campaign_run_id` の slot 追加も新凍結世代発行もしない)。
- **D1936 項 13:** 本番領域の fixture 残存の追跡・削除・新 guard は床値取得より先に置かない。
- **D1936 項 14:** 項 11 修正後に C3c で実値を取り、その後 D2 へ進む (D2 は 2026-09-10 に land 済み)。
- **D1936 項 15:** 残る一括追認は統合時まで待つ。FORMULA_ID は D1909 で既決なので再裁定しない。
- **本依頼:** 3 件を同一 land 単位。新規 official 床値本走なし。FORMULA_ID 維持。
  被覆の全単射照合は B2 (inspector) の scope なので触らない。規律 2 を緩めない。Codex author = D95。
  仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

## 変更面の実アンカー表 (2026-09-14 に親が main f5423e2ff 上で実測)

| アンカー | 現状 |
|---|---|
| `orchestrator/campaign/s8b_floor_campaign.py:185` | `_FLOOR_PROTOCOL_REL = "output/s8b-freeze/floor_protocol.json"` (legacy anchor) |
| 同 `:186` | `_FLOOR_PROTOCOLS_REL = "output/s8b-freeze/floor-protocols"` (versioned namespace) |
| 同 `:312-316` | `_PREFLIGHT_FIXED_FILES` = legacy protocol / holdout_freeze / selector_predictions / journal の 4 件 |
| 同 `:324` | `_CHAIN_RECORD_PATTERNS` に `floor-protocols/[0-9a-f]{64}--[0-9a-f]{40}\.json` を含む |
| 同 `:834-838` | `_derived_reseal_protocol_relpath()` が組から versioned path を一意導出 |
| 同 `:1032-1060` | `resolve_current_floor_protocol()` → `IndexedFloorProtocol.path` (legacy か versioned) |
| 同 `:5201-5204` | `_floor_preflight_freeze_allowlist(root, *, freeze_path, freeze_sha256, protocol_sha256)` — resolved path を受け取らない |
| 同 `:5219-5231` | `_PREFLIGHT_FIXED_FILES` を capture するループ (versioned は capture 対象外) |
| 同 `:5242-5248` | 凍結 hold の分岐。保留されるのは `elif sha256(captured[legacy]) != protocol_sha256` 側だけ |
| 同 `:5274-5280` | `historical_protocol` (pre_oracle_head の legacy blob) を `captured[legacy]` と比較 |
| 同 `:5285-5292` | journal `expected_header.protocol_sha256` = historical **legacy** hash |
| 同 `:5313-5318` | **欠陥 1**: `allowlist[_FLOOR_PROTOCOL_REL] = protocol_sha256` (resolved の hash を legacy path へ) |
| 同 `:5456-5462` | `bounded_actual` の分類。versioned は `chain_records` 側へ落ちる |
| 同 `:5464-5470` | `bounded_actual != set(freeze_allowlist)` の exact 一致要求 |
| 同 `:5471-5482` | **欠陥 2 の片側**: `launch certificate: freeze allowlist hash 不一致` を無条件に出す |
| 同 `:5517-5527` | `clean_scan_digest` は `freeze_allowlist ∪ chain_records` の和で digest を作る |
| 同 `:7136-7171` | `_require_supplied_protocol_authority()` が resolver 記録へ束縛済み — **resolved path は官製経路で既に手元にある** |
| 同 `:7504-7524` | 唯一の production 呼び手 (`mode == "official"`) |
| `orchestrator/tests/test_s8b_floor_campaign.py:11550-11700` | 既存の preflight allowlist テスト群 |
| `orchestrator/tests/test_frozen_artifacts.py:48,97,123` | legacy protocol の bytes を sha256 `261cec1c…` で pin (23 件 exact keyset) |
| `orchestrator/campaign/freeze_verification_hold.py:20-21` | 保留中 check_id 2 件 (`protocol-bytes-expected-pin` / `sealed-protocol-ccbench-pin-current-head`) |

**実測した gate 入力の実値 (DW-O13):** resolver が返す実 path は
`output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json`、
その bytes sha256 = `2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a`、
legacy bytes sha256 = `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac`。
2 file の差は `ccbench_pin` 1 field のみ (legacy `d706650c…` / versioned `511c9538…`)。
現行 `external/ccbench` gitlink は `511c9538e4e8efa54b45cda62e72389ed3b706ec` で versioned 側と一致する。
両 file は repo に実在し tracked。したがって**要求する値は到達可能**である。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1) C3c の scope。** C3c の一次定義 (`…/t1851-unit-c3b-floor-range/next-unit-d2.md` 末尾) は
  「項 11 解決後に official を再走し attempt registry 側 gate の実値域を供給する」である。依頼は
  「C3c の実装」かつ「新規 official 床値本走は含めず」と明示するので、**本 wave は実装のみ**とし、
  実測 (投入) は後続 wave へ残すと裁定する。受け皿 (実値域 receipt の producer 新設) は作らない —
  C3b は receipt を docs で供給しており、新設は DW-G05 の「要求外の追加実装」に当たる。
- **(P2) 修正の形。** `allowlist` の legacy entry を resolved path へ**置換**するか、legacy entry を
  自身の bytes hash へ直して resolved entry を**追加**するか。親の provisional 裁定は**追加案**。
  理由: `_assert_freeze_allowlist` は `bounded_actual == set(freeze_allowlist)` を exact に要求し、
  legacy は `_PREFLIGHT_FIXED_FILES` にあるので `bounded_actual` から外せない。置換は
  `preflight scope と allowlist が不一致` を新たに踏む。追加案は検査を 1 本増やすだけなので
  受理集合を広げない。resolved == legacy のときは 1 entry に畳む必要がある。
- **(P3) 二重比較の扱い。** 項 11 を直すと両検査が同じ正しい対象を見るので実害は消えるが、
  hold は依然として無条件検査に影ることになる。親の裁定は**そう明記するだけ**とし、
  hold の射程拡大 (裁定 2 案 b) も解除 (案 c) も採らない。
- **(P4) journal `expected_header.protocol_sha256`。** これは pre_oracle_head 時点の legacy hash であり
  resolved hash ではない。親の provisional 裁定は**現状維持** (selector journal の同一性は
  pre_oracle 時点の系譜に束縛されるべきで、実行時 resolution とは別の量)。

## 不変条件

1. **凍結 23 件の bytes を 1 bit も変えない。** legacy protocol も versioned protocol も書き換えない。
   `FROZEN_MANIFEST` / `FROZEN_KEYSET_PROVISIONAL_82803D6D` / `HELD_FROZEN_MANIFEST_KEYS` は不変。
2. **受理集合を広げない (規律 2)。** 同じ強度の検査を正しい対象へ向けるだけ。緩める向きの変異は採らない。
3. `freeze_verification_hold.HELD` と `HELD_CHECK_IDS` (21 件 / sha256 pin) を変えない。解除はユーザー明示のみ。
4. `FORMULA_ID` (`s8b-floor-stats/v2`) を維持する。result schema の既定 (v4) も変えない。
5. B2 (inspector) の被覆全単射照合、attempt registry の slot 一意性、fixture 残存の追跡に触らない。
6. `launch_floor_attempt()` / `launch_probed_floor_attempt()` の既存 production 入口の署名と挙動を変えない。
7. official campaign を投入しない。Pegasus へ qsub しない。

## 成果物の形

- `orchestrator/campaign/s8b_floor_campaign.py` の preflight 1 面の修正 (Codex author = D95)。
- 公開 production 経路を通る正例 1 件・負例 2 件以上のテスト (`orchestrator/tests/test_s8b_floor_campaign.py`)。
- `output/insights/2026-09-14/t1851-c3c-protocol-binding/` に brief・plan・敵対相談・裁定・レビュー・
  変異台帳・逐語を収録 (D1941 の日付配下配置)。
- `docs/spool/` へ worklog / decisions fragment (canonical 3 台帳は段 9 の land が追記)。

## 並列分割方針

変更面は 1 file 1 関数に閉じるので実装子は 1 本。段 2 plan 1 本、段 3 敵対 2 本 (レンズ A = 受理集合と
規律 2 への攻撃、レンズ B = 閉包と consumer 取り残し)、段 6 レビュー 2 本 + fix 1 本。
