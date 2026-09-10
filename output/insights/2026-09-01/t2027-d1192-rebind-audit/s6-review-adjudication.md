# 段 6 レビュー裁定 — [T-2027]/[T-2043] D1192 択 (1)

## レビューの実施状況

- レンズ A (正しさ境界・受理集合): 1 回目は内容が完結していたが `## 総括` 見出しを欠き、
  launcher が `failure_class=f43_fragment` で不採用にした。gate を迂回せず prompt を是正して
  投げ直した。1 回目の出力は
  `artifact-root/t2027-d1192-rebind/t2027-d1192-rebind-review-b6fa0a9c.../attempt-0001.output.md`
  に保全してある (未採用と明記)。そこから出た 1 件の所見は親が実測で確認して採用した (下記 R1)。
- レンズ B (呼び出し閉包・実効性): `tools/check_codex_output.py` rc=0 で採用。

## must-fix (段 6 fix で直す)

### R1. 先頭が `//` の絶対 path で uncaught `ValueError` が漏れる

- 出所: レンズ A 1 回目。**親が実測で確認済み。**
  `os.path.abspath("//x")` と `os.path.normpath` は POSIX の規定により先頭の二重 slash を
  保存する。その値に `Path(...).relative_to(Path("/"))` を当てると
  `ValueError: '//x' is not in the subpath of '/'` が出る。
- 影響: 呼び手 (`s8b_binary_admission`、`buildcache._build_v2_impl`) はいずれも
  `except CompilerInputError` しか持たないため、binary admission receipt の発行器が
  構造化拒否ではなく異常終了する。該当 cell は compiler-input anomaly として記録されず、
  receipt と certified 選択が欠落する。v1 は `resolve(strict=True)` が `/x` へ正規化して
  いたので**退行**である。
- 採用する修正の向き: **入力 path を絶対化する 1 箇所で、先頭の連続 slash を 1 つへ畳む。**
  親が特定した位置は `collect_compiler_input_manifest()` 内の
  `absolute = Path(os.path.normpath(os.path.abspath(raw_path)))` (`s8b_compiler_input.py:1032`)。
  ここで畳めば snapshot / fetchcontent-masstree / filesystem の 3 分岐すべてと、
  `relative_to(snapshot)` および `relative_to(origin_masstree)` の比較が同時に救われる。
  分岐ごとに個別対処しない。
  根の側は対処不要である — `_strict_root()` は `os.path.realpath` を通すので二重 slash を
  既に畳んでいる。validator の filesystem 分岐 (`s8b_compiler_input.py:926`) も、
  検証済みの相対 POSIX path を `/` へ join するだけなので二重 slash を作れない。
  負例は `pytest.raises(CompilerInputError)` で**例外の型まで**固定する。正例として、
  `//` で綴った入力が単一 slash で綴った場合と同一の manifest と digest を生むことを固定する。
- scope: D1192 が変更する collector の path 正規化そのもの。scope 内。
- 欠陥 A と同族である (正規化述語を通過した値が下流で domain 例外の外へ出る)。
  台帳へはこの**型**で記録する。

## real だが scope 外 (実装せず裁定パッケージへ返す)

### R2. oracle の descriptor 経路に現在の masstree 根が届かない

- 出所: レンズ B 所見 1。
- 親の裏取り: `s8b_oracle_driver` の wrapper は `expected_materialization_descriptor` だけを
  注入する。descriptor 経路は `allow_external_compiler_inputs=True` を強制する。
  そして `pipeline.py` と `s8b_oracle_driver.py` のいずれにも `fetchcontent_base_dir` の
  供給が**無い** (両 file を全文検索して 0 件)。つまり oracle build の masstree は
  build 後に破棄される作業用 directory の中へ取得され、**再束縛先の安定した根が
  そもそも存在しない**。
- **本 wave の変更が入れた欠陥ではない。** 変更前の v1 でも、同じ oracle cache hit は
  絶対 path の `resolve(strict=True)` が失敗して
  `external compiler input is unavailable` で落ちていた。根本原因は同一で、
  本 wave はその経路を悪化させても改善してもいない (誤差は診断文言だけ)。
- 是正には oracle build へ安定した共有依存基底を与える設計判断が要る。これは D1192 の
  裁定文が扱っていない新しい設計であり、ユーザー裁定へ返す。
- レビュー B の「D1192 の run 間 cache 再利用が完成したという解釈は oracle 経路により
  反証される」という指摘は**正しい**。本 wave が閉じるのは床値の descriptor 経路だけであり、
  この限界は記録して返す。

### R3. floor の現在の根の供給が `sort_best` の同居に依存する

- 出所: レンズ B 所見 2。
- 親の裏取り: production の `build_cells` 呼び手は 2 箇所とも
  `cells = enumerate_cells(freeze, stock_configuration=protocol["stock_configuration"])`
  の**完全列挙**を渡す。絞り込んだ集合を渡すのはテストだけである。
  `enumerate_cells` が要求するのは `stock_configuration` の在籍であって `sort_best` ではない
  ため、`sort_best` を持たない freeze は構造上ありうる。
- `DW-G04` に従い、発火条件を満たす既存 artifact path も計測 ID も名指しできないので
  実装しない。レビューが挙げた代案「その経路を明示的に禁止する」は gate の新設にあたり、
  ユーザーが本 wave の scope から明示的に外している。
