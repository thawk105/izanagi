# NO-GO

## 段 3 blocker 対応表

| 段 3 所見 | 判定 | 実差分での状態 |
|---|---|---|
| A1/B1 — `受けて` の因果・別対象読み | **partial** | `受けて` は消え、因果・時系列条件 `R` は除去された。一方、連用形 `裁定され` の省略主語が `wave` に固定されず、別対象の裁定を拾う第三読解が残る。 |
| A2/B3 — `実装差分` の射程 | **partial** | `実装面` に改めたため dispatcher 経由の読者には正しく束縛される。しかし `core.md` 単体から定義元へ到達できず、正しさ防壁内では未定義語になる。 |
| A3/B5 — 本 wave の自己免除 | **closed** | 段 4 が本 wave を `C=false`、通常経路、matrix 非免除として変更不能に固定している。 |
| B2 — `かつ` による裁定と wave の並列読み | **closed** | `かつ` 案は採用されていない。残る省略主語問題は A1/B1 の partial として扱う。 |

## 所見 1 — 連用形が第三の免除集合を作る

severity: blocker

主張: `「実装しない」と裁定され実装面差分ゼロの wave` は、意図した「同一 wave が裁定済みかつ差分ゼロ」だけに閉じていない。次の読みが成立する。

| 攻撃した係り受け | 結果 |
|---|---|
| `裁定され` の主語 = 当該 `wave` | 意図どおり `C∧Z`。 |
| `裁定され` の省略主語 = 直前文脈の変更案・別 wave | 成立する。`免除は、（別対象が）「実装しない」と裁定され、実装面差分ゼロの wave の変異 matrix だけ` と読め、`E∧Z` になる。これが第三読解。 |
| `裁定され` の主語 = 文頭の `免除` | 文法上は切れるが、「免除を実装しないと裁定する」という意味が不自然で、独立した有力読解とは数えない。 |
| `実装面差分ゼロ` が matrix に係る | 自然には成立しない。直後の `の wave` が差分ゼロを wave へ直接束縛している。 |
| `だけ` の係り先 | 回帰なし。旧文・新文とも直前の matrix を含む名詞句に付き、次文も受入全走の非免除を明示する。 |

file:line 根拠: [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79)、[core.md:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:80)、[s4-adjudication.md:23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s4-adjudication.md:23)、[s4-adjudication.md:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s4-adjudication.md:27)、[s3-lensB.md:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s3-lensB.md:15)

### 免除集合の独立再検算

`C` は当該 wave 自身の「実装しない」裁定、`Z` は定義どおりの実装面差分ゼロ、`E` は別対象の「実装しない」裁定とする。旧文は裁定済みの正本意味 `C∧Z` と比較した。

| 具体 wave 像 | C | Z | E | 旧正本意味 | 新・意図読解 | 新・第三読解 `E∧Z` |
|---|---:|---:|---:|---|---|---|
| 当該段 4 で「実装しない」、実装面変更なし | 1 | 1 | 0 | 免除 | 免除 | **非免除（縮小）** |
| docs-only 通常経路。ただし直前文脈の別案が「実装しない」裁定済み | 0 | 1 | 1 | 非免除 | 非免除 | **免除（拡大）** |
| 本 T-765。規範文を置換する通常経路 | 0 | 1 | 0 | 非免除 | 非免除 | 非免除 |
| 「実装しない」裁定後、実行可能 probe だけ変更 | 1 | 0 | 0 | 非免除 | 非免除 | 非免除 |
| 通常のコード実装 wave | 0 | 0 | 0 | 非免除 | 非免除 | 非免除 |

成果物影響: 第二行では、現行が非免除とする wave が変異 matrix・kill 証拠なしで受理集合へ入る。第一行では正規の免除 wave を不当に狭める。`check_docs.py` の構造・byte 検査が緑でも、この意味差は検出されない。

推奨対応: `裁定され` の連用中止をやめ、両属性が直接 `wave` を修飾する形へ戻す。段 3 A の `「実装しない」裁定済み・実装面差分ゼロの wave` 等を再候補とし、予算を含めて段 4 へ差し戻す。

## 所見 2 — `実装面` の定義へ core 単体から到達できない

severity: must-fix

主張: `実装面` の正確な集合は command の凍結境界だけが定義するが、`core.md` はそのファイルや節を指していない。`DW-C00` の「入口に従い」も入口のパスを示さない。command-first の正式 dispatcher では読めるものの、`core.md` を正本として直接読む consumer には「コード・テストだけ」「全非 docs」「実行可能物と機械設定」の選択肢が残る。

file:line 根拠: [dev-wave.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:31)、[dev-wave.md:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:34)、[core.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:7)、[core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79)、[README.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/README.md:31)

成果物影響: 狭い意味を採る standalone consumer は、probe・harness・script・機械設定だけを変更した `C=true` wave を `Z=true` と誤分類し、必要な変異台帳行を免除できる。

推奨対応: 免除文から凍結境界の定義へ明示的に逆参照できるようにする。現行の L1 余白 1 byte では収まりにくいため、黙って scope を広げず、brief が許す同一 L1 内の意味等価な縮約を含めて段 4 で再裁定する。

## 所見 3 — 過剰変更はない

severity: nit

主張: 未 commit 差分は `docs/dev-wave/core.md` の当該 1 行だけで、1 insertion / 1 deletion。新しい機械 gate・義務・定義は追加されず、受入全走の非免除文も変更されていない。

file:line 根拠: [brief.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:5)、[core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79)、[core.md:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:80)

成果物影響: 過剰変更による追加の受理集合・gate・参照変更はない。

推奨対応: 係り受けと定義到達性の修正時にも、この 1 文だけという scope を維持する。pytest・`check_docs.py` は本レビューでは再実行していない。

## 総括

実差分は scope 内だが、`裁定され` の省略主語により旧正本と異なる免除集合が成立するため NO-GO。  
`実装面` も core 単体から定義へ到達できず、防壁文として未閉鎖である。  
A3/B5 と B2 は closed、A1/B1 と A2/B3 は partial。