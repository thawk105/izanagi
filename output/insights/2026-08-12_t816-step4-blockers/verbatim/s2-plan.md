## 総括

read-only 調査のみで、編集・テスト実走はしていない。

- `d706650` の Python literal は全 42 行。分類は **A=23、B=19、C=0**。
- (P1) の「承認定数 2 個」では閉じない。実値としては `silo_ladder_rung1.py`、その contract、さらに非 Python の `patches/ledger.json` も前進必須。
- parser は v1 互換分岐を作らず、`C` を exact 7-field、`E` を必須とする。件数不一致・`E` 欠落・重複は structured framing integrity、`E` txid 不一致は `ParseError` とする。
- `_tmp_trace` は変換を吸収させず、28 呼び出しを明示的 v2 化する。helper 自動変換は負例を隠すので採らない。
- 新 integrity counter を JSON/text に出すため、`report.py` と exact-schema consumer も閉じる必要がある。

## 1. pin 閉包の分類表

A は現在値との比較・checkout・identity に使われるため前進必須、B は固定 preimage・凍結成果物・自己完結 test token なので据置。

| # | file:line | 分類 | コード上の根拠・処置 |
|---:|---|:---:|---|
| 1 | `orchestrator/campaign/s8b_approved.py:29` | A | `CURRENT_PIN` と full SHA の現行契約説明。`511c953` へ。 |
| 2 | `orchestrator/campaign/s8b_approved.py:67` | A | `test_s8b_approved.py:49-64` が prefix と実 gitlink に比較。full SHA へ。 |
| 3 | `orchestrator/campaign/axis_trigger_gating.py:27` | A | 値は `pin.CURRENT_PIN`。現行 binding のコメントを更新。 |
| 4 | `orchestrator/campaign/s5_permutation_coverage.py:5` | A | 現行 positive-control driver の対象 commit 説明。 |
| 5 | `orchestrator/campaign/s5_permutation_coverage.py:22` | A | `PIN=pin.CURRENT_PIN` の現行説明。 |
| 6 | `orchestrator/campaign/s5_permutation_coverage.py:49` | A | 同じ live binding のコメント。 |
| 7 | `orchestrator/campaign/pin.py:6` | B | `028f34d→d706650` という導入履歴。残し、後ろへ `→511c953` を追記。 |
| 8 | `orchestrator/campaign/pin.py:15` | A | 「現 working-tree」の値として使う説明。`511c953` へ。 |
| 9 | `orchestrator/campaign/pin.py:20` | A | 「新 izanagi-trace commit」の現行説明。511 を主語に書き直す。 |
| 10 | `orchestrator/campaign/pin.py:28` | A | live `CURRENT_PIN` 本体。`511c953` へ。 |
| 11 | `orchestrator/campaign/s6_sort_sweep.py:77` | A | live `pin.CURRENT_PIN` のコメント。 |
| 12 | `orchestrator/campaign/backoff_sweep.py:46` | A | live `pin.CURRENT_PIN` のコメント。 |
| 13 | `orchestrator/campaign/p3_s4_loop_sort.py:28` | A | 現行 sort driver pin の説明。 |
| 14 | `orchestrator/campaign/p3_s4_loop_sort.py:97` | A | live `pin.CURRENT_PIN` のコメント。 |
| 15 | `orchestrator/campaign/p3_s4_loop_trigger_gating.py:35` | A | 現行 trigger driver と歴史的 backoff pin の対比。前者だけ更新。 |
| 16 | `orchestrator/campaign/silo_ladder_rung1.py:50` | A | `:1390,1889,2545,3564,3791-3805,3990` 等で checkout・provenance と比較する実 pin。full SHA へ。 |
| 17 | `orchestrator/campaign/silo_ladder_rung1_contract.py:543` | A | `_check_ledger_consistency():495-565` が ledger の `base_commit` と exact 比較。 |
| 18 | `orchestrator/tests/test_campaign.py:654` | B | `_campaign_id_from_historical_preimage` に渡し、`:667` で `_PRE_T343_*` と比較する歴史 preimage。 |
| 19 | `orchestrator/tests/s1_expected_goldens.py:460` | B | `:658-675` で凍結 report 内の source lines と比較。実 gitlink とは比較しない。 |
| 20 | `orchestrator/tests/test_s8b_floor_campaign.py:3244` | B | 固定 seal consumer replay 用 clone の歴史的 pin。隣接 SHA 群と一体の凍結 fixture。 |
| 21 | `orchestrator/tests/test_s1_direct_comparison.py:124` | B | synthetic `_freeze()` の固定 identity。live pin と比較しない。 |
| 22 | 同 `:342` | B | 上の fixture pin を `prepare_cell` へ渡す自己完結 test input。 |
| 23 | 同 `:353` | B | mock に渡った同じ fixture pin の期待値。 |
| 24 | 同 `:367` | B | fixture-local mismatch test の引数。 |
| 25 | 同 `:400` | B | fixture-local quarantine test の引数。 |
| 26 | 同 `:660` | B | synthetic predicate rejection の引数。 |
| 27 | 同 `:688` | B | 同上。 |
| 28 | `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1825` | A | `cfg.ccbench_commit == T.PIN` と live 値を独立固定。 |
| 29 | `orchestrator/tests/test_p3_build_authority_cli.py:86` | A | `:173,270` で S6/TRIGGER の live `PIN` と比較。 |
| 30 | `orchestrator/tests/test_s1_report.py:37` | B | synthetic freeze/report fixture の identity。 |
| 31 | `orchestrator/tests/test_campaign_lock_codec.py:73` | B | partial-v1 codec の任意 payload。repo pin と無関係。 |
| 32 | 同 `:89` | B | exact-key rejection 用の任意 payload。 |
| 33 | `orchestrator/tests/test_p3_s4_loop_sort.py:426` | A | `cfg.ccbench_commit == S.PIN` の live 独立期待値。 |
| 34 | `orchestrator/tests/test_s8a_trigger_sweep.py:62` | A | producer artifact pin。production `s8a_trigger_sweep.py:149-155` が live `PIN` と比較。 |
| 35 | 同 `:284` | B | `:267-301` の pre-T343 historical campaign-id preimage。 |
| 36 | 同 `:431` | A | `:434` で `W.PIN` と直接比較する live 独立期待値。 |
| 37 | `orchestrator/tests/test_s8b_protocol_builder.py:51` | A | `_build_golden():79-84` が承認定数と実 gitlinkから作る現行 canonical bytes。 |
| 38 | `orchestrator/tests/test_s6_sort_sweep.py:353` | A | `:356` で `W.PIN` と直接比較。 |
| 39 | `orchestrator/tests/test_t126_qualification_driver.py:100` | B | source evidence と evaluate に同じ任意 token を渡す admission fixture。 |
| 40 | 同 `:115` | B | 上と対になる入力。 |
| 41 | 同 `:190` | B | stock fixture の自己完結 token。 |
| 42 | 同 `:205` | B | 上と対になる入力。 |