- backlog として返す。

## refuted (実装しない)

### R5. `filesystem` tag で stale masstree 根を current 根の検査なしに受理できる

- 出所: レンズ A2 所見 1。
- 親の裏取り: 指摘された「`allow_external_inputs=True` かつ origin 根 `None`」の組み合わせは
  **既存テスト 11 件が現に使っている設計どおりの mode** である
  (`test_s8b_compiler_input.py` の 293/334/389/406/422/440/509/527/558/572/623 行)。
  masstree の根が分からないときに外部入力を絶対 path 相当の `filesystem` として記録するのは
  v1 と同じ意味論への退化であり、この変更が新設した受理拡大ではない。
- **認可された経路からは到達しない。** 修正 B 以降、`buildcache._build_v2_impl` は
  `allow_external_compiler_inputs` が真のときに必ず origin 根を解決して渡し、偽のときは
  外部入力そのものを拒否する。したがって「外部入力を許すのに根が無い」manifest を
  sanctioned producer は生成できない。
- 別 FetchContent 基底配下の入力が `filesystem` へ落ちる経路も検討したが、origin は
  その build 自身の CMakeCache から読むため、パイプライン上は入力の基底と origin が一致する。
- 受領書は `filesystem` entry について「現在の根で検証した」とは主張していない。
  主張していない保証が破れているわけではないので、must-fix にしない。
- **ただし保護の射程は明記する** — 本 wave が現在の canonical 根へ再束縛するのは
  `fetchcontent-masstree` と分類された入力だけである。`filesystem` 入力は記録時の絶対位置で
  bytes を検査する。この限界は主張せず記録する (絶対規律 7)。
- レビューが指摘した「stale A を指す `filesystem` の負例テストが無い」点は nit として下記へ送る。

### R6. production floor の cache identity が run-local な source root を含み、run 間 hit が成立しない

- 出所: レンズ A2 所見 2。
- 親の裏取り: **事実として正しい。** `buildcache.py:2225` のコメント自身が
  「正式 S8b 経路では admission preimage が絶対 `source_root` を含み、materializer が
  毎回一意な worktree を作るため cache hit は起きない」と記している。
- **しかしこれは本 wave が直す赤とは別の話である。** [T-2043] が実測したとおり、
  床値 job の赤は **cache hit 条件ではなく無条件**で、cache が空の初回実行でも落ちる。
  build 自身が作業用 directory を破棄してから受領書発行へ進むためである (F754)。
  本 wave が直すのは**同一 job 内の受領書発行時点の再束縛**であり、そこが赤の実体である。
  受領書へ渡す現在の根 (`dependency_binding.source_root`) は共有 prebuild 済みの依存根なので、
  作業用 directory の破棄を生き延びる。
- D1192 の「run 間の cache 再利用は失わない」は、修正が**事態を悪化させない**ための制約で
  あって、修理される機構ではない。本所見はその制約の充足を反証しないし、
  31 件クラスの修理も反証しない。
- 変更前から存在する性質であり、是正には admission preimage の構成を変える設計判断が要る。
  backlog として返す。

## nit (実装しない)

### R4. 7 件クラスの境界を固定する回帰テストがない

- 出所: レンズ B 所見 3。レビュー自身が「現時点の成果物値への影響はない」と述べている。
- 本 wave は 7 件クラスを実装しないと裁定済みであり、その境界を固定するテストの追加は
  射程裁定が出てからでよい。`DW-G05` により must-fix にしない。

## レビューが反証しなかった親の前提

- (P1) 実装は択 (1) の忠実な実装であり受理集合を裁定の外へ広げていない — 反証なし。
  レンズ A は v1 拒否条件と v2 の 1 対 1 対応表を作り、認められる受理拡大は
  「消えた origin A の代わりに同じ相対 path と hash を持つ current B を受理する」
  D1192 本体だけだったと報告した。
- (P2) 欠陥 B は実 S8b では発火しない — レンズ B が CMake 述語の値域を現行 pin と
  Unix Makefiles で照合し、一致すると報告した。
- (P3) schema pin は D1192 却下案と別物で遷移時 1 回の miss に留まる — レンズ B が
  identity の構成を確認し、正常に current root を供給する経路では 1 回だけと報告した。
- (P4) v1 は read-only 互換のまま — 反証なし。
- 31 件クラスは official full-floor で救われる — レンズ B が 6 段の経路を辿って支持した。
- 7 件クラスは黙って受理されず、誤った再束縛も起きない — レンズ B が支持した。

## 変異の追加登録 (`DW-M01`: 段 6 の real 所見は fix 前に登録する)

段 4 で登録した 7 件に、R1 を守る 1 件を**fix の前に**足す。

| ID | 実効 gate | 単一変異 | 単一赤理由 |
|---|---|---|---|
| M14-DOUBLE-SLASH-ACCEPTED | collector の入力正規化 | 先頭の連続 slash を畳む処理を外す | `//` 入力が uncaught `ValueError` へ落ちる |

期待 node は fix 後の最終 commit で probe 走行により実測して完全集合を確定する
(`DW-M07` / `DW-M08`)。anchor の逐語も同じ commit で再検証する。

## fix の分割

Codex `role=fix` 1 本。編集面は `orchestrator/campaign/s8b_compiler_input.py` と
`orchestrator/tests/test_s8b_compiler_input.py` だけ。R1 のみを直す。
