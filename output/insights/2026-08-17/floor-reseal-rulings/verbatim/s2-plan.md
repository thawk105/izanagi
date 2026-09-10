指定資料はすべて読めました。結論は、親の P1 resolver 案を採用して問題ありません。現在の admission は不変で、`FROZEN_MANIFEST` 登録を強制する経路も 0 件です。以下の行番号は現在の HEAD 基準です。書き込みと pytest は行っておらず、worktree は clean です。

## 静的に確認した現在値

- versioned artifact は 0 件で、`output/s8b-freeze/floor-protocols/` 自体が存在しない。
- legacy anchor は [floor_protocol.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/output/s8b-freeze/floor_protocol.json:1) の 1 件。
- 現行 contract と legacy の `contract_sha256` はともに `e576e9cd…e242c01`。
- legacy pin は `d706650cdb31e442bef45b9b4216951d4fb40969`、HEAD gitlink は `511c9538e4e8efa54b45cda62e72389ed3b706ec` で不一致。前 wave の同じ実測は [README.md:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/output/insights/2026-08-16_floor-reseal-authority/README.md:19)-[28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/output/insights/2026-08-16_floor-reseal-authority/README.md:28) にある。

## file:line 実装プラン

1. index の contract 単位封鎖を撤去する。

   - [s8b_floor_campaign.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:753)-[762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:762) の `same_contract` 列挙、条件分岐、エラー文「同一 contract_sha256 が複数ある」を全削除する。
   - 直前の組単位ガード [s8b_floor_campaign.py:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:748)-[752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:752) は変更しない。
   - legacy と versioned の双方がこの helper を通る [s8b_floor_campaign.py:825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:825)-[827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:827)、[877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:877)-[879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:879) はそのままにする。

2. issuer の先行 contract 占有拒否を撤去する。

   - [s8b_floor_campaign.py:966](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:966)-[975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:975) の `occupied_contract_paths` とエラー文「同じ contract_sha256 に 2 件目を発行できない」を全削除する。
   - target pair の実測と検証 [s8b_floor_campaign.py:949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:949)-[965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:965)、組からの path 導出 [s8b_floor_campaign.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:722)-[739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:739)、create-only writer [s8b_floor_campaign.py:1192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:1192)-[1213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:1213) は維持する。

3. resolver を P1 に変更する。

   - 対象は [s8b_floor_campaign.py:892](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:892)-[911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:911)。
   - `_head_commit_oid(root)` を 1 回だけ呼び、その OID を `_scan_floor_protocol_index_at_commit(root=root, commit_oid=head_commit)` と `_ccbench_gitlink(root, head_commit)` の双方へ渡す。公開 `scan_floor_protocol_index()` と別時点の HEAD 読みを組み合わせない。
   - まず従来どおり各 record を現行 contract で絞る。その集合内から `record.ccbench_pin == head_pin` を探し、exact があれば返す。
   - exact が無い場合だけ、現行 contract 候補が exact 1 件なら返す。0 件または複数件なら既存の count 付き fail-closed を維持する。
   - stale contract を pin 一致だけで選ばない。exact 候補は必ず現行 contract 候補の部分集合とする。
   - arbitrary first、最大 pin、辞書順、mtime といった別の曖昧性解消規則は入れない。HEAD 再照合や新しい gate も足さない。
   - docstring [s8b_floor_campaign.py:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:893) をこの優先順位に合わせる。

4. admission 本体は変更しない。

   - [certified_writer_admission.py:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/certified_writer_admission.py:201)-[224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/certified_writer_admission.py:224) の resolver、exact type、disk SHA、strict parse、current contract、compute/calibration の全検査を残す。
   - current validator [s8b_floor_campaign.py:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:491)-[561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:561) は contract を照合するが、`ccbench_pin` と HEAD の照合はしない。ここも変更しない。

## resolver による現在 admission の不変証明

現在の分岐は次のとおりです。

1. index は legacy 1 件だけ。
2. legacy contract は現行 contract と一致するため、current 候補は 1 件。
3. legacy pin は HEAD pin と不一致なので、exact 候補は 0 件。
4. P1 の fallback 条件「current 候補が exact 1 件」を満たし、従来と同じ legacy record を返す。
5. `_admit_floor` は同じ path、同じ bytes、同じ indexed SHA、同じ document、同じ registered contract を検査する。
6. pin-vs-HEAD 検査は後段に存在しないため、compute/calibration までの全 predicate の真偽は変わらない。

