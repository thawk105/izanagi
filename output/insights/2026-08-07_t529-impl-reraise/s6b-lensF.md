# 所見

## must-fix

### F-1 — 公開 `Mapping` API の受理集合は実際に変わっている

共有 leaf は `contract_sha256` を `isinstance(value, str)` で検査するため、`str` 派生型も受理します（[s8b_floor_contract.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_contract.py:90)、[同:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_contract.py:140)）。

一方、

- current lane は記録 hash の型を使わず `lookup(env_tag)` し（[s8b_floor_campaign.py:327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:327)）、値の等価比較だけで通します（[同:362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:362)）。
- historical lane は `resolve_by_contract_sha256` の exact `str` 検査で同じ値の派生型を拒否します（[env_contract.py:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:355)、[同:361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:361)）。

同一 hash 値を持つ `class HashText(str)` を protocol に入れた非 pytest probe でも、current は ACCEPT、historical/public は `FloorCampaignError` で REJECT になった。これは実装報告の「今日は同一」という主張（[s5b-impl.md:75](/work/1/SFC/tanab/dev-wave-jobs/t529-impl-reraise/s5b-impl.md:75)）への反証である。問いの「返さない入力が1つでもあれば must-fix」という基準に該当する。

**成果物影響:** `str` 派生型を保持する programmatic consumer では凍結 protocol の read-only 受理集合が縮み、それを参照するレポート・試行台帳が再検証不能になる。コミット済み JSON bytes と値自体は不変。

## should-fix

### F-2 — production `main` の historical 配線を新テストが固定していない

追加された将来 g2 正例は公開 leaf の直接呼出し（[test_s8b_floor_campaign.py:4429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4429)）、live 負例は `run_campaign` の直接呼出し（[同:4481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4481)）である。production consumer である `main` の `validate_protocol` 呼出し（[s8b_floor_campaign.py:3557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3557)）を g1/current-g2 状態で通す試験はない。

既存 main 試験は official の早期拒否（[test_s8b_floor_campaign.py:1115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:1115)）と、current=g1 で壊れた freeze を読む pilot 試験（[同:4922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4922)）だけである。`main` を current に戻す変異は、今回追加された3試験をすべて通過できる。

**成果物影響:** CLI consumer の配線が後退しても leaf 試験だけは緑になり、g2 活性化後に凍結 protocol を参照する実レポート・試行台帳の入口だけが再び拒否されうる。

## nit

### N-1 — 「全 caller」表は direct caller 表としては完全だが、入口表としては不足

実装報告の直接 caller 一覧（[s5b-impl.md:27](/work/1/SFC/tanab/dev-wave-jobs/t529-impl-reraise/s5b-impl.md:27)）に直接呼出し漏れはなかった。ただし shell 入口 [floor_campaign.sh:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/floor_campaign.sh:894) と subprocess 経由の `main` 呼出し [test_s8b_floor_campaign.py:4935](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4935) は表にない。

なお production shell は `official` を渡すため、現状は protocol を読む前の早期拒否（[s8b_floor_campaign.py:3548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3548)）で historical lane に到達しない。

**成果物影響:** 現時点の値・受理集合への影響はない。入口被覆率の表現だけが過大。

### N-2 — 未 collection なのに「テスト赤はありません」は未確認

報告自身が pytest の collection に到達していないと認めつつ「テスト赤はありません」と記述している（[s5b-impl.md:62](/work/1/SFC/tanab/dev-wave-jobs/t529-impl-reraise/s5b-impl.md:62)）。正確な状態は赤・緑とも不明である。

**成果物影響:** なし。試験状態の報告精度のみ。

# 独立確認

## 今日の exact JSON 入力と例外境界

実在する exact `str` の JSON 入力に限れば、historical/current の受理判定と正規化結果は一致する。

- 両 env は各1世代だけ（[env_contract.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:231)）。
- hash は全 env・世代で一意に強制される（[同:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:302)）。
- `REGISTRY` は同じ `GENERATIONS` の末尾 object から構築される（[同:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:344)）。
- 凍結 protocol の pegasus hash は現 current hash と一致する（[floor_protocol.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/s8b-freeze/floor_protocol.json:1)）。

