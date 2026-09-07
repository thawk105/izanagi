---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-a1-pilot-attempt2
seq: 2
---

## 新規

### {{F:a1-noreplace-publish-lustre}}. A-1 の group submission receipt を `renameat2(RENAME_NOREPLACE)` で公開する経路が、Lustre 上の durable base で決定的に失敗した [テスト代表性] [手順漏れ]

- 事象: 2026-09-07 19:03 JST、A-1 pilot (study `paper-story-a1-20260901-balanced5-pilot-v1`) の
  attempt-0002 で 3 本の qsub がすべて受理され qstat 可視性判定も 3 本とも通った直後に、
  `no-replace submission receipt publish failed: Invalid argument` で rc=2 になった。
  group receipt `receipts/submission.json` は生まれず、3 job は計算ノードで body preflight を通ってから
  `acquisition receipt did not appear within 60 seconds` で bench に入らず終わった。測定値は 0 点。
- 根本原因: `orchestrator/campaign/paper_story_a1_paired.py` の `_publish_submission_receipt` が
  `_renameat2_directory(staging, path, _RENAME_NOREPLACE)` で完成名へ移すが、policy
  `execution.durable_measurement_base` が固定する `/work` 配下は Lustre で、この flag を受け付けない。
  同じ directory での実測は `renameat2(RENAME_NOREPLACE)` = errno 22 (EINVAL)、`flags=0` = 成功、
  `os.link()` = 空き先に成功・既存先に errno 17 (EEXIST)、tmpfs では `RENAME_NOREPLACE` が成功。
  flag は kernel にあるが Lustre が実装していない。この経路は環境と混雑によらず決定的に落ちる。
  attempt-0001 は 1 段手前の F852 で落ちていたため、公開まで到達したのは attempt-0002 が初めてで、
  **実機で一度も通っていない手順が投入 gate に置かれていた** — F852 と同じ型で層だけが違う。
  同じ file の `_observe_materialization_publish` は公開先と同じ file system で
  `RENAME_NOREPLACE` を 1 回試して `EINVAL` なら fallback を選ぶ機構を既に持つが、
  submission receipt の公開だけがその機構を持たない。
- 恒久対応: 一次資料 `output/insights/2026-09-07_a1-pilot-attempt-0002/README.md` §5・§7 の裁定パッケージ
  (公開機構 3 案と実測表、親推奨は `os.link()` による公開)。実装は {{T:a1-noreplace-publish-fix}} が
  Codex `role=author` で持ち、Lustre 上で公開が成立する正例と、既存先を上書きしない負例を同じ commit へ足す。
  受理集合を広げる素の rename への退避は採らない。
- 再発検知: 投入 gate に file system 依存の primitive (`renameat2` の flag、`O_TMPFILE`、
  advisory lock 等) を置く wave は、段 1 で対象の durable base 上に最小 probe を 1 回走らせ、
  fixture が代表していない環境差を投入前に出す。`docs/dev-wave/core.md` `DW-S01` の
  「別 program 起動物の実在棚卸し」の対象に、公開先 file system が primitive を受けるかを含める。
