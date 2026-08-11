NO-GO。正例を現実の floor artifact から作れず、新設 CLI も実行経路に接続されず、承認情報も既存 proof chain に結び付かない。

## 所見

1. **BLOCKER — approved CLI が実行経路から呼ばれない**

根拠: プランは `build-approved` を新設するが、実際の `run-block` は任意の `--manifest` を `verify_manifest` へ渡すだけです（`s2b-plan.md:250-305`, `orchestrator/campaign/s8b_oracle_driver.py:1119-1129`, `:1544-1564`）。report と judge も既存 manifest を直接消費します（`orchestrator/campaign/s8b_oracle_report.py:1747-1773`, `orchestrator/campaign/s8b_oracle_judge.py:157-249`）。

成果物影響: 任意の holdout/config subset で作った manifest が既存経路を通り、各 holdout の `unique-best` と certified 選択を変えられる。

直し方: driver・report・judge の公式経路を approved-spec 経由へ変更し、既存の汎用 `build_manifest` 経路を公式実行から除外する。

2. **BLOCKER — reviewed spec の承認が manifest / 台帳へ残らない**

根拠: 新 spec は `s2b-plan.md:167-249` で定義されるが、manifest のトップレベルキーには spec hash/pointer がありません（`orchestrator/campaign/s8b_oracle_manifest.py:34-39`）。`build_manifest` も spec を受け取りません（同 `:693-769`）。

成果物影響: manifest/report/ledger だけを見ても「承認済み spec から生成されたか」を証明できず、同じ freeze hash の未承認 schedule が certified 選択に混入する。

直し方: `spec_sha256` と承認 record hash を manifest に含め、driver・report・judge 全てで同一 approved record を再検証する。

3. **BLOCKER — A-12 により production の v2 candidate は作れない**

根拠: プラン自身が floor result 不在時は writer 前に失敗するとしています（`s2b-plan.md:106-120`）。現行 floor campaign の official mode も未確定のため拒否されます（`orchestrator/campaign/s8b_floor_campaign.py:3510-3569`）。既存 fixture は document 内の `floor` と `budget` を埋めるだけで、official result、protocol blob、source path、closure を生成しません（`orchestrator/tests/s8b_v2_freeze_fixture.py:19-67`）。

成果物影響: 実 floor に基づく candidate、ratified generation、certified 選択が一つも生成できず、fixture 正例だけが緑になる。

直し方: official floor artifact が存在する wave まで producer の production 正例を受け入れない。fixture を使う場合も、実 producer の path/blob 読み取りを通す完全な filesystem fixture にする。

4. **MAJOR — `measurement_closure` の commit/handoff 契約が不足している**

根拠: プランは repository scan で closure を作るだけです（`s2b-plan.md:106-120`）。しかし ratified loader は closure の全 path/hash が generation commit と worktree の双方に存在することを要求します（`orchestrator/campaign/s8b_ratified_freeze.py:898-927`, `:930-1007`）。candidate と closure を同じ generation commit に確実に入れる手順・検査がありません。

成果物影響: active loader が `closure-not-in-generation` / `closure-dirty` で拒否するか、closure の不足により launch 時の source hash 検査が失敗する。

直し方: producer が closure snapshot を出力し、ratification 時に generation commit の実 blob と完全一致することを必須化する。

5. **MAJOR — 承認 namespace が二重化し、既存 active pointer と結び付かない**

根拠: 新 budget approval と spec approval は別 path・別 record です（`s2b-plan.md:122-146`, `:227-248`）。一方、既存 ratified の approval/active/revocation namespace は既に存在します（`orchestrator/campaign/s8b_ratified_freeze.py:64-120`, `:1189-1211`）。既存 loader が generation hash を確認しても、新 budget/spec approval record 自体は検証しません（同 `:1214-1334`）。`s8b_experiment_numbers` の reps/extime は既存 validator が既に承認値を拘束しています（`orchestrator/campaign/s8b_experiment_numbers.py:14-15`, `orchestrator/campaign/s8b_oracle_manifest.py:398-407`）。

成果物影響: budget approval と active generation approval のどちらが権威か不明になり、台帳の reservation 値と ratified generation の budget の由来を一意に追跡できない。

直し方: 既存 ratified approval chain を拡張して approval hash を一つにする。独立 record を残すなら、その hash を generation と active pointer に機械的に結び付ける。

