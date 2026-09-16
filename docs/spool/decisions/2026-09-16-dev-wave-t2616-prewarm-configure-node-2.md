---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2616-prewarm-configure-node
seq: 2
---

## {{D:early-prewarm-fire-condition-parsed-option}}. 早期 prewarm の発火条件は parsed option 面で判定し、実 parser の destination と一致させる

**決定:** receipt memo / oracle environment memo の prewarm を `pytest_configure_node` (collection 前)
で起動する条件を、次の連言とする。(1) controller である、(2) `_izanagi_acceptance_shard_spec` が
実在する、(3) `collectonly` でない、(4) 全 suite 選択であり parsed option に narrowing が一切ない。

**(4) の判定面は `config.args` ではなく parsed option (`config.option`) を正本とする。**
narrowing として扱う名前は pytest の**実 parser の destination** と一致させ、その一致を
機械的に確かめる対照を同じ file に置く。最低限 `keyword` / `markexpr` / `deselect` / `lf` /
`failedfirst` / `stepwise` / `stepwise_skip` / `ignore` / `ignore_glob` / `pyargs` /
`override_ini` を含める。

**理由:**
- pytest は `PYTEST_ADDOPTS` と ini の `addopts` を parse 前に argv へ前置するため、
  `config.args` には現れない絞り込みも parsed option には現れる。args 面で判定すると
  環境由来の narrowing を取りこぼす。
- 名前を手で列挙すると実 parser との食い違いが静かに入る。本 wave は実際に `--ff` の
  destination を `ff` と誤記し、**同じ wave が足した test も同じ誤名を使ったため、test が
  実装の誤りと自己整合して検出できなかった**。実 `Parser` へ plugin の addoption を登録して
  destination を照合し、さらに独立した CLI 入力でも検査する対照だけが、綴り誤りと列挙漏れの
  両方を落とす。
- 条件を緩めると D518 が却下した「無条件 prewarm」が焦点走へ漏れ、consumer を含まない走行に
  解決 1 回分が丸乗りしてテスト時間規則を破る。

**却下した選択肢:**
- shard spec の実在だけを条件にする — plugin 自体は焦点選択を禁じないので、spec があっても
  焦点走でありうる。
- `config.args` だけで全 suite を判定する — 環境由来の narrowing を取りこぼす。
- 名前の列挙を手書きのまま対照を置かない — 本 wave が実際に踏んだ食い違いを再発させる。

## {{D:early-prewarm-wait-is-minimal-delta-over-existing-flock}}. 早期 prewarm の待ちは既存 flock の上の最小差分とし、待ち機構を作り直さない

**決定:** worker 側の待ちは新規機構を作らず、既存の cache flock の上に次の 1 点だけを足す。
controller が `workerinput` で**明示した早期 job があるときに限り**、lock 内で本体不在を見ても
即赤にせず期限まで retry する。明示が無ければ従来どおり即 `cache-missing` で赤にする。
期限の上限は 120 秒固定とし、**成功を返す直前にも共有 deadline を確認**して、越えていれば赤にする。
lock の retry は競合 (`EAGAIN` / `EACCES`) だけを対象にし、`EIO` 等は最初の故障で赤にする。
`.failed` marker は本体より優先する。

**理由:**
- `prewarm` の `write_once()` は `_locked(...)` の内側で production resolver を呼ぶので、
  cache の flock は解決の全所要 (実測 28.328 秒) のあいだ保持される。reader も同じ blocking flock の
  中にいる。**プロセス跨ぎの待ちは元から成立しており**、欠けているのは「reader が writer より先に
  lock を取ったとき本体不在で即赤になる」1 点だけである。
- 宣言した上限が実際には縛らない保証は、この repo が繰り返し戒めている恒真な保証である。
  期限の確認が lock 取得の前にしか無ければ、期限を越えて成功した読取りをそのまま通してしまう。
- 故障 (`EIO` 等) を競合と混同して再試行すると、一度赤になる故障が後続の成功で隠れる。

**却下した選択肢:**
- cache が無いときに既定値を返す、または worker が自分で resolver を呼ぶ — production resolver を
  呼べる唯一の経路が prewarm であるという性質を壊す。
- 上限を観測値の倍率だけで決める (`ceil(2 × max(W))` 等) — 上限が無く、設計が定めた 120 秒を
  超えうる。
- 未明示の miss も待つ — 現行の即赤を緩める。

## {{D:unreachable-barrier-must-be-labelled-not-counted}}. production から到達しない防壁は、そう明記して gate と数えない

**決定:** 実装に残るが production 経路からは到達しない分岐は、削除せずに**到達しないことと、
同じ事象に対する production の fail-closed がどこで成立するか**をコメントで明記する。
変異台帳では gate でなく診断として別枠に記録し、kill の本数に数えない。

**理由:**
- 本 wave の `publication-regressed` は、待機経路が使い捨ての reader を 1 回使うだけなので
  同じ instance が再度その判定へ到達しない。test だけが到達する分岐を「効いている防壁」として
  数えると、防壁の本数が実効性を伴わずに増える。
- 同じ事象 (公開後の本体消失) に対する production の fail-closed は、consumer の読取りが
  `cache-missing` を投げる別経路で成立している。所在を書けば、読み手は到達不能な分岐を
  保護と誤解しない。

**却下した選択肢:**
- 分岐ごと削除する — test が失う検出力の代替を用意していない。
- そのまま残して何も書かない — 恒真な保証を防壁として数える誤りを温存する。
