# 結論

このプランはそのまま実装不可。must-fix 4 件、should 1 件。特に S4 は既出失敗 F27 の完全な再演であり、親 brief の「DW-O09 不成立」は明確に誤り。

## [A-1] must-fix — S4 は自己ハッシュ generator を変更し、凍結 proof chain を即座に破壊する

**file:line:** `brief.md:20,32-34,43-45,51`、`plan-out.md:111-131,220,230`、`orchestrator/campaign/s1_known_axes_freeze.py:31,634-637,721-727`、`output/s1-freeze/known_axes_freeze.json:5-7`

**なぜ壊れるか:**

1. S4 は `s1_known_axes_freeze.py` に import と定数式を追加するため、同ファイルの bytes が必ず変わる。
2. `known_axes_freeze.json` は generator 本体の SHA-256 を記録している。
3. `verify_document()` は現行 generator の hash と記録値を比較し、不一致なら `generator sha256 不一致` で停止する。
4. したがって「SILO_CMAKE_REL の評価値が同じ」は無関係。編集した事実だけで既存 freeze が拒否される。
5. これは `docs/failures.md:344-360` の F27 と同一失敗である。

影響は S1 単体に閉じない。

- `orchestrator/campaign/s8b_oracle_driver.py:400-413` が公式 gate から `s1_known_axes_freeze.verify()` を呼ぶ。
- `orchestrator/campaign/s1_measurement_freeze.py:249-257` が known freeze bytes を hash 束縛する。
- `output/s8b-freeze/holdout_freeze.json:9-11` も known freeze の hash を pin する。
- `orchestrator/tests/test_frozen_artifacts.py:38-44` の `FROZEN_MANIFEST`、`orchestrator/campaign/t080_freeze_migration.py:44-45` の trust-root literal にも波及する。

よって「凍結 bytes 不変」と S4 は両立不能。S4 を scope から落として独立 literal＋対向テストに留めるか、DW-O09 を成立扱いに巻き戻して全 pin 閉包・再発行可否を裁定し直す必要がある。

## [A-2] must-fix — S1 は独立の認可 gate を畳み、以前止まった入力を通す

**file:line:** `brief.md:25-27,46-47`、`source_digest.py:78-81,550-552,662-698`、`docs/axis-onboarding.md:70-73,114-119`

親の放置影響は向きが逆である。EBS だけを拡張した場合、そのファイルは digest 対象にはなるが、現行 ALLOWLIST が拒否する。「編集可能だが digest 対象外」になるのは ALLOWLIST だけを広げた場合である。

具体的反例:

1. 将来 `EVOLVE_BLOCK_SOURCES` に `cc/silo/future.cc` だけを追加する。
2. submodule で同ファイルに tracked 改変を入れる。
3. 現行実装では `future.cc not in ALLOWLIST` により `assert_worktree_within_allowlist()` が停止する。
4. 導出後は EBS 追加だけで ALLOWLIST にも自動追加され、同じ入力が通る。
5. include・macro guard を満たす通常の本文変更なら、その後も digest 生成まで進む。

digest 被覆は増えるので直ちに偽 cache hit ではない。しかし「EBS 拡張」と「編集認可面の拡張」という二段の trust-boundary review を一段に畳む、明白な fails-closed 反転である。`axis-onboarding.md` も両定数の明示的拡張を信頼境界変更として要求している。

これを採るなら「値だけの機械的変更」「全変更 fails-closed」「新 D なし」では扱えない。安全側は ALLOWLIST literal を残し、EBS との不一致をテストで停止させる方式である。

## [A-3] must-fix — P1 は frozen packet を検査していない。live EBS 化でも stale packet が通る

**file:line:** `s6_proposal_rounds.py:77-79,94-124,195-215,231-266,361-375`、`output/insights/2026-07-13_s6-round-execution-design.md:77-92`、`test_s6_proposal_rounds.py:211-246`

`freshness_check()` が読むのは frozen payload ではなく、可変な `N1_PROVENANCE` である。一方、ledger に書かれる次の値は `cmd_verify()` で照合されない。

