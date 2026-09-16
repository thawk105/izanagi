# [T-2718] 材料レポートの lock 読取りへ呼び手の purpose を通し、歴史閲覧の exact-62 / exact-24 を再拒否しない

authority: none
default_effect: no-state-change

対象 branch: `worktree-dev-wave-t2718-layer3-lock-purpose`
起点 main: `1042a1bc9` (2026-09-17)
実装 commit: `783117cf0` (Codex `role=author`)
実測日: 2026-09-17 (JST)
実行場所: Pegasus。焦点走・login probe・実 corpus probe は login node、変異本走は `run_tests.py --force-dispatch` が計算ノードへ dispatch。

## 1. 何が壊れていたか

`layer3_report._read_campaign_lock` (材料レポートの lock 読取り) が呼び手の purpose を見ず、常に通常 decoder
`decode_campaign_lock` を呼んでいた。`build_report` は 733 行で `require_admitted_campaign(purpose=HISTORICAL_RAW)`
を通した後、755 行で同じ lock を通常 decoder で読み直すため、中央の歴史閲覧 admission が受理した exact-62 / exact-24 の
lock を `campaign.lock schema が不正` で再拒否していた (T-2483 の段 3 レンズ B が指摘、entry 1568 で起票)。

D422 は「各 consumer は purpose を呼び出し方で表明する」、D1653 は「旧 grammar は HISTORICAL_RAW に限り別 decoder で読む」
と定めており、本 wave はその表明を材料レポートの読取りまで通しただけで、新しい方針は作っていない。

## 2. 実装 (commit `783117cf0`、layer3_report.py + test_layer3_report.py の 2 file・11 hunk)

- `_read_campaign_lock(path, *, purpose: CampaignReadPurpose)`: 必須 keyword、既定値なし。`path.read_text` より前に
  `type(purpose) is not CampaignReadPurpose` を TypeError にする (文字列・`str` subclass・同名同値の別 Enum を拒否、
  `CampaignReadPurpose("HISTORICAL_RAW")` は正規 member なので通る)。HISTORICAL_RAW → `decode_historical_campaign_lock`、
  それ以外の有効値 → `decode_campaign_lock`。例外変換の文面・順序は不変。返却型は 2 型の union。
- `build_report` は HISTORICAL_RAW (733 行の admission と同じ)、`build_accepted_report` は CERTIFIED_ACCEPTANCE を表明。
- WAL の knowledge provenance 検証 (`wal.knowledge_provenance_and_receipt_sha256_for_material_report`) へは decoded object
  でなく `decoded_lock.identity` (dict) を渡す。wal.py の `_decoded_campaign_lock_value` は `DecodedHistoricalCampaignLock`
  を `AttemptTopologyError` で拒否するが、`schema_version` を持たない dict は identity として扱い、63 / v1 の
  `DecodedCampaignLock` も `.identity` へ正規化されるので意味は等価 (wal.py:1733-1769、1095-1140 を親が読解、
  段 3 レンズ B (B-4) と段 6 レンズ A (RA-4) が独立に同結論)。**wal.py (enforcement source closure 内) は触っていない。**
- `decode_campaign_lock` / `decode_historical_campaign_lock` / admission の実装と受理集合は不変。
- テスト 7 関数・14 ケースを追加 (既存 155 → 162 関数、削除 0、既存 2 関数は purpose 追記のみ):
  合成 exact-62 / 24 (`test_artifact_admission` の committed closure repo + `_new_schema_campaign` + rewrite helper) を
  **実 admission** で通した `build_report` の完走 (固定 epoch は観測値の固定文字列)、同 lock に対する
  `build_accepted_report` の拒否 (例外全文 `campaign.lock schema が不正` + cause `CampaignLockCodecError`)、
  purpose 省略 / 非 exact 型の TypeError (存在しない path でも TypeError = 読取りより前)、63 / v1 の purpose 別返却型、
  authority commit への HEAD fallback、identity 渡しの knowledge 検査の等価性と拒否 parity。

## 3. 受理集合の before / after

- `build_report` (歴史閲覧用途): 変更前は v1 / 現行 63 だけ。変更後は中央の HISTORICAL_RAW admission と後段検査
  (ancestry・records/threads・WAL・calibration・schema) を満たす v1 / 63 / exact-62 / exact-24。
  解消したのは **歴史 grammar を理由とする decoder 段の再拒否だけ**で、材料レポート固有の入力条件は不変
  (段 3 A-6 / B-1、段 6 RA-5 の限定)。
- `build_accepted_report` (certified): 不変。exact-62 / 24 は通常 decoder で拒否され、v1 / 63 は従来の receipt・
  certified admission・E1 条件に従う (段 6 RA-3 の追跡表、固定入力に対して I1 成立)。

