# 段 1 brief — [T-2076] D1271 + [T-493] sort comparator 権威集合

## scope

1. **[T-2076] / D1271:** sort SWO oracle が親へ報告する関係行列を、候補 comparator から不可視な
   親側の基準と突き合わせて検証する最小実装を入れる。閉じる対象は
   `SORT_SWO_GUARANTEE_BOUNDARY` の
   `does-not-guarantee[reported-relation-matrix-is-comparator-true-relation]`。
2. **[T-493]:** `sort_best.comparator` に閉じた権威集合を入れ、`s1_known_axes_freeze` の
   生成・検証層が権威集合外の comparator と name/comparator 不整合を fail-closed で拒否する。
3. 1 と 2 は D1271 の指示どおり **1 つの変更単位** (1 wave・1 受入枠) で行う。

## 確定済みユーザー裁定 (前提として動かさない)

- D1271: 基準を候補から不可視な親側へ移し、そこで比較する。「限界として明記するだけ」は却下済み。
- D1271: T-493 と同じ変更単位で行う。別々にすると受入枠を 2 回使う。
- ユーザー指示: 基準が不可視であることの**負例**(候補側から基準を書き換えようとしたら witness が
  残る) を対で入れる。
- ユーザー指示: 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- D95: 実装面は Codex `role=author` が書く。親は直接編集しない。

## 覆った前提 (段 4 で再裁定する新事実)

- **(N1)** D1271 / D696 が名指しする `trusted_snapshot` / `snapshot_corpus()` は現行実装に存在しない。
  T-1574 の `36baa7a7b` (2026-08-25、D1271 起票日より前) が corpus を read-only arena + seccomp で
  守る方式へ置換済み。実装側 grep hit 0 件、`test_sort_swo_oracle.py` は
  `assert "trusted_snapshot" not in source` という否定 assert を持つ。
- **(N2)** しかし D825 が「保証しないもの」として exact field に固定した残余
  (`active_write_set` / `active_order` / `sort_called` / `relation[]` が候補と同じ書込み可能領域に残る)
  は生きており、`_TU_PREFIX` にも `// Known residual` として明記されている。D1271 が却下した
  「現状維持のうえ限界として明記する」はこの状態そのものである。したがって D1271 の意図は
  この残余を閉じることであり、裁定は生きていると読む。**この読み替えの当否は段 3 の攻撃対象。**
- **(N3)** D825 は閉じる方法を「検証済み IR + trusted interpreter」か「broker の ptrace 相当」の
  2 択と書いたが、第 3 の経路 (比較のたびに harness が実際に受け取った要素の同一性 witness を
  観測 fd へ出し、親が自分の canonical corpus 模型と突き合わせる) を検討していない。
  出た bytes は候補が取り消せず、基準は Python 側にしか無い。(P1) として下記に置く。

## 不変条件

- 絶対規律 2 を緩めない。anomaly / 不整合を検出した候補は即 reject。受理集合を広げる変更を入れない。
- 隠蔽 (候補 TU から識別子名を消す) を防壁として数えない (D696 / D766 / D825)。
- `output/s1-freeze/known_axes_freeze.json` の bytes を変えない。T-493 は**検証層の追加**であり
  凍結物の再発行ではない (T-492 と同じ扱い)。凍結済み comparator 3 件が権威集合の要素であることは
  親が実測済み: balanced=`sp_dd`=`_two("rcdptr_", False, False)`、write-heavy / read-heavy=`sk_ad`=
  `_two("key_", True, False)`。
- `ORACLE_CONTRACT_ID` は機械導出であり、TU・保証境界・protocol version の変更で必ず変わる。
  consumer の exact 一致検査 (4 箇所以上) を同じ変更単位で揃える。
- 正しさ検査器を未定義動作の上に立てない (D825)。`munmap` / 封印は採らない。

## 成果物の形

- 親側基準との突き合わせを行う実装 + 構造化された reject/finding (規律 3: なぜ壊れたかを返す)。
- `sort_best.comparator` の閉じた権威集合 module と、`s1_known_axes_freeze` 側の要求。
- 正例: 現行の正当な候補 (`sk_ad` 等) と凍結済み 3 entry が従来どおり通ること。
- 負例: 候補 comparator が基準側 (`active_write_set` 等) を書き換えたときに witness が残り
  reject されること。権威集合側の負例は「集合外の comparator 文字列」と
  「name と comparator の組が食い違う entry」。

## 変更面の実アンカー (worktree 相対 path:line、着手時点)

