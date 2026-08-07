---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-07
wave: dev-wave-t529-impl-reraise
seq: 3
---

## 新規

### {{F:mutation-collection-preflight}}. 変異 harness の collection 事前検査で 3 度 fail-closed した [手順漏れ]

- 事象: 変異本走を 3 度連続で開始前に止めた。(a) runner に全走を渡したところ collection が
  計算ノードへ dispatch され、端末側の中継出力が切り詰められて、登録した期待 node 9 件が
  「pytest collection に実在しない」と判定された。(b) 対象を 4 test module へ絞ると
  `--collect-only` が 1 秒未満で終わり、`run_tests.py` の bounded scope が cgroup を
  attest できず rc=16 (`_SCOPE_ATTEST_SECONDS = 1.0` の race) になった。
  (c) parametrize 済み test を素の関数名で登録したため実在しないと判定された。
- 根本原因: runner argv と `--runner-mode` の組み合わせを、先例の台帳に当たらず自分で組んだ。
  `--runner-mode local` を指定しても `run_tests.py` は login node の headroom 次第で
  内部 dispatch へ倒れるため、mode と実態が食い違う。harness は dispatch mode では
  job stdout ファイルを直接読むので切り詰めの影響を受けないが、local mode では中継出力を読む。
- 恒久対応: 変異本走の runner は先例と同じ
  `--runner-mode dispatch` + `python3 tools/run_tests.py --force-dispatch -rf <対象 module> -p no:cacheprovider`
  を既定とする。memory `mutation-runner-dispatch-recipe` に控え、
  投入前に直近の `mutation-ledger.json` の `runner_identity.command` を読んで合わせる。
- 再発検知: harness の事前検査そのもの (期待 node の実在検査と collection rc 検査) が
  fail-closed で止める。3 度とも実装差分は 1 byte も汚さずに止まった。

### {{F:stale-done-file-short-circuits-waiter}}. 前回投入の `.done` 残骸で待ちが即座に返った [手順漏れ]

- 事象: 変異本走を投入し直した直後に完了待ちを張ったところ、待ちが即座に返った。
  掴んだのは前回投入 (期待 node 不備で abort した回) が残した `.done` で、
  実際の走行は継続中だった。結果ファイルが無いことに気づいて初めて誤りが判明した。
- 根本原因: launcher が `.done` を投入前に消していなかった。`.done` は「今回の走行が終わった」
  ではなく「同名ファイルが存在する」しか意味していなかった。
- 恒久対応: 背景 job の launcher script は投入直前に `rm -f <job>/<name>.done` を必ず実行する
  (`run-mutation6.sh` / `run-mutation7.sh` で実装済み)。待ち側は `.done` を掴んだあと
  必ず結果ファイルの実在も確認する。
- 再発検知: 待ちが想定より極端に早く返ったら、まず `.done` の mtime と log の mtime を比べる。
  結果ファイルの不在は即座に stale を疑う。
