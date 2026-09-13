---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-t1706-schedule-bytes-toctou
seq: 2
---

## {{D:schedule-authenticated-bytes-one-read}}. A/B 装置の schedule は 1 回だけ読み、認証した bytes をその後の file 状態から切り離す

**決定:** `tools/codex_reasoning_ab.py` の 3 入口 (`supervise_pair` / `_replay_manifest` /
`make_packets`) は、schedule file を**一度だけ読み、その同じ bytes から descriptor SHA・
`schedule_sha256`・解析済み schedule のすべてを導く**。

- `supervise_pair` の authority は **run root の frozen copy** である。source との bytes 比較を
  残したまま、frozen を 1 回読み、その bytes を SHA と解析の両方に使う。
  source bytes を authority にしてはならない — それは現行が持つ「壊れた frozen を拒否する力」を失う。
- `_replay_manifest` と `make_packets` は `_artifact_path_with_bytes` から bytes を受け取る。
  この helper は `_artifact_path` と同じ検査順序・rc・reason を持ち、**内部で `read_bytes()` を
  1 回だけ**呼ぶ。`_artifact_path` 自体は変更しない。
- bytes を受け取る JSON loader へ渡してよいのは、**同じ操作で同じ path から読んだ bytes だけ**である。

**受理集合について明示する事実:** 呼び出し中に変化しない input に対する受理・拒否・rc・reason は
不変である。**呼び出し中に変化する input に対しては挙動が変わり、それが本決定の目的である。**
例えば descriptor 照合の後に file が消えた場合、従来は再読が失敗して拒否したが、以後は
最初の読みで得た bytes で続行する。これは検査の弱化ではなく、
**認証した bytes を、その後 file が何を持っているかから切り離す**という契約である。

**理由:**
- 同一 UID の書き手が A→B→A と差し替えると、従来は A の SHA を receipt に残したまま B の slots
  (arm↔model の割付、price version、cardinality、slot_id 集合) で検査・集計が通った。
  receipt の `schedule_sha256` は「どの schedule で測ったか」を認証する trust root なので、
  ここが開いている限り certified 判定の意味が保証されない。
- 読む回数を減らすだけでは足りない。**残る 1 回が元と同じ対象を読まなければ、
  欠陥は別の場所へ移るだけである** ({{F:one-read-swaps-the-observed-artifact}})。

**却下した選択肢:**
- **source bytes を supervisor の authority にする** — 段 2 の起草案。読み回数は減るが、
  frozen の観測を失い、書き込み後に壊れた frozen を現行どおり拒否できなくなる。
- **`_artifact_path` の戻り値を `(path, bytes)` へ変え全 caller を移行する** — 横断 refactor であり、
  本題に不要な変更面を広げる。
- **file descriptor を保持して inode を固定する** — 同一性の要件は「hash と解析の入力が同じ bytes で
  あること」であり、読み取り後の immutable bytes を共有すれば満たされる。
