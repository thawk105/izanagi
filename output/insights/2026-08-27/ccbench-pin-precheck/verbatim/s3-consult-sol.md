## 所見一覧

### 1

- 対象: D16 / D18 / D20、`patches/ss2pl-lock-protocol-study.patch:1-56,1327-1345,2694-2705`
- 内容: `master` の merge 自体は D14 の TRACE 契約を保つが、現行の SS2PL study patch は merge 後の基底へ適用できない。親の「競合ゼロ」は submodule merge だけに限定され、実際の SS2PL 材料経路まで一般化できない。
- 深刻度: blocker
- 根拠:
  - 実体確認: merge 後は `cc/ss2pl/CMakeLists.txt:1-15` が既に `CCBENCH_SS2PL_DLR` と `WORKLOADS ycsb bomb tpcc` を持つ。一方 patch は旧 `WORKLOADS bomb tpcc` を置換し、同じ DLR/YCSB 面を追加する。
  - 実体確認: `git apply --check` は現行 pin では成功したが、親の merge probe では次で失敗した。

    > `error: patch failed: cc/ss2pl/CMakeLists.txt:1`  
    > `error: patch failed: cc/ss2pl/transaction.cc:10`  
    > `error: cc/ss2pl/ycsb_ss2pl.cc: already exists in working directory`

  - 実体確認: upstream 側は `cc/ss2pl/transaction.cc:160-164,343-345` で `ERROR_LOCK_FAILED` を返し、`:178-184` で DLR0 timeout を実装する。patch の再基底でこれらを落とすと #121/#122 の便益を再び失う。
  - 推論: 推奨経路は「merge して re-pin」だけでは不足し、study patch を D18/D20 の inert 境界を保って再基底し、upstream の timeout・failure propagation を保持したことの独立検査が条件になる。

### 2

- 対象: `orchestrator/campaign/build_admission.py:242-257,458-477`、`orchestrator/campaign/artifact_admission.py:578-581,1042-1049`、`orchestrator/campaign/campaign_lock.py:29-55`
- 内容: E1 epoch が変わらなくても、`pin.CURRENT_PIN` 更新は build-admission policy を変え、既存 post-policy campaign の受理を別経路で拒否する。P4 は E1-stale の狭い意味では正しいが、受理集合不変の根拠にはならない。
- 深刻度: blocker
- 根拠:
  - 実体確認: policy preimage は path 名に `ccbench` を持たない key で pin を束縛する。

    > `"repo_stock_pin": CURRENT_PIN`

  - 実体確認: `BuildAdmissionPolicy` はこの preimage 全体の SHA-256 を `sha256` とする。
  - 実体確認: artifact admission は既存 lock に焼かれた policy と現行 policy を exact 比較する。

    > `if search["build_admission"] != policy.as_preimage():`  
    > `raise ArtifactAdmissionError("post-policy campaign lock admission policy differs")`

  - 実体確認: exact 25 path には `build_admission.py` も `pin.py` も含まれない。したがってこの挙動変更は `recorded-current-closure-mismatch` を起こさない。
  - 実体確認: E0 は `artifact_admission.py:795-804` の authority 欠落分類で、pin bump 前後とも certified acceptance では既に拒否される。`current-closure-unavailable` も exact 25 path の読取・HEAD blob 不一致だけで、gitlink/pin 更新単独では発火しない。
  - 推論: 旧 policy を持つ post-policy v2 campaign は、E1 表示値が同じまま admission だけ失う。これはユーザー裁定パッケージに「既存 campaign への影響 0」として載せられない。

### 3

- 対象: D444 / D471 / D491、`orchestrator/campaign/s8b_floor_contract.py:52-64,583-600`、`orchestrator/campaign/s8b_floor_campaign.py:1095-1139,1237-1239,1267-1297`
- 内容: P2 の「再計測不要」は支持できるが、`s8b_approved.CCBENCH_FULL_SHA` を reseal の事前条件とした親の説明は誤り。引用箇所は別 API の `build_protocol_document()` である。
- 深刻度: major
- 根拠:
  - 実体確認: D444 は可変 field を `contract_sha256` / `ccbench_pin` の2件、不変 field を16件と明記し、承認定数からの再導出を禁じる。
  - 実体確認: `_reseal_protocol_at_root()` は固定 HEAD の gitlinkを直接読む。

    > `target_pin = _ccbench_gitlink(root, head_commit)`  
    > `successor = copy.deepcopy(anchor.document)`  
    > `successor["contract_sha256"] = ...`  
    > `successor["ccbench_pin"] = ...`

  - 実体確認: `reseal_protocol()` はこの private core を呼ぶだけで、`s8b_approved` を参照しない。
  - 実体確認: `CCBENCH_FULL_SHA` 照合は `build_protocol_document():1280-1285` にだけあり、人間用の初期 builder 経路である。
  - 実体確認: 16 field には測定由来の `wired_min_rel_floor` もあるが、D444 はそれを人間専有・byte-exact 継承と明示している。現契約上、pin bump を理由に再取得する field はない。
  - 推論: 正しい順序は「gitlink と live 定数・golden 等を同一 commit で更新 → committed HEAD を対象に reseal → 新 protocol を追加 commit」。issuer は HEAD の gitlinkしか使えないため、2 commit 間では D491 resolver が `E=0` となる一時的な admission 停止を避けられない。

