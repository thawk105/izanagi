## 所見

### 1. [must-fix] `known_axes_freeze` の再 pin が、下流の byte-hash 束縛を破壊している — real

`output/s1-freeze/known_axes_freeze.json` の実 SHA は更新後 `7d6790d2...` だが、下流 3 箇所は旧 bytes の `354f4b87...` を保持している。

- `output/s1-freeze/measurement_freeze.json:1297`

  > `"known_axes_freeze": { ... "sha256": "354f4b875a3c..." }`

- `output/s8b-freeze/holdout_freeze.json:9`

  > `"known_axes_freeze": { "path": "output/s1-freeze/known_axes_freeze.json", "sha256": "354f4b875a3c..." }`

- `orchestrator/campaign/t080_freeze_migration.py:45`

  > `KNOWN_AXES_RAW_SHA256 = "354f4b875a3c..."`

これは単なる未更新メタデータではない。

- `orchestrator/campaign/s1_measurement_freeze.py:403-408` は `implementation_hashes` と実 bytes を exact 比較する。
- `orchestrator/campaign/s8b_oracle_driver.py:208-211` は新しい `known_axes_freeze.json` を読み、旧 SHA と違えば明示的に拒否する。

  > `"known_axes raw bytes が legacy pin と不一致"`

さらに `known_axes_freeze` 自身も、例えば `output/s1-freeze/known_axes_freeze.json:51-53` で旧 `s8a_trigger_sweep.py` SHA を保持し、`s1_known_axes_freeze.py:844-854` が実 source bytes と exact 比較する。現 source SHA は記録値と一致しない。

したがって R1 の「生きた driver が verify するので再 pin」は逆である。既存の T-080 adapter は旧 bytes を保持することで live 経路を成立させており、top-level pin だけの再 pin はその経路を壊す。下流を再 pin すると holdout freeze・移行 receipt・floor protocol・seal の凍結閉包まで書き換えることになり、B 分類禁止と衝突する。

**成果物影響:** `s1_report` は measurement freeze を受理できず、8b oracle は `known-axes-freeze-verify` refusal で停止するため、レポートと certified 選択が生成されない。

---

### 2. [must-fix] `s8a_trigger_freq_t48.json` は TRACE=0 同一性では再 pin できず、現 consumer schemaにも不適合 — real

`orchestrator/campaign/s8a_trigger_freq.py:11-16` は、この artifact が明示的に TRACE=1 で得た値だと規定する。

> `計装 ... を TRACE=1 ビルドに重ねる`  
> `trace I/O は実行を遅くし絶対頻度・abort 率を歪める`

新 pin は TRACE=1 経路を実際に変更している。

- `external/ccbench/cc/silo/transaction.cc:602-605`

  > `read_set_.size()` / `write_set_.size()` を C 行へ追加

- 同 `:698`

  > `stream(thid_) << "E " << izanagi_txid`

特に `node-vali` のゼロ判定は構造証明ではなく経験値である。

- `orchestrator/campaign/s8a_trigger_freq.py:27-30`

  > `node-vali ≈0 は ... 経験的予想`

従って TRACE=0 preprocess 同一性はこの artifact には適用できない。出力量・タイミングが変われば、実効 reason 集合が変わる可能性がある。

加えて現在の JSON は `build_admissions` field を持たないが、live consumer は exact 1 件を要求する。

- `orchestrator/campaign/s8a_trigger_sweep.py:161-165`

  > `build_admissions は characterization build 1 件の receipt が exact に必要`

つまり pin 書換え後も `load_effective_reasons()` は静的に fail-closed となる。再測定するか、この artifact を歴史物として退役させる必要があり、機械的再 pin は成立しない。

**成果物影響:** S8a sweep は実効 reason 集合をロードできず停止する。検査を迂回した場合も candidate 集合・campaign-id・偵察レポートが誤った実効 reason 集合から導出されうる。

---

### 3. [must-fix] 現用 runbook に旧 gitlink の live preflight が残っている — real

`docs/phase3-8b-restart-runbook.md:145`:

> `P1 | git ls-tree HEAD external/ccbench | 160000 commit d706650c…`

直後の `:150` は次を命じる。

> `P1〜P3 のいずれかが期待と違えば、その段へ進まず`

`511c9538` への land 後は P1 が必ず赤になる。`docs/phase3-8b-restart-runbook.md:41,59` は日付付き実測のため歴史記録として正しいが、`:145` は「毎回の preflight」の現用期待値であり、前進漏れである。旧 floor protocolを歴史再開するなら、そのための旧 commit checkout を明記する必要がある。

**成果物影響:** runbook に従う床値再開は入口で恒常停止し、freeze v2・oracle・certified 選択へ到達しない。

## refuted

### 4. artifact の pin field 以外も変わった — refuted（byte 差について）

pin をプレースホルダへ置換した base/worktree の SHA は完全一致した。

| artifact | 正規化 SHA |
|---|---|
| `s8a_trigger_freq_t48.json` | `9b72c89f...` |
| `known_axes_freeze.json` | `76428deac...` |
| `measurement_freeze.json` | `43b87ac7...` |

従って測定値・floor・件数・時刻の直接改変はない。ただし「pin 以外を変えなかったため内部 hash が古い」という所見 1、および TRACE=1 値の再利用問題は残る。

**成果物影響:** 数値の直接改ざんはない。semantic validity は所見 1・2 の理由で失われる。