- `n1_provenance_sha256`
- `submodule_pin`
- `population_sha256`

fails-closed 反転の具体経路:

1. live EBS を拡張する。旧 N1 のままなら freshness は停止する。
2. N1 provenance を現行ソース・現行 EBS に合わせて更新する。
3. freshness は新 N1 対 live EBS なので通る。
4. frozen payload は旧 edit surface のままでも、ledger 内の旧 payload hash と一致するため通る。
5. `cmd_verify()` は新 N1 hash と ledger の旧 `n1_provenance_sha256` を比較しない。
6. `cmd_run()` はその verify 後、旧 frozen payload を実行する。

つまり「以前は止まっていたのに、N1 更新後は stale packet のまま通る」。提案された focused test は membership 述語しか叩かず、この consumer 取り残しを検出しない。

凍結時点 hard-code を守る最強の反論は、`opened` が実験処置の一部だからである。freeze-time EBS と live EBS は別概念として保持すべきで、前者で packet の再現性を検証し、後者との差を別の staleness gate として報告・停止すべきである。少なくとも N1 hash、submodule pin、frozen payload の相互束縛を `cmd_verify()` の公開経路で検査する必要がある。

## [A-4] must-fix — 新規 test file は受入全走を静的に落とす

**file:line:** `plan-out.md:133-138`、`orchestrator/tests/README.md:62-74`、`orchestrator/tests/test_plain_runner_coverage.py:60-74`

計画中の `test_edit_surface_contract.py` には自走 harness がなく、README の pytest-only allowlist 追加も計画されていない。したがってメタテストは同ファイルを `offenders` に入れる。`tools/run_tests.py` 全走受入とは両立しない。

さらに新規 path は `s8b_floor_campaign.clean_scan_digest()` の `repository_files` preimage（`s8b_floor_campaign.py:1597-1639`）も変える。これは `docs/failures.md:656-678` の F39 型なので、DW-O09 を「bytes 不変」だけで不成立にしてはならない。

既存 `test_campaign.py` 等へ追加すれば、新規 path と harness 問題の双方を避けられる。

## [A-5] should — 「全出現を掃引済み」「既存被覆ゼロ」は事実でない

**file:line:**

- `.claude/agents/coder.md:13` — designated source を「現在 backoff.hh のみ」とする operational copy
- `orchestrator/tests/test_campaign.py:2977-3000` — ALLOWLIST の 3 許可パス＋外部反例を既に検査
- `s1_known_axes_freeze.py:663-666` — 生成文書内に `cc/silo/CMakeLists.txt` の別 hard-code
- `orchestrator/tests/s1_expected_goldens.py:296-299,461` — CMake path の独立 golden
- `output/insights/2026-07-10_s8a-n1-provenance.json:200-217,259` — freeze-time opened 集合と導出規則
- `docs/axis-onboarding.md:70-73` — EBS/ALLOWLIST を独立 trust-boundary とする契約

これらをすべて導出対象にすべきという意味ではない。むしろ live copy、独立 golden、歴史記録、凍結 snapshot を分類しないまま「ドリフト面」と一括したことが A-1〜A-3 の誤裁定を生んでいる。

## 攻撃したが破れなかった軸

- 現行値だけを比較すれば、`frozenset(EVOLVE_BLOCK_SOURCES) | {OPTIONS_CMAKE}` は同じ 3 要素の `frozenset` であり、`sorted(ALLOWLIST)` のエラーメッセージも不変。
- `EVOLVE_BLOCK_SOURCES` 自体は tuple・要素順とも不変なので、digest の parts 順序は変わらない。
- 現行 EBS では S3 の追加列は引き続き `include/backoff.hh` 1 件で、外側の `sorted()` 後の regen 順も不変。
- S2/S3 単独については、`source_digest` import に import-time I/O・乱数消費・逆 import はなく、現行値で payload/seed/hash-ledger bytes が変わる経路は静的には見つからなかった。
- 現行定数のままなら `assert_worktree_within_allowlist()` の受理集合は同一。反転は A-2 の将来 EBS 変更時に発生する。

ファイル変更・pytest 実走は行っていない。以上は静的検査による所見。