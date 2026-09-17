## 所見一覧 (番号・real/refuted/判定不能・file:line・1 行要旨)

参照略号：`T`＝`orchestrator/tests/test_s8b_oracle_driver.py`、`H`＝`orchestrator/campaign/s8b_holdout_freeze.py`、`M`＝`orchestrator/campaign/t080_freeze_migration.py`、`G`＝`orchestrator/campaign/s8b_oracle_driver.py`。`brief`・`plan` は指定 job dir の `s1-brief.md`・`s2-plan.md`、裁定名は同 `verbatim/` 内のファイルを指す。

1. **real** — `plan:10`、`T:1380`、`T:1431`、`T:1450`：射影集合との差は今回の取り込み増分を測れるが、実 repo 全体に対する検出力の一致を保証しない。
2. **real** — `T:1382`、`H:352`：copytree の名前除外は tracked 状態より優先されるため、将来の tracked `*.pyc` 等を production scan から fixture へ移す経路は欠ける。現在の tracked 該当物は読み取り列挙でゼロ。
3. **real** — `T:1431`、`T:1450`、`H:383`：historical blob と known pin は現在の source bytes／path 集合を置換しうる。現在の差の全量は**判定不能**。
4. **real** — `T:830`、`M:37`、`H:45`：receipt／draft は fixture コピーから除外されるが、production の既定 scan 除外には含まれない。
5. **refuted** — `H:1049`、`M:1741`、`G:299`：現在の追加 file に三軸語が無いという条件下で、live file count の増加だけが拒否を生む経路は確認できない。
6. **real** — `M:1831`、`M:2009`、`M:2277`：basis／HEAD／receipt bytes の束縛は存在する。index 切替 probe は実際の発行 A/B の代替にはならない。
7. **real** — `T:1688`、`T:1705`：既存の可視性検査は output コピーまでであり、builder の再 index 化後の config.h 欠落を検査しない。
8. **判定不能** — `config.h:1`、`H:558`：将来の conjunction 混入を機械的に検出する差はあるが、通常の configure 再生成で実際に混入する根拠は無い。
9. **real** — `brief:12`、`brief:13`、`plan:94`：一般解を「add 1 file」「件数非依存」と扱う説明は不正確。現在の入力は419 path。
10. **real** — `brief:9`、`plan:128`：login node での性能測定指定は提示された実行規律に反する。
11. **real（限定）** — `T:1382`、`H:374`：親の「untracked 0」は非 ignored 可視集合なら再確認できたが、ignored を含めると9件ある。全件 `__pycache__/*.pyc` だった。

## 忠実性の定義と規律 2 (攻撃点 1・3)

**plan の定義は今回の差分測定には使えるが、ユーザー依頼にある「実 repo と1件ずれ」の全域的な形式化には不足する。**

実 repo の scan 集合を `R`、現行 fixture を `A`、取り込み後を `B`、構築規則による期待集合を `E` とする。`B−A={config.h}` と `E−B` の縮小は、`R−B` が空であることを意味しない。fixture 側には追加・置換もあるため、全体を単純に `A⊂R` と書くのも不正確である。検出不足は `R−A` と、共通 path の bytes 差で扱う必要がある。

| 対象 | 判定 | 検出不足の方向と根拠 |
|---|---|---|
| (a) copytree の除外 | **real：構造上の穴。現在の該当欠落は反証なし** | `T:1382` は全階層の `__pycache__`・`*.pyc` を除外する。`H:352` は tracked regular file を拡張子で除外しない。読み取り列挙では現在の tracked 該当物はゼロだった。 |
| (b) basis 上書き | **real** | `T:1431` は現在の bytes を historical blob で上書きする。現在の source にだけある conjunction は、同じ path が fixture に残っても消えうる。`T:1427` に歴史的 migration 再現の理由があるが、実 repo の現在の scan と同一にはならない。 |
| (c) submodule pin | **real：差が生じる経路。現在差は判定不能** | `T:1450` は known pin を checkout する。一方 `H:383` は対象 root の submodule index を列挙し、`H:618` 以降は working bytes を読む。現在の checkout の追加 tracked file・変更 bytes は fixture に反映されない場合がある。 |
| (d) receipt／draft | **real** | `T:830` で除く2 path は `output/t080-migration/` 配下（`M:37`）。既定除外は `output/s8b-freeze/` だけ（`H:45`）。元の receipt の内容を fixture で検査することと、新規発行物を `M:1985`・`M:2048` で検査することは別である。 |