### 4

- 対象: `orchestrator/campaign/freeze_verification_hold.py:16-38`
- 内容: P3 の「CCBench pin 照合9件」という分類は不正確。production で CCBench current pin を直接比較するのは5件、テスト helperのみが1件、protocol SHA の間接影響が1件で、残る14件は別対象である。
- 深刻度: major
- 根拠: 各 ID の独立判定は次のとおり。

| # | check ID | pin bump との関係 |
|---:|---|---|
| 1 | `frozen-artifacts.manifest-bytes` | 無関係。既存4 artifact bytes の manifest。versioned protocol は D471 により非登録。 |
| 2 | `s1-known-axes.ccbench-submodule-head-pin` | 直接・production。artifact pin と submodule HEAD 比較。 |
| 3 | `s1-measurement.recorded-pin-current-pin` | 直接・production。記録 pin と `pin.CURRENT_PIN` 比較。 |
| 4 | `s8b-floor.protocol-bytes-expected-pin` | 間接。CCBench pin ではなく、captured legacy protocol SHA と選択 protocol SHA の比較。 |
| 5 | `s8b-floor.sealed-protocol-ccbench-pin-current-head` | 直接だがテスト helper のみ。production call site はない。 |
| 6 | `s8b-holdout.design_source-implementation-bytes` | 無関係。設計文書 bytes。 |
| 7 | `s8b-holdout.frozen-head-current-head` | CCBench 固有でない。`current_head` 指定時の commit equality、通常経路は ancestor 検査。 |
| 8 | `s8b-holdout.generator-implementation-bytes` | 無関係。generator source bytes。 |
| 9 | `s8b-holdout.known_axes_freeze-implementation-bytes` | 無関係。known-axes artifact bytes。 |
| 10 | `s8b-oracle.known-axes-live-bytes` | artifact を不変にする限り無関係。live raw SHA 比較。 |
| 11 | `s8b-oracle.known-axes-recorded-pin` | CCBench pin ではない。holdout 内の known-axes SHA pin。 |
| 12 | `t080.historical-holdout-artifact-bytes` | 無関係。`H_mig` の歴史 blob。 |
| 13 | `t080.historical-known-axes-artifact-bytes` | 無関係。`H_mig` の歴史 blob。 |
| 14 | `t080.draft-known-axes-ccbench-current-pin` | 直接・production。 |
| 15 | `t080.live-holdout-artifact-bytes` | artifact を不変にする限り無関係。 |
| 16 | `t080.live-known-axes-artifact-bytes` | artifact を不変にする限り無関係。 |
| 17 | `t080.live-known-axes-ccbench-current-pin` | 直接・production。 |
| 18 | `t080.static-holdout-artifact-bytes` | artifact を不変にする限り無関係。 |
| 19 | `t080.static-known-axes-artifact-bytes` | artifact を不変にする限り無関係。 |
| 20 | `t080.static-known-axes-ccbench-current-pin` | 直接・production。 |
| 21 | `t080.static-known-axes-recorded-pin` | CCBench pin ではない。holdout record の known-axes SHA pin。 |

  - 実体確認: `s8b-floor.sealed-protocol...` は `test_s8b_floor_campaign.py:1685-1694` の helper にしか存在しない。
  - 実体確認: #11 は `s8b_oracle_driver.py:238-251`、#21 は `t080_freeze_migration.py:2438-2452` で known-axes artifact SHA を比較している。
  - 推論: HELD 内の追加負債は主として上記5本の current-pin 比較であり、「9本すべてが pin bump で赤になる」という費用計算は使えない。HELD 外では所見2・5・6の経路が別途残る。

### 5

- 対象: `patches/ledger.json:6-10`、`orchestrator/campaign/silo_ladder_rung1.py:57`、`orchestrator/campaign/silo_ladder_rung1_contract.py:538-564`
- 内容: 親は ladder の2定数を live 更新対象としつつ、`patches/ledger.json` を歴史記録として「触らない」に分類しており、相互に矛盾する。
- 深刻度: major
- 根拠:
  - 実体確認: 次の3箇所が同じ base を独立に固定する。

    > `silo_ladder_rung1.py:57: PIN = "511c9538..."`  
    > `silo_ladder_rung1_contract.py:543: "base_commit": "511c9538..."`  
    > `patches/ledger.json:10: "base_commit": "511c9538..."`

  - 実体確認: contract は ledger entry の `base_commit` を `expected_scalars` と exact 比較する。
  - 推論: driver/contract を新 pin に更新して ledger を残せば静的契約が赤になる。正しい択一は「ladder 全体を歴史的基底に固定して3箇所とも残す」か「3箇所と派生 receipt/hash を一括再基底する」であり、親の混合案は成立しない。