既存 admission fixture も legacy bytes をコピーし [certified_writer_fixtures.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/certified_writer_fixtures.py:110)-[112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/certified_writer_fixtures.py:112)、異なる gitlink `"1" * 40` を設定する [certified_writer_fixtures.py:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/certified_writer_fixtures.py:118)-[123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/certified_writer_fixtures.py:123)。したがって [test_campaign.py:4944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_campaign.py:4944)-[4981](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_campaign.py:4981) が実 admission の fallback 回帰になる。

変更される受理 bit はありません。停止すべき不整合は見つかりませんでした。

対案の「resolver を触らない」は不採用が妥当です。同一 contract、異なる pin の 2 件目を許すと、現 resolver は [s8b_floor_campaign.py:906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:906)-[910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:910) で count=2 を拒否し、`_admit_floor` が [certified_writer_admission.py:220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/certified_writer_admission.py:220)-[223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/certified_writer_admission.py:223) で admission rejection に変換します。つまり issuer が許可した正規状態を production consumer が全面拒否します。

## 撤去点と依存点の完全一覧

ライブ実装・テストで contract 単位封鎖を直接 pin している箇所は次の全件です。

- source helper、条件、エラー文:
  - [s8b_floor_campaign.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:753)-[762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:762)
  - [s8b_floor_campaign.py:966](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:966)-[975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:975)
- 逐語テスト名、期待エラー:
  - [test_s8b_protocol_builder.py:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:636)-[644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:644)
  - [test_s8b_protocol_builder.py:647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:647)-[664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:664)
  - [test_s8b_protocol_builder.py:1030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:1030)-[1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:1040)
- contract 一意性を暗黙に前提とする resolver テスト:
  - [test_s8b_protocol_builder.py:945](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:945)-[968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:968)
  - [test_s8b_protocol_builder.py:977](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:977)-[995](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:995)。resolver が private commit-pinned scan を使うため、mock 対象も private helper へ移す。
- resolver path のメタ pin:
  - [test_s8b_protocol_builder.py:998](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:998)-[1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:1027)。この wave は実発行しないため変更しない。将来 exact HEAD artifact が発行された時点で、固定 consumer 6 件の未結線を赤にする sentinel として残す。
- [test_s8b_floor_contract.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_floor_contract.py:1)-[380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_floor_contract.py:380) には contract 単位 index 封鎖の依存はない。変更不要。

durable docs では次を扱います。

- D444 の撤去対象は [decisions.md:18656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/decisions.md:18656)-[18658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/decisions.md:18658) の決定 5。
- 組単位一意性 [decisions.md:18639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/decisions.md:18639)-[18640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/decisions.md:18640)、23 key 不変 [decisions.md:18666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/decisions.md:18666)-[18668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/decisions.md:18668)、pin 前進が新しい組を作るという既記録 [decisions.md:18693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/decisions.md:18693)-[18695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/decisions.md:18695) は維持する。
- canonical `docs/decisions.md` は直接編集せず、新規 `docs/spool/decisions/2026-08-17-dev-wave-t1218-floor-reseal-rulings-2.md:1` で D444 決定 5だけを限定 supersede する。P1、pair 一意性、create-only、非登録、追加 gate なしも明記する。
- worklog は `docs/spool/worklog/2026-08-17-dev-wave-t1218-floor-reseal-rulings-1.md:1`、insight は `output/insights/2026-08-17_floor-reseal-rulings/README.md:1` を候補とする。
- 現裁定の durable 根拠は [worklog archive:514](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/archive/worklog-phase3-0816-595-596.md:514)-[515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/archive/worklog-phase3-0816-595-596.md:515) と [1047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/archive/worklog-phase3-0816-595-596.md:1047)-[1052](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/archive/worklog-phase3-0816-595-596.md:1052)。

前 wave の逐語・変異 pin も全件、歴史資料として残します。書き換えず、新 decision と insight で supersede 関係を記録します。

- 前 wave 要約: [README.md:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/output/insights/2026-08-16_floor-reseal-authority/README.md:44)-[52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/output/insights/2026-08-16_floor-reseal-authority/README.md:52)、[98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/output/insights/2026-08-16_floor-reseal-authority/README.md:98)-[103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/output/insights/2026-08-16_floor-reseal-authority/README.md:103)。
- 逐語 adjudication/author: `verbatim/s4-adjudication.md:51,80`、`verbatim/s5-author.md:10,16,49,82`。
- 逐語 review/fix: `verbatim/s6-lensC.md:7-12,37-41,53,66-72`、`verbatim/s6-lensD.md:61-62,113,129`、`verbatim/s6-fix1.md:8-19,68`、`verbatim/s6-fix2.md:52`、`verbatim/s6-focus.md:10,36-37,58-62,79`、`verbatim/s6-focus2.md:17`。
- 旧コードと旧 nodeid の機械 pin: `mutation/spec-round2.json:7-26,42-58,81-98,119-124` と `mutation/spec-probe.json:9,26,40,63-64,73,78,89-94`。
- 生成済み result にも旧 nodeid が埋め込まれている: `mutation/result-round2.json:35,48-72,143-169,197-210,295-310,738-910`、`mutation/result-probe.json:35-56,126-193,358-466,1031-1215`。これらは過去実測なので更新しない。
- cross-wave の collection ledger にも旧 nodeid がある: `output/insights/2026-08-16_t419-seam-checknet/mutation-ledger.json:778,794` と同 `mutation-ledger-probe.json:1945,1961`。これも生成済み歴史資料であり更新対象外。

