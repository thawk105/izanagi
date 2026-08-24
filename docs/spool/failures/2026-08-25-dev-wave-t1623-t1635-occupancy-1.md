---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1623-t1635-occupancy
seq: 1
---

## 新規

### {{F:strict-suffix-defeated-by-normalization}}. 厳密 suffix 判定を正規化後の値に掛けて防壁を骨抜きにした [恒真ゲート]

- 事象: 削除済み cwd を非占有として数える条件に「`readlink` の結果が正確に `" (deleted)"` で
  終わること」を課したが、実装は `os.readlink()` の戻り値を `_lexical_absolute()` で
  正規化してから suffix を判定していた。cwd link の生値が
  `/outside/gone (deleted)/child/..` のような入力は正規化で `/outside/gone (deleted)` へ
  畳まれて判定を通り、本来 `indeterminate` + cwd issue であるべきものが
  `status="unoccupied"` / `issues=[]` になった。撤去してよいと誤答する側へ倒れる。
- 根本原因: 「readlink の**結果**」という裁定文言を、実装が「readlink 由来の値」と読み、
  正規化を挟んでも同じだと扱った。suffix は path の意味ではなく **kernel が付ける文字列の目印**
  であり、正規化はその目印を保存しない。
- 恒久対応: `_read_process_cwd()` が `os.readlink()` の**文字列そのもの**を返し、
  `_deleted_cwd_spellings()` が `readlink_text` を受け取って生値に対して判定する。
  `... (deleted)/child/..` の回帰 node を `orchestrator/tests/test_check_worktree_occupancy.py` へ置いた。
- 再発検知: 変異 A3 (suffix の末尾一致要求を恒真化) が当該回帰 node を殺すこと。
- 家族: 「防壁を足したのに、足した層の手前で前提が壊れている」型。
  防壁の入力が加工されていないかを、防壁そのものと同じ厳しさで確かめる必要がある。

### {{F:broad-match-regex-hides-early-error}}. レビュー用 regex が広すぎて別の早期エラーを拾い偽の緑になった [恒真ゲート]

- 事象: runner exclusion の payload/token drift を検査する test が
  `pytest.raises(..., match="runner exclusion")` で受けていたため、
  検査したい比較へ到達する前に発生した別の早期エラー
  (契約表が exactly-one でないことによる `UsageError`) を拾って**緑のまま通っていた**。
  意図した drift 検出はまったく行われていなかった。
- 根本原因: 例外の**発生**を検査の合格条件にし、**どの理由で発生したか**を固定しなかった。
  同じ prefix を持つメッセージが複数あると、最初に当たったものが合格を作る。
- 恒久対応: drift test の regex を payload 側と token 側の**固有メッセージ**へ分けた
  (`orchestrator/tests/test_pytest_collection_config.py`)。
- 再発検知: 早期エラー側の条件を成立させる負例で、drift test が**赤になる**ことを確かめる。
- 家族: F490 と同じ「gate の述語が到達可能な値域を測られていない」型の変種で、
  こちらは述語ではなく**期待する失敗理由**の側が緩い。

## 再発

### F489

- **再発: 2026-08-25** — 同型の 3 例目だが、**台帳が記録していた原因が誤っていた**。
  2026-08-24 の再発追記と `[T-1623]` 起票文はどちらも「消滅 pid 型 issue」と書いていたが、
  本 wave の実測では **pid は消えていない**。犯人は `/proc/<pid>/cwd` の指す directory が
  削除済みの**生存プロセス** 2 本 (`State: S`、cwd link は `.../tmp (deleted)`) で、
  `os.readlink` は成功し `resolve(strict=True)` だけが `FileNotFoundError` を投げていた。
  `_read_process_cwd()` が両者を 1 関数に混ぜていたため、原因の異なる 2 つが同じ
  `missing/cwd` issue へ潰れていた。pid が生存しているので D705 の有界 3 再試行では
  構造的に解けず、誰も居ない空 directory ですら `rc=2` になった (5 scan 連続で同一 pid)。
  原因の誤記録が「再試行で直るはず」という誤った期待を生み、修理を 1 日遅らせた。
  恒久対応は {{D:deleted-cwd-classification}}。

### F525

- **再発: 2026-08-25** — 修理にあたり実測したところ、偽陽性を作る wrapper は
  `timeout` だけではなかった。空 directory へ各 wrapper 経由で走らせた実測では
  **`timeout` / `flock` / `/usr/bin/time` / `strace` の 4 種**が `occupied` を返し、
  一方 `nohup` / `env` / `stdbuf` / `setsid` / `nice` / `ionice` は自分を exec で
  置き換えるためプロセスとして残らず発火せず、`xargs` は対象が stdin 由来で argv に載らなかった。
  当初案の exe allowlist `{shell, timeout, nohup, env, xargs, stdbuf}` は
  **発火する 4 種のうち 1 種しか覆わず、載っている 5 種のうち 3 種は到達不能**という、
  過少と過剰を同時に抱えていた。恒久対応は {{D:invoker-allowlist-by-measurement}}。
