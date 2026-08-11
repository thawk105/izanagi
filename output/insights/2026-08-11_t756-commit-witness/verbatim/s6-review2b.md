## 所見

### R2-1

**主張:** M14 は生存する。CLI が `--expected-commits` を受け取っても verifier へ渡さない欠陥を、新設テストは検出しない。

- 根拠: `orchestrator/verifier/cli.py:66-69`、`orchestrator/tests/test_verifier.py:759-766`、`orchestrator/tests/test_build_site_gate.py:56-80`
- 失敗経路: `expected_commits=args.expected_commits` を削除しても、CLI テストは実 commit 数 2 に対して witness 2 を指定しているため、witness を無視した旧動作でも rc=0。S2 テストは subprocess を mock して argv だけを見るため、CLI 内部の無視を検出しない。
- 深刻度: **blocker**
- 成果物影響: S2 calibration の CLI 経路で末尾欠落 trace が再び certified になり得る一方、M14 は緑のままになる。
- 処方: `g1_serial` に `--expected-commits 3 --json` を渡し、rc=1、`verdict=indeterminate`、`certified=false`、mismatch note を literal で検査する node を追加する。

### R2-2

**主張:** 「witness 無しの `result_to_dict` の byte 不変性」を固定するテストは存在せず、現行比較は self-fulfilling である。

- 根拠: `orchestrator/tests/test_verifier.py:710-740`
- 失敗経路: `baseline = result_to_dict(verify_trace_dir(trace_dir))` は期待値へ現在の production 出力を流し込んでいる。旧 key の削除・名称変更・順序変更が baseline と witnessed の両方へ入れば比較を通る。JSON bytes、literal dict、旧 commit 出力のいずれとも比較していない。
- 深刻度: **must-fix**
- 成果物影響: witness 無し API/CLI の凍結出力が変わっても、byte compatibility を保証したというテスト証拠にならない。
- 処方: witness 無し fixture の `json.dumps(..., ensure_ascii=False, sort_keys=False)` 等、実 consumer と同じ直列化 bytes を独立 literal または固定 fixture file と完全一致させる。現在値から実行時生成しない。

### R2-3

**主張:** M05 は事前登録位置のままでは注入不能であり、実装へ再照準すると複数 node が落ちて帰属も非一意になる。

- 根拠: 裁定 `s4-adjudication.md:113` は `verifier/report.py` とするが、delta の実装は `orchestrator/verifier/core.py:35-39`。`orchestrator/verifier/report.py` は当該 commit で不変。
- 失敗経路: 登録どおり report.py の `expected - observed` を置換しようとしても anchor がない。core.py を符号反転すると `test_commit_count_witness_result_is_structured`、`test_result_to_dict_commit_witness_changes_notes_without_new_keys`、`test_pipeline_tail_loss_witness_reaches_verifier` がすべて赤になる。
- 深刻度: **must-fix**
- 成果物影響: mutation harness が PARSE_ERROR/anchor mismatch になるか、期待 node 不足による MISMATCH を KILLED と誤認する。
- 処方: M05 の位置を `core.py:39` へ直し、赤くなる全 node を `expected_nodes` に列挙する。

### R2-4

**主張:** M01、M02、M03、M04、M05 は単一 node 帰属ではなく、期待 node を一つだけ登録すると MISMATCH になる。

- 根拠: `orchestrator/tests/test_verifier.py:606-766`、`orchestrator/tests/test_campaign.py:6150-6189`
- 失敗経路: 同じ witness gate を direct verifier、structured output、pipeline の複数層で検査しているため、一つの production 変異が複数 node を同時に落とす。M04 も少なくとも `:697` と `:710` の schema 非挿入 assert に当たる。
- 深刻度: **must-fix**
- 成果物影響: 変異自体は検出されても mutation ledger が MISMATCH となり、14件 KILLED の受入根拠を満たさない。
- 処方: 実測前に `expected_nodes` を完全集合へ更新する。単独帰属を要求するなら重複 assert を整理するが、正しさ回帰を削るより完全集合登録を推奨する。

## 変異14件の静的検算