C はなし。各比較先が live binding か固定 preimage かをコードから判定できた。

### pin 実装順

1. 親が `external/ccbench` gitlink を `511c9538e4e8efa54b45cda62e72389ed3b706ec` へ進める。
2. author が `pin.py:28`、`s8b_approved.py:67`、`silo_ladder_rung1.py:50`、`silo_ladder_rung1_contract.py:543` を更新する。
3. contract の実比較先である `patches/ledger.json:10` も同じ full SHA へ更新する。patch bytes が不変なら `patch_sha256` は変えない。
4. A のコメント・独立期待値を更新する。`PREVIOUS_PIN="028f34d"` と `KICKOFF_PIN*` は据置。
5. pin が campaign-id preimage に入るため、次も新しい current 値を計算して更新する。ただし歴史集合は残す。
   - `test_campaign.py:312-323,669-672`: `_PRE_T343_*` と `_T343_*` を保持し、新しい current 集合を追加。
   - `test_s8a_trigger_sweep.py:66-77,320-322`: 同様に historical d706 集合と新 current 集合を分離。
6. `test_s8b_protocol_builder.py:48-63,91-95,108-118` は新 canonical bytes から `_GOLDEN_SHA` と approved-protocol SHA を再導出する。`test_s8b_floor_campaign.py:3242-3255` の固定 seal SHA 群は変えない。