### 6

- 対象: `orchestrator/tests/test_s8b_protocol_builder.py:51-67,95-122`、`orchestrator/tests/test_p3_build_authority_cli.py:175,991-1005`、`orchestrator/tests/test_p3_s4_loop_sort.py:680,867-869`、`orchestrator/tests/test_p3_s4_loop_trigger_gating.py:124-129,797-820,2025`、`orchestrator/tests/test_s8a_trigger_sweep.py:80-94,333-341,456-464`、`orchestrator/tests/test_s6_sort_sweep.py:370-378`、`orchestrator/tests/test_t126_qualification_driver.py:398-416`
- 内容: F10 の「live束縛7件」は閉包不足。full SHA検索では短縮 pin、`repo_stock_pin`、policy SHA、campaign-id digest を取りこぼす。
- 深刻度: major
- 根拠:
  - 実体確認: `test_s8b_protocol_builder.py` は `CCBENCH_FULL_SHA` を含む canonical bytesと、その `_GOLDEN_SHA`、承認 protocol SHA を独立 literal で固定する。`s8b_approved.py` 更新時には3者が変わる。
  - 実体確認: `test_p3_build_authority_cli.py:175`、`test_s6_sort_sweep.py:370`、`test_s8a_trigger_sweep.py:456` は短縮 `"511c953"` を独立期待値として持つ。
  - 実体確認: `ident.py:166-183` は `ccbench_commit` だけでなく、`repo_stock_pin` を含む `search_config` 全体から campaign-id hash を導く。このため `test_p3_s4_loop_sort.py:867-869` や `test_p3_s4_loop_trigger_gating.py:797-820` の literal ID も動く。
  - 実体確認: `test_s8a_trigger_sweep.py:80-82` は現 policy SHA `949ddc...` を独立 pin する。
  - 実体確認: `b10_backoff_shape_sweep.py:79` も `pin.CURRENT_PIN` の consumer だが、親の「自動追随14本」一覧に無い。
  - 推論: これは単なるテスト修正費ではなく、campaign namespace、resume identity、build receipt policy の世代交代である。F10 の在庫表をそのまま実装費見積りに使えない。

## 親の結論のうち支持できるもの

1. P1の方向性 — D16上、`master` を trace branch に取り込むこと自体は正しい。merge probe の `Options.cmake:15-19,68` は `CCBENCH_TRACE` / `TRACE=${CCBENCH_TRACE}` を保持し、trace実装は `#if TRACE` 内に残る。
2. P2の核心 — D444の16 field byte-exact継承に従う限り、床値protocolの再計測は不要。
3. P4の狭義 — pin関連の必要編集が exact 25 path を変えない限り、既存E1表示値が `E1-stale` へ変わる件数は0。
4. F4 — merge経路では `EXPECTED_SOURCE_LINES` の変更がOptions.cmake側1行に縮む。ただしユーザー裁定つき更新は必要。
5. FROZEN_MANIFEST — versioned floor protocolを23件manifestへ追加しないというD471の扱いは正しい。
6. P5 — 「上げない」なら既存gitlink・凍結bytes・受理状態をこのwaveが変更しない。SS2PLのSIGSEGVは既存実装の欠陥であり、変更しない選択が新しいartifact汚染を起こす証拠はない。

## 親の結論のうち支持できないもの

1. P1を現状のまま推奨案とすること — SS2PL study patchがmerge後に適用不能。patch再基底と#121/#122保持を条件にした案が正しい。
2. P2の「`s8b_approved`を先に更新しないとresealできない」 — 誤り。resealはHEAD gitlinkを直接使い、承認定数を参照しない。
3. P3の「pin照合9件」 — 正しくはproduction直接5件、test-only直接1件、protocol SHA間接1件。
4. P4を受理集合無影響まで一般化すること — `repo_stock_pin` がbuild-admission policyを変更し、旧post-policy lockはpolicy mismatchで拒否される。
5. F10のlive束縛7件・自動追随14本を閉包とすること — ladder ledger、protocol builder goldens、短縮pin期待値、policy SHA、campaign-id goldens、B10 consumerが不足している。

## 総括

推奨は「条件付きで上げる」だが、現時点では条件未充足である。  
条件1はSS2PL study patchをmerge後基底へ再実装し、upstreamのtimeout・lock-failure修正を保持すること。  
条件2は`repo_stock_pin`更新で旧post-policy campaignを失効させるか、歴史policyを扱うかをユーザー裁定すること。  
条件3はladder ledger・builder golden・短縮pin・policy/campaign identityまで閉包を再発行すること。  
床値protocol自体の再計測は不要だが、pin commitとreseal commitの間には一時的なadmission停止がある。  
pytestは実施していない。結論は静的読解とmerge probe上の`git apply --check`による。