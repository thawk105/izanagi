# 段 1 brief — [T-1250] 版を束縛した次世代の条件契約 record

## scope

`docs/phase3-8c-preregistration.md` の改訂手続きブロックへ「世代 record は判定器の版を持ち、
判定器・評価器・射影の受理意味を変える変更は版を bump して新世代を要する」を書き、**同じ commit で**
schema v2 の第 4 世代 record `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g4.json`
(`ruling_reference` = `D458`) を発行する。あわせて実 repository の tip record が版を束縛していることを
検査するテストを新設する。

## 確定済みユーザー裁定

- D458 (1)〜(5)。特に (2) 新規発行は常に v2、(3) tip が v1 なら `decider-version-unbound` で発効させない。
- D458 却下欄: `spurious-revision` に「版が違えば許す」例外を作らない。doc 改訂で保護 hash が変わるため
  例外は不要。**この wave で例外を新設してはならない。**
- 規律 2: 条件を弱める方向の変更は採らない。§5 の記入、C01〜C12 の充足、評価器の実装は scope 外。
- 実装面は Codex `role=author` (D95)。

## 不変条件

1. `activation_report_at(ROOT, HEAD)` の `effective` は **false のまま**でなければならない
   (§5 未記入・C01〜C12 は `evaluator-exception`)。この wave が変えるのは
   `decider_version_reason_code` が `decider-version-unbound` → `decider-version-match` になる 1 点だけ。
2. g1〜g3 の bytes は 1 bit も変えない。legacy v1 として読めるまま残す。
3. `DECIDER_VERSION` の値 (`s8c-decider/v1`) は bump しない。判定器・評価器・射影の受理意味を
   この wave では変えないため。
4. `prepare_revision` / `_record_document` / 判定器 3 module の**コードを変更しない**。
   変更すれば `DECIDER_VERSION` の bump 要否判断が発生し、scope が変わる。
5. doc への追記は改訂手続きブロック (保護対象 §6 配下) の中に置く。§0 と §5 の値には書かない。

## 成果物の形

- `docs/phase3-8c-preregistration.md`: 改訂手続き段落への追記 (数行)。
- `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g4.json`:
  `python3 -m orchestrator.campaign.s8c_preregistration prepare-revision --ruling-reference D458
  --revision-reason "<確定文>"` が生成する canonical JSON。**手書きしない。**
- `orchestrator/tests/test_s8c_preregistration_invariant.py`: 実 repo tip の版束縛テスト (新設)。
- 記録: worklog / decisions fragment (`docs/spool/`)。

## 純増検出力 (既存被覆の性質検索の結果)

合成 repo 側は `test_matching_decider_version_preserves_activation_conjunction` /
`test_mismatched_decider_version_is_not_effective` / `test_legacy_v1_tip_is_readable_but_not_effective` /
敵対 str 部分クラス 2 本 / digest 束縛 1 本が既に覆う。
**実 repository を対象にした版束縛の検査は 1 本も無い。** `test_repository_legacy_v1_generations_remain_readable`
は param (1,2,3) の legacy 可読性のみ。純増分は「この repo の tip が v2 であり、
`decider_version` が走っている `DECIDER_VERSION` と一致し、報告が `decider-version-match` を返す」こと。

## 判断が割れうる前提 (親の provisional 裁定であり攻撃対象)

- **(P1)** doc への追記は既存の「無記録の変更、記録のない差し戻し、世代を伴わない条件文の変更、
  世代だけを増やす空改訂は機械検査で赤になる」文の**前**に独立の 1 文として置く。文言は
  「世代 record は判定器の版 (`DECIDER_VERSION`) を持つ。判定器・評価器・射影のいずれかで
  受理集合・拒否理由・射影された判定入力の意味を変える変更は、版を bump して新世代を要する。
  整形など意味不変の変更では bump しない。」
