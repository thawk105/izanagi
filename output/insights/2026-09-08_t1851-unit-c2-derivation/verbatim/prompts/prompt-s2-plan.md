単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- 親の段 1 brief: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s1-brief.md`
- **契約の正本 (これが scope を決める)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 直前の単位 C1b の実装記録: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-c1b-implementation/README.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 2 — 単位 C2 の実装 plan を file:line 粒度で起草する

作業 root は read-only である。**書込み可能な tmp は無い。** したがって
**pytest 緑を要求しない。静的読解と grep による実測だけで結論を出す。**
テストの実走は親が行う。**走らせていないものを緑と書かないこと。**

**file を 1 つも作れない。** 成果物は**最終メッセージの本文へ全文を書く**こと。
「file へ書いた」と述べても親には届かない。

予算が尽きそうなら、**途中結論を下の出力形式どおりに書いて終わること** (無出力が最悪)。

## scope

契約 v3.1 の 3 節と 9 節が「C2 が持つ」と切った 4 点を実装する plan を作る。

1. runner の構造化 `execution_failure`
2. campaign の算出変更
3. rep observation の 6 key → 7 key 化とそれに伴う凍結 gate の pin 閉包
4. `launch_floor_attempt()` の実環境値域の供給

## 親が既に実測した事実 (再測は不要。誤りと判れば指摘すること)

| 対象 | 実測 |
|---|---|
| runner の rep 実行例外捕捉 | `orchestrator/calibrator/runner.py:958-981` の 2 枝。どちらも `n_exec_fail += 1` と自然文 note の append |
| 集約 note | `runner.py:1029` と `runner.py:1247` が `f"{n_exec_fail}/{reps} reps failed to execute"` |
| campaign の算出 | `orchestrator/campaign/s8b_floor_campaign.py:1879` の `_EXEC_FAIL_RE` を `notes` へ当てる (`:1882-1892`) |
| rep observation の現 key 集合 | exact 6 key。`complete` 述語が `set(observation) == {6 key}` を要求 (`s8b_floor_campaign.py:1039-1045`)、欠落時 padding は `:1904-1917` |
| rep observation の生成 | `runner.py:990-1000` の `finally` 節 |
| `launch_floor_attempt()` の production 呼び手 | **0 件** |
| launcher module の import 元 | **repo 全体で 1 件、`orchestrator/tests/test_s8b_floor_attempt_launcher.py:24` だけ** |
| campaign から `attempt_registry` への参照 | **0 件** |
| 変更しうる 7 file の whole-file SHA-256 golden | **0 件** (現 hash を repo 全体で検索) |
| `FROZEN_MANIFEST` | output 23 path の figure 束縛のみ。対象外 |

## 決めてほしいこと

### A. 4 点目の射程 (親の provisional 裁定を攻撃してよい)

親の provisional 裁定は「C2 は campaign 側が実値を構造化して産出する状態を作り、
その実値域を実 campaign 経路の実測として記録するところまでを持つ。
`launch_floor_attempt()` を実際に呼ぶ配線は別単位に残す」である。

- この読みで契約 9 節の「実値域は C2 が供給する」を満たせるか。
- 満たせないなら、**何をどこまで配線すれば満たせるか**を file:line で示すこと。
- 配線する場合の変更量 (触る file 数・行数の見積り) を出すこと。

### B. 構造化 `execution_failure` の形

- rep observation の 7 番目の key として何を載せるか (key 名、値の型、値域)。
- 例外が起きなかった rep では何を載せるか (`None` か、それとも key 自体を出さないか)。
  **`complete` 述語が `set(observation) == {...}` の exact 等値なので、key の有無を
  rep ごとに変えると述語が壊れる。** どちらを採るか根拠つきで決めること。
- 例外の型・message をどこまで載せるか。**外部由来の文字列を信頼経路へ持ち込まない**
  という規律 6 の観点で論じること。

### C. campaign の算出変更

- `_count_exec_failures` と `_EXEC_FAIL_RE` を消すか残すか。消す場合の呼び手の閉包。
- 新しい算出が `rep_integrity_failures` と**別の量**であり続けることを、
  どの test でどう固定するか (契約 3 節)。
- 証跡 carrier が欠落したとき (`s8b_floor_campaign.py:1904-1917` の padding 経路) の
  7 番目の key の値をどうするか。

### D. 6 key → 7 key の pin 閉包を閉じ切る

親が引いた閉包 (brief 5 節) を出発点に、**残りを file:line で列挙すること。**
とくに次を確定させること。

- `orchestrator/tests/s8b_v2_freeze_fixture.py:155-163` が作る 6 key の observation が、
  `test_s8b_holdout_freeze.py` / `test_s8b_oracle_driver.py` /
  `test_s8b_oracle_manifest.py` / `test_s8b_oracle_report.py` の
  **どの 64hex literal に伝播するか**。伝播しないなら「しない」と根拠つきで書くこと。
- `missing_perf_events` を参照する 12 file のそれぞれについて、
  **6 key の exact 等値に依存しているか / いないか**を 1 行ずつ判定すること。
- `orchestrator/tests/test_official_perf_closure.py` の `_REVIEWED_PERF_FILES` (`:43`)、
  `_production_perf_files()` (`:533`)、集合等値 assert (`:905`) に触れずに済む実装配置。
- `orchestrator/tests/test_t671_source_binding.py` の 63 path exact tuple と
  件数 assert (`:267-269`) に触れずに済む実装配置。

### E. 実装子の分割

何本・直列か並列か・各子の所有 file を排他で決めること。
**同じ file を 2 本の子に持たせないこと。**

### F. 変異の照準 (次段で事前登録する)

この変更で「通れば正しさが壊れているはず」の変異を 5〜10 件、
**変異する file:line と、それを殺すはずの test node id** の対で挙げること。
**通常経路で殺せないものがあれば、そう明記して専用の kill 手段を書くこと。**

## 禁止

- file を作らない・書き換えない。commit しない。`git` の状態を変えない。
- 走らせていないテストを緑と書かない。
- 新しい production file を足す案を既定にしない (brief 5 節の 2 つの exact inventory が落ちる)。
- v1 (非 v2) 側の event key 集合・受理集合を変える案を出さない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式 (この見出しをこの順で使う。本文へ全文を書く)

## A. 4 点目の射程
## B. 構造化 execution_failure の形
## C. campaign の算出変更
## D. pin 閉包の残り
## E. 実装子の分割
## F. 変異の照準
## 親の実測への異議
## 総括
