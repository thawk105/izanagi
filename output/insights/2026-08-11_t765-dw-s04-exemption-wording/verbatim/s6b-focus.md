# NO-GO

## 1巡目所見の対応表

| 1巡目所見 | 現状 | 判定根拠 |
|---|---|---|
| 所見1 — `裁定され` の省略主語 | **partial** | 通常の断定連用では二属性が同じ `wave` に係る。一方、`で` の原因理由読みが新たな条件 `R` を作り、格助詞読みでは外部対象 `E` も残る。 |
| 所見2 — `実装面` の定義到達性 | **closed** | 新語 `実装面` を撤回し、旧正本と同じ `実装差分` に戻った。射程の既存問題は残るが、この差分による意味変更ではない。 |
| 所見3 — 過剰変更 | **closed** | 未commit差分は `core.md` の1物理行、1 insertion / 1 deletionだけ。明示的な新gate・義務・定義はない。 |

## 所見1 — 原因理由の `で` が免除集合を狭める

severity: blocker

主張: `裁定済みで` の通常読みは改善しているが、原因理由の `で` は「裁定済みであるため実装差分ゼロ」という因果条件 `R` を導入する。これは段4が既に blocker とした `C∧Z∧R` の再発であり、旧正本の `C∧Z` と一致しない。

### `で` の三読解

| 読み | 免除条件 | 集合変化 | `裁定済み` の被適用者 |
|---|---|---|---|
| (i) 断定の連用「〜であり」 | `C∧Z` | **変化なし** | 同じ `wave` |
| (ii) 場所・手段の格助詞 | 同じwaveの状態フィルタなら `C∧Z`。外部の裁定済み工程・判定欄を補えば `E∧Z` | 外部補完では**拡大・縮小し得る** | `wave` 以外の工程・記録 `E` が可能。ただし通常読みより不自然 |
| (iii) 原因理由の接続 | 同一対象なら `C∧Z∧R` | **縮小** | 通常は同じ `wave`。外部原因を補うと `E∧Z∧R` も可能 |

`C` は当該waveの「実装しない」裁定、`Z` は実装差分ゼロ、`E` は別対象の同裁定、`R` は裁定がゼロ差分の原因であること。

### 免除集合の独立再検算

| 具体wave像 | C | Z | E | R | 旧 `C∧Z` | (i) 断定連用 | (ii) 外部格助詞 `E∧Z` | (iii) 同一wave因果 `C∧Z∧R` |
|---|---:|---:|---:|---:|---|---|---|---|
| 非実装裁定により変更を行わなかったwave | 1 | 1 | 0 | 1 | 免除 | 免除 | **非免除** | 免除 |
| 既に差分ゼロで、その後「実装しない」と裁定したwave | 1 | 1 | 0 | 0 | 免除 | 免除 | **非免除** | **非免除** |
| 別案だけが非実装裁定済みのdocs-only通常wave | 0 | 1 | 1 | 1 | 非免除 | 非免除 | **免除** | 非免除 |
| 非実装裁定後に実行可能probeを変更したwave | 1 | 0 | 0 | 0 | 非免除 | 非免除 | 非免除 | 非免除 |
| 通常のコード実装wave | 0 | 0 | 0 | 0 | 非免除 | 非免除 | 非免除 | 非免除 |

少なくとも第二行で旧正本との差が生じるため blocker。第三行は、格助詞として外部の裁定状態を補う読みを採った場合の免除拡大である。

file:line 根拠: [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79)、[brief.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:25)、[brief.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:26)、[s4-adjudication.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s4-adjudication.md:7)、[s6-focus.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s6-focus.md:16)

成果物影響: 因果読みでは正規の免除waveに不要な変異matrixを要求する。外部対象読みでは、当該wave自身が非実装裁定を受けていないのにmatrixを免除でき、kill証拠のないwaveが受理記録へ入る。

推奨対応: 原因・格助詞にならない属性区切りへ置換する。例えば `免除は「実装しない」裁定済み・実装差分ゼロの wave の変異 matrix だけ。` は98 bytesで、現状と同じL1使用量に収まる。置換後は3巡目の焦点レビューで係り受けを再確認する。

## 所見2 — `実装面` の到達性回帰は解消

severity: must-fix

主張: 1巡目で導入されていた未定義語 `実装面` は消え、旧文と同じ `実装差分` に戻ったため、この差分による射程変更はない。probe・harness・script・機械設定を含むかという既存問題は、別裁定へ返すという親方針と整合する。

file:line 根拠: [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79)、[brief.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:17)、[dev-wave.md:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:34)、[s6-focus.md:44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s6-focus.md:44)

成果物影響: 現差分は `実装差分` の受理集合を旧正本から変更しない。既存の射程問題自体は将来の誤分類要因として残る。

推奨対応: 本waveでは再定義せず、予定どおり独立の裁定パッケージへ送る。

## 所見3 — 回帰・過剰変更なし

severity: nit

主張: `だけ` は `[条件を満たす wave の変異 matrix]` 全体に係り、被免除物は変異matrixだけである。直後の「受入全走は免除せず」と実repoテスト実走義務は逐語的に維持されている。差分は `docs/dev-wave/core.md` の1物理行だけで、98 bytes、L1余白4という親実測と整合する。

file:line 根拠: [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79)、[core.md:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:80)、[brief.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:5)

成果物影響: matrix以外の受入義務、gate、定義、参照先に明示的変更はない。ただし所見1の原因読みが暗黙の追加条件 `R` を作る。

推奨対応: 所見1の修正時も1文・1行のscopeと、後続文の逐語を維持する。

## 総括

通常の断定連用読みは旧正本と一致するが、原因理由の `で` が `C∧Z∧R` を再導入するためNO-GO。  
`実装差分` への復帰、matrixだけの免除、受入全走非免除、1行scopeには回帰なし。