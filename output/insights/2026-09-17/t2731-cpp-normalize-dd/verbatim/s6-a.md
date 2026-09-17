## 所見 (real 候補)

**対象 GCC・固定 argv の通常経路について、実装を差し戻す must-fix は確認できませんでした。署名検査と説明・証拠の範囲に should が 3 件あります。**

**A6-1 — G は「環境 prefix 不一致」という拒否理由を固定していない。**

- **根拠:** `orchestrator/tests/test_campaign.py:11984`、`orchestrator/campaign/source_digest.py:1691,1695,1702`。
- **real と主張する理由:** `pytest.raises(RuntimeError)` のみなので、偽 compiler の起動失敗・非ゼロ終了でも成功する。現物の正常経路では意図した prefix 不一致に到達するが、テスト単体は裁定 §3 の署名を保証しない。また、修正前実装へ新テストだけ載せると、G の `finally` が未存在の `_CPP_ENV_PREFIX_CACHE` を参照し、意図した「例外が出ない」失敗を `AttributeError` で覆う。
- **重要度・放置時の影響:** **should**。製品の現在の受理集合は変わらないが、レポートで G の緑／赤を拒否署名の証拠として過大評価できてしまう。
- **是正案:** **scope 内**。既存 G の例外検査に「環境 prefix と不一致」「fails-closed」を指定する。修正前比較も行うなら cleanup を cache 未存在に対応させ、赤理由を保存する。新しい gate は不要。

**A6-2 — A-3 の受理変更が製品側 docstring に明示されていない。**

- **根拠:** `orchestrator/campaign/source_digest.py:1666,1672,2180,2195,2230`、`s4-ruling.md:15`。
- **real と主張する理由:** A-1／A-2 は追記済み。一方、TRACE 有効枝の未使用 `#define`／`#undef` も差分素材になるという A-3 は docstring にない。HEAD にない当該指令を追加すると、本文の展開結果が同じでも `D_variant != D_stock` になり得る。author 報告はこの変更を正しく記載している。
- **重要度・放置時の影響:** **should**。実装による受理変更は意図どおりだが、レポートが「比較式不変」を「受理集合不変」と引用する余地が残る。
- **是正案:** **scope 内**。既存 docstring に「比較式は維持するが、TRACE 条件付きの未使用指令も比較対象になる」を追記する。除外処理は追加しない。

**A6-3 — 焦点走ログの証拠範囲は「login・実 compiler 確認済み」ではない。**

- **根拠:** `s5-focus-run.log:2,10,16,22,38`、`s4-ruling.md:46,75`、`s5-impl.diff.txt:17`。
- **real と主張する理由:** ログは `gen_S` への dispatch、request `2748.nqsv`、child rc=0、`38 passed, 3 skipped` を記録している。compiler の実体・版、個別 node の結果は記録していない。commit message は計算ノード・g++ 11.4 と説明するが、このログ単独から compiler は裏付けられない。
- **重要度・放置時の影響:** **should**。製品値は変わらないが、実行場所・compiler・実 submodule 検証のレポートと証拠参照が不正確になる。
- **是正案:** **scope 内**。焦点走は計算ノード実行と記載し、compiler や個別 node の確認は対応する既存証拠へ結び付ける。この集計ログを受入全走や規律 7 完了の証拠にしない。

## 拒否の署名と正例の照合

| 対象 | 静的照合結果 |
|---|---|
| 拒否 1 | A／B／H の追加指令は prefix 後に残り、baseline と異なる digest・非 stock token になる。指令を持つこと自体を RuntimeError にする変更ではない。 |
| 拒否 2 | `source_digest.py:1702` で指定の RuntimeError。warning・skip・best-effort への格下げなし。 |
| 未参照 CMake 供給 | working-tree／HEAD がそれぞれ自分の defines に対応する prefix を除くため、追加供給だけを identity へ混入させない。 |
| comment-only | コメントは前処理で消え、stock 比較を維持する。 |

裁定の拒否 1 は、**登録対象の指令追加と、前段検査・前処理が正常終了する条件**で読む必要がある。「指令を含む任意の source は必ず非 stock」ではない。HEAD にも同じ指令がある場合や、別の既存検査で停止する入力まで含む全称命題にはできない。

prefix 周辺は次のとおりです。

- **cache key:** `source_digest.py:1677` は `(cxx, tuple(sorted(defines.items())))`。argv の defines もソートするため、辞書挿入順による取り違えはない。別の `cxx` 文字列は別キー。
- **環境の固定条件:** 同じ `cxx` 名が後で別実体を指す場合や、環境・`BUILD_FLAGS` の変更はキーに含まれない。固定 compiler・固定 argv を超える保証はない。
- **空 prefix:** rc=0・stdout 空なら保存され、`startswith("")` は恒真になる。対象 GCC の提示実測では非空であり、通常 source 編集からこの状態を作る経路は確認できない。任意 wrapper の正常性まで保証する実装ではない。
- **失敗結果:** cache 代入は再帰呼出しの正常終了後。起動例外・非ゼロ終了時の部分 stdout は保存されない。本体失敗時に残るのは、先に正常取得した環境 prefix。
- **再帰:** 現物の `_environment_only=True` 呼出しは `source_digest.py:1680` の空入力のみ。非空入力で呼ぶ製品経路は確認できない。
- **剥がしすぎ:** `removeprefix` は先頭の完全一致部分を一度だけ除く。同文の source define が直後に続いても、その指令は残る。
- **builtin:** undef→再define は source 側に残る。undef 後の未定義名を `#if` が参照すれば、従来どおり `-Werror=undef` で停止する。`__COUNTER__`／`__DATE__` の本文展開を prefix として保存する経路はない。先行断片実測もこの判断を支持する（`s3-a-out.md:78`）。

