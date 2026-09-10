単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer

必読事項の射影: 次の 4 ファイルを読め。**どれか 1 つでも読めなければ即停止し、その旨だけを出力せよ。**

- 親 brief (段 1。**これ自体も攻撃対象**):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/brief-s1.md`
- 段 2 プラン (攻撃対象):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s2-plan.md`
- 一次資料 (前 wave の insight 全文。§11 が残る限界):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/verbatim-insight-rejected-witness.md`
- 設計正本 §3 の逐語 (§3.3 issuer の位置と create-only 順序、§3.5 member 写像):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/verbatim-design-s3.md`

# 段 3 — 敵対相談 レンズ B (整合と実効性: bytes 不変・pin 閉包・端から端の材料)

あなたは izanagi の dev-wave 段 3 の敵対検証子である。プランを守るな、検査せよ。親 brief 自身も検査対象である。
**実装はするな。ファイルを 1 byte も編集するな。commit するな。**

## repo

cwd は worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer` (local main 34af5a571 と同一)。
プランが引く file:line は必ず現物で確かめよ。巨大ファイルは `grep -n` で位置を出してから `sed -n 'A,Bp'` で読め。
書込可能な tmp が無いので pytest の緑を要求しない。静的検査でよい。走らせていないものを緑と書くな。
予算が尽きそうなら途中結論を出力形式どおりに書いて終われ。無出力が最悪である。

## このレンズの攻撃面

1. **端から端の正例の材料は実在するか。** プランの「実 verifier 走から作った record を fixture の origin 一式へ差し替えて consumer を FC07 まで通す」test について、差し替えに要る各材料 (ledger member の `constraint_sha256` / `evidence_digest`、`_wal_records` の trigger binding、`build_attempt_id`、source closure / authority の digest 連鎖、`recovery envelope` の salts) が `reflux_origin_fixture_builder.py` と `reflux_origin_ledger.py` の現行 API で差し替え可能かを file:line で検査せよ。**差し替えられない材料があれば名指しし、プランの到達点が実際にはどこで止まるか**を書け。「実装したふり」を許すな。
2. **bytes 不変の裏取り。** fixture builder と `test_reflux_result_evidence.py` の golden 4 個、`test_reflux_formal_consumer.py` の baseline digest (`test_baseline_schema_and_every_entry_match_independent_recalculation`) が、プランの編集面で 1 byte も変わらないことを file:line で裏取りせよ。(P1) の import 差し替えが consumer の source-hash や `test_consumer_source_has_no_nonaborted_construction_or_success_variant` に触れないか確かめよ。
3. **pin 閉包。** `git grep` で `reflux_result_evidence` / 新関数名候補 / 新 test file 名の pin (自走 harness の登録、`orchestrator/tests/README.md`、`acceptance_duration_ledger.json` の被覆率 gate、xdist group、role 名) を全列挙し、プランの「pin 閉包」節の見落としを名指しせよ。path 検索 0 件を pin なしと結論するな。
4. **S3 (ordered WAL projection の producer) の実効性。** `_canonical_wal_interval` (618-645) は canonical-list 経路と frame 経路の 2 つを受理する。production `wal.jsonl` は frame 経路である。プランの逆関数が、frame 境界 (改行)・build_attempt 区間の決め方・`source_wal_ref` の content-addressed path・byte_start/byte_end の決定性で consumer の検査を通るかを file:line で検査せよ。通らない入力があれば示せ。含める価値が無いなら scope 外へ送る根拠を書け。
5. **親の実測値の一般化。** brief §1 の fixture 実測は `test_verifier.py` の synthetic Silo source 束縛の下での値である。production の verifier 呼び出し (`pipeline.py` 1590 付近) は同じ束縛か。束縛の差で `certified` / `integrity.clean` が変わり、producer の 3 方向分岐の到達可能性が test と production で食い違わないか検査せよ。
6. **scope の境界。** プランが親 brief §2 の scope 外 (provenance issuer、run_campaign 配線、production 呼び手) を暗黙に前提にしていないか、逆に scope 内で不要な一般化・gate・台帳を足していないか (DW-G05) を検査せよ。

## 出力形式

所見ごとに H2 見出し `## B-<n>: <一言>` を置き、各所見に次を必ず書け:
- **主張** (1〜2 文)、**根拠** (file:line)、**帰結** (放置時に成果物・受理集合・参照がどう変わるか 1 行、DW-G05)、**推奨** (採用 / 修正案 / scope 外へ送る)、**確度** (real 確定 / 要実測 / 推測)。
最後に `## 総括` (5 行以内: real 確定の件数、最も重い所見、プランを支持するか) を必ず置け。
出力へ結合文字 U+0300〜U+036F を使うな。
