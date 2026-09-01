---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1981-t088-floor-rerun
seq: 1
title: [T-1981][T-088] 消費済み 12 cell の再測定を第 2 の独立観測で確かめ、2 つの測定世代が同じ 12 cell を同時に保持することを実機で見た (実測のみ、実装差分ゼロ、branch worktree-dev-wave-t1981-t088-floor-rerun、終端はエントリ 1135 が閉じた、変異 matrix は DW-S04 の免除)
---

## 本文

- **同一タスクの wave が 2 本、7 秒差で床値 job を投入した。** 本 wave の `964044.nqsv`
  (10:40:16 作成) と、別 session `dev-wave-t1981-t088-floor-remeasure` の `964035.nqsv`
  (10:40:09 作成)。依頼文が同じで、どちらも [T-1981] 残件の実機証明を目的にしていた。
  相手 session から連絡があり、両者で分担を決めた — **測定は 2 本とも走らせ、
  [T-1981]/[T-088] を閉じる記録と land は先発の 964035 側が持つ。本 wave は締めの fragment を
  書かず、自分の走行を第 2 の独立観測として渡す。**
- **「片方を落とすべきか」は実測で決めた。** 共有台帳の lock は
  `s8b_holdout_admission.py:602` が `fcntl.flock(fd, fcntl.LOCK_EX)` を **timeout も
  `LOCK_NB` も付けずに**取る。競合しても失敗せず直列化するだけなので、
  「並行しているせいで片方が偽の赤で落ちる」経路は台帳境界に無い。lock file は
  `git rev-parse --git-common-dir` 配下の同一 inode で、両 worktree が共有する。
  node 占有の節約より、床値 job が過去に何度も落ちてきた事実に対する冗長性を採った。
- **結果として、2 本走らせたからこそ取れた観測が 1 つ得られた。** 台帳には
  `measurement-generation-claims` が 24 件、**世代 digest 2 つがそれぞれ同じ 12 cell を
  同時に保持している**状態が実機で成立した。D1190 決定 3 (別世代からは同じ論理 attempt を
  消費できる) の陽性証拠であり、1 本では取れない。
- **依頼文の前提 2 件が一次資料と食い違っていたので、着手前に実測して brief に出した。**
  (a) 依頼文と [T-088] の持ち越し本文は「2026-08-24 に一度走って**途中で死に**、成果物が
  残っていない」とするが、worklog 1053 が否認している — 当該 run
  (`945229.nqsv` / campaign run id `20260824T205358Z-2c8cf9be`) は driver_rc=0 で完走し、
  12 cell x 8 session = 96 attempt がすべて valid だった (worklog 924 の記録とも一致)。
  **D1124 の決定自体は覆らない** — 中核の論拠は run が死んだか否かに依存しない。
  ただし成果物影響は「床値が 1 つも出ない」ではなく「**同じ cell を測り直せない**」が正しい。
  持ち越し stub は 1029 から一度も更新されていなかった。
  (b) 1112 の「根クラス 1 だけ直しても床値の主経路は赤のまま」は、より新しい 1119 が
  訂正済みだった — 床値 job の赤は cache hit 条件ではなく**無条件**で (F754)、原因の
  `_external_entry` は `2e35a2596` で置換され、受理境界の欠陥 4 件も 1119 が着地させている。
  残る根クラス 2 (D1322、実装待ち) は run 間 cache hit の話で、1119 は「run 間 hit はそもそも
  成立しない」を real だが backlog と裁定している。**[T-2043] の「赤の解消は未確認」を
  確認する行為が本 wave の投入そのものだった。**
- **投入前に台帳を実測し、証明が恒真にならないことを確かめた。** `claims` 36 件・
  `consumed` 228 件・`ledger.jsonl` 36 行、role 内訳は floor_campaign / n_pilot /
  oracle_driver が各 12。**旧 12 cell は退避も削除もせずそのまま残して投入した。**
  投入元の `git rev-parse --git-common-dir` が `/work/1/SFC/tanab/izanagi/.git` であることを
  実測で記録した (推論しない)。
