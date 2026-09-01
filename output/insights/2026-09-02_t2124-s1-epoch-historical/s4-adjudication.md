# [T-2124] 段 4 裁定 — S-1 epoch gate の歴史 purpose 移送

親裁定。段 3 のレンズ A (正しさ境界) / レンズ B (実効性と scope) の所見を real/refuted と
採用/不採用で確定し、plan v2 と変異事前登録を固定する。

## 所見の裁定

### 所見 A-1 / B-2 (同一): 「既存 30 件の S-1 出力を 1 byte も変えない」は成立しない

**real、採用。これは親 brief の誤りである。**

- S-1 report が読むのは `output/campaigns/` の 30 directory ではなく、freeze と `ROLES` (4 件) と
  与えられた `--output-root` から `layout_for` が決める **4 campaign** だけである
  (`s1_report.py:59`、`:942`、`s1_direct_comparison.py:457-490`)。
- `output_root` は repository 外の正規 root も受理する (`layout.py:323-367`)。
  そこに記録 commit / blob map が正しい v2 lock があれば、変更前は
  `E1-stale / current-closure-unavailable` で拒否され、変更後は受理される。**出力は変わる。**
- 再生成すれば `generated_at_head` が現 HEAD になるため、実装差分と無関係に bytes は変わる
  (`s1_report.py:1018-1021`)。

**訂正後の主張 (これだけを worklog と insight に書く):**

1. repo 内 official root の canonical S-1 campaign 4 件 (`s1-direct-develop-…d0f495bf`、
   `…floor-…b82b9229`、`…block1-…74ff9ba2`、`…block2-…9645b16a`) はいずれも v1 lock であり、
   これらに対する epoch 判定は変更前後で同じ `E0 / v1-authority-absent` 拒否である。
2. tracked な `output/reports/s1_direct_comparison/report.json` が変わらないのは
   **本 wave が producer を走らせないから**であって、再生成が byte-identical だからではない。
   受入全走から同 producer を起動する経路が無いことはレンズ A が静的に確認した
   (`tools/run_tests.py:550-572`、`test_s1_report.py` の生成テストは `tmp_path/output` へ書く、
   `test_s1_9pair_figure_provenance.py` は読んで digest 照合するだけ)。

**対応: 実装面の変更なし。新しい product test を足さない** (両レンズが scope 外と判定、DW-G05)。
親 brief の該当行を訂正し、worklog へ訂正後の主張だけを書く。

### 所見 B-1: reason envelope 全体と scope 文字列の literal 固定は scope 外

**real、採用。plan の当該部分を不採用にする。**

- 既存 node は `campaign_verifier_epochs["block1"]` を `e0.identity_scope` /
  `e0.excluded_scope` から取った値と exact dict 比較しており (`test_s1_report.py:538-544`)、
  `_rejected_epoch_projection` の field 追加・欠落・値変更は**すでに殺せる**。
  レンズ B 自身が「提案された強化は mutation power を増やしていない」と判定した。
- literal 固定は稼働中の T-733 と衝突する。T-733 は
  `CAMPAIGN_VERIFIER_EPOCH_SCOPE` を 24 path から 62 path の文言へ変えており
  (`artifact_admission.py:72`)、literal を書くと正しい S-1 実装でも本 node が落ちる。
- 依頼文の「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」に正面から当たる。

**対応: 既存 node の assert 形 (production 定数から取った値との比較) を維持する。
literal を書かない。reason envelope の exact dict 比較を新設しない。**

### 所見 B-3: 焦点走に `test_ccbench_spawn_sites.py` を含める

**real、採用。**

同 file は campaign 配下の全 Python file を AST parse し、`s1_report.py` を明示 allowlist entry と
して持つ直接 consumer である (`test_ccbench_spawn_sites.py:147`、`:324`、`:1927`)。
DW-O26 の参照関係による consumer 拡張に該当する。
親が実測: 同 file の `pytest.main([__file__, "-q"])` は `__main__` 下の自走 harness であり
スイート全体を再帰起動しない (`:2285`)。受入台帳の node 数 18。焦点走に含めても安全。