6. **MAJOR — テストが production caller と主要拒否分岐を落とせない**

根拠: positive test は synthetic fixture 前提で、driver/report/judge の approved-spec 呼び出しを検査していません（`s2b-plan.md:337-379`）。既存 judge には holdout 間の configuration set 不一致を検出する部分検査があります（`orchestrator/campaign/s8b_oracle_judge.py:194-203`）が、active freeze の全 product とは比較しません。

成果物影響: generic manifest の bypass や caller 未配線が残ってもテストは緑になり、subset による report/judge の certified winner 変更を検出できない。

直し方: 有効な synthetic active root を作った上で、driver → report → judge の実経路を通す。全 holdout/config product、spec hash、caller bypass を一つずつ検査する。

7. **MAJOR — 変異の単一理由帰属ができない**

根拠: プランのテスト列挙（`s2b-plan.md:351-379`）に、各変異と期待 node の対応がありません。実行経路は active freeze 不在、manifest検証、gate の順に早期終了します（`orchestrator/campaign/s8b_oracle_driver.py:1062-1081`, `:1119-1145`）。

成果物影響: spec gate の変異が schedule/config/closure 検査を先取りし、期待 node が `MISMATCH` になる。また caller 未配線変異は新 CLI の単体テストでは生存する。

直し方: 各変異に valid active root と単一 predicate を用意し、期待 node を明示する。早期拒否で後段を検査できないケースは別テストへ分離する。

8. **MAJOR — P5 の file ownership が実際には素集合でない**

根拠: brief は A を holdout module/test、B を spec/manifest/test としています（`s1-brief.md:129-130`）。しかしプランは B 相当の candidate ratification 検査を既存 `test_s8b_ratified_freeze.py` に追加します（`s2b-plan.md:364-365`）。fixture は serial 前処理とされるものの、ratified test の所有者は定義されていません（同 `:337-349`）。

成果物影響: 実装子間で ratified test/helper の変更が衝突し、candidate の loadability 検査だけが抜けるか、統合時に patch が上書きされる。

直し方: `test_s8b_ratified_freeze.py` を B の所有に明示する。最も安全なのは、candidate producer と spec/CLI/ratification compatibility を別 wave に分けること。

9. **MINOR — M-4 / M-5 の一般化が過大**

- M-4 の「`s8b_oracle_manifest.py` に main/argparse がない」は正しいです（同ファイル末尾 `:935`）。ただし project 全体に CLI がないわけではなく、driver の `gate-check/run-block`（`s8b_oracle_driver.py:1544-1613`）、report CLI（`s8b_oracle_report.py:1736-1777`）、judge CLI（`s8b_oracle_judge.py:278-300`）は既に存在します。  
  影響: 既存 caller の監査を省き、「CLI を追加すれば効く」と誤認する。

- M-5(i) は旧 `generate` に限れば正しい（`s8b_holdout_freeze.py:577-606`）。ただし新 producer だけを安全化しても、旧 producer の任意 output path は残ります。M-5(ii) は完全不在ではなく judge に部分検査があります（`s8b_oracle_judge.py:194-203`）。M-5(iii) の budget approval match 不在は正しい（`s8b_oracle_manifest.py:626-656`）。  
  影響: 既存の部分検査を新 gate の完全検査と取り違え、config product と budget provenance の欠落を見逃す。

直し方: M-4 は「approved-manifest builder CLI が不在」と限定する。M-5 は「全 product と approval record への拘束が不在」と再定義する。

file:line の照合では、プランが引用した既存定義の行番号に致命的な stale reference は見つかりませんでした。`s8b_oracle_spec.py`、`build_approved_manifest` などは新設予定 API なので、現時点で存在しないこと自体より、呼び出し側が未変更であることが問題です。並行 wave 所有の `s8b_floor_campaign.py`、`orchestrator/tests/README.md`、runbook への直接編集も確認できませんでした。

## 総括

**NO-GO。** A-12 のため production candidate の正例がなく、synthetic fixture だけでは実効性を証明できない。  
approved CLI は driver/report/judge に未接続で、spec・budget approval も既存 ratified chain に残らない。  
まず official floor artifact、単一の承認 binding、公式 caller の切替を確定し、その後に wave を分割すべきです。