| # | anchor | 役割 |
|---|---|---|
| A1 | `orchestrator/campaign/sort_swo_oracle.py:89` `SORT_SWO_GUARANTEE_BOUNDARY` | 閉じる対象の非保証 field |
| A2 | 同 `:764` `_TU_PREFIX` / `:900` 前後 `// Known residual` と file-scope static 群 | 残余の実体 |
| A3 | 同 `:930` 付近 `template <class Compare> void sort(...)` と `emit_bool` | witness を出す層 |
| A4 | 同 `:47-51` version 定数群、`:2546-2582` contract components / `ORACLE_CONTRACT_ID` | 契約 ID 導出 |
| A5 | 同 `:53` `_MAGIC` / `:56` `_HEADER` / `:57` `_RECORD_SIZE` / `:1375` `_broker_order` / `:2122` `_run_matrix` | 親側 wire と既存の親側基準 (order 置換は既に親が持つ) |
| A6 | `orchestrator/campaign/s6_sort_sweep.py:109-170` `_one/_mk/_single/_two/CANDIDATES/STOCK_NAME/candidate_names` | 権威集合の機械導出元 (15 候補 + stock) |
| A7 | `orchestrator/campaign/s1_known_axes_freeze.py:483` `_sort_entry` / `:730` entry 組立 | 現状 comparator を型検査だけで素通しする箇所 |
| A8 | `orchestrator/campaign/trigger_gate_binding.py` 全体 / `s1_known_axes_freeze.py:86-175` | 模倣すべき trigger 軸の閉集合と name↔predicate 束縛の実装形 |
| A9 | `orchestrator/campaign/s8b_sort_swo_receipt.py:119-197`, `orchestrator/critic/digest.py:208-268,977-1031`, `orchestrator/campaign/s1_direct_comparison.py:697`, `orchestrator/campaign/p3_s4_loop_sort.py:194` | contract ID / guarantee boundary の exact 一致 consumer |
| A10 | `orchestrator/tests/test_sort_swo_oracle.py`, `test_s1_known_axes_freeze*`, `orchestrator/tests/s8b_floor_evidence_fixture.py:17-46` | 期待値と fixture の追随先 |
| A11 | `orchestrator/tests/test_frozen_artifacts.py:41` `FROZEN_MANIFEST` | 凍結 bytes 不変の関門 |

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-a)** 実装形は「比較のたびに harness が実際に読んだ 2 要素の内容由来の同一性 witness を
  観測 fd へ emit し、親が自分の canonical corpus 模型 (`_CORPUS_MANIFEST` /
  `_canonical_corpus_serialization`) と `_broker_order` から導く期待列と完全一致で照合する」。
  一致しなければ reject。
- **(P1-b)** 候補が書き換えうる基準は実質 `active_write_set` の指す先だけで、`active_order` と
  `relation[]` は報告経路に効かない (relation は書かれるだけで読まれない)。したがって witness は
  `active_write_set` 経由の要素同一性で足りる。
- **(P1-c)** 保証境界の文言を「保証する」側へ移し、`CONTRACT_VERSION` / `PROTOCOL_VERSION` を
  上げる。`critic/digest.py` へ legacy-v4 世代を足すかは、現行 v4 契約 ID を持つ**生きた**成果物が
  実在するかで決める (親の全件検索では歴史的 insight 1 件のみ、生きた consumer 無し)。
- **(P1-d)** 権威集合は `s6_sort_sweep.CANDIDATES` から機械導出し、独立に literal を再掲しない。
  名前重複・実装重複を起動時に fail-closed で検査する (`_build_trigger_name_mask_index` と同形)。

## DW-G05 成果物影響 (放置したときに成果物がどう変わるか)

- 1 を放置すると、certified 選択の材料である SWO PASS 受領証が「候補が申告した関係行列」に
  基づいたままになる。候補が基準を差し替えれば、実 corpus 上は SWO でない comparator が
  PASS 受領証を得て床値 campaign の受理集合に入る。受理集合が広がる方向の穴である。
- 2 を放置すると、`known_axes_freeze` の `sort_best.comparator` は campaign provenance が返した
  任意文字列を通す。凍結物の値そのものが権威集合外へ drift しても検出できない。

## 分割方針

- 実装面があるので軽量版ではない。段 2 plan 1 本、段 3 敵対相談 2 本 (レンズを分ける)、
  段 5 実装子は編集 path 所有で 2 単位に分けうる (oracle 側 / 権威集合側)。ただし contract ID と
  fixture が両者に跨るため、段 4 で一枚岩に寄せる可能性を残す。段 6 敵対レビュー 2 本 + fix。
- 変異事前登録は段 4 (`DW-M01`)。負例 2 系統 (基準書換え witness、権威集合外 comparator) は
  それぞれ単一理由性をコードで確認してから登録する。

## 受入・実測環境

- 受入全走は `tools/dev_wave_wait.py acceptance --lease-optional` 経由。所在は worklog、
  機体固有情報は runbook を正本とする。新規の性能計測・campaign 実走は行わない。
- `test_sort_swo_oracle.py` は D669 により受入全走から恒久除外されている。したがって oracle 側の
  緑は焦点走で親が実測し、除外の事実を記録に書く。
