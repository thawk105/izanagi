---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-mocc-trace-pair
seq: 3
---

## 新規

### {{F:mocc-shared-hydrate-inplace}}. 共有 hydrate 先を job が in-place でビルドし、2 本目以降が必ず fail-closed する [手順漏れ] [計測汚染]

- 事象: mocc trace pilot の 2 本目が build 前に rc=1 で止まった。message は
  `fetch_third_party: ignored artifacts are forbidden in hydrated source: masstree`。
  1 本目 (TRACE=1) の完走後に投げた TRACE=0 が 19 秒で落ちた。
- 根本原因: hydrate 先が repo 内の共有 path 1 つに固定されていた。masstree は autotools で
  source tree を in-place ビルドするので、1 本目が ignored artifact を残す。次 job の
  hydrate はそれを検出して fail-closed する。**この共有のため複数 job の同時走行も衝突する。**
- 恒久対応: {{D:mocc-trace-pair-gate}} と同じ変更単位で、hydrate destination を job 私有の
  scratch 配下へ移した。hydrate 側に explicit staging root の option を足し、未指定時は
  従来の定数を使うので他 caller の受理集合は変わらない。
- 再発検知: 実 hydrate に explicit staging root を渡し、出力の `source_root` がその root で
  あることを mock 抜きで確かめる検査。および pilot からその option を外すと落ちる caller contract 検査。
- 補足: 同じ事象は 1 つ前の mocc TRACE=0 pilot でも起きており、当時は「本 pilot 値を変えない
  scope 外所見」として専用 handoff へ送られていた。対を N 本取る wave では回避不能な一次の障害になった。

### {{F:submit-residue-blocks-next-submit}}. 投入 script が clean-tree 検査の後に repo 内へ artifact を書き、自分の残骸で次の投入を塞ぐ [恒真ゲート] [手順漏れ]

- 事象: 2 本目の投入が `working tree is dirty; Mocc trace submission aborted` で rc=2 になった。
  dirty の中身は 1 本目の投入自身が作った preflight capture だった。
- 根本原因: clean-tree 検査が preflight capture の**前**にあり、capture 先が repo 内だった。
  検査は自分の tool が後で書く path を除外していなかった。`--attempts-root` は投入側だけの
  flag で job 側は repo 内の固定 path を読むため、外へ逃がす回避も使えなかった。
  加えて `qsub` に `-o` / `-e` が無く PBS の stdout/stderr も submit directory へ落ちていた
  (`docs/pegasus-runbook.md` §8 の投入前チェックリストに既に項目がある事故型)。
- 恒久対応: clean-tree 判定を tool 所有 prefix 限定の除外にし、除外対象が regular file であり
  symlink でないことを検査する。実効 attempts root を clean 判定の前に正規化して除外へ反映し、
  PBS の `host:path` 構文と衝突する `:` を含む root を拒否する。attempts root を job へ伝播し、
  PBS の stdout/stderr を nonce ごとの submission dir へ向ける。必須 argv が増えたので
  投入 receipt の schema 版を上げた。
- 再発検知: custom attempts root で 2 回続けて投入できることの検査、`:` を含む root の拒否検査、
  所有 prefix 内の symlink と所有外 untracked の双方を拒否する検査。

### {{F:evidence-not-bound-to-producer}}. 証拠 artifact を filename でしか指さない receipt は、事後に渡された任意 bytes を追認する [恒真ゲート] [テスト代表性]

- 事象: 新設した対の checker が「TRACE=1 leg は certified である」と検査していたが、
  その根拠にする verifier 出力の bytes が実 job の生成物である保証が無かった。
  段 3 の 2 レンズが独立に同じ穴を突き、`trace_dir` と txns だけ実物に合わせた合成 JSON を
  渡せば certified な leg を偽造できることを示した。
- 根本原因: producer 側の receipt が証拠 artifact を filename か null でしか記録しておらず、
  bytes の hash を残していなかった。consumer 側で hash を計算しても、それは
  「事後に渡された bytes の hash」であって producer への束縛にならない。
- 恒久対応: job 側が verifier 出力・throughput・identity report の SHA-256 と、
  実行した判定器の実体 path と SHA-256 を receipt へ記録する。consumer は渡された bytes を
  その値と照合する。receipt schema は必須 field を増やしたので版を上げた。
- 再発検知: 各 mode で「receipt の記録 SHA と渡した bytes が食い違う」負例を単独照準で持つ。
  identity report については report bytes を 4 番目の入力として要求し、receipt の記録値と照合する。
