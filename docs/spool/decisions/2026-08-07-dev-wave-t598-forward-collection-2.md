---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t598-forward-collection
seq: 2
---

## {{D:wave-usage-missing-rule}}. wave 消費の欠測は集計 model call 0 で判定し、走査 file 数では判定しない

**決定 (1): 集計 model call が 0 なら常に `missing` とする。** `observed_zero` のような
「完全に走査したうえでの 0」を表す field を作らない。wave は Claude が駆動するので真の消費 0 は
存在せず、集計 0 は誤 selector・消えた保存先・窓外のいずれかでしかない。

**決定 (2): `files_scanned` を欠測条件に使わない。** 同 field は file を開いた数であって
filter 一致件数ではない。cwd / 時間窓の選択は全 file 読了後に request 単位で行われるため、
「多数の file を読んだが対象 request は 0 件」が完全走査の 0 として保存されうる。

**決定 (3): status は error → missing → incomplete → complete の順で判定する。**
collector を呼べなかった場合が最優先で、resource failure が自然欠測へ化けるのを防ぐ。
打切り (`limit_reached`) と collector の issue は `incomplete` に落とし、値は捨てない。

**理由:**
- D220 決定 3 は「該当 0 件は観測値 0 ではなく欠測として記録する」と定める。走査 file 数による
  判定はこの要求を満たさない。実測でも、消えた保存先を指すと issue なしの 0 が返った。
- この規則なら canonical collector の schema を一切変えずに要求を満たす。母集団を出す既定 (D206) とも
  両立し、台帳を再解釈する第 2 の parser も作らない。
- 「完全走査した 0」という状態を設計から消せば、誤 selector を正常観測として保存する経路も消える。

**却下した選択肢:**
- collector へ filter 一致 request 数の field を追加する — 凍結済み schema の受理集合が広がり、
  同じ version 文字列が二つの受理集合を表すことになる。集計 model call が同じ情報を持つため不要。
- 集計 0 を `complete` として保存し、利用側で解釈する — 撤回不能な記録に偽の観測値を残す。
- `--strict` を常用して欠測を fatal にする — 消えがちな保存先の不在が fatal 化し、
  ほぼ全 wave が不完全判定になって status が信号を失う (実測)。

## {{D:wave-usage-selector-and-siting}}. wave の identity は worktree path とし、収集は実行場所が確証できるときだけ走らせる

**決定 (1): selector は project slug (1 個以上、繰り返し可) と worktree 絶対 path の
path 境界一致とする。** 一致条件は `cwd == p` または `cwd.startswith(p + "/")`。
canonical collector へ `--cwd-under` を追加し、既存の部分一致 filter は変更しない。

**決定 (2): 時間窓を必須にしない。** worktree は wave 専用に生成・破棄されるので
worktree path 自体が wave の identity である。収集は wave 末に行うため、
開始時刻の権威ある供給元が実行時点に存在しない。

**決定 (3): 保存先の識別子を必須引数にする。** 作業ディレクトリから導出しない。
保存先 directory が存在しないことは検出できるが、存在して窓が空のときは検出できないため、
導出は偽のゼロを作る。

**決定 (4): 実行場所が確証できないときは収集しない。** ログインノードと判定された場合だけでなく、
判定の証拠が得られない場合も collector を呼ばず `blocked` を記録する。
分類の実測はユーザー端末の手番であり、AI は行わない。

**決定 (5): 保存先が repository 配下でないことを機械検査する。** 祖先を根まで辿り、
`.git` が file であるか、または HEAD を持つ directory であるときに repository とみなす。
worktree root を基準にした判定は本体 checkout を素通りさせるため使わない。

**理由:**
- 部分一致だけでは、worktree 名を prefix に持つ別 wave (`<名前>-fix` など) を誤って取り込む。
  実測では該当 record の cwd が worktree root ちょうど 1 種類だったので、境界一致で足りる。
- 全 project 走査は raw ID の衝突で fatal になるため、slug の明示は省略できない (実測)。
- 実行場所の規範は、未計測の実行体を軽い側へ倒すことを禁じている。手動実行であることは
  この分類を免除しない。fail-closed を機械化すれば、分類が済んだ時点で同じ契約のまま収集が始まる。
- `.git` の有無だけで repository を判定すると、過去の job が残した空の `.git` directory を
  repository と誤判定して正当な保存先を恒久的に拒否する (実測)。

**却下した選択肢:**
- 保存先の識別子を作業ディレクトリから導出する — 符号化が変われば古い保存先を走査し、
  欠測ではなく偽のゼロを記録する。
- 収集を wave の完了条件にする — 消費削減は最適化圧力であり、正しさ側を攻撃しに来る前提で扱う。
- 手順の本文を byte 予算の外にある文書へ置く — 規範 detail の逃がしにあたる。
  契約は pointer 1 行に留め、実効性は必須引数による機械強制に持たせた。