これらを今回一括修正する必要はない。ただし、射影で除外したものを「一致した」と数えてはならない。今回の成果は「意図的な再構成を前提とした、config.h の追加的な可視性回復」と限定するのが正確である。

規律2との関係では、両案を次のように評価する。

- **hard-code**：今回のコピー済み1 file を確実に取り込む。対象欠落時に失敗する実装なら、その失敗を隠さない。ただし将来の同型 path は救わない。
- **一般解**：構築時 snapshot とコピー契約を対応させ、予期しない欠落を失敗にするなら、将来の同型欠落にも強い。
- **存在しない path を一律に黙って捨てる一般解**：意図的除外とコピー失敗を区別できない。`T:835` の output コピーが既に持つ fail-closed な姿勢にも逆行する。

したがって「一般解」という名前だけで規律2に近いとは言えない。黙って捨てる一般解より、契約の狭い hard-code の方が今回の保証は明確である。

**現状維持は新たな集合縮小ではないが、既知の検出不足を維持する。** D2086:23 の「構築時点」は時間の契約であり、構築時点に既に存在する tracked file を落としてよいという裁定ではない。実 repo 直接検査は別経路として存在する（`T:3450`、`G:169`、`M:2343`）が、それで fixture 自身のコピー忠実性が保証されるわけではない。反対に、今回の欠落が production scanner 自体の対象を減らすわけでもない。

## 判定不変と DW-G05 (攻撃点 2・4)

**現在の config.h を basis commit 前に正しく追加して新規発行する場合、受理・拒否が変わる静的反証は見つからなかった。ただし「束縛経路が無い」「成果物が同一」は誤りである。**

読み取り検査で、config.h は10,448 bytes、`ycsb_rratio`・`ycsb_zipf_skew`・`ycsb_rmw` はすべて0件だった。検索式はこれらの literal を必要とする（`H:64`）。そのため現在の file の追加は軸別 count・conjunction・positive control を増やさない。

束縛経路は次のように分かれる。

- `H:580` は軸別 count と conjunction path を hash 化する。単に「conjunction が無い」だけでは semantic hash 不変の証明にならないが、今回は三軸語がすべて無いためこの経路も変わらない。
- `H:1049` は保存済み count の型と非負性だけを検査する。live count との等値比較ではない。
- `M:1734` は projected document 全体を hash 化するため、その保存済み `search` も間接的には束縛される。ただし追加 file に応じて保存済み document を再生成する処理ではない。
- `M:1741` の live semantic hash は `search` を含まない。`M:1755` の reconstruction 再実走も、この構造を比較する。
- gate は `G:599 → G:169` の receipt 検証と、`G:299 → M:2490` の adapter 検証を通る。ここに live file count の追加比較は見つからなかった。

**basis OID は判定に関係する。** `M:1831` は HEAD と指定 basis、`M:2009` は draft 内 basis と HEAD を照合する。`M:1797` は選択された source の bytes/mode を basis blob に束縛する。追加後の basis に対して receipt を新規導出すれば整合するが、古い receipt を流用すれば同値とは限らない。

fixture test の期待値は `T:1765` の `HEAD^` から導出される。`T:3511` の固定 `migration_basis_commit` は実 repo 検査（`T:3450`）であり、この builder の新しい basis を固定値と比較するものではない。

plan:99 の index のみの切替では B は既存 HEAD に対して staged addition となる。scan は測れるが、発行をそのまま実行すると `M:1833` の clean 条件に反する。この probe から主張できるのは、列挙・scan の差と所要、および静的に限定した判定不変までである。

DW-G05 は意味を分ける必要がある。

- **実 repo の既存 certified 選択・レポート・台帳への現在の影響**：反証なし。本 wave が fixture の調査に限定されることが前提。
- **fixture の全レポート／成果物 bytes 不変**：**反証あり**。`H:647` の file count、`M:1967` の basis、`M:2277` の receipt hash・validation HEAD・observation が変わる。
- **将来の検出力の差**：機械的には **real**。この path に conjunction が入れば、tracked の実 repo 側は読むが、現行 fixture 側は ignored untracked として落とす。
- **通常の configure 再生成でその conjunction が生じる現実性**：**判定不能**。`config.h:1` は生成物であることを示すだけで、その混入経路を示さない。生成物なので無関係とも、将来必ず問題になるとも言えない。scanner は C の意味を解釈せず text を読むため、コメント等に入った場合も対象になる。

## 変異事前登録案 (攻撃点 5)

**既存の可視性検査が取り込み削除変異を殺すという仮説は refuted。**