## 2. parser / integrity の file:line プラン

### `orchestrator/verifier/parse.py`

- `:4-27`
  - `C <txid> <thid> <epoch> <tid> <read_count> <write_count>` と `E <txid>` を明記。
  - txn frame を `C ... E` と定義し、R/W 件数、終端必須、P/A は非相関という不変条件を追記する。
- `:46-79`
  - `TxnFramingViolation` を追加する。字段は `kind`, `txid`, `expected_reads`, `observed_reads`, `expected_writes`, `observed_writes`。
  - `kind` は `count-mismatch`、`missing-end`、`duplicate-end` の閉じた三種。
  - `ParseIssues.framing_violations: List[TxnFramingViolation]` を追加。
- `:82-89`
  - current txn の実件数を比較して structured issue を作る小 helper を置く。read/write のどちらか一方でも違えば txn 当たり `count-mismatch` 1 件とする。
- `_parse_file():89-184`
  - current とともに宣言 read/write 数、直前に正常 close した txid を保持。
  - `C` は `len(f) == 7` を明示検査してから unpack。5-field v1 は専用 `ParseError` にし、5/7 両対応分岐は作らない。
  - 宣言件数は整数かつ非負。負数・余分な field も `ParseError`。
  - open txn 中に次の `C` が来た場合、前 txn の件数照合と `missing-end` を記録してから新 txn を開く。
  - `R/W` だけを件数対象にし、X/I/P/A は数えない。
  - `E` は exact 2-field。
    - open txid と一致: 件数照合後に close。
    - current がなく、直前 close と同じ txid: `duplicate-end` を記録して継続。
    - current がなく別 txid: orphan `E` として `ParseError`。
    - open txid と異なる: framing の帰属が曖昧なので既存 `_expect` と同型の `ParseError`。
  - 新しい `C` を開いた時点で「直前 close」状態を消す。これにより duplicate-C テストの第2 frame の正常 `E`を duplicate-E と誤認しない。
  - EOF で current が残れば件数照合と `missing-end` を記録。
  - P/A は frame 外でも従来どおり受理、X/I は open frame を必須とする。
- `_expect():186-194`
  - エラー文を「C の後かつ E の前の open txn」に合わせる。
- `parse_trace_dir():197-226`
  - txid 密連番検査は変更しない。framing と whole-txn 欠落は別の integrity 軸に保つ。

宣言件数は DSG の材料ではないので、`Txn` に保持せず `_parse_file` の局所状態に留める。

### `orchestrator/verifier/model.py`

- `Integrity:102-161`
  - `framing_violations: int = 0` を `malformed_keys` 近傍へ追加。
  - docstring に「件数/E framing が壊れた trace は辺欠落の可能性がある」と記載。
  - `clean():155-161` に `framing_violations == 0` を追加。
- `VerifyResult.verdict:197-209`
  - 分岐順は変えない。acyclic + framing 不正は `indeterminate`、既に cycle が実証された場合は従来どおり `non-serializable`。いずれも `certified=False`。

### `orchestrator/verifier/core.py`

- `:40-61` の既存 parse issue 配線に続けて、
  - `dsg.integrity.framing_violations = len(issues.framing_violations)`
  - kind 別件数と先頭 5 件の txid・expected/observed を `notes` に追加。
- `:121-132` の統計は実 R/W 行数のまま。宣言値を統計値として採用しない。

### report と downstream schema

新 counter を隠さないため、次も実装対象に含める。

- `orchestrator/verifier/report.py:58-70,103-113`
  - JSON integrity に `framing_violations`、text の UNCLEAN 行にも同 counter を追加。
- `orchestrator/campaign/silo_ladder_rung1.py:1131-1145`
  - acceptance に `framing_violations == 0` を明示。