**焦点走の file 集合 (確定):**
`orchestrator/tests/test_s1_report.py`、`orchestrator/tests/test_ccbench_spawn_sites.py`。
`test_s1_9pair_figure_provenance.py` は凍結 report を読むだけで `s1_report.py` を import も
再生成もしないため含めない (レンズ B の判定を採用)。

### 所見 B (正例 assert の分類)

**real、採用。** `capture_call_count == 1` だけが「可用性 gate が外れた」の存在証明であり、
他は回帰 pin である。`epoch.campaign_verifier_epoch.startswith("E1:")` は
`CampaignVerifierEpoch` constructor 自身が E1 prefix を検証するため冗長 (`artifact_admission.py:186`)。
**冗長な 1 本は落とす。残り 4 本は正例本体として残す。**

### レンズ A が「破れなし」と確認した項目 (異論なしを確定)

1. `CERTIFIED_ACCEPTANCE` の拒否集合は (a) exact 型不正、(b) E0、(c) E1 の現行閉包取得不能の 3 群。
   局所 `state == "E0"` が残すのは (b) だけで、(c) は落ちる。
   **これは D1387 が明示的に許した緩和であり、絶対規律 2 の違反ではない。**
   (a) は中央 gate 呼出しを残すので不変。
2. `_recorded_campaign_verifier_epoch` 内の `_verify_committed_loader_binding` は v2 のみで走り、
   purpose 判定より前である。`ArtifactAdmissionError` へ変換され S-1 は
   `campaign_verifier_epoch_validation_failed` として WAL 読取前に返す。**挙動不変。**
3. exact 型検査 `_validate_read_purpose` は迂回されない。
4. 負例が実 callee を通る形は成立する。module import 時に実関数を保存し、
   test 本文の後勝ち monkeypatch から直接呼ぶ。転び方 (fixture 適用後に保存する、
   dispatcher から差し替え済み属性を再参照して再帰する、dispatcher 自身が E0 診断を合成する) は
   plan が避けている。
5. 正例の v2 helper は HEAD commit の実 blob を読み production encoder を通すため、
   記録 commit / blob 検証は実経路で走る。恒真ではない。
   親が追加実測: `s1_report.py` と `test_s1_report.py` は
   `CONTRACT_LOADER_RELATIVE_PATHS` の 24 path に**含まれない**ため、
   本 wave の未 commit 編集が記録 binding 検証を赤にすることはない。
6. `replay.py` と `s8b_oracle_report.py` は `s1_report` を import せず、間接影響なし。
   どちらも `CERTIFIED_ACCEPTANCE` を直接渡したままである (D1387 のとおり移さない)。
7. `s1_direct_comparison.py` に epoch 判断は無い。非 dry-run producer の live binding 検証は
   certified producer admission であり、歴史 report reader の purpose と矛盾しない。

## 親の provisional 裁定の確定

- **(P1) 確定。** E0 拒否は `_campaign_verifier_epoch_from_lock_bytes` の局所に置く。
  `artifact_admission` に第 3 purpose・wrapper・flag を新設しない。両レンズとも異論なし。
- **(P2) 確定。** 正例は v2 lock + `capture_contract_loader_binding` の失敗 seam で示す。
  存在証明は `capture_call_count == 1`。

## plan v2 (実装子へ渡す確定仕様)

**変更してよい file は 2 つだけ:**
`orchestrator/campaign/s1_report.py`、`orchestrator/tests/test_s1_report.py`。

1. `s1_report._campaign_verifier_epoch_from_lock_bytes` (302-310 行):
   `recorded` 取得後に `if recorded.diagnostic.state == "E0": raise CampaignVerifierEpochRejected(recorded.diagnostic)`
   を置き、中央 gate へ渡す purpose を `CampaignReadPurpose.HISTORICAL_RAW` にする。
   中央 gate の呼出し自体は残す (exact 型検査を失わないため)。