上位束の Q3 文書 [calibration-freeze-authority-bundle-design.md:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/calibration-freeze-authority-bundle-design.md:10)-[19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/calibration-freeze-authority-bundle-design.md:19)、[177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/calibration-freeze-authority-bundle-design.md:177)-[186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/calibration-freeze-authority-bundle-design.md:186)、[837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/calibration-freeze-authority-bundle-design.md:837)-[845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/calibration-freeze-authority-bundle-design.md:845) は実発行を g2 chain へ送る P2 と両立しており、本 wave では変更しません。

## `FROZEN_MANIFEST` 非登録の裏取り

登録を強制する経路は 0 件でした。

- [test_frozen_artifacts.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_frozen_artifacts.py:41)-[88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_frozen_artifacts.py:88) は明示された 23 key だけを持ち、namespace の directory scan はしない。
- 暫定 keyset [test_frozen_artifacts.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_frozen_artifacts.py:90)-[117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_frozen_artifacts.py:117)、held/keep 分割 [119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_frozen_artifacts.py:119)-[151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_frozen_artifacts.py:151)、23 件と exact key-set の assert [227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_frozen_artifacts.py:227)-[248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_frozen_artifacts.py:248) は、versioned artifact を追加しない側を支持する。
- launch scan は versioned path を chain record として認識する [s8b_floor_campaign.py:265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:265)-[272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:272)。`_assert_freeze_allowlist` は rglob するが [3817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:3817)-[3865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:3865)、chain record は fixed allowlist へ要求せず動的に hash 化する。
- `clean_scan_digest` も fixed allowlist と chain record を merge するだけ [s8b_floor_campaign.py:3911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:3911)-[3925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:3925)。既存正例 [test_s8b_protocol_builder.py:1309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:1309)-[1315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:1315) が空 allowlist でも exact versioned path を受理する。
- `s8b_ratified_freeze.py` は namespace 全体を走査する [816](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_ratified_freeze.py:816)-[840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_ratified_freeze.py:840) が、世代 chain の正規表現は [86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_ratified_freeze.py:86)-[91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_ratified_freeze.py:91) の明示された種類だけで、その他の file は resolution 対象から外す [1161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_ratified_freeze.py:1161)-[1165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_ratified_freeze.py:1165)。
- 同 scan は全 file に introduction/history 検査を課す [s8b_ratified_freeze.py:1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_ratified_freeze.py:1089)-[1092](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_ratified_freeze.py:1092)。これは commit・履歴不変条件であり、`FROZEN_MANIFEST` 登録ではない。
- ratified generation が versioned path を明示的に指した場合は、通常の closure path と hash として束縛される [s8b_ratified_freeze.py:899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_ratified_freeze.py:899)-[928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_ratified_freeze.py:928)。mere existence による registry 登録ではない。
- `s8b_oracle_manifest.py` は active ratified generation の freeze path を射影するだけ [814](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_oracle_manifest.py:814)-[841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_oracle_manifest.py:841) で、`output/s8b-freeze` の inventory scan はない。verify も caller から受け取った snapshot を検証する [990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_oracle_manifest.py:990)-[1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_oracle_manifest.py:1027)。
- `tools/check*.py`、`tools/run_tests.py`、`tools/hold_inventory.py` を `FROZEN_MANIFEST`、`floor-protocols`、`output/s8b-freeze` で走査した結果は 0 hit。登録を強制する checker はない。

## テスト計画

