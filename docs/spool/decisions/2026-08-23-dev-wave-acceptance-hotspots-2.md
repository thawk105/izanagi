---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-acceptance-hotspots
seq: 2
---

## {{D:scan-gate-fail-closed}}. 走査型 gate の列挙失敗は空集合へ潰さず構造化拒否にする

**決定:** `tools/codex_reasoning_ab.py` で directory を走査して「見つからなければ通す」構造を持つ
4 箇所は、`os.scandir` を明示的に使い `OSError` を path 付きの構造化 `ValidationError` へ翻訳する。
対象は filesystem allowlist の走査、git closure の空判定、pseudo-ref の列挙、metadata manifest の
収集である。`Path.rglob` / `Path.glob` / `Path.iterdir` の失敗時戻り値を仕様で確認せずに
走査型 gate へ使わない。**これは受理集合を狭める変更である。**
読める静止 tree に対する結果は不変で、`filesystem_files` と `manifest_sha256` の bytes は変わらない。

**理由:**
- F363 が同型を記録し、D464 が恒久対応として `os.scandir` 化と `OSError` の error 翻訳を要求している。
  本 file の 4 箇所はいずれもその再発である。
- とくに git closure の空判定は反転が明確で、`.git/logs` を列挙不能にすると
  「reflog closure is not empty」が出ない。走査型の防壁が黙って通過側へ倒れる。
- 読めない subtree の未許可 file は `extra` に現れないため、allowlist は片方向にだけ緩む。
  tracked file が隠れれば `missing` になるが、未許可 extra だけなら検出されない。
- 同型が 1 file 内で独立に 4 例再現しており、族としての一般化条件を満たす。

**却下した選択肢:**
- 現行の fail-open を温存する — 既存挙動の保存に見えるが、実体は恒久対応が存在する型を
  新しく書くコードで意図的に再実装することである。
- `os.walk` へ機械置換する — 既定で全 `OSError` を握り潰すため、同じ穴をより広く作る。
- 走査の一部だけを直す — 走査型 gate は 1 箇所でも通過側へ倒れれば閉包が崩れる。

## {{D:git-fsck-parallel-with-ordered-consumption}}. fsck の待ちは並行化してよいが、結果の消費は入力順に 1 対 1 で行う

**決定:** `git fsck --unreachable --no-reflogs` の待ちは repository 単位で並行化してよい。
条件は次のとおりで、いずれかを満たせないなら並行化しない。
(a) repository と future を同じ pair object へ束縛し、`as_completed` を使わず入力順に
ちょうど 1 回ずつ `result()` する。(b) 全結果を回収する前に成功 return しない。
(c) executor 構築・submit・result のいずれの失敗も空 `reasons` へ degrade させない。
「並列化できないので skip」する fallback を置かない。(d) worker 例外は repository / label 付きの
`ValidationError` へ翻訳し、成功分の reason と未 submit state の診断も入力順で保持する。
**異常時に実際に起動された fsck の件数は保証対象外**とし、そう明記する。
正しさ境界の判定に `assert` を使わない (最適化フラグで消えるため)。

**理由:**
- fsck の argv・対象集合・判定式は変えないので、理想条件下では同じ predicate を評価する。
  検査 predicate を決定的に削る `--connectivity-only` とは同型でない。
- 「fsck を実行した」と「結果を同じ repository の gate へ消費した」は別物である。
  `ThreadPoolExecutor` の context manager は worker を待つが `result()` を呼ぶ保証はない。
  未消費の future があると、非 0 rc・unreachable stdout・worker 例外がすべて黙って捨てられる。
- 先行起動は避けられないため、異常時の起動件数まで同値を要求すると並行化自体が採れない。
  一方、正常経路の対象集合・回数・結果消費は完全に保証できる。
- 1 件だけを reason 化すると、実在した repository failure が構造化 JSON と台帳から欠落する。

**却下した選択肢:**
- `_one_git_closure_reasons` 全体を並行化する — `_git`・metadata・commit-graph verify・HEAD 読取まで
  背景へ移り、副作用面と例外面が不必要に広がる。
- 全 fsck を `subprocess.Popen` で先行起動する — `_run` の環境遮断と `check=False` 契約を複製し、
  pipe と部分失敗の後始末を新たに所有することになる。1 snapshot あたり 4 process なので利得も小さい。
- 1 件失敗したら残る future を捨てる — 拒否側には倒れるが、実在した corruption reason が消える。

## {{D:chain-metric-is-load-confounded}}. 受入の性能比較は node 単位の実測を第一証拠にし、鎖と wall は交絡込みで報告する

**決定:** 受入全走の性能改善を主張するときは、変更が届く**個別 node の所要**を第一証拠にする。
直列鎖の総和と wall も併記するが、**計算ノードの負荷で交絡する**ことを明記し、
同一走の work 総和を添えて交絡の大きさを読めるようにする。単発の前後比較で採否を決めない。

**理由:**
- 本 wave の実測で、対象 node は変更前 3 走 170.92〜171.68 秒、変更後 2 走 93.83〜93.87 秒と
  負荷に依存せず安定した。一方、同じ 2 走の鎖は 197.0 と 266.4 秒、wall は 229.5 と 303.2 秒で、
  後者の走は work 総和が 7,443.9 から 11,457.6 秒へ膨らんだ混雑ノードだった。
- 鎖は wall より安定するが (変更前 5 走で 320.9〜329.7 秒、幅 1.9%)、鎖を構成する他 node が
  負荷で伸びるため、変更の効果と負荷の差を分離できない。
- D531 は非対の before/after 比較を退けており、node が交絡すると明記している。
  node 単位の実測はその交絡を受けにくい。

**却下した選択肢:**
- wall だけで報告する — 変更前 5 走で 345.9〜391.3 秒、幅 12% あり、改善量より分散が大きい。
- 混雑した走を捨てて良い走だけを載せる — 都合の良い走の選択になる。
- 2×2 ablation で寄与を分離する — 本 wave の 3 変更は同じ経路に相乗するため、
  分離には走行数が要る。必要なら別 wave の裁定事項とする。