- 同 `:1454-1460`
  - exact integrity key-set に新 field を追加。
- `orchestrator/tests/test_silo_ladder_rung1_driver.py:73-87`
  - fixture integrity に zero fieldを追加。
- `orchestrator/tests/test_t152_write_intent_coverage.py:27-49`
  - `INTEGRITY_COUNTERS` の独立 mirror に追加。future-counter zero gate のテスト対象にもする。

## 3. fixture 16 本の機械移行

対象は次の exact list に固定する。

```text
g1_serial/trace_0.log
g2_rmw_chain/trace_0.log
g3_readonly/trace_0.log
g3_readonly/trace_1.log
g4_rw_no_cycle/trace_0.log
integrity_orphan/trace_0.log
m1_commit_at_genesis/trace_0.log
m2_version_dup/trace_0.log
p1_phantom_skew/trace_0.log
p1_phantom_skew/trace_1.log
r1_write_skew/trace_0.log
r2_lost_update/trace_0.log
r2_lost_update/trace_1.log
r3_cycle3/trace_0.log
r4_mixed_cycle/trace_0.log
r5_nonlatest_transitive/trace_0.log
```

author は一度きりの converter を書いてよい。置き場所は一時的に
`orchestrator/tests/fixtures/_migrate_v2_once.py` とし、実行・検証後に削除して commit へ含めない。

converter の契約:

1. 上の 16 path と実列挙が exact 一致しなければ停止。
2. 入力 `C` は exact 5-field、既存 `E` は無し、と確認。
3. C から次の C/EOF までの、同じ txid の R/W 行だけを数える。txid を採番し直さない。
4. C に件数を追加し、次 C/EOF の直前に `E <txid>` を追加。
5. C/R/W 以外の tag があれば自動変換せず停止し、その file だけ目視処理する。
6. 変換後から count 2 個と E 行を除く逆射影が元 bytes と一致することを assertion。
7. R/W/key/version/op/行順/file 分割を一切変えない。

代表 sanity anchor:

- `r1_write_skew/trace_0.log:1-6`: txid 0/1 とも `read=1, write=1`。
- `r5_nonlatest_transitive/trace_0.log:1-12`: txid 1/2/3 は `0,1`、txid 4/50 は `1,1`。既存の非密 txid は保存する。

## 4. `test_verifier.py` の変更計画

- `_tmp_trace():197-204` は byte writer のままにする。v1→v2 自動変換、既定件数、escape flag は追加しない。
- `_tmp_trace` 28 呼び出しは `:213-592,612-664,803-806` の各 literal を明示 v2 化する。
  - X/I は C と E の間だが R/W 件数には含めない。
  - P/A は可能な箇所では E の外へ置き、非相関性を明示する。
  - duplicate-C テスト `:271-285` は各 C frame に各1個の Eを付け、dup-C だけを孤立させる。
- `:603-607` の既知偽陰性説明を更新し、FN-2 は閉鎖、FN-1 の witness 無し API だけが残るとする。
- `:609-639` の FN-1 2 テストは、txid 0 を完全な v2 frame に変えるだけで期待値を維持。
- `:642-657`
  - `test_characterization_txn_tail_loss_is_indeterminate` へ改名。
  - txid 1 の C は `read_count=1, write_count=1` を宣言し、その後を切り落として E も欠落させる。
  - `missing_txids == 0`、`serializable is True`、`framing_violations == 2`（count mismatch + missing-end）、`verdict == "indeterminate"`、`certified is False` を固定。
- `:759-798` の frozen JSON に `"framing_violations": 0` を追加する。exact bytes assertionは緩めない。

新設する負例・正対照:

- `test_v1_c_record_is_rejected`: 5-field C が `ParseError`。これだけを意図的 v1 literal として残す。
- `test_declared_read_and_write_counts_must_match`: read-only mismatch と write-only mismatch の両ケースを検査。
- `test_missing_end_is_indeterminate`: 件数は一致、Eだけ欠落。ParseErrorではなく integrity、certified false。
- `test_duplicate_end_is_indeterminate`: 正常 E の直後に同 txid の E。txn 数は増えず framing 1。
- `test_end_txid_mismatch_is_parse_error`: open txid 0 に `E 1`。
- `test_zero_read_zero_write_frame_is_valid`: `C ... 0 0` + E が clean/certified。過剰拒否防止。