## 4. 実在 corpus での実測 (親、patch 適用後の wave worktree、probe は Codex author 作・repo 外で実行)

| 主体 | HISTORICAL_RAW 読取り | CERTIFIED_ACCEPTANCE 読取り | `build_report` の到達点 | lock/WAL bytes |
|---|---|---|---|---|
| exact-62 t2364-20260907b rr5 | 成功 (`DecodedHistoricalCampaignLock`、62 path) | `campaign.lock schema が不正` (exact key 集合) | `campaign search_config の records/threads が整数でない` | 不変 |
| exact-62 t2364-20260907b rr50 | 同上 | 同上 | 同上 | 不変 |
| exact-62 a6-20260908b rr95 | 同上 | 同上 | 同上 | 不変 |
| exact-24 t2022-20260827 rr5 | 成功 (24 path) | 同上 | 同上 | 不変 |
| 63 対照 a6-20260909b rr95 | 成功 (63 path) | 成功 (`DecodedCampaignLock`) | 同上 | 不変 |

変更前 (段 1 の親実測) は exact-62 / 24 が 755 行で `campaign.lock schema が不正` で止まっていた。変更後は 5 本すべてが
同じ到達点で止まる。**依頼文の「実在 3 本で材料レポートが生成できる」は本 wave の scope では到達しない**: これらは
paper-story 認証 campaign で、search_config に records/threads が無い (keys: aggregate, attempt_id, build_admission,
current_pin, effect, historical_pin_role, ordered_cells, ordered_genomes, protocol_schema, protocol_sha256, reps, screening,
study, verify, workload)。63 対照も同じ検査で止まるので grammar と無関係であり、読取り経路の本題を超える。段 4 で
縮小を確定し (段 3 B-2)、paper-story 形の材料レポート対応は次の一手へ新規項目として送った。
逐語: `verbatim/real-corpus-probe-script.md`、生 JSON: `verbatim/real-probe/`。

## 5. 不変条件 I5 (63 / v1 の出力不変) の実測

- tracked campaign 3 本 (v1 lock の `backoff-sweep-silo-read-heavy-sweep-6f169f90` は report 生成、他 2 本は
  `legacy-unclassified` 拒否) を変更前 / 後の code で `build_report` し、generator sha256 を除いて IDENTICAL。
- 段 6 レンズ B (RB-1、must-fix) の要求で、**同一の合成 63 campaign** (`test_layer3_report._campaign`、admitted、runs 1) を
  旧版 (1042a1bc9) と新版 (783117cf0) の layer3_report.py で report し、generator sha256 を除いて IDENTICAL
  (`verbatim/i5-63.log`)。
- 既存 persisted report との fresh 比較 (autonomous_trial_completeness) は generator sha256 で差が出る。これは本 file を
  編集した過去の全 wave と同じで、規律 7 により記録は無効化されない (段 3 B-5)。persisted 不在の campaign は fresh rebuild
  より前に `_fail` するので新しい比較経路は生まれない (autonomous_trial_completeness.py:4366-4378、段 6 RB-8 を親が閉じた)。

## 6. 段 3・段 6 の所見と裁定

逐語は `verbatim/s3-a.md`、`verbatim/s3-b.md`、`verbatim/s6-a.md`、`verbatim/s6-b.md`。段 4 裁定の全文は `verbatim/s4-ruling.md`。

