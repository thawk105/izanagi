静的レビューの判定は **NO-GO** です。pytest は実行しておらず、ファイル変更も行っていません。must-fix は 4 件です。

### 1. T-627 の (c) を同一 wave 内で自己解除している

深刻度: **must-fix**

根拠: ユーザー裁定は「(c) 実 schema 確定まで置かない、DW-G04 は上書きしない」です（[rulings-inbox:359](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md:359)）。元の択一では、`GenerationEntry` と `is_valid_successor` を使う (b) と、実 schema まで待つ (c) は別案でした（[worklog:819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/docs/archive/worklog-phase3-0807-294-295.md:819)）。D228 も実装形を実 schema と合わせて「別途裁定する」としています（[decisions.md:10674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/docs/decisions.md:10674)）。

しかしプランは「この wave で schema が確定するから停止条件充足、再裁定不要」として (b) 相当を前倒ししています（[s2-plan.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:7)、[同:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:10)）。これは (b)/(c) の択一区別を消しており、F158 型の権限逸脱です。

さらにテスト表は T-624 の失敗を回避し切れていません。例えば exact な `(generation, hash)` membership と env 集合検査を保ったまま、delta 部だけを次のように誤実装できます。

```python
if all(d == 0 for d in deltas):
    reject()
if any(d > 1 for d in deltas) and all(d >= 0 for d in deltas):
    reject()
if any(d < 0 for d in deltas) and all(d <= 1 for d in deltas):
    reject()
accept()
```

これは表にある no-op、単独 skip、単独 downgrade、hash swap、env-set change を拒否し、実 g2 の `(0,+1)` を受理します。一方、登録済み endpoint 間の `(+2,-1)` は受理します。プランは負例を一 node にまとめ（[s2-plan.md:227](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:227)）、この相殺ケースも、registry membership で先に落ちない fixture も指定していません。先行 wave で同型の aggregate-delta 誤実装が全表を通った事実とも整合します（[T-624 README:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/output/insights/2026-08-07_t624-activation-noop/README.md:24)）。

成果物影響: 未批准の遷移受理集合が production authority となり、`(+2,-1)` 等で serial/state hash だけ進んだ非単調な contract 集合を certified 選択・レポート・台帳が参照し得ます。

修正案: 親 P3 を採用し、本 wave では D228 述語を実装しないこと。serial 2 以降を発行可能な production issuer も有効化せず、schema land 後に T-627 の (b) をユーザー再裁定へ返してください。後続テストは各性質を独立 node にし、登録済み endpoint を使う `(+2,-1)` を必須負例にします。

### 2. 「実 g2 素材」でも temporary serial 2 record は合成正例である

深刻度: **must-fix**

根拠: B(a) は「DW-G04 維持・合成正例を作らない」です（[s1-brief.md:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s1-brief.md:34)）。それに対してプランは、一時 record directory に serial 2 を組み立てる正例を採用しています（[s2-plan.md:6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:6)、[同:228](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:228)）。94a4 calibration と g2 catalog row が実在しても、activation record、issuer 実行、レビュー済み commit、production authority head は合成です。D215 も temporary commit による後継世代正例を発火証拠として明示的に却下しています（[decisions.md:10171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/docs/decisions.md:10171)）。

このテストは、loader 内の単純な `generation > 1` 拒否なら確かに落とします。しかし、production commit-binding や issuer にだけ残る serial 2 拒否は通過しません。したがって「テスト seam の無条件 fuse」は落とせても、「レビュー済み authority 経路の永久 fuse」とは区別できません。P1 が実 serial 2 の commit を禁止する以上、P1・P2・B(a) は現プランでは同時充足しません。

成果物影響: test-only g2 は committed activation 台帳・report・ledger に現れないため、production 側が永久に g1 を選び続ける実装でも「g2 activation 正例あり」と誤って land できます。

修正案: temporary serial 2 は通常の unit test と明記し、DW-G04 発火証拠や永久 fuse 排除証拠に数えないこと。P1 を維持するなら本 wave は full activation 完了を名乗れません。実 serial 2 を正例にするなら、g2 活性化と既存 current consumer への影響をユーザーへ再裁定してください。

### 3. 「レビュー済み commit」という trust root が loader に結線されていない

深刻度: **must-fix**

根拠: 確定裁定は trust root をレビュー済み commit としています（[s1-brief.md:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s1-brief.md:37)）。ところが loader API は単に worktree directory を読み（[s2-plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:38)、[同:65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:65)）、issuer はその production directory へ commit 前に直接書きます（[同:167](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:167)、[同:175](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:175)）。