| nodeid 候補 | 変更または期待 | pair ガードまで消す誤実装で赤になるか |
|---|---|---|
| `orchestrator/tests/test_s8b_protocol_builder.py::test_reseal_protocol_public_entry_accepts_same_contract_with_new_pin` | 現 [636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:636) を反転。legacy と同じ g1 contract、異なる HEAD pin の発行成功、導出 path、index 2 件、legacy bytes 不変を確認 | いいえ。pair が異なる正例 |
| `...::test_reseal_protocol_second_issue_same_pair_is_create_only_and_preserves_first_bytes` | 現 [647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:647) を改名。2 回目は「既に存在する create-only」で拒否し、初回 artifact bytes と件数が不変 | いいえ。pair ガードを消しても create-only が拒否する |
| `...::test_floor_protocol_index_accepts_same_contract_with_different_pin` | 現 [1030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:1030) を反転。legacy pair と pin 違い pair の両方を assert | いいえ。異なる pair の正例 |
| `...::test_floor_protocol_index_includes_legacy_and_rejects_duplicate_pair` | 現 [930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:930)-[942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:942) を無変更で維持 | **はい**。pair ガードを消すと legacy と versioned の同一組が上書き登録され、例外が出ない |
| `...::test_current_floor_protocol_resolver_falls_back_to_single_contract_match_when_head_pair_missing` | 現 [945](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:945) を改稿。legacy pin と HEAD pin の不一致、current 候補 1 件、legacy 解決を明示 | いいえ |
| `...::test_current_floor_protocol_resolver_prefers_exact_head_pair_among_same_contract_records` | 新設。同じ current contract の old-pin と HEAD-pin の 2 record を置き、HEAD record を返す。scan と gitlink が同じ commit OID を受けたことも assert | いいえ。ただし旧 resolver や任意 fallback を赤にする |
| `...::test_current_floor_protocol_resolver_rejects_ambiguous_same_contract_without_head_pair` | 新設。同じ current contract の 2 件がどちらも HEAD pin でない場合、count=2 で fail-closed | いいえ。任意選択を赤にする |
| `...::test_current_floor_protocol_resolver_rejects_zero_current_matches` | 現 [977](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:977) の mock を commit-pinned private scan に追従 | いいえ |
| `orchestrator/tests/test_campaign.py::test_p2_actual_floor_and_t126_admission_accept_valid_evidence` | 無変更で実行。現在の pin 不一致 fallback と実 admission PASS の回帰 | いいえ |
| `...::test_floor_admission_uses_authority_resolver_not_legacy_literal` | [test_campaign.py:4984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_campaign.py:4984)-[5024](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_campaign.py:5024) を無変更で実行 | いいえ |
| `...::test_floor_admission_rejects_disk_bytes_different_from_index_record` | [test_campaign.py:5027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_campaign.py:5027)-[5062](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_campaign.py:5062) を無変更で実行 | いいえ |
| `...::test_clean_scan_accepts_exact_versioned_protocol_chain_record` | FROZEN 非登録の既存正例として無変更実行 | いいえ |

重要なのは、public API の同一組再発行テストは create-only を検査するため、pair index ガード削除の mutation killer にはなりません。組単位ガードの取り違えは `test_floor_protocol_index_includes_legacy_and_rejects_duplicate_pair` が直接赤にします。この 2 層を別々に残します。

変異計画では、削除した各 contract gate の再挿入、pair gate の削除、create-only の上書き化、resolver の旧 count=1 化、fallback 削除、曖昧時の先頭選択を別変異として登録します。

## やってはいけないこと

- [floor_protocol.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/output/s8b-freeze/floor_protocol.json:1) を含む既存凍結 bytes の変更。
- この wave での versioned artifact 実発行。
- `FROZEN_MANIFEST`、23-key pin、held/keep 分割への追加または差し替え。
- 「登録してはならない」を強制する新しい逆向き gate。
- contract ごとの件数、世代ごとの件数、事前登録、pointer namespace などの新束縛。
- HEAD exact record だけを必須にして legacy fallback を消すこと。
- stale contract、未検証 bytes、任意 path、caller 指定 pin の受理。
- `_admit_floor` の indexed SHA、current contract、compute/calibration 検査の緩和。
- 固定 path consumer 6 件をこの wave で先行変更すること。実発行と consumer 結線は後続 chain の所有。
- pytest を直接起動すること。親の実測は `tools/run_tests.py` 経由とし、関連テスト、`check_codex_agents.py`、`check_docs.py`、commit 後 provenance を実施する。

## 総括

P1 resolver は current contract を先に絞り、HEAD pin exact を優先し、単独 legacy へだけ fallback すればよい。  
今日の repo では exact 0、current 候補 1 のため、`_admit_floor` の受理 bit は変わらない。  
撤去対象は index と issuer の contract 単位 2 gate、およびそれを pin する 3 テスト期待値である。  
pair 一意性と create-only は別々の負例で維持し、pair ガード削除を既存 duplicate-pair test が検出する。  
`FROZEN_MANIFEST` 登録を強制する scan、meta test、allowlist、checker は 0 件である。  
本調査は read-only、pytest 未実行、worktree 無変更で完了した。