### 5. `FROZEN_MANIFEST` の SHA 誤計算・hash 検査弱体化 — refuted

実 bytes の SHA は manifest と一致した。

- `known_axes_freeze.json` = `7d6790d2...`
- `measurement_freeze.json` = `4d4fa53f...`

`orchestrator/tests/test_frozen_artifacts.py:125-136` の exact byte 比較、`:139-152` の key-set/64hex 検査も削除・正規化・例外追加されていない。

**成果物影響:** manifest 単体の改変検出力は維持される。ただし manifest 外の hash 束縛漏れが所見 1。

### 6. B 分類・歴史 campaign-id の過剰前進 — refuted

`PREVIOUS_PIN="028f34d"`、`KICKOFF_PIN*="dff0f1e..."` は不変。固定 fixture、seal replay の `test_s8b_floor_campaign.py:3718`、`output/campaigns/**`、`output/s8b-freeze/floor_protocol.json` も未変更だった。

campaign-id は `_T343_*` / `_T530_*` を保持したまま `_T816_*` を追加しており、歴史集合の上書きはない。`test_s8b_protocol_builder.py` の golden は current builder の canonical bytes であり、凍結済み floor protocol/seal とは別物なので更新は妥当。

**成果物影響:** 歴史 campaign-id・seal replay・固定 fixture の参照集合は不変。

### 7. R2 の 3 校正 JSON に live pin consumer がある — refuted

以下を basename/path で検索したが、producer と説明文以外に pin 比較 consumer はなかった。

- `s8a_trigger_gating_coverage.json`
- `s5_permutation_coverage.json`
- `s1_verify_extime.json`

`axis_trigger_gating.py` の参照も構造的ゼロの説明コメントだけである。据置は妥当。

**成果物影響:** 3 artifact を旧 pin の歴史記録として残しても現行受理集合は変わらない。

### 8. 恒久的な pin 集合・legacy reader・同一性証明 field の混入 — refuted

追加差分に pin 集合受理、版別分岐、v1 reader、同一性証明 field はない。`HISTORICAL_CCBENCH_PIN_FULL` は凍結 rung1 evidence の固定 SHA であり、現行 pin の複数受理には使われていない。

**成果物影響:** verifier の受理集合は v2 専用のまま。

### 9. TRACE=0 artifact に対する同一性推論そのもの — refuted

submodule 差分は全て字句上 `#if TRACE` 内にあり、TRACE=0 では compiler 版に依存せず除去される。したがって trace-disabled の S1 性能値に限れば、g++-12 preprocess 証拠より強く source 差分自体が同一性を支持する。

ただし TRACE=1 の `s8a_trigger_freq_t48.json` には適用不能であり、所見 2 に分離した。

**成果物影響:** trace-disabled 計測値を再測定しないこと自体では、certified 性能値は変化しない。

## 旧 pin 残存監査

生の `grep -rn "d706650" .` は rc=0。巨大な campaign JSON、Git object、`__pycache__` binary も拾うため、tracked text は `git grep -n -I` で再集計した。合計 639 token。

| 区分 | files / lines / tokens | 判定 |
|---|---:|---|
| `output/campaigns/**` | 37 / 37 / 37 | 全件、各 campaign の歴史 provenance |
| `output/env/pegasus/**` | 36 / 75 / 78 | 全件、凍結 raw bundle・job receipt・過去計測 |
| `output/insights/**` | 108 / 198 / 449 | 全件、過去 plan/review/台帳 |
| `docs/archive/**` | 17 / 31 / 32 | 全件、archive worklog |
| current docs | 5 / 15 / 15 | decisions/failures/design は歴史。runbook `:145` だけ real |
| Linux calibration | 4 / 4 / 4 | R2 の歴史 artifact |
| source/test | 10 / 21 / 21 | 下記の固定 preimage/fixture |
| その他 | 3 / 3 / 3 | frozen ledger、floor protocol、T810 prereg |

source/test の 21 行は次のとおりで、全件据置が正しい。

- `pin.py:6` — `028f34d → d706650` の導入史
- `test_campaign.py:672`、`test_s8a_trigger_sweep.py:288` — 歴史 campaign-id preimage
- `s1_expected_goldens.py:460` — 凍結 report golden
- `test_campaign_lock_codec.py:73,89` — 任意 fixture payload
- `test_s1_direct_comparison.py:124,342,353,367,400,660,688` — fixture-local identity
- `test_s1_report.py:37` — synthetic fixture
- `test_s8b_floor_campaign.py:3718` — 固定 seal replay
- `test_silo_ladder_rung1_evidence.py:76,1059` — v1 凍結証拠
- `test_t126_qualification_driver.py:100,115,190,205` — 自己完結 fixture token

`__pycache__` の binary hit は生成キャッシュで、tracked source/artifact ではない。

## 総括

- must-fix: **3**
- nit/backlog: **0**
- refuted: **6**

最も危険なのは所見 1。`known_axes_freeze` の 1-field 再 pin が、T-080 receipt・holdout freeze・measurement freeze の旧 byte SHA を同時に破り、S1 report と8b oracle の両方を fail-closed にする。R1 は撤回または凍結系列全体の再発行裁定が必要であり、現差分のまま land すべきではない。

pytest・build・実 consumer は実走していない。報告は静的検査と byte/hash 再計算のみ。