既存 static preflight の source binding も、検査対象は import 済み Python module だけです（[certified_writer_preflight.py:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/certified_writer_preflight.py:85)、[同:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/certified_writer_preflight.py:123)）。activation JSON は対象外です。

また gap/predecessor 検査は末尾削除を検出しません。`00000002.json` を除くと、serial 1 だけの chain は gap も bad predecessor も持たないため、予定テスト（[s2-plan.md:226](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:226)）をすべて満たす valid prefix rollback になります。

成果物影響: 未 commit の serial 2 で current hash を g2 に切り替えたり、末尾削除で g1 に戻したりでき、成果物の `source_commit` と certified 選択・report・ledger が参照した activation state が分裂します。

修正案: production loader は、各入口が束縛する reviewed `source_commit` の Git blob 集合から record を読むか、worktree の directory 集合・bytes がその commit と exact 一致することを検査してください。untracked extra、modified record、committed tail の欠落を拒否する必要があります。issuer の候補は live authority directory 外へ出し、commit 前は loader が見ない形にします。外部署名への変更は不要で、既決の Git trust root を実装へ結線する修正です。

### 4. ever-active 全 entry の calibration eager 検証が、履歴障害を全 current admission へ伝播する

深刻度: **must-fix**

根拠: プランは authority cache 読込時に、全 ever-active entry を `load_verified_calibration()` へ渡します（[s2-plan.md:141](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:141)）。同 loader は artifact の現在の存在を要求し（[calibration_verify.py:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/calibration_verify.py:101)）、v2 を現在の effective-clock policy と比較し（[同:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/calibration_verify.py:130)）、legacy は唯一の grandfather SHA に限定します（[同:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/calibration_verify.py:144)）。

したがって親の「linux g1 と pegasus g1 は今日通る」は点時点の事実にすぎません。例えば Linux の legacy file（[env_contract.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:247)）が欠落しただけで、Pegasus current lookup まで全滅します。将来 g2 が current のとき、歴史 g1 の policy drift でも同じです。一方、oracle report は既に「選択された歴史 contract の calibration」だけを利用時に検証できます（[s8b_oracle_report.py:1217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_oracle_report.py:1217)、[同:1230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_oracle_report.py:1230)）。

成果物影響: 使われていない履歴較正一件の欠落・旧 policy 化で全 current registry が消え、全 certified writer/selection が拒否され、oracle 行も対象 hash に無関係に `protocol_violation` へ変わります。

修正案: activation state load は record/hash-chain と exact catalog pair だけを検証してください。calibration は `lookup(env_tag)` で選択 current entry を、historical consumer では解決した entry だけを検証・cache します。「古い一 entry の不良は、その hash を参照する証明だけを拒否する」という正例を追加してください。

### 5. 「壊れるのは live admission だけ」は一般化しすぎている

深刻度: **should-fix**

根拠: 親 brief は floor の二 lane 実測から「壊れるのは live admission だけ」としています（[s1-brief.md:57](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s1-brief.md:57)）。しかし `silo_ladder_rung1 verify-result` は read-only 検証中に current `lookup("pegasus")` を呼び、記録済み calibration path/hash/contract hash と比較します（[silo_ladder_rung1.py:3512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/silo_ladder_rung1.py:3512)、[同:3535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/silo_ladder_rung1.py:3535)、[同:4833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/silo_ladder_rung1.py:4833)）。committed artifact は g1 を固定しています（[silo_ladder_rung1.json:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:12)）。

ただし現在の同 artifact は旧 `env_contract.py` source SHA も固定しており（[同:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:67)）、current runtime-module gate が先に発火します。したがって g2 拒否は現状では別層に mask されており、新しい受理縮小の実証には使えません。それでも「read-only current consumer が存在しない」という一般化は誤りです。

成果物影響: 将来 source binding を更新した g1 silo evidence は、g2 活性化後に offline `verify-result` から外れます。初期 serial 1 の land 時点では変化しません。

修正案: activation 影響表へ floor、oracle driver、T126/static preflight、execution guard、silo offline verifier を分けて列挙してください。silo を historical 化するか current のままにするかは別の受理集合変更なので、実 g2 activation の裁定パッケージへ返します。

### 6. pegasus g1 literal pin は 4 file ではなく 5 file

深刻度: **should-fix**

根拠: 親の 4-file 集計（[s1-brief.md:62](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s1-brief.md:62)）に、追跡済み raw bundle の [`gap-result-receipt.json:22`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/gap-result-receipt.json:22) が含まれていません。pin は path 名や role 名 key ではなく、汎用の `contract_sha256` key にあります。これは raw bundle 検証で final document と照合される実参照です（[silo_ladder_rung1.py:2811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/silo_ladder_rung1.py:2811)、[同:3454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/silo_ladder_rung1.py:3454)）。