| id | 生存 or kill | 帰属一意性 | 備考 |
|---|---|---|---|
| M01 | **kill** | **非一意** | `observed_commits=expected_commits` で tail-gap、file削除、structured、pipeline mismatch 等が赤。変異は意味的に有効。 |
| M02 | **kill** | **非一意** | `clean()` の witness 連言削除で mismatch 系と partial-state 系が複数赤。notes だけでなく実効 gate に当たっている。 |
| M03 | **kill** | **非一意** | 完全 trace は本当に witness=2 を渡す。`==`→`!=` で direct negative control と matching CLI が赤。他 integrity 違反による先取りなし。 |
| M04 | **kill** | **非一意** | 無条件 key 挿入は `test_commit_witness_partial_state...` と `test_result_to_dict...` が検出。ただし事前登録がいう専用 byte regression は不存在。 |
| M05 | **登録どおりは注入不能**／core 再照準なら **kill** | **非一意** | delta は report.py でなく core.py。再照準後は structured/direct/pipeline の少なくとも3 node が赤。 |
| M06 | **kill** | 一意 | 重複2行以外は正常。`test_commit_witness_parser_rejects_duplicate_stdout` が直接赤。後段 gate の先取りなし。 |
| M07 | **kill** | 一意 | 欠落を0にすると `test_commit_witness_parser_rejects_missing_stdout` が赤。mock pipeline の missing-witness control は parser を迂回するため帰属を奪わない。 |
| M08 | **kill** | 一意 | batch=1、main witness=trace数、fake verifier=green。guard 無効化時だけ `test_pipeline_nonzero_batch_commits...` が commit 側へ進んで赤。 |
| M09 | **kill** | 一意 | fixture は trace C=1、witness=2。手前の rc/empty/abort/witness/batch gate はすべて正常で、kwarg 削除時のみ pipeline control が赤。 |
| M10 | **kill** | 一意 | allowlist 恒真化で不存在 TPCC binary の subprocess 起動へ進み、直接 control が期待例外を得られず赤。mock の structured-WAL test は影響を受けない。 |
| M11 | **kill** | 一意 | preexisting guard 無効化で不存在 YCSB binary 起動へ進み、直接 control が赤。意味的 no-op ではない。 |
| M12 | **kill** | 一意 | mismatch fixture は stdout counterだけを4→5へ変え、hash/manifestを再生成済み。外側照合を削除すると failure が消え、期待 assert が赤。 |
| M13 | **kill** | 一意 | reason を集合から外すと該当 record が `other` へ移り、単一の critic control が赤。受理 gate ではなく診断感度 pin。 |
| M14 | **生存** | なし | CLI 内で flag を無視しても matching fixture は旧挙動と同じ。S2 argv testもCLI内部を実行しない。再照準必須。 |

明示すべき結果は、**生存 M14**、**登録位置不成立 M05**、**帰属非一意 M01/M02/M03/M04/M05** である。

## 恒真性と production 1行対応

完全な恒真ではないものも含め、主要な新設 node の検出対象を次のように追跡した。

- tail-gap／file削除／structured mismatch: `core.py:29` または `model.py:161`
- complete-trace negative control: `model.py:152`
- partial witness state: `model.py:148-153`
- existing integrity-red との連言: `model.py:157`
- CLI multiple-dir／負数／非整数: `cli.py:61`、`:33`、`:30`
- pipeline missing/batch guard: `pipeline.py:979-989`
- pipeline verifier 結線: `pipeline.py:995-998`
- stdout parser controls: `pipeline.py:244-246`
- `_run_trace` parser 結線: `pipeline.py:342-348`
- YCSB／空 trace_dir 前提: `pipeline.py:320-325`
- ladder mismatch: `silo_ladder_rung1.py:2852-2857`
- critic reason: `critic/digest.py:119-124`

例外は `test_cli_expected_commits_accepts_single_trace_dir` である。arg の受理自体は検査するが、肝心の `cli.py:68` を削除しても緑であり、M14 に対して恒真である。

## Negative control と fixture

Negative control は検算したが破れなかった。

- `test_commit_count_witness_accepts_complete_trace` は2件の完全 traceに実際に `expected_commits=2` を渡し、clean/certified/serializable を検査している。
- 入力は txid 0,1 の密連番、別 key への独立 write で、commit witness 以外の integrity 違反や cycle はない。
- pipeline の matching control も witness=100、batch=0 を渡し、verifier 呼出し値と COMMIT 到達を検査する。ただし verifier 本体は mock なので、過剰拒否の本証拠は direct negative control 側である。

Positive control の単一理由性も検算したが破れなかった。

- tail-gap/file削除後には txid 0 が残るため `missing_txids=0`、DSG acyclic、witness mismatch のみ。
- pipeline tail-loss fixture も rc、非空、abort count、witness存在、batch=0を満たし、commit数不一致だけが赤理由。
- ladder mismatch fixture は stdout hash と raw manifest を再束縛しており、外側 commit-count 照合だけが失敗理由になる。

## 揮発値と meta-test

揮発値は検算したが破れなかった。新設期待値に working-tree hash、実環境の絶対パス、時刻はない。`480595` は commit 済み raw evidence の固定 transaction 数であり、揮発環境値ではない。`/fixture/...` と `/not/executed/...` は意図的な合成パスである。

Meta-test は `orchestrator/tests/test_mutation_harness.py:354-362` にあり、collection に存在しない expected node を fail-closed にする。今回の新 node 名はソース上に実在する。ただし裁定 §F は説明名だけで完全な pytest node id をまだ固定していないため、M01〜M14 の spec 作成時には改名後の `test_characterization_tail_txid_gap_is_indeterminate_with_commit_witness` を含む正確な node id を登録する必要がある。

## 総括

commit 前判定は **NO-GO**。production gate 自体ではなく、テスト証拠に二つの穴がある。

1. **M14 が生存する**ため、CLI witness 結線の欠陥を検出できない。
2. **byte 不変性テストが literal bytes を固定せず self-fulfilling** である。

加えて M05 の位置を core.py へ直し、M01/M02/M03/M04/M05 の複数 failed node を完全登録すべきである。pytest は指示どおり実行しておらず、以上は commit `ee81c431` に対する静的検算である。