例外は両 resolver とも `EnvContractError → FloorContractError`（[s8b_floor_campaign.py:312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:312)、[同:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:332)）、さらに公開境界で `FloorCampaignError`（[同:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:369)）へ翻訳される。`main` も型で捕捉しており（[同:3567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3567)）、メッセージ差による上位 `except` の捕捉変更はない。

## 公開関数 caller

production の直接 caller は `main` の1件だけ（[s8b_floor_campaign.py:3559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3559)）。

テストの直接 caller は以下で、実装報告の direct 表と一致した。

- `test_s8b_floor_campaign.py`: 399, 997, 1002, 1007, 1016, 1036, 1053, 1061, 1075, 1082, 2474, 4445, 4473, 4896
- `test_s8b_floor_contract.py`: 175
- `test_s8b_protocol_builder.py`: 101, 167, 178, 187, 417
- `test_s8b_ratified_freeze.py`: 284

builder、発行 read-back、fresh/resume は private current lane に移っている（[s8b_floor_campaign.py:510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:510)、[同:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:652)、[同:2829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2829)）。別 production module の直接 caller はなく、prediction runner は builder 経由で current（[s8b_prediction_runner.py:1463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_prediction_runner.py:1463)）。qualification と共有 leaf の同名関数は別物である。

## 凍結境界・scope

基準 commit `8e42a564` と byte compare し、次を確認した。

- `floor_protocol.json`: 774 bytes、SHA-256 `261cec1c…e74aac`、基準 commit と完全一致。
- `FROZEN_MANIFEST` 全ファイル bytes も基準 commit と完全一致し、期待値は同じ hash（[test_frozen_artifacts.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_frozen_artifacts.py:45)）。
- 実装 patch は作業ツリー差分と一致し、変更対象は campaign 本体（[s5b-impl.patch:1](/work/1/SFC/tanab/dev-wave-jobs/t529-impl-reraise/s5b-impl.patch:1)）とそのテスト（[同:201](/work/1/SFC/tanab/dev-wave-jobs/t529-impl-reraise/s5b-impl.patch:201)）だけ。
- bootstrap fuse は残存し（[env_contract.py:316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:316)）、2世代目を拒否する（[同:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:322)）。g2・activation record/receipt は追加されていない。

scope 逸脱は確認できなかった。

## [T-615] とテストの実効性

[T-615] の read-only 目的はコード上達成している。

g1 が historical index に残り g2 が current になれば、公開関数は記録 hash を historical resolver へ渡して g1 を取得する（[s8b_floor_campaign.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:308)、[同:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:389)）。CLI でもまずここを通る（[同:3559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3559)）。その後の fresh/resume は current admission を再実行して g1/current-g2 を拒否する（[同:2829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2829)）。したがって「read-only 受理」と「実行権限」の分離は保たれている。

追加試験も単なる呼出し回数確認ではない。historical の返却内容・引数・fallback 不在（[test_s8b_floor_campaign.py:4445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4445)）、unknown/cross-env/不正返却の拒否（[同:4452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4452)）、fresh の calibration/measure/I/O 前拒否（[同:4510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4510)）まで確認しており、実装削除で通る恒真試験ではない。ただし F-1 の同値性と F-2 の production 入口は未被覆である。

pytest は実走しておらず、緑は主張しない。

## 総括

1. **今日の受理集合は変わった。** 公開 `Mapping` API では `str` 派生型の反例がある。ただし実在する凍結 JSON bytes の受理と成果物値は変わっていない。

2. **[T-615] の目的は達成。** g2 current 時も公開 historical lane から凍結 g1 を受理でき、live fresh/resume は current で拒否される。静的確認のみで pytest は未実走。

3. **親が次に実測すべきこと:** F-1 を修正し、real-registry parity・`str` 派生型・g1/current-g2 の `main` 経路を追加したうえで、`tools/run_tests.py` 経由で campaign/contract/builder/ratified/prediction/frozen-artifact と M9〜M11 を再走する。