新 8 node の修正前予測は以下です。自分で実走した結果ではありません。

| node | 修正前予測 | 理由 |
|---|---|---|
| A／B | 赤 | 指令が消費され、非 stock・digest 不一致の assert が失敗 |
| C／D／E | 緑 | コメント・未参照供給は旧出力にも残らない |
| F | 赤 | live 枝の追加指令が消え、兄弟 variant と同じ token／digest |
| G | 赤 | 旧実装は prefix を比較しない。ただし cleanup が赤理由を覆う（A6-1） |
| H | 赤 | 同名同値の source 再定義が消え、stock と一致 |

A／B／C／D／H は実 `resolve`・`compute`・`baseline`、E は実 `compute`・`baseline`、F は実 `resolve`・`compute` の前後関係を検査しています。共有 fixture の変更、揮発 payload や出力 digest の焼込みはありません。

G は実 `subprocess.run` を通り、現物の `-x c++ -` と stdin が shell script に渡ります。script は stdin を消費して空／非空で分岐しますが、argv の正しさ自体は検査していません。

## 不変条件と規律 7

- **inert template = stock:** `BACKOFF_FIXED`／`BACKOFF_NOINLINE` が未参照なら、追加供給行は各環境 prefix として除去される。静的に支持できる。
- **compute／baseline:** source 順序、文脈タグ、NUL 結合、UTF-8、SHA-256 は維持されている（`source_digest.py:1715,1991,2129`）。「同値 ⇔ 同一 pre-image」は SHA-256 衝突を除く前提。同じ実プログラムとの同値ではない。
- **trace:** `D_variant == D_stock` の比較式は維持。比較素材には指令が増えるため、受理集合不変とは言えない。
- **HOLE_ESCAPE／nm:** 差分対象外。現物でも生指令拒否と trace symbol 拒否が残る（`diff_quarantine.py:490`、`buildcache.py:3761`）。今回の B は binary 検査の証拠ではない。

裁定 §4 の予測に、静的に反する挙動は見つかりませんでした。

| 対象 | 再導出 |
|---|---|
| M3b／M6 | top-level 指令が stock／variant 双方の pre-image に加わるため N1a／N1b が赤になる予測。既存 N2a／N2b と合わせ全 4 node。 |
| M6 trace | 同じ source 指令が TRACE=0／1 双方に残り、backoff 本文に TRACE 参照がない条件では差分検査通過の予測を維持。 |
| M0 | コメント除去により同 identity、SURVIVED の予測。 |
| M3a | live variant 側だけ指令が残り、N1b＋N2b の予測。 |
| M4／M4b | 基準 template との差を指令列が残す。variant 相互の全面的識別は保証しない。 |
| 未変異 baseline | 対象 template に追加指令がなく、同一 compiler 条件なら旧 token 維持を支持。固定 token の実測一致は未確認。 |

source-level 変異の期待集合も、S1=A/B/F/H、S2=D/E、S3=G、S0=空集合という登録と静的に整合します。

ただし、**4 node が赤という集計だけでは規律 7 の条件を満たしません**。一律 RuntimeError でも赤になるため、裁定どおり token 不一致・reference 不一致という赤理由が必要です。提示された焦点走ログには recipe observations や baseline `token.txt` の結果はありません。

## 主張の限定の更新

A-1／A-2 は `source_digest.py:1672` に適切に記載されています。A-3 は A6-2 の補足を推奨します。

追加すべき限定は次のとおりです。

- G が現在固定しているのは例外型までであり、拒否理由の署名までではない。
- cache の議論は固定 compiler・固定実行環境を前提とする。
- 焦点走集計と、登録変異の期待署名・baseline token 一致を区別する。
- 「有効枝の指令は別 identity」は、基準との差として残る登録対象について述べる。

「全 compiler で token 不変」「非再帰境界の全面閉塞」「trace 受理集合不変」「今回 nm 拒否まで実証」は引き続き書けません。`__DATE__` に関する既存 docstring の「毎回 cache-miss」も、この実装から導ける一般保証ではありません。

## 総括

**裁定 (a) の実装は、登録対象の指令を identity に残し、未参照の環境供給を除く設計として支持できます。must-fix は未検出、should は A6-1〜A6-3 です。**

登録済み衝突の修復完了は、裁定済みの変異署名と token の証拠に依存します。本レビューは静的検査のみで、テスト・compiler の実走、書込み、commit、push は行っていません。