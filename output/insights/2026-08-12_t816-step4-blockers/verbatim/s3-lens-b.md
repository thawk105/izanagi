## 総括

判定は **NO-GO**。段2の `A=23 / B=19 / C=0` は成立しない。少なくとも `C` が複数あり、Python 42行と ledger だけでは pin 閉包になっていない。

現 worktree は gitlink `d706650...`、submodule 内には `511c9538...` の object は存在するが、HEAD は旧 pin のまま。`g++-12` は `/usr/bin/g++-12`、12.3.0。checker・pytest・land は未実走である。

### 分類の訂正

| 箇所 | 判定 | 根拠 |
|---|---|---|
| `silo_ladder_rung1.py:50` の `PIN` | A | live driver の現行 pin |
| `silo_ladder_rung1_contract.py:543` の `base_commit` | A | ledger 検査の live contract。`test_silo_ladder_rung1_evidence.py:1269` でも `base_commit == PIN` |
| `test_p3_build_authority_cli.py:86` | A | `:173`, `:270` で driver の現行 `PIN` と比較 |
| `patches/ledger.json:10` | A | 上記 contract の入力。ただし既発行 evidence の更新は C |
| `s1_expected_goldens.py:460` | **C** | 「pin bump 時だけ裁定つきで更新」と明記。値が変わらなくても B と無裁定で確定してはいけない |
| `test_s8b_protocol_builder.py:51,63` | **C** | live gitlink から builder を再構成し、旧 canonical bytes/SHA と比較する。更新は floor trust root の再発行 |
| `test_s8b_floor_campaign.py:3244` の seal 群 | B | 旧 pin を clone して検証する歴史 fixture。変更してはいけない |
| historical campaign ID / seal | B | 既発行 WAL・proof の参照 |
| current campaign ID / report golden | **C** | 機械的再導出は可能だが、既存 certified report の参照変更を伴う |

「承認定数2個」は literal 数と、live contract・凍結 trust root・既発行証拠の変更権限を混同している。

### 1. S1 freeze の閉包漏れ

(a) `known_axes_freeze.json:4` と `measurement_freeze.json:4` は旧 pin を保持する。前者は実 submodule HEAD と比較し、後者は `pin.CURRENT_PIN` と比較する（`s1_known_axes_freeze.py:868`, `s1_measurement_freeze.py:429`）。land 後に HEAD が `511c9538` なら、旧 bytes を据え置く限り live verify/report が赤になる。

(b) land 後の `s1_known_axes_freeze.verify()`、`s1_measurement_freeze.verify()`、S1 report 経路で再現する。実走は未確認。

(c) 据え置きなら freeze verification が拒否。再発行なら JSON bytes、`FROZEN_MANIFEST` の known/measurement SHA（`test_frozen_artifacts.py:39`）と T080 の raw hash・proof 参照が変わる。これは A ではなく C。新 commit の差分が `transaction.cc` だけなので source-lines の値変更は不要そうだが、`s1_expected_goldens.py:460` の裁定ゲートは残る。

### 2. Python 42行外の live artifact

(a) `output/env/linux-baremetal/calibration/s8a_trigger_freq_t48.json:4` は旧 short pin を持ち、`s8a_trigger_sweep.py:151` が現行 `PIN` と exact 比較する。新 pin では sweep の入力校正が拒否される。既発行 Silo result も `ccbench_pin_full` が旧値（同 JSON:24, 309）で、`silo_ladder_rung1.py:3564` が現行 pin への再束縛を要求する。

(b) 新 pin の worktree で S8a sweep または committed Silo result の current-binding validation を実行する。

(c) 再測定しなければ current selection/report は生成されず、既存 result は「現行証拠」として拒否される。再発行なら calibration SHA、binding/provenance pin、certified report の source reference が変わる。これは親の 42-hit 集計にない C/A 境界である。

### 3. S8b protocol と T080

(a) `s8b_approved.py:67`、`output/s8b-freeze/floor_protocol.json:1`、独立 golden は旧 full pin を trust root としている。`s8b_floor_campaign.py:488` は実 gitlink と approved full SHA を比較する。さらに T080 receipt は known artifact と migration-basis の旧 pin を要求する（`t080_freeze_migration.py:2064`, `:2073`）。

(b) 新 pin で `test_s8b_protocol_builder`、`t080_freeze_migration.verify_receipt()`、`freeze_protocol()` を通す。

