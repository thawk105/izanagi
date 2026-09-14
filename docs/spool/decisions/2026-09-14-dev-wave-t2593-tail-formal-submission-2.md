---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-t2593-tail-formal-submission
seq: 2
---

## {{D:cohort-entry-without-new-pegasus-executable}}. 集団報告の入口は新しい Pegasus 実行体を作らず、手順文書と CLI 束縛テストで置く

**決定:** B-10 静的 tail 本走の 3 workload を 1 集団として報告する入口を、
`tools/pegasus/` 配下の新しい実行体としては作らない。操作手順を
`docs/b10-backoff-static-tail-submission.md` に置き、その手順に書いた argv を**文書から抜き出して**
本走 driver の argument parser へ通すテストで束縛する。文書と CLI が乖離すればテストが赤になる。

この形が保証しないことも同じ文書に書く。shell の wrapper が無いので、wrapper の終了コード伝播は
検査対象にならない。

**理由:**
- `tools/pegasus/` 配下へ実行体を置くと、admission registry へ実行場所の分類を宣言する必要が生じる。
  `test_bash_pegasus_execution_inventory_is_synchronized` が、拡張子・実行 bit・shebang の
  いずれかを持つ file の集合と registry key の集合の一致を要求する。
- その分類を実測で裏づける材料 (完走した 3 本の campaign) が、入口を作る時点では存在しない。
  分類を実測なしに動かさないことは既決である。
- 3 走を 1 集団として束ねる仕組みは既に 2 箇所にある。投入 receipt の group id と workload ごとの
  出力 root、および driver の報告 subcommand が 3 つの campaign lock 間で集団の同一性を
  突き合わせる経路である。欠けていたのは両者をつなぐ乖離しない手順だけだった。

**却下した選択肢:**
- 薄い shell を 1 本置いて registry へ分類を足す — 実測なしの分類宣言になる。
- 置き場所を `tools/pegasus/` の外へずらす — inventory 検査を意図的に避ける形であり不正直。
- 手順を書かずに driver の CLI だけを正本とする — 3 campaign の選び方 (出力 root ではなく
  その配下の campaign directory を明示して渡す) が人の記憶に残り、取り違えが検出されない。

## {{D:legacy-argv-invariance-verifies-variable-fields}}. 投入 script の「旧系列 argv 不変」検査は、可変値を消さずその場で検証する

**決定:** B-10 の投入 script を編集する wave で「既存系列の起動 argv を変えていない」ことを示す
テストは、可変値を正規表現で潰して比較しない。可変値ごとに、その値が**何と一致すべきか**を
その場で検証する。

- job script の SHA-256 は、現行 job script の実 bytes から計算した値と一致すること
- 投入 nonce は 3 job と manifest 事象で同一であること
- group id の時刻部は、起動の直前と直後に取った UTC の窓に入ること
- 同じ引数で 2 回起動して group id が異なること

残る全部 (環境変数名・値・順序、workload の fan-out、出力 path の組み立て) は完全一致で比較する。
生成された投入 receipt の schema・事象種別・走行種別と argv の対応も同じ走行で観測する。

**理由:**
- 投入 script が job へ渡す環境変数には job script 自身の SHA-256 が入る。job script を編集する
  wave では、旧系列の argv に現れるこの値が必ず変わる。bytes 完全一致の比較は、書いた瞬間に
  赤になるか、値を潰して恒真になるかのどちらかにしかならない。
- 値を潰すと、誤った 64 桁 SHA を渡す編集が「argv 不変」の緑をすり抜ける。その job は
  実行前に SHA 束縛で拒否されるので、検査が通ったこと自体が誤った安心になる。
- group id を固定値へ置換する編集も、形式だけの検査では通る。固定化されると同じ出力親への
  次回投入が receipt 衝突で拒否される。

**却下した選択肢:**
- 可変値を比較対象から除外する — 上記のすり抜けを許す。
- 可変値ごと bytes 一致を要求する — 編集のたびに赤になり、検査として機能しない。
- 期待値を検査対象の script から逆算する — 二重定義の片側だけを変える編集に追随して緑になる。