| 所見 | 判定 | 対応 |
|---|---|---|
| A-1 decode した bytes と admission digest が束縛されず、755→795 行の読取り窓で差し替えられる | 本変更に帰属する回帰としては refuted、既存弱点としては real | 現行 code でも同じ窓で任意の現行 63 lock を差し込める (identity 置換は既に可能) ので、旧 grammar を加えても能力は増えない。並行書き手を仮定する検査の新設はユーザー引数 (仮想リスク向けの検査は scope 外) と DW-G05 で禁じられており実装しない。**裁定パッケージ候補**として次の一手へ新規項目 |
| A-2 P2 (identity 渡し) の等価性が未証明 | real (検証要求) | 親が wal.py を読解 (receipt helper 840/894/946 は lock を取らない、1000-1200 で lock を消費するのは `_knowledge_lock_binding` だけ)、B-4 / RA-4 が独立に同結論。拒否 parity test を追加 |
| A-3 必須 enum dispatch は D1653 の boolean 緩和でない | refuted | — |
| A-4 固定入力で certified 昇格の迂回なし | refuted | I1 の裏取り |
| A-5 P4 は 63 対照 1 本からの外挿 | real | 予測に改め、修正後に 5 本それぞれを実測 (§4) |
| A-6 / B-1 「中央 admission の受理集合と一致」は過大 | real | §3 の限定 |
| B-2 実在 3 本の完全生成は scope 内で不可能 | real | 縮小を確定、別項目へ (§4) |
| B-3 consumer 取り残しなし / B-4 identity 渡しは等価 | refuted | plan 確定 |
| B-5 completeness 比較は generator hash を除外しない | real (nit) | §5 に記録 |
| B-6 enum 境界ケース / B-7 committed repo は rewrite helper の依存でない | real (nit) | test に反映 (正例 `CampaignReadPurpose("HISTORICAL_RAW")`、負例 str subclass・別 Enum、実 admission fixture) |
| RA-1 patch は 2 file・11 hunk (probe は repo 外) | real (nit) | 本 README と worklog の記載を訂正 |
| RA-2 / RB-1 I5 の 63 成功経路が未比較 | real (RB-1 は must-fix) | §5 の同一 63 campaign 比較で閉じた |
| RA-3 certified 受理集合の拡大 | refuted | I1 成立 |
| RA-4 identity 渡しによる knowledge 検査の緩和 | refuted | — |
| RA-5 purpose 分岐・例外変換は D422 / D1653 と整合、規律 2 に違反しない | refuted | — |
| RA-6 読取り窓は既存課題 | real / 裁定パッケージ候補 | A-1 と同じ項目 |
| RB-2 固定 epoch の恒真化 | refuted | 62 は既存 literal の転記、24 は実 admission の観測値を固定 |
| RB-3 fixture は実 admission を通す | refuted | — |
| RB-4 receipt seam は検査対象の外側 | refuted | DW-O14 適合 |
| RB-5 / RB-6 / RB-7 / RB-9 | refuted (nit) | — |
| RB-8 consumer の persisted 不在分岐 | real (確認範囲) | 親が 4366-4378 行を読み閉じた (§5) |

## 7. 変異 matrix

台帳は `verbatim/mutation-spec-final.json` / `verbatim/mutation-final-ledger.json`。期待 node は login probe
(`verbatim/mutation-probe-login.json`、実装子 worktree へ注入 → pytest → 復元 → sha256 照合) で採取した完全集合。
runner は `python3 tools/run_tests.py --force-dispatch -rf orchestrator/tests/test_layer3_report.py` の 11 走
(baseline 1 + 変異 10)、harness は wave worktree (commit `783117cf0`、clean) へ直接。

**baseline = PASSED (rc=0)、負例 9/9 KILLED (期待 node 完全一致)、等価 M10 = SURVIVED (期待どおり)、MISMATCH 0、TIMEOUT 0。** 走行後に wave worktree の clean と HEAD (`783117cf0`) を親が確認した。

| id | 変異 | 期待 node 数 (login probe) |
|---|---|---|
| M01 | purpose 分岐を除去し常に通常 decoder | 8 |
| M02 | 分岐を反転 (HISTORICAL_RAW → 通常、それ以外 → 歴史) | 10 |
| M03 | 常に歴史 decoder | 6 |
| M04 | `build_accepted_report` の読取りを HISTORICAL_RAW へ | 2 |
| M05 | `build_report` の読取りを CERTIFIED_ACCEPTANCE へ | 4 |
| M06 | exact 型検査を除去 | 1 |
| M07 | WAL への受け渡しを decoded object へ戻す | 107 |
| M08 | purpose に既定値 HISTORICAL_RAW を付ける | 1 |
| M09 | 型検査を `read_text` の後へ移動 | 1 |
| M10 | 等価変異 (分岐を decoder 変数経由にする)、SURVIVED 期待 | 0 |

M07 が 107 node に効くのは、`build_report` が今は常に歴史 decoder を使うため decoded object を渡すと wal.py の型検査が
全経路で拒否するから (identity 渡しが load-bearing)。M04 は例外全文 + cause の一致 (`^campaign\.lock schema が不正$`) を
要求するため、後段の admission 拒否では緑にならない。M09 は「存在しない path でも TypeError」の 1 assert だけが検出する。

## 8. 主張の格 — 言えないこと

- 実在 3 本の**材料レポートは生成できていない** (§4)。生成できたのは合成 exact-62 / 24 campaign であり、実在 3 本は
  decoder 段を通過して 63 対照と同じ到達点で止まることまで。
- I1 (certified 受理集合不変) は**固定入力**に対する主張。755→795 行の読取り窓での差し替え (A-1) は既存の構造で、
  本 wave は新設も解消もしていない。
- 「並行編集なし」は 2026-09-17 の測定時点で、unmerged branch の三点 diff と全 worktree の dirty 走査
  (layer3_report.py / test_layer3_report.py の 2 file) に限る。
- 変異 matrix の期待 node は login node の pytest 直呼びで採取し、本走は計算ノードの `run_tests.py` 経路。
  両者の node 集合の一致は harness の KILLED 判定 (完全一致契約) が検査した。