(c) 旧 protocol/freeze/proof を B として保存すれば、current freeze は T080 refusal になる。SHA を再導出すれば protocol、holdout、selector journal、`FROZEN_MANIFEST`、T080 receipt の再発行が必要。`test_s8b_floor_campaign.py:3244` の seal replay は旧 pin のまま残すべきで、親の「current golden を更新」は無裁定では実行できない。

### 4. campaign-id は「既知」だが無害ではない

(a) `ident.py` の canonical preimage は `ccbench_commit` を含む。したがって新 campaign ID が移動すること自体は仕様だが、旧 WAL directory と certified report の ID は移動しない。`replay.py:97` が prefix discover を実装しているのは、この drift が実害だったためである。

(b) 旧 `output/campaigns` だけを残した状態で新 pin の config から ID を再計算し、直接 directory lookup する。

(c) 新 ID は未発行 directory を指し、selection が空・skip・別 report 参照になる可能性がある。`campaign_id`、`campaign_path`、`meta.ccbench_commit`、winner/source refs が変わる。historical ID は B、current golden の移動は C とすべきである。

### 5. N1 — mtime は T-167 を無効化しない

(a) push approval は `511c9538` が `d706650` を親として push された事実だけを記録する（rulings-inbox:12）。T-167 は `c9c1a9c` を採用済みと記録し、write-intent shadow は `not_integrated` のままである（worklog:577、ruling package:25）。「mtime が早いから後の push が Q1(a) を supersede した」という規範は正本に存在せず、**mtime の権限は未確認**。

(b) `511c9538` のまま、write-set drop mutation を correctness trace に通す。新 commit は shadow を含まず、T-152 の `I` 行を生成しない。

(c) `write_intent_violations=0` のまま verifier が serializable/certified を返し得る。FN-2 の同時欠落型が残り、T-152 ledger は `not_integrated` のまま。N1 は解決済みではなく C（rebase、兄弟維持、破棄の明示裁定）である。

### 6. N2 — SI の「今日の実損ゼロ」は一般化できない

(a) `pipeline.py:1024` と Silo correctness `silo_ladder_rung1.py:2864` は generic `verify_trace_dir` を呼ぶ。parser は protocol を引数に取らず、C は固定5 field、未知 tag は `ParseError`（`parse.py:102`, `:175`）。worklog:638 も SI が v1 のままであることを hard block と記録している。

(b) universal v1 rejection 後に SI v1 trace を generic verifier へ入力する。

(c) 現行 Silo YCSB の限定された実行だけなら変化がない可能性はある。しかし SI trace、直接 verifier、将来の qualification/移植経路では `trace-parse-error`、certified=false/indeterminate になり得る。SI live route が本当に皆無という主張は未確認であり、T-838 は C のまま。

### 7. qualification の key-level pin

`contract.py:481` の series identity schema は `ccbench_gitlink` を identity key に含み、`t126_driver.py:402` が HEAD の gitlink を preimage に入れ、`identity.py:123` が commit tree と exact 比較する。collector も `ccbench_gitlink` を durable receipt に保存する（`collector.py:516`）。

新 qualification は新 series/attempt ID になる。旧 receipt を新 checkout で検証すれば gitlink mismatch で拒否される。既発行 T126 receipt の checked-in durable manifest の有無は未確認。存在するなら歴史 B と current reissue C を分離し、無裁定で書き換えてはいけない。

### 8. checker / fold / land

checker の正しい対象は superproject ではなく `.../external/ccbench`（`check_trace0_preprocess_identity.py:431`）。引数は full OID、`--expect-paths cc/silo/transaction.cc`、`--cxx g++-12`。old が new の祖先であることも検査する（同:371, 373, 378）。worklog 445 の g++-11/12・bundle clone pass は記録済み実測だが、当時 gitlink は d706650 のままであり、land-tip の証明ではない。

`dev_wave_land.py:1330` は gitlink 変更を検知し、`dev_wave_land.py:2309` は submodule HEAD が target gitlink と同期していなければ postcondition failure にする。`check_docs.py` は実行されるが、`FROZEN_MANIFEST` と全 durable artifact の意味的再発行を代行しない。Codex hook が発火したとは主張しない（AGENTS.md:18）。

## 裁定パッケージ候補

1. `c9c1a9c` を失効・再実装するのか、`511c9538` を c9 の上へ積み直すのか。
2. SI を含む protocol-scoped v1 rejection の許可範囲。
3. S1/S8b/T080 の旧 freeze を歴史として保持するのか、新 pin 版を正式再発行するのか。
4. S8a calibration、Silo certified evidence、外部 T126 receipt の再測定・再発行方針。