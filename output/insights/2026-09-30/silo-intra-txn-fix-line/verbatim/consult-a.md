## 所見

- **C1｜must-fix｜P3** — 前回の計装 patch は `#line 658` を hunk の文脈に含むため、`#line 661` にした新 tip には厳密適用できない。放置すると trace job が計装前に停止し、新 tip の D1・D2b を再確認できない。**推奨:** 新 tip 用 patch を作り、厳密適用と「`#if TRACE` を除けば土台と一致」の照合を行う。根拠: `instr-silo-gate-witness-F.patch:136-152`、`tip-7e5fa528-silo-transaction.cc:701`、`launch_gate_liveness_v2.py:135-136`。
- **C2｜must-fix｜P2・P3** — 流用予定の起動器は修正 tip の直接の親を F と固定している。新 tip の直接の親は `7e5fa528` なので、現状では CI build、D297、trace の前提検査が通らない。放置すると実行前の停止を CI/D297/trace の結果と取り違える。**推奨:** 直接の親を `7e5fa528` と検査し、別に F が祖先であることと F→新 tip の差分 path が Silo の 1 file であることを検査する。根拠: `s1-brief.md:4,9-11`、`run_ci_then_judge.sh:14-19`、`run_judge_v2.sh:46-50`、`launch_gate_liveness_v2.py:111-122`、`mk-synth.sh:24`。
- **C3｜should｜P2** — (b) の差分 path は既知の 4 file だが、brief は `--expect-paths` を省いている。放置すると想定外の変更 file が増えても、比較が一致さえすれば (b) を pass と読める。**推奨:** (b) に `cc/mocc/transaction.cc`、`cc/silo/transaction.cc`、`include/tpcc.hh`、`include/trace.hh` の 4 path を指定する。根拠: `s1-brief.md:9`、`silo-intra-txn-fix/README.md:63`、`check_trace0_preprocess_identity.py:217-237`。
- **C4｜should｜P2・計算見積り** — (a) F→新 tip は、取引内の値の修正があるため前回と同じ理由で拒否される見込みで、今回必須の (b) の証拠を増やさない。`7e5fa528`→新 tip も `ERR` の行番号差による拒否が見込まれる。放置すると追加の拒否結果を成果の判定材料と誤読しうる。**推奨:** D297 の本走は必須の (b) に絞り、(a) は前回の結果を参照する。根拠: `s1-brief.md:9,13`、`silo-intra-txn-fix/README.md:59-65`、`predict.log:25-30`。
- **C5｜must-fix｜P5・成果物** — 前回の主 checkout 取り込み script は、同名 branch が既に `7e5fa528` を指すと停止し、さらに「tip の親 = F」を要求する。放置すると新 tip を主 checkout の submodule ref に取り込めず、D2305 項 6 の順序で push を依頼できない。**推奨:** 既存 ref から新 tip への fast-forward を確認して取り込む手順に更新し、取り込み後に push 依頼を出す。根拠: `fetch-fix-to-main.sh:23-34`、`s1-brief.md:5,14`、`D2305-item5-6.md:14-15`。
- **C6｜should｜P5・成果物** — 前回 commit message の「TRACE=0 #line directives are untouched」は新 commit 後の branch 全体の説明として偽になる。放置すると一次資料、上流説明、[T-2917] の前提が旧 tip のまま残る。**推奨:** 新 commit message と一次資料・spool・push 依頼文に、4 本を +3 した理由、D297 (b) の実測結果、新 tip の完全 SHA を明記する。根拠: `s1-brief.md:12,14`、`md_12.txt:19,23`、`silo-intra-txn-fix/README.md:31,93-104`、`7e5fa528` の commit message。

## brief で正しいと確認した点

- read の修正 hunk は行数を変えず、update は +3 行。したがって update 前の `#line 365/381` は据え置き、後の 4 本だけ +3 する選択は整合する。TRACE=0 の `ERR` は候補で P′ と同じ `106/693` になった。根拠: `tip-7e5fa528-silo-transaction.cc:366,384,528-536,669,701,731,755`、`predict.log:5-29`。
- probe の `-P` 比較は Silo 単体の予測として有用。行 marker を残した差は、検査器の .cc 正規化と header の完全展開比較ではそのまま拒否理由にならない。ただし include 展開、他の entry・文脈、GCC 11・12 の (b) pass は未確認。根拠: `predict.sh:21-31`、`predict.log:29-70`、`source_digest.py:1647-1689`、`check_trace0_preprocess_identity.py:831-859`。
- P′→P‴ を親子にし、新 tip と同じ tree を持たせる (b) の構成は検査器の祖先条件に合う。F→新 tip も F が祖先なので (a) の比較自体は可能。根拠: `mk-synth.sh:29-38`、`check_trace0_preprocess_identity.py:1081-1090`。
- `#line` の数値変更は通常の trace 記録や判定器の入力を変える経路が見当たらないが、診断に使う論理行番号は変わる。format は新 tip の clean checkout で実行して確認する必要がある。CI build script の `PARENT_OID` に `7e5fa528` を渡す設計は妥当。根拠: `tip-7e5fa528-silo-transaction.cc:608-619,669-755`、`run_ci_build_v2.sh:39-45`。

## 総括

4 本だけを +3 する方針と D297 (b) の取り直しは妥当です。実行前に **計装 patch、直接親を固定した起動器、主 checkout への fast-forward 取り込み**を直す必要があります。(b) の一致は予測段階であり、上流 CI 相当・D297・trace の緑はまだ主張できません。