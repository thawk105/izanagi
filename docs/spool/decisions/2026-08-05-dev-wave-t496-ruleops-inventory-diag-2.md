---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t496-ruleops-inventory-diag
seq: 2
---

## {{D:ruleops-failclosed-threshold-unchanged}}. 断続的な赤への一次対応は、fail-closed 閾値でなく診断で行う

**決定:** `tools/ruleops.py` の fail-closed 挙動 (exit code、`GIT_TIMEOUT_SECONDS`、
retry の不在) は変えない。並列受入全走で稀に出る exit 2 への対応は、まず**呼び出し側が
理由を残すこと**に限る。閾値の変更・retry の導入は、原因が理由行付きで特定できてから
独立に裁定する。

**理由:**
- exit 2 の理由は失われていなかった。ruleops は例外送出の直前に必ず
  `ruleops: <reason>: <detail>` を stderr へ出しており、捨てていたのはテスト側である。
  原因不明のまま閾値を緩めるのは、観測できていない失敗に対して受理集合を広げる操作にあたる。
- 並行アクセスで発火しうる理由は `git-unavailable` / `git-timeout` / `git-failed` /
  `head-moved` の 4 つに絞れ、reason 行で一意に判別できる。どれが起きたかが分かれば、
  必要な対応 (閾値・retry・呼び出し側の直列化・外部アクターの排除) は理由ごとに異なる。
  1 標本・理由不明の段階で共通の緩和を当てると、効かない対策を「対応済み」と記録してしまう。
- 診断の追加は受理集合を 1 bit も動かさない。rc==0 を要求する点は変えず、
  失敗時の message だけが増える。閾値変更と違い、誤ったときの被害が無い。

**却下した選択肢:**
- `GIT_TIMEOUT_SECONDS` の引き上げ — 到達可能性は probe で実測したが、request 889456 が
  timeout だった証拠はない。理由不明のまま上げると、真に固まった git を待つ時間だけが伸びる。
- git 呼び出しの retry — `head-moved` は retry で消えるが、それは
  「並行して HEAD を動かす者がいる」という**観測すべき事実を隠す**。正しさ検査の入力を
  黙って作り直す機構は、規律 2 の方向に反する。
- テストを `xfail` / 再試行にする — 赤の原因を消さずに赤の表示だけを消す操作であり、
  受理集合を無裁定で広げる。