- **合格条件は前 wave が凍結した裁定をそのまま継承し、緩めなかった** (逐語は
  `output/insights/2026-08-27_t1981-holdout-oneshot-removal/verbatim/s4-adjudication.md` §6-C)。
  4 点は (1) `already consumed` 系の拒否が出ない、(2) `campaign-start` が新 journal に出る、
  (3) 最初の attempt 消費が通る、(4) driver_rc=0・terminal completed・96 session・
  floors 有限。**`floor-driver/run-linked` は build と予約より手前に出るので合格条件にしない**
  という注意書きも守った。4 点すべて充足した。
- **相手 session が本 wave の実測を 1 件訂正し、受け入れた。** 本 wave は台帳の現況として
  「`ledger.jsonl` 36 行は不変」と伝えたが、これは投入前に測った値を測り直さずに書いたもので、
  実際には 60 行へ増えていた (旧 12 + 新 2 run 各 12)。`claims` 36 / `consumed` 228 の不変は
  再測でも一致した。**結論は変わらず、むしろ「新しい予約が台帳へ着地した」証拠が 1 つ増えた。**
- **本 wave が相手 session を 1 件訂正し、受け入れられた。** 測定世代の導出は**三段**である
  (`s8b_holdout_admission.py:795-802`, `:805-814`)。
  `measurement_generation_id = sha256({observation_role, campaign_run_id})`、
  `measurement_generation_digest = sha256({measurement_generation_id, observation_role,
  campaign_run_id})`、marker の file 名に使う
  `measurement_generation_claim_digest = sha256({measurement_generation_digest,
  cell_effect_digest})`。相手が最初に一致を取ったのは第 1 段の id で、digest ではなかった。
  **本 wave も同じ取り違えを一度書いており、相互に直した。** D1190 決定 2 が定めているのは
  id の導出であって digest ではない。
- **旧 v1 claim との照合は `cell_effect_digest` では成立しない。** 旧 claim はその field を
  持たないため、両者共通の不変座標 — `key` の 6 field (ccbench_pin / configuration_id /
  env_tag / freeze_holdout_key / freeze_sha256 / observation_role) と `cell_id` — を
  canonical JSON にして集合比較した。**両世代とも旧 floor_campaign 12 cell と完全一致した。**
- **`submit_floor.sh --dry-run` の緑は投入可能性の証拠にならない。** dry-run は third-party の
  payload staging を飛ばす。新規 worktree で dry-run rc=0 を得た直後の実投入が
  `floor third-party source root is missing or unsafe` で rc=2 になった。
  `python3 tools/pegasus/fetch_third_party.py hydrate --cache-root
  /work/1/SFC/tanab/izanagi-thirdparty-cache` を先に走らせる必要がある。
  **相手 session も独立に同じ順序で同じ 3 つの rc を踏んだ** (dry-run rc=0 →
  実投入 rc=2 → hydrate 後 rc=0)。
- **実測値。** request `964044.nqsv`、Elapse 2981 秒 (49.7 分、所要は job の Elapse を正とする)、
  source commit は `2bf9cf387643bf7ac087c31f5c38cfcc5539de68` = 着手時点の main で、
  **wave の差分をひとつも含まない tip で測っている。** mode=pilot、
  campaign run id `20260901T014045Z-2c8cf9be`、env_tag=pegasus、
  ccbench_pin `511c9538e4e8efa54b45cda62e72389ed3b706ec`。journal の event 内訳は
  campaign-start 1 / round-start 8 / session-start 96 / session 96 / round-complete 8 /
  terminal 1 で、terminal の status は `completed`。96 session すべて valid、
  `excluded` は空、全 cell で `machine_anomaly` false、cv の最大は 0.015189 (閾値 0.15)。
  床値は rr20 が `scalar_alt` 36025.347768718944 / pairs 35548.244999999995
  (p2_2_flag_opt のみ 36025.347768718944)、rr80 が `scalar_alt` 75975.56513657157 /
  pairs 45835.665 (同じく p2_2_flag_opt のみ 75975.56513657157)。`eligible_for_refreeze` は
  pilot なので false。ポイント消費は 2 job 合算で約 30.5 (13176.47 → 13146.01)。
- **完走後の台帳。** 世代 claim 24、世代 consumed 192 (= 96 x 2 job)、
  `attempt-ledger.jsonl` 420 行 (= 228 + 192)。**旧 `claims` 36 件と旧 `consumed` 228 件は
  投入前と 1 件も変わっていない。** 新 marker は
  `measurement-generation-consumed/{claim digest}-{sha256(attempt_id)}.json`、
  旧 96 marker は `consumed/{claim digest}-…` で名前空間が分かれている。
  本 job の submission record と job evidence 全体を `grep -rl "already consumed"` して 0 件。