pytest 非依存 runner があるため、負例は既存様式の `try/except ParseError` と `try/finally` で書く。

## 5. `test_campaign.py` の trace literal

- `:6011-6039`
  - `C 0 0 5 10 0 1`
  - W、I、`E 0` の順。I は write_count に含めない。
- `:6184-6208`
  - `C 0 0 1 1 0 1`、W、`E 0`。
  - framing が clean なので notes は従来どおり commit-witness mismatch 1件だけ。
- `:6317-6320`
  - parser へ届かない stale-file sentinel だが、意図的 v1 負例以外を残さないため `C ... 0 0\nE 0\n` へ更新。
- `:654` の historical d706 preimage は据置。ただし `:312-323,669-672` の current campaign-id golden は新 pin から再導出する。

## 6. 想定される赤と判別基準

| 赤 | 分類 | 判別基準 |
|---|---|---|
| strict parser 導入直後、16 fixture・28 `_tmp_trace`・parsed campaign literal が `malformed C` | 意図した移行途中 | v2 移行後に消えること。互換分岐で緑にしてはいけない。 |
| 旧 `txn_tail_loss_is_false_green` の certified assertion | 意図した受理集合変更 | 新期待は acyclic/indeterminate/not-certified。 |
| v1 負例が ParseError にならない | 回帰 | 5/7 field 両対応は失格。 |
| count mismatch、E欠落、E重複が certified | 回帰 | 全て `framing_violations>0`、clean false。欠落・重複を ParseErrorだけにするのも brief 契約違反。 |
| E txid mismatch が ParseError | 意図どおり | 帰属不能な framing syntax として扱う。 |
| frozen JSON、silo-ladder exact schema が新 key で赤 | 意図した report schema 変更 | exact expected setへ fieldを足す。schema検査を緩めない。 |
| `test_s8b_approved` が旧 gitlinkを報告 | 移行途中 | 同テストは `git ls-tree HEAD` を使うため、dirty gitlinkだけでは緑にならない。commit済み land tipで再走。 |
| p3/s6/s8a の pin assertion・current campaign ID が赤 | 意図した content-addressed 変更 | historical ID集合は不変、新 current 集合だけ再導出。 |
| s8b protocol golden SHA が赤 | 意図した current protocol bytes 変更 | 新 canonical bytesから再計算。固定 seal E2E の旧 SHA は変更しない。 |
| silo-ladder contract が ledger `base_commit` mismatch | pin 閉包漏れ | contract と `patches/ledger.json:10` を同時更新。 |
| 511 上で rung patch apply/contract が失敗 | 回帰 | pin を戻さず、out-of-tree patch の適用性を調査。submodule source は編集禁止。 |
| valid v2 fixture の txn/read/write/edge/cycle/anomaly が変化 | 回帰 | C metadata/E は DSG 意味論を変えてはならない。 |
| B 行の historical campaign ID、S1 freeze、seal replay、codec fixture が変化または赤 | 回帰 | sweeping replacement の兆候。B は据置。 |

## 7. 受入と変異

- 関連テストは必ず `tools/run_tests.py` 経由で、verifier、campaign、s8b approved/protocol、s6/s8a/p3、silo ladder、t152 を走らせる。
- land 対象 commit で `test_s8b_approved.py` を再走し、gitlink/full/prefix の三者一致を確認。
- 同じ tip で brief 指定の `check_trace0_preprocess_identity.py --old d706650… --new 511c9538… --cxx g++-12 --expect-paths cc/silo/transaction.cc` を実行。
- 事前登録変異は最低でも「C を5-field受理へ戻す」「count比較を無効化」「EOF missing-Eを無視」「duplicate-Eを無視」の4種。上記各負例が個別に kill することを確認する。