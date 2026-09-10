# 段 6 裁定 — must-fix の確定 (T-2115)

親がレビュー A / B と自分の実測を突き合わせて裁定した。これが fix 子の契約である。

## 親が実走して確定させた事実

| # | 検査 | 結果 |
|---|---|---|
| 1 | 焦点走 15 file (1205 件) | 赤は `test_write_out_is_create_only_and_preserves_existing_bytes` の 1 件だけ |
| 2 | create-only の実挙動 (独立 probe) | 既存 file があれば `FileExistsError`、bytes も保持。**実装は正しい** |
| 3 | trace-hook 述語 (実 submodule) | silo=True / mocc=False / tictoc=False / cicada=False / 不在=False |
| 4 | 未コンパイル decoy file | `cc/mocc/decoy.cc` を置くだけで False → **True に反転する** |
| 5 | 3 行すべてコメント | False のまま (レビュー A の「コメント内 include も受理」は**誤り**) |
| 6 | include と guard が生きていてフック呼出しだけコメント | **True になる** (レビュー B の指摘が正しい) |
| 7 | dead `#if 0` 内のフック呼出し | **True になる** |
| 8 | genome body の検証 | `mocc\|garbage`、`silo\|B=x`、`silo\|Z=1,A=0`、`silo\|A=1,A=2`、`silo\|` がすべて受理される |

## must-fix (6 件)

### P-1. create-only test が機構を一度も通っていない

`orchestrator/tests/test_between_run_floor.py::test_write_out_is_create_only_and_preserves_existing_bytes`
は既存 file を `<scope>/` に置いているが、`_write_out` の書き込み先は `<scope>/calibration/` である。
そのため衝突が起きず、例外も上がらず、test が赤になる。**実装は正しいので直すのは fixture の path。**
既存 file を `<scope>/calibration/` に置き、`FileExistsError` が上がることと bytes が保持されることを
実際に確かめる形にする。期待値の緩和ではない。

### P-2. trace-hook 述語が「実際にコンパイルされる source」に束縛されていない

`_protocol_source_has_trace_hook_evidence_only` は `cc/<protocol>/` 配下を `rglob` するため、
build に含まれない file を 1 つ置くだけで受理へ反転する (親の実測 4)。
**その protocol の binary に実際に入る source だけを見る**ように狭める。
対象は `cc/<protocol>/CMakeLists.txt` の `ccbench_add_protocol(... SOURCES ...)` が列挙する file とする。
列挙を読めない・SOURCES が無い場合は fail-closed で偽を返す。

### P-3. 述語がコメント・dead branch のフック呼出しを受理する

include と `#if TRACE` が生きていれば、フック呼出しがコメントアウトされていても、
dead な `#if 0` の中にあっても真になる (親の実測 6・7)。
**照合の前に行コメント (`//`) とブロックコメント (`/* */`) を除去する。**
プリプロセッサの条件は評価しない — それは本 wave の範囲外である。
**docstring を実際の強さに合わせて書き直す**: これは text-level の検査であり、
プリプロセッサ条件を評価しないこと、hook の意味論的正しさ・verifier が通ること・測定値の正しさの
いずれも証明しないこと、目的は fail-closed の拒否であって hook 実在の証明ではないことを明記する。
現在の docstring の「active な trace.hh include」という表現は、実測 6 の反例があるため誤りである。

### P-4. canonical genome の body を検証していない

`genome.protocol_from_floor_genome` は `|` の後を捨てるため、
`mocc|garbage` から `silo|A=1,A=2` まですべて受理される (親の実測 8)。
この helper は floor JSON だけでなく `layer3_report._campaign_protocol` 経由で **WAL の genome にも**
使われており、receiptless な `build_start` は他の exact parser を通らない。
**body も検証する** — `name=整数` の組をカンマ区切りで並べた形であること、名前が重複しないこと、
名前順に並んでいること (`Genome.canonical()` が作る形)、body が空でないこと。
違反は拒否する。負例 test を実測 8 の 5 形すべてについて足す。

### P-5. create-only が半端な公開を残しうる

JSON を先に作ってから Markdown を組み立てて作るため、後半で例外が出ると JSON だけが残り、
次回は create-only precheck が再生成を拒否する。
**両方の内容を作りきってから file を作る**。2 つ目の作成に失敗したら 1 つ目を削除して、
半端な公開を残さない。この失敗経路の test を足す。

### P-6. M1 の変異が単一理由でない

M1 の正例は同一 workload の silo/mocc 2 file を置くため、protocol 比較を除去すると
後段の `len(matches) != 1` が独立に拒否する。赤の理由が一つに絞れない。
**wrong-protocol の floor をちょうど 1 件だけ置く負例**を足し、protocol 比較の除去だけが
赤の理由になる形にする。

## nit (直さない)

- レビュー B の所見 4 (焦点走 15 file が最小閉包でない): 段 7 の受入全走が repo 全体を走るため補完される。
  焦点走を広げる代わりに、受入全走の結果で判定する。
- レビュー A の所見 1 のうち TOCTOU の指摘: 述語判定と build の間に別 snapshot が入る点。
  P-2・P-3 を入れた後も残るが、submodule の作業ツリーを書き換えられる主体は
  そもそも hook 自体を足せる。本題の範囲を超えるため実装しない。
- レビュー B の「include を共通 header に置く正当な移植が偽になる」: fail-closed 側の誤りであり、
  安全な向きである。移植が実際に来た時点で述語を見直す。

## 変更しないこと

- 裁定 §3.7 の scope 外項目は引き続き実装しない。
- 既存テストの期待値を緩めない。P-1 の fixture path 修正と P-4/P-6 の負例追加は緩和ではない。
- `output/` の bytes、docs、submodule、commit には触れない。
