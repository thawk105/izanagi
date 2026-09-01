---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t2115-cross-protocol-impl
seq: 2
---

## {{D:floor-admission-bound-to-compiled-source}}. 測定を許す protocol の判定は、実際にコンパイルされる source の事実へ束縛する

**決定:** between-run floor の生成を許す protocol は、固定の許可リストで決めない。
その protocol の CCBench source を実際に読み、trace hook の証拠がある場合だけ受理する。
読む範囲は `cc/<protocol>/CMakeLists.txt` の `ccbench_add_protocol(... SOURCES ...)` が
列挙する source に限る。照合の前にコメントと literal `#if 0` の dead block (入れ子を含む) を
除去する。CMakeLists を読めない、SOURCES が無い、証拠が揃わない場合は拒否側へ倒す。

**この判定が証明しないこと**を述語の docstring に逐語で書く — プリプロセッサ条件を評価しないこと
(literal `#if 0` だけを dead として扱う)、hook の意味論的正しさ、verifier が通ること、
測定値の正しさ。目的は fail-closed の拒否であって hook 実在の証明ではない。

**理由:**

- 固定の許可リストは、「hook が無いから拒否している」という主張をコードの事実に束縛しない。
  hook の有無に関係なく同じ結果を返すため、移植が完了した後も拒否し続ける恒真な検査になる。
  負例は常に緑になり、機構が壊れても誰も気づかない。
- 現行 pin から測定へ至る経路で、この判定だけが唯一の関門である。実測で確認した —
  `source_digest` の allowlist は既に mocc の編集面を含み、buildcache は protocol 汎用で、
  floor driver は trace 無効 build を verifier に通さない。他に止める層は無い。
- 走査範囲を protocol directory 全体にすると、コンパイルされない file を 1 つ置くだけで
  判定が反転する。コメントや dead branch を除かないと、移植途中の無効化されたフック呼出しが
  証拠として数えられる。いずれも実測で再現した。
- 完全なプリプロセッサ評価は目的に対して過剰である。text-level の検査であることを名前と
  docstring で明示すれば、検査していないことを検査したと読ませずに済む。

**却下した選択肢:**

- 許可する protocol 名を定数集合で持つ — 上記のとおり主張が事実に束縛されない。
- 判定を廃し、測定側の運用規律に委ねる — 規律 2 の関門を人間の注意力へ移すことになる。
- プリプロセッサ条件評価器を実装する — 判定の目的を超え、保守対象を増やす。

## {{D:legacy-floor-record-basis-must-be-stated}}. 出所を確認できない較正 record の一致は、根拠を成果物へ明記する

**決定:** protocol を記録していない歴史的な within-run 較正 record は、silo campaign にだけ一致させる。
ただしその一致の根拠を成果物へ `genome-absent-legacy-record` として記録し、
確認済みの protocol と書き分ける。「silo と確認した」と読める表示をしない。

**理由:**

- within-run 較正の producer は binary の path を手渡しで受け、genome を記録しない。
  既存 record には protocol の手がかりが 1 文字も無い (file 全体に protocol 名が現れない)。
  したがって「legacy = silo」は歴史についての仮定であって、bytes から導ける事実ではない。
- 厳密に拒否すると、既存 campaign の within-run floor が一致なしへ落ち、
  公式レポートの値が変わる。実在する測定の意味を、記録形式の後付け変更で無効にしない (規律 7)。
- 仮定を仮定として表示すれば、下流は根拠の強さを区別できる。表示せずに一致させると、
  出所不明の値が確認済みの値と同じ顔で成果物へ入る。

**却下した選択肢:**

- 歴史的 record を無条件で拒否する — 既存成果物の値を変え、再測定できない過去を無効にする。
- 根拠を表示せず silo として一致させる — 検査していないことを検査したと読ませる。
- 全 record へ protocol を後から書き足す — 出所を知らないまま bytes を書き換えることになる。
