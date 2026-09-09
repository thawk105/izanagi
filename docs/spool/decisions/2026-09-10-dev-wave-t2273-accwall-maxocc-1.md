---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-10
wave: dev-wave-t2273-accwall-maxocc
seq: 1
---

## {{D:slowest-shard-floor-is-material-group}}. 受入の最遅 shard の床は t080 群ではなく shard-2 の material-report group である

**決定:** D1894 が要求した「着手前に、床が `test_t080_*` 群へ移ったことを実測で確かめる」の
答えを **否**として記録する。受入全走の最遅 shard は shard-2 であり、その最大 worker 占有は
xdist group `p3-b4-material-report` を 1 worker が背負う区間である。
`test_t080_*` 群は shard-0 の最大 worker 占有の担い手ではあるが、最遅 shard の床ではない。

D1894 の決定本体 (次の短縮対象は最大 worker 占有) は維持する。対象を
**実測で最遅である shard の**最大 worker 占有と読み替えて実装した。
この読み替えの追認はユーザー裁定へ返す。

**理由:**

- 2026-09-09 の 9 走 (repo 外の shard 成果物 `junit.xml` と `report.json`) で、最遅 shard は
  9 走中 8 走が shard-2 だった。shard-2 の wall は 9 走すべて 300 秒超 (313.27〜365.94 秒)。
  t080 群を持つ shard-0 は 253.16〜388.51 秒で、300 秒超は 3 走だけである。
- shard-2 の最大 worker 占有は gw0 の 256.93〜308.57 秒で wall の 78〜84%。
  2 番目に忙しい worker は 94.6〜148.3 秒しかない。gw0 の 49 item は
  `group_to_workers` が示すとおり `p3-b4-material-report` そのものである。
- その group の 57.3〜64.3% が単一 node
  `test_p3_b4_material_report.py::test_normal_path_assembles_binds_evaluates_and_builds_document`
  で、module scope fixture の構築費用がそこに載る。
- **`wall = 最大 worker 占有 + 残余` は D1830 が示すとおり定義上の恒等式**であり、
  独立な構造下限ではない。主張は「観測 9 走で shard-2 が一度も 300 秒を切らなかった」に留める。

**却下した選択肢:**

- 依頼と `[T-2495]` の名指しどおり t080 だけを短縮する — 最遅 shard の wall が 1 秒も動かない。
  依頼自身が求める成果物 (短縮後の最遅 shard wall) を満たせない。
- D1894 の前提が外れたことを理由に着手しない — 決定本体は最大 worker 占有を対象と定めており、
  実測で最遅の shard を対象にすることはその決定に従う形である。
- 前提の失効を記録しない — 次の担当者が同じ 9 走の測り直しをやり直す。

## {{D:fixture-owned-oracle-kills-are-parse-error}}. 変異 harness は fixture 由来の kill を KILLED として記録できない

**決定:** oracle が module / function scope fixture の中にある変更では、変異の kill が
pytest ERROR として出るため `tools/mutation_harness.py` は `PARSE_ERROR` を返す。
この場合、**検出の証拠は baseline 緑 (rc=0) からの rc≠0 と `errors=N`** とし、
`status` が `PARSE_ERROR` であることを実装の欠陥と読まない。台帳へはこの理由を明記する。

harness を変更しない。`FAILED ` 行だけを解析する契約と、`rc≠0` かつ失敗 node 0 件を
`PARSE_ERROR` とする fail-closed は、node 完全一致を要求する既存の kill 判定を支えている。

**理由:**

- `tools/mutation_harness.py` の失敗 node 抽出は `FAILED ` で始まる行だけを読む。
  pytest は fixture setup の失敗を `ERROR ` として報告するため、抽出は 0 件になる。
  `_observed_status` は `rc != 0 and not failed` を `PARSE_ERROR` と判定する。
- これは fail-closed として正しい。node 完全一致で KILLED を数える契約 (F33) の下で、
  解析できない出力を KILLED と数えるほうが危険である。
- 本 wave で 4 変異すべてがこの経路に入った。いずれも baseline 緑からの rc=1 で、
  anchor は file 内で一意、注入 diff はすべて相異なる。検出は成立している。
- `-r` の文字を増やしても解決しない。抽出器が読むのは `FAILED ` 行だけである。

**却下した選択肢:**

- ERROR 行も KILLED の証拠として解析させる — 失敗 node の完全一致契約の射程を広げる変更であり、
  本 wave の scope 外である。必要なら独立の裁定を要する。
- oracle を fixture から test 本体へ移す — 検査の実行回数と適用対象が変わる。
  速さのために検査の構造を動かす形であり採らない。
- 変異を登録しない — 実装面の差分がある wave で変異 matrix を免除できるのは差分ゼロのときだけである。
