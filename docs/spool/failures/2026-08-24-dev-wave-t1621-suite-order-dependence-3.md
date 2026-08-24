---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-24
wave: dev-wave-t1621-suite-order-dependence
seq: 3
---

## 新規

### {{F:grep-counts-code-inside-string-literals}}. grep が文字列リテラル内の生成コードを実コードと数え、在否の棚卸しを 3 回誤らせた [誤前提] [観測]

- 事象: 受入 suite の順序依存を棚卸しする wave で、親が grep 起点に立てた在否の主張が
  **同一 wave 内で 3 回**誤った。(a) module scope fixture を 11 件と数えたが実体は 9 件で、
  2 件は内側 pytester 用 suite と一時 git repo へ書き出す template の**文字列リテラル内**だった。
  (b) 「module import 時に環境変数を直書きするテストが 2 件ある」と書いたが、どちらも
  生成子スクリプトの文字列リテラル内だった。(c) `xdist_group` の crude 走査が
  group 名を 6 種検出したが、権威ある golden は 3 種で、残りは group 契約テストの負例文字列だった。
- 根本原因: この repo は**子 process 用のスクリプトと内側 pytester 用の suite を三重引用符の
  文字列として持つ**。`grep` は字面しか見ないので、その中の `@pytest.fixture(scope="module")`、
  `os.environ[...] = ...`、`@pytest.mark.xdist_group("...")` を実コードとして拾う。
  在否・件数の主張は「安い代理指標」で立ててはならない (F270 と同型の構図)。
- 恒久対応: memory `ast-not-grep-for-python-inventory` — Python の在否・件数を数える走査は
  `ast.parse` + `ast.walk` で行い、grep の hit 数を inventory として報告しない。
  権威ある閉包 (golden 定数・frozenset 正本) が存在する対象では、走査結果でなくその閉包を数える。
- 再発検知: 「N 件ある / 無い」と書く前に、その数の出所が AST か権威ある閉包かを述べる。
  述べられない数は報告しない。段 2 / 段 3 の子は同じ file を読むので、
  親の grep 起点の件数は子の反証対象として brief へ明示する (本 wave では実際に子が 3 件とも反証した)。

## 再発

### F270

- **再発: 2026-08-24** — 四度目。受入 suite の順序依存 wave で、親が段 1 brief に
  「D746 の land 時の受入全走が、ほぼ最大の順序変更に対する負の対照として既に成立していた」と書いた。
  根拠は素の collection 順と所要降順の**正規化平均位置ずれ 0.315** である。
  **測った対象が実物でなかった。** (1) 距離の採取に使った `--collect-only` は受入の並べ替えを
  明示的に無効化するので、得た順序は「実 D746 後の順」ではない。(2) 実装は work unit 粒度なのに
  親は item 粒度で計算し、未知の擬似 cost も「第 96 位の既知 unit」ではなく「第 96 位の既知 item」で
  代用した。(3) 直接 pytest で採った node 集合は canonical な受入 collection と一致しない。
  さらに数の読み方も誤っていた — 正規化平均絶対変位は完全逆順で約 0.5、ランダム置換で約 0.333 なので、
  0.315 は「ランダム置換とほぼ同じ」であって「ほぼ最大」ではない。
  段 3 の敵対レンズ 2 本が独立に反証し、親が撤回した。実害は無し (記録前に反証された)。
  **代理指標が「状態を返す CLI の代わり」でなく「自作の offline 近似」の形を取ったのが今回の新しさ**で、
  memory `measure-state-dont-infer-from-proxy` の射程は自作の近似計算にも及ぶ。
  同 wave で構造的結論 (unit 内順序が保存される) だけは proxy でなく実装から得ており、
  こちらは撤回していない。