`T:1633` の検査は合成 source の output を対象とし、`T:1688` でコピー helper の返す集合、`T:1694` でコピー先の regular file を検査する。コピー先を新しい Git repo として index 化した後の集合は検査しない。対象も `orchestrator/` ではない。

`T:1735` の e2e は現在の config.h が無くても判定を満たす設計で、`T:1765` の basis 独立導出もこの file の membership を要求しない。調べた経路に、追加取り込みを削除しただけで赤になる既存 assert は見つからなかった。テスト未実行なので、変異の実際の SURVIVED／KILLED は未判定である。

plan:165 の新しい membership assert は、今回の「1件を可視にする」という仕様を直接検査するため妥当である。新規 test に依存することを明示すればよい。

**合成 source は一般解を採用する場合に必要性が高い。** config.h だけを救う退化を検出するには、別名の tracked-and-ignored file を source 側に置く必要がある。fixture 作成後に file を置く既存負例ではコピー／再 index 化の脱落を検査できない（D2068:11）。

hard-code の狭い契約だけを採用するなら、任意 path に対する一般性の負例はその契約を超える。欠落 path の黙殺を禁止する負例は、一般解の採用条件に対応する。

## 親 brief の誤り (攻撃点 6)

| 記述 | 判定 | 根拠・修正 |
|---|---|---|
| P1：419件、418件が root ignore 由来 | **誤りの疑いは refuted** | 読み取り列挙で再確認した。418件は `.gitignore:25`、1件は masstree `.gitignore:8`。ただし全 scan 集合の差が1件という一般化は未証明。 |
| orchestrator の untracked 0 | **real：表現の限定不足** | `--others --exclude-standard` は0。ignored を含む `--others` は9件で、全件 `__pycache__/*.pyc`。現在は `T:1382` の除外対象だが、「全実体が tracked」の根拠にはできない。 |
| P2：判定不変 | **現在 bytes・適切な再発行に限定すれば反証なし** | `H:1049` と `M:1741` は支持する。ただし `M:1831`・`M:2009` の basis 整合性を前提に加える必要がある。 |
| P3：ms級 | **判定不能** | 時間未測定。13 scan の正常経路内訳は `plan:117` とコードに整合するが、一般解は419 path を処理する。10 KBから wall は導けない。 |
| P4：1手、件数非依存の一般解 | **real：過大主張** | コマンド回数と処理量は別。非コピー対象を入力に含みうる（`T:830`・`T:1382`）。D2086:23 の snapshot 契約にも合わせる必要がある。 |
| DW-G05：レポート・台帳は変わらない | **real：対象の限定不足** | 実 repo の既存成果物なら反証なし。fixture の report／receipt／observation を含めるなら `H:647`・`M:2277` が反証。 |
| login node で実測 | **real** | この所要測定は性能測定。提示された AGENTS 規律では計算ノード対象。D2068:27 の交互対比較条件は login node 実行の許可ではない。plan:128 の修正が必要。 |

brief の主要コードアンカー自体は一致していた。ただし「判定不変を静的確認済み」（brief:3）は、発行全経路の実走同値性まで確認したと読めないよう限定すべきである。

## 裁定パッケージ候補 (scope 外)

以下は採用 wave の候補であり、本調査での実装要求ではない。

- **狭い修復案**：config.h の force-add と、実 builder の index／production 列挙／source bytes の検査。
- **一般解案**：構築時 snapshot のコピー契約を入力とし、意図的除外と予期しない欠落を区別する。別名の tracked-and-ignored file とコピー欠落を使う合成負例を付ける。
- **発行同値性の確認案**：採用位置で basis を作り直し、正常な発行・verify・gate を確認する。これは index 切替による scan 所要測定とは別の検証とする。

今回の裁定では「取り込みの操作費」「scan 増分の対比較」「13回換算のモデル値」「未測定の発行 wall」を区別するだけでよい。追加 gate や一般化 helper を本 wave に持ち込む必要はない。

## 総括

**plan は局所的な影響測定として進められる。ただし、射影集合への一致を実 repo 全体への忠実性と同一視せず、判定不変を現在の bytes と正しい basis 再導出に限定すること。**

419／418件と三軸語0件は再確認できた。現在の受理判定が変わる反証は見つからなかった一方、fixture の report・basis・receipt bytes は変わる。既存 test が config.h の取り込み削除を検出する根拠は無い。

ファイル変更、pytest、性能測定は行っていない。時間増分、発行全経路の実走同値性、変異 KILLED は未確認であり、緑とは報告しない。