- **(P2)** `revision_reason` は D458 の内容を 1 行で写す
  (`T-1250 (D458): 世代 record へ判定器の版を束縛する — 改訂手続きに版 bump 規範を追加し、schema v2 の第 4 世代を発行する`)。
- **(P3)** 新設テストは `test_s8c_preregistration_invariant.py` へ置く (実 repo を読む族の既存所在)。
  `test_repository_legacy_v1_generations_remain_readable` の param は (1,2,3) のまま**変えない**
  (g4 は v2 であり legacy 族ではない)。
- **(P4)** g4 生成は親が既存 CLI を実行する artifact 生産であって実装面ではない (D95 決定 (2) の
  所在・拡張子判定に該当しない)。テスト新設だけを Codex author が担う。
- **(P5)** [T-324]「事前登録の 3 件の改訂と同一 wave で land」は**充足済み (stale)**。
  束ねる対象は無い。根拠は下記実測。

## 起動時実測 (2026-08-17 00:48〜00:55 JST、base main = 5a19b8ab)

| 事実 | 実測手段 | 結果 |
|---|---|---|
| tip 世代 | `ls output/s8c-preregistration/condition-freeze/` | g1/g2/g3 の 3 件、いずれも schema v1 |
| 現行発効状態 | `python3 -m orchestrator.campaign.s8c_preregistration check` | `NOT_EFFECTIVE freeze=valid` / `decider-version-unbound` |
| D458 実装の着地 | `git grep DECIDER_VERSION` | main に `DECIDER_VERSION`・`SCHEMA_VERSION` v2・一致検査あり |
| T-324 の 3 件の改訂 | `git cherry main worktree-dev-wave-t1132-t1134-prereg-contract` 他 3 branch | 未着地 commit 0 件 (g2=D410, g3=D438 として着地済み) |
| pin 閉包 | `git grep condition-freeze -- docs output tools orchestrator` | 台帳 pin は `output/README.md:24` の記述と invariant test の `legacy_prefix` だけ。bytes を pin する manifest / trust root は無し |

## 変更面の実アンカー

| path:line | 役割 |
|---|---|
| `docs/phase3-8c-preregistration.md:244-250` | 改訂手続きブロック (保護対象、追記先) |
| `docs/phase3-8c-preregistration.md:240-242` | 凍結される範囲 (追記が保護範囲内であることの根拠) |
| `orchestrator/campaign/s8c_preregistration.py:41-52` | `FREEZE_DIR` / `FREEZE_BASENAME` / `DECIDER_VERSION` / schema 定数 |
| `orchestrator/campaign/s8c_preregistration.py:1808-1834` | `_record_document` (v2 の field 集合) |
| `orchestrator/campaign/s8c_preregistration.py:1837-1917` | `prepare_revision` (spurious-revision 判定と exclusive-create) |
| `orchestrator/campaign/s8c_preregistration.py:1727-1774` | 版一致判定と `ActivationReport` |
| `orchestrator/campaign/s8c_preregistration.py:1050-1120` | `_load_freeze_record` の v1/v2 分岐 |
| `orchestrator/tests/test_s8c_preregistration_invariant.py:126-170` | 実 repo の世代連鎖テストと legacy 可読性テスト |
| `orchestrator/tests/test_s8c_preregistration_core.py:1997-2100` | 合成 repo の版一致・不一致・敵対テスト群 |
| `output/README.md:24` | 台帳 namespace の記述 |
| `tools/check_docs.py:64` | 当 doc は `LIVING_DOCS` (凍結対象外) |

## 分割方針

実装面はテスト 1 file のみ。Codex author 1 単位で足りる。並列分割しない。
段 2 プラン 1 本、段 3 敵対 2 本 (受理集合が動くため軽量版にしない)、段 6 敵対レビュー 2 本。

## 受入・実測の環境

worktree 内で `python3 tools/run_tests.py` を相対・素の名前ちょうどで背景投入する。
焦点走は変更した test file と、production file 側の検査 (`test_s8c_preregistration_core.py`、
`test_check_docs*`) を含める。
