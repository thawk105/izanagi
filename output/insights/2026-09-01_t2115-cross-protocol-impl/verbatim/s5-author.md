## 変更内容

- `genome.py`: mocc の YCSB 向け 3 軸・8 genome を登録。RWLOCK、delay、YCSB 限定性を notes に明記。共有 canonical genome parser も配置。
- `between_run_floor.py`: protocol 別 baseline、source-bound trace-hook admission、mocc 用 stem、create-only 出力を実装。silo の baseline/stem は維持。
- `screening_driver.py`: `(protocol, workload)` で floor を一意選択。不正・欠落 genome を拒否。
- `backoff_sweep.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`: 実 baseline genome の protocol を screening へ転送。
- `layer3_report.py`: WAL `build_start.payload.genome` から campaign protocol を決定し、floor キーを `(protocol, records, threads, workload)` に変更。legacy within-run は silo のみ一致させ、`protocol_match_basis=genome-absent-legacy-record` を記録。
- `layer3_schema.json`: floor result の optional `protocol` と legacy 根拠 field を追加。既存 report は引き続き valid。
- test 8 file に M1〜M4、source 正負例、create-only、parser、legacy、schema、3 caller の転送検査を追加・追随。
- 新 module、docs、output、external、hooks、tools の変更なし。commit も未実施。

## 実走結果

- 実走できた test nodeid: **なし**。pytest child は一度も起動していません。
- M1〜M4・受理集合を対象にした 20 function selector と、mocc space 3 selector を `tools/run_tests.py` へ渡しましたが、すべて `rc=16 / child_started=false`。
- 原因は sandbox から Pegasus 予約台帳を更新できず local admission が拒否され、dispatch も `qstat -Q: EACCTAUTH Unknown user-id` で失敗したためです。pytest 直起動や site/marker 偽装はしていません。
- 裁定 §5 の直接・consumer・内容走査型 15 file はすべて**実装済み・未実走**です。
- 静的検査は成功:
  - 全変更 Python file の AST parse
  - `layer3_schema.json` の JSON parse
  - `git diff --check`
  - `python3 tools/check_codex_agents.py`
  - `python3 tools/check_docs.py`
- runner が生成した未起動 dispatch directory 3 件は、その exact directory のみ除去済みです。

## 変異の単一理由性

- **M1**: valid な silo/mocc floor は parser/schema/CV を通過し、`stored_protocol == protocol` だけが選択を分けます。Layer 3 は別 consumer。単一理由性を静的確認済み。
- **M2**: admitted な mocc campaignと、shape が同一の silo/mocc floor を使用。screening は経路外で、`doc_protocol == protocol` だけが選択理由です。静的確認済み。
- **M3**: mocc は CLI、baseline map、source_digest allowlist、protocol 汎用 buildcache で受理済み。現在止めるのは trace-hook source 述語だけです。現 mocc の負例と hook を持つ合成 source の正例を対にしました。
- **M4**: `space_for()` は `SPACES` の直接 lookup のみで、別の mocc 受理層はありません。
- 対応 test はすべて実装済みですが、mutation 実走は未実施です。

## 波及

- 所有外 production caller: `SILO_SPACE` の直接 consumer、`source_digest.py`、`buildcache.py`、Layer 3 の render/accepted-report 経路。
- 共有 fixture: screening floor fixture に canonical genome を追加。Layer 3 fixture は protocol 指定時だけ canonical protocol を固定し、既定挙動は維持。
- consumer test: `test_guided.py`、`test_backoff_sweep.py`、`test_screening_opt_in.py`、`test_p2_2_site_aware.py`、各 sweep test、`test_t1416_backoff_compiler_binding.py`。
- 内容走査型: `test_s8b_floor_campaign.py`、`test_official_perf_closure.py`、`test_ccbench_spawn_sites.py`、`test_pegasus_floor_scoping.py`。
- `genome.py` と 3 caller の凍結 artifact 内 source SHA は stale になります。成果物 bytes は変更していません。
- 既存 between-run JSON 4 件は `git diff --exit-code -- output` で無変更を確認済みです。

## 受理集合

- workload 一致でも genome 欠落・非文字列・`|` 不在・空 protocol の between-run floor: **受理可能 → 拒否**。
- `space_for("mocc")`: **KeyError → 3 ブール軸・8 genome を受理**。
- 現行 pin の mocc floor: **指定不能 → source 証拠不足で build 前拒否**。
- 同 workload の silo/mocc floor: 要求 protocol の一件だけを選択。同 protocol 重複は引き続き拒否。
- Layer 3 の wrong-protocol floor、および protocol 不明・複数 campaign: report は生成し、両 floor は no-match。
- genome 無し legacy within-run: silo campaign のみ一致し、legacy 根拠を明記。mocc には不一致。
- tictoc/cicada、screening の records/threads、`registered/`、within-run producer は変更なし。
- 静的監査で意図しない受理・拒否変更は見つかっていません。

## 未完・懸念

- pytest と焦点走は実行基盤制約により未実走です。runner が local admission または compute dispatch を利用できる環境で再実走が必要です。
- 親 docs 未 land に由来する想定赤の集合は **なし**。既知の live freeze mismatch は本 wave 以前から held で、今回未実走です。
- certified mocc campaign、within-run certified calibration 閉包、tictoc/cicada は裁定どおり残余です。
- commit は作成していません。

## 総括

mocc genome、protocol 別 floor、screening、Layer 3 の接続を裁定 v2 どおり実装しました。  
M1〜M4 の kill test と受理集合 test も追加済みです。  
既存 output bytes と禁止範囲に差分はありません。  
pytest は基盤制約で未実走のため、最終受入は親側での再走が必要です。