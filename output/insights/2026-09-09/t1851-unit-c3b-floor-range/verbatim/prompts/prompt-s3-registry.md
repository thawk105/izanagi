単独段 dispatch: stage=consult; lane=sol; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- 共有 admission root (repo 外、read-only): `/work/1/SFC/tanab/izanagi/.git/izanagi/s8b-holdout-admission-v1`
- 既存 registry: `/work/1/SFC/tanab/izanagi/.git/izanagi/s8b-holdout-admission-v1/floor-attempt-registries/db07b575390d1e6e76763c9dc7f5be9e07e270e101cd763eabc973b77e59cb41/d388477f0272b8d41fbc0e82956841cf5eff45f68b0c8fd40e74dc1bb6dae920/registry.jsonl`
- 同 freeze 直下の catalog: `/work/1/SFC/tanab/izanagi/.git/izanagi/s8b-holdout-admission-v1/floor-attempt-registries/db07b575390d1e6e76763c9dc7f5be9e07e270e101cd763eabc973b77e59cb41/consumption-catalog.jsonl`
- 親の段 1 brief: `/home/SFC/tanab/.claude/jobs/c311da24/tmp/dev-wave-t1851-unit-c3b/s1-brief.md`
- 段 2 plan: `/home/SFC/tanab/.claude/jobs/c311da24/tmp/dev-wave-t1851-unit-c3b/out-s2-plan.md`
- 2026-09-01 に同じ file を blocker と報告した所見 (A-5): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-01_t1946-t2107-registry-wiring-design/verbatim/s3-r1-lens-a.md`
- 直前単位 C3a の記録: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-09_t1851-unit-c3a-wiring/README.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 焦点相談 — 既存 registry が official 走行を塞ぐか

作業 root は read-only である。**書込み可能な tmp は無い。** pytest 緑を要求しない。
静的読解と grep と上記 file の読み取りだけで結論を出す。**走らせていないものを緑と書かないこと。**

**file を 1 つも作れない。** 成果物は**最終メッセージの本文へ全文を書く**こと。
予算が尽きそうなら、**途中結論を下の出力形式どおりに書いて終わること** (無出力が最悪)。

この段では commit を作らない。git の状態を変えない。

## 親が実測した事実

1. 共有 admission root は git common dir 配下で全 worktree 共有である
   (`s8b_holdout_admission.py:620-637`)。
2. `floor-attempt-registries/` 直下に entry が 1 つだけある。freeze `db07b575…`、
   protocol `d388477f…`、schedule `8e88f839…`、`schema_version` は
   `s8b-floor-attempt-registry/v1`、genesis の `slots` は **96 件**、
   全 193 行の内訳は `freeze` 1 + `start` 96 + `pre-observation-seal` 96 で、
   **`classification` も `terminal` も 0 件**である。
3. `start` 行の `process_identity` は `{"execution_uuid": "campaign-fixture-execution",
   "pid": 101, "starttime": "campaign-fixture-starttime"}`、`run_start_receipt_sha256` は
   `4444…44` である。**test fixture の値が本番の共有 root に書かれている。**
   file の mtime は 2026-08-27 19:53。
4. 段 2 plan は、現行コードの genesis が **288 slot** (`repetition=0..7`、
   `measurement_ordinal=0..2`、`attempt_ordinal={0}`) を宣言すると読んだ。
5. `db07b575…` は test の `_freeze_sha(_freeze_document())` と同一値として
   `test_s8b_floor_campaign.py` の失敗ログに現れる。

## 決めたい問い (この順に答える)

**Q1. fresh な official production 走行が使う `freeze_sha256` と `protocol_sha256` は、
上記の `db07b575…` / `d388477f…` と一致するか。**
- `protocol_sha256 = _canonical_sha256(protocol)` である
  (`s8b_floor_campaign.py:8667-8677`)。この `protocol` が official 走行で何から作られるかを
  現物で辿り、`output/s8b-freeze/floor_protocol.json` および `tools/pegasus/floor_campaign.sh` が
  driver へ渡す引数から、実行時の値が上の 2 値と一致するかを判定せよ。
- 一致する / しない / 静的には決まらない、のどれかを明示し、根拠を file:line で示す。
  **決まらない場合は「実行時にしか決まらない」と正直に書き、投入前に安価に確かめる方法を書け。**

**Q2. 一致する場合、走行はどこで何と言って止まるか。**
- 既存 genesis (96 slot) と新 plan の genesis (288 slot) が同じ path で出会ったとき、
  どの関数のどの行が何を検査し、どの例外文言になるかを追え。
- `slot was reserved more than once` (`attempt_registry_core.py:1232-1235`) に到達するのか、
  その手前の genesis 照合で止まるのかを区別せよ。
- **fail-closed で止まるのか、既存 genesis を再利用して静かに進むのか**を判定せよ。
  後者なら正しさ上の重大事である。

**Q3. `consumption-catalog.jsonl` (96 行) は何を塞ぐか。**
- 2026-09-01 の A-5 は「freeze 直下の未知 entry を fail-closed にする」計画に対し、
  この catalog が未知 entry として止めると報告した。**その後 C1b / C2 / C3a で解決されたか**を
  現物で確かめよ。解決されていないなら、official 走行のどの段で止まるかを示せ。

**Q4. 親が取りうる手はどれか。** 次を評価し、推奨を 1 つ選べ。
- (a) そのまま投入し、止まるならその停止を実測として記録する (fail-closed の実証)。
- (b) 投入前に fixture 行の由来を特定し、どのテストが本番 root へ書いたかを報告する
  (実装面の修正は本 wave の scope 外。報告だけ)。
- (c) 別の freeze / protocol 世代で走らせる。**これが可能かを現物で判定せよ** —
  可能でないなら「不可能」と書け。
- (d) 走行を諦め、裁定パッケージへ返す。
- **本 wave の目的は「gate 入力の実値域を実測して receipt にすること」である。**
  止まった場合でも「どの gate がどの値で止めたか」は実測値であることを考慮せよ。

**Q5. 上記の fixture 行が本番 root にあること自体の危険度。**
- 規律 2 (正しさゲート) と規律 6 (信頼境界) の観点で、これが何を脅かすかを 1 段落で書け。
- 本 wave が触ってよい範囲 (親は実装面を編集しない、land しない) を踏まえ、
  どこへ報告すべきかを述べよ。

## 出力形式

次の H2 だけを使い、この順で書く。

## 総括
## Q1 protocol と freeze の一致判定
## Q2 一致時の停止点
## Q3 catalog の影響
## Q4 推奨する手
## Q5 危険度と報告先
## 未解決の問い

結合文字 U+0300〜U+036F を出力に使わないこと。