成果物影響: g1 bytes を変えない本 wave では値は不変ですが、4-file inventory を後続 pin migration の閉包とすると raw proof bundle だけ旧参照のまま残ります。

修正案: tracked file を対象に exact hash を `git grep` し、件数を 5 file に訂正してください。raw receipt は歴史 artifact なので書き換えず、inventory に追加するだけです。

### 7. process receipt の自己照合は production 受理集合に対して非 load-bearing

深刻度: **nit**

根拠: guard は caller から receipt を受け取らず、cached receipt を取得して同じ cached state、PID、seal、object identity と比較します（[s2-plan.md:203](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:203)、[同:212](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:212)）。この condition を除いても、その直後の current `lookup()` が authority loader を起動します（[execution_guard.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/execution_guard.py:64)）。forged/stale/cross-process receipt のテスト（[s2-plan.md:232](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:232)）は leaf 直接呼出しだけで、偽 receipt が production guard に到達する call edge がありません。

成果物影響: 記述された call graph では receipt assert を削除しても certified 受理集合・JSON・WAL は変わらず、直接 unit test だけが赤くなります。

修正案: authorization contract を選択した時点の receipt を caller が保持し、guard へ渡して照合するか、保証を「guard が authority loader を発火させる」に狭めて forged/stale receipt を load-bearing 証拠に数えないでください。

### 8. ever-active 限定自体には、現存する certified artifact の締出し反例は見つからない

深刻度: **nit**

根拠: 初期 record は両 env の g1 を active にします（[s2-plan.md:105](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:105)）。追跡ファイルを予定 g2 contract hash `1346c20b…` で exact 検索した範囲では、docs/insights/test を除く既存 certified artifact は 0 件でした。存在する 94a4 記録は calibration publish/self-comparison であり（[published-self-comparison.json:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/output/env/pegasus/calibration/attempts/0_892707.nqsv/published-self-comparison.json:2)）、g2 contract hash を記録した run/proof chain ではありません。

成果物影響: serial 1 時点の直接的な historical 受理縮小はなく、拒否されるのは登録後も未 active の将来 g2 hash だけです。

修正案: A(b) は弱めないでください。ただし、この直接縮小ゼロと、所見 4 の calibration eager 検証による間接的な全体縮小を区別して計画へ記録します。

### 9. 8c condition 12 の凍結 evidence contract は activation receipt を観測しない

深刻度: **should-fix**

根拠: 先行 wave が指摘した `s8c_preregistration_evidence_contract.v1.json` は、condition 12 で `lookup` と既存 execution receipt だけを列挙しています（[evidence contract:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:431)、[同:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:463)）。プランの pin 閉包（[s2-plan.md:247](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:247)）にはこれがありません。現 evaluator も関数名の存在だけを見て（[s8c_preregistration_evidence.py:585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8c_preregistration_evidence.py:585)）、最終的には常に `EVIDENCE_UNDEFINED` です（[同:603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8c_preregistration_evidence.py:603)）。

成果物影響: 現在は C12 が satisfiable でないため certified 選択は変わりませんが、将来 activation receipt を C12 証拠と名乗る際は required-evidence 集合と `evidence_contract_sha256`／condition-freeze 参照が旧意味のまま残ります。

修正案: 凍結 g1 bytes は本 wave で変更せず、「C12 は activation receipt を証明しない」と射程を明記してください。必要になった時点で新 condition-freeze generation とユーザー裁定を伴う別 wave にします。

## 総括

1. **判定: NO-GO**

2. **must-fix: 4 件**

   - T-627 (c) を同一 wave 内で自己解除し、未批准の遷移形を production 化している。
   - temporary serial 2 は合成正例であり、B(a)/DW-G04 と永久 production fuse の区別を満たさない。
   - activation JSON が reviewed commit に束縛されず、uncommitted activation と valid-prefix rollback を許す。
   - 全 ever-active calibration の eager 検証が、一件の履歴障害を全 current admission へ拡大する。

3. **親 provisional 裁定への賛否**

   - **P1: 賛成。** g2 は登録のみ、初期 authority は両 env g1 が妥当です。ただし serial 2 issuer の production 有効化も、実 activation 裁定まで止める必要があります。
   - **P2: 反対。** テスト seam の無条件 fuse は落としますが、temporary record は合成正例であり B(a) を満たしません。
   - **P3: 賛成。** ユーザーが選んだのは (c) です。schema land 後に実装形を再裁定し、同一 wave 内で (b) へ自動移行してはいけません。
   - **P4: 賛成。** production module top-level での `lookup()` 発火反例は静的検索では見つからず、import I/O を避けて CLI parse 後に遅延する方向は裁定 E と整合します。