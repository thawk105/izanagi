# NO-GO

## 対応表

| 対象 | 状態 | 判断 |
|---|---|---|
| 1巡目 所見1 — `裁定され` の省略主語 | **partial** | 省略主語と外部対象 `E` は消えたが、免除条件を一意に `C∧Z` へ閉じる目的は、中黒の選択読み `C∨Z` により未達。 |
| 1巡目 所見2 — `実装面` の定義到達性 | **closed** | `実装面` を撤回し、旧正本と同じ `実装差分` に戻った。既存語の射程問題は本差分による回帰ではない。 |
| 1巡目 所見3 — 過剰変更 | **closed** | 差分は `core.md` の1物理行、1 insertion / 1 deletionだけ。 |
| 2巡目 所見1 — 原因理由・格助詞の `で` | **partial** | `で` と条件 `R` は消えたが、推奨された `・` が別の選択条件 `C∨Z` を許す。 |
| 2巡目 所見2 — `実装差分` への復帰 | **closed** | 現在も旧正本と同じ語を使用している。 |
| 2巡目 所見3 — `だけ`・受入全走・1行scope | **closed** | これら三点には回帰なし。ただし免除条件そのものには新規 blocker がある。 |

## 所見1 — 中黒は `かつ` に固定できず、`C∨Z` が成立する

severity: blocker

主張: `「実装しない」裁定済み・実装差分ゼロの wave` の中黒は、本文書群の慣行上、連言だけを表さない。免除資格を二種類並べた選択条件、すなわち「裁定済み、または実装差分ゼロ」と読むことができる。この場合、免除集合は旧正本の `C∧Z` から `C∨Z` へ拡大する。

### 四読解の検算

| 読み | 免除条件 | 旧 `C∧Z` との差 |
|---|---|---|
| (i) 並列・かつ | `C∧Z` | なし |
| (ii) 選択・または | `C∨Z` | **厳密な拡大** |
| (iii) 同格・言い換え | `C` または `Z` に縮約 | 両属性は同義でないため不正確。どちらへ縮約しても拡大 |
| (iv) 複合語・一体ラベル | 累積属性と定義すれば `C∧Z` | その定義が本文にないため、選択読みを排除できない |

### `docs/dev-wave/` の中黒慣行

連言・累積の実例:

- `範囲・言語・起動手順は入口に従い`は三項すべてへの要求。[core.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:7)
- `build・環境変数・外部 command ... を棚卸し`も全カテゴリの列挙。[core.md:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:39)
- `台帳・test・trust root を全列挙`は明示的な累積要求。[operations.md:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/operations.md:52)

選択・いずれかの実例:

- `指定 reference が不在・読めない`は、不在または読めない場合の停止条件。[core.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:22)
- `process の非 0 終了・timeout`は、いずれか一方で停止する条件。[core.md:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:122)
- `反転・緩和・skip・削除を禁じ`は、各操作のいずれも禁止する選択肢列挙。[workers.md:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/workers.md:60)

したがって本文書の局所慣行は、中黒を連言演算子に固定していない。免除条件の列挙も停止条件と同じ資格判定文脈であり、`C∨Z` は成立する読みである。

### 免除集合の独立再検算

`C` = 当該 wave が「実装しない」裁定済み、`Z` = 当該 wave の実装差分ゼロ。

| 具体 wave 像 | C | Z | 旧 `C∧Z` | 並列 `C∧Z` | 選択 `C∨Z` |
|---|---:|---:|---|---|---|
| 「実装しない」裁定、実装差分なし | 1 | 1 | 免除 | 免除 | 免除 |
| 「実装しない」裁定後、実行可能 probe を変更 | 1 | 0 | 非免除 | 非免除 | **免除へ拡大** |
| 本 T-765 のような docs-only 通常経路 | 0 | 1 | 非免除 | 非免除 | **免除へ拡大** |
| 通常の実装 wave | 0 | 0 | 非免除 | 非免除 | 非免除 |

file:line 根拠: 現在文は [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79)。旧正本と確定意味 `C∧Z` は [s4-adjudication.md:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s4-adjudication.md:22) および [s4-adjudication.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s4-adjudication.md:30)。中黒案の出所は [s6b-focus.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s6b-focus.md:43)。

成果物影響: `C=0,Z=1` または `C=1,Z=0` の wave が変異 matrix・kill 証拠なしで受理台帳へ入る。特に本 T-765 自身が `C=0,Z=1` であり、選択読みでは自己免除が再開する。

推奨対応: 現文を正本へ入れない。3巡上限なので第4巡の自動修正文面を重ねず、親が blocker を real/refuted に裁定する。real なら旧正本へ fail-closed に戻すか、二属性の連言を明記した別文を人間裁定へ送る。**現文は旧正本より悪化している**—旧正本の確定意味 `C∧Z` に対し、現文は `C∨Z` という免除拡大を許す。

## 所見2 — `だけ`・被免除物・後続義務・差分scopeは維持

severity: nit

主張: `だけ` は `[条件付き wave の変異 matrix]` に係り、免除対象は変異 matrix だけである。直後の `受入全走は免除せず、実 repo を読むテストがあれば…実走` は逐語で維持されている。`git diff --unified=0` は `core.md:79` の1行だけ、numstat は `1/1`、現在文は98 bytesだった。

file:line 根拠: [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79)、[core.md:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:80)、[s4-adjudication.md:29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s4-adjudication.md:29)。

成果物影響: matrix以外の受入義務や他節には明示的変更なし。ただし `だけ` は前置条件を連言へ固定しないため、所見1の免除拡大を救済しない。

推奨対応: blocker 処理時も後続文と1行scopeを維持する。pytestおよび `check_docs.py` は指示どおり実行していない。

## 総括

NO-GO。中黒は本文書内でも選択列挙に使われ、`C∨Z` による免除拡大が成立する。  
現文は旧正本より悪化しており、3巡上限どおり追加fixではなく親のfail-closed裁定へ戻す。  
`だけ`、matrix限定、受入全走非免除、1行scopeには回帰なし。