- **2026-08-24 の値との比較は断定していない。** worklog 1053 は当時の値を rr20 `scalar_alt`
  3.555e+04 / rr80 4.551e+04 と記録するが、今回の rr80 は `scalar_alt` 7.598e+04 で
  **pairs 値の 4.584e+04 のほうが 1053 の記録に近い**。1053 の 4.551e+04 がどちらの量かを
  当時の result.json で確かめていないので、「値が動いた」とも「動いていない」とも書かない。
- **子は 0 本。** 設計択一が割れず、正しさ防壁に触れず、受理集合も変えない実測 wave なので
  `DW-C00` の既定の軽量版とした。実装面の差分はゼロで、`DW-S04` により変異 matrix を免除する。
  受入全走は免除していない。
- 走行の一次資料は repo 外へ退避した (job directory 配下の evidence bundle と
  `/work/1/SFC/tanab/izanagi-job-evidence/pegasus/964044.nqsv/`)。repo には入れていない。
- **[T-1981]/[T-088] の終端は先発 wave が閉じた (エントリ 1135)。本 wave はそちらを重複させず、
  本項の carry からも外している。** 分担どおり、本 wave の走行は第 2 の独立観測として
  先発の記録に組み込まれた。
- **先発が 3 走行を並べて構造を 1 つ見つけたので、本 wave の値の読み方もそれに従う。**
  rr80 の非 p2_2 pair は 3 走行で 45509.145 / 45692.985 / 45835.665 と 0.72% 以内に収まるのに、
  `scalar_alt` は 45.5k / 48.5k / 76.0k と動く。差はすべて p2_2_flag_opt 由来で、
  床値は通常 3% の相対床に張り付き、最高スループット cell のノイズ項がそれを超えたときだけ
  持ち上がる。**本 wave が rr80 で得た 75975.57 は「値が動いた」ではなくこの性質の現れである。**
  繰り返し測れるようになって初めて見えた観測であり、gate は足していない。
- **本 wave が断定を避けた点は、先発が一次資料で埋めた。** 1053 の rr80 4.551e+04 が
  `scalar_alt` か pairs かは、945229 の evidence bundle の result.json で `scalar_alt` = 45509.145
  かつ 5 pair 同値と確定した。材料は先発の側にあり、本 wave の手元には無かった。

- **明示 carry が並行 wave の land を止める経路を実測した。** 本 fragment は当初
  `[T-1981]` `[T-088]` `[T-2043]` の 3 件を `### carry` へ明示していたが、先発 wave が
  前 2 件を完了させて active 集合から外したため、そのままでは fold が
  `transition-target: active でない操作対象` で止まる状態になっていた。
  `tools/spool_fold.py:1815-1830` を両 wave が独立に読んで裏を取った — `carry` は `新規` 以外の
  操作として `action_by_id` に入り、直後の `set(action_by_id) - set(active_by_id)` が
  空でなければ例外になる。**停止は land lock の内側で起きるので、受入全走を通した後に初めて分かる。**
  `docs/spool/worklog/README.md` の「明示 carry と暗黙 carry は同じ出力を生む」は、
  当該項が active であり続ける間だけ真であり、**その一文が正当化している並行 wave の状況で
  ちょうど偽になる。** 触れない active 項は fold が自動 carry するので、
  自分が動かさない項を明示 carry する理由は無い。本 wave は carry を `[T-2043]` 1 件へ落とした。
  文書の是正は本 wave の scope 外 (依頼が実機証明だけに絞られている) なので次の一手へ立てる。

## 次の一手差分

### carry

- [T-2043]

### 新規

- {{T:spool-carry-explicit-active-drift}} **P2・新規**: `docs/spool/worklog/README.md` の
  「明示 carry と暗黙 carry は同じ出力を生む」を、並行 wave で偽になる条件付きの記述へ直す。
  別 wave が先に完了・見送りした項を明示 carry している fragment は fold が
  `transition-target` で止まり、しかも停止は land lock の内側なので受入全走を通した後に初めて
  分かる。**是正は文言だけとし、`spool_fold.py` の挙動は変えない** — 現行の拒否は正しく、
  変えるべきは「安全側だと読める書き方」のほうである。