2. `test_s1_report.py` 負例: 既存 `test_non_e1_campaign_is_structured_and_wal_is_not_read` を
   実 callee 経由へ直す。module import 時 (autouse fixture 定義より前) に production 関数を
   保存し、test 本文の dispatcher から block1 の lock bytes だけを保存済み実関数へ渡す。
   **既存の assert 形は変えない。literal を書かない。reason の exact dict 比較を新設しない。**
3. `test_s1_report.py` 正例: 新規 node
   `test_v2_epoch_gate_is_historical_when_current_closure_is_unavailable`。
   共有 helper で v2 lock bytes を作り、`capture_contract_loader_binding` を
   `ContractLoaderBindingError` を投げる関数へ差し替え、
   中央 gate を production へ委譲する透明 spy で包み、実 S-1 callee を呼ぶ。
   assert は 4 本: `observed_purposes == [HISTORICAL_RAW]`、`capture_call_count == 1`、
   `epoch.state == "E1"`、`epoch.reason_code == "recorded-closure"`。
   `startswith("E1:")` は冗長なので入れない。

**新しい file・module・公開 API を作らない。`docs/` と `output/` を編集しない。**

## 変異事前登録 (DW-M01。実装前に凍結する)

| # | 変異 (位置) | 期待 | 殺す node | 単一理由性の確認 |
|---|---|---|---|---|
| M1 | 局所 E0 `raise` を削除 (`s1_report.py` の epoch gate 内) | KILLED | `test_non_e1_campaign_is_structured_and_wal_is_not_read` | v1 lock を前後で拒否する層は無い。`HISTORICAL_RAW` は E0 をそのまま返し WAL 読取へ進むため、拒否 reason の不在として赤になる |
| M2 | purpose を `CERTIFIED_ACCEPTANCE` へ戻す (同 gate) | KILLED | `test_v2_epoch_gate_is_historical_when_current_closure_is_unavailable` | v2 lock は記録 binding 検証を通るため、赤理由は現行閉包 seam の失敗 1 つに絞れる |
| M3 | 中央 gate 呼出しを削り `return recorded.diagnostic` にする (同 gate) | KILLED | 同上 (`observed_purposes` が空) | spy が呼ばれないことが唯一の赤理由 |
| M4 | E0 で `CampaignVerifierEpochRejected` 以外を投げる (同 gate) | KILLED | `test_non_e1_campaign_is_structured_and_wal_is_not_read` | `_assess_campaign` は当該型だけを rejection envelope にし、他は validation failure へ落ちる。赤理由は reason code の相違 1 つ |

**登録しない変異:** plan が挙げた「`_rejected_epoch_projection` の field を削除・差替え」は、
本 wave の変更箇所ではなく既存 node がすでに殺す。DW-M01 の単一理由性 (同じ入力を拒否する層が
前後に無い) を満たさないため事前登録から外す。

**受理集合の方向:** 本 wave は受理集合を**広げる** (可用性 gate を外す)。したがって
DW-M01 の「受理集合を縮小する wave の過剰拒否正例」は該当しない。広げすぎの検出は M1 / M4
(E0 が受理されてしまう変異) が担う。

## gate の禁止と、通る正例 (DW-S04)

**禁止 (署名で書く):**
`s1_report._campaign_verifier_epoch_from_lock_bytes(lock_bytes: bytes) -> CampaignVerifierEpoch`
は、`_recorded_campaign_verifier_epoch` が返す診断の `state` が `"E0"` のとき
`CampaignVerifierEpochRejected` を送出せずに返ってはならない。

**通る正例:** 記録 commit と 24 path blob map が記録 commit の実 blob と一致する v2 lock bytes は、
現行閉包の取得が `ContractLoaderBindingError` で失敗していても、
`state == "E1"` / `reason_code == "recorded-closure"` の診断として**返る**。
