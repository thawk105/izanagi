# 実装プラン

変更対象は指定された 2 fragment だけとする。D121 の既存 bytes、phase 文書、前 wave の逐語資料、コード、テストは変更しない。

中核となる判別は次の非対称な評価順である。

- P4 は「軸 (iii) に関する事前のユーザー裁定」を先に見る。
- P6 は「契約が実装済みか」を先に見てから、主張の有無を見る。

これにより、軸 (iii) を採らない構成へ batch-freeze を要求せず、P6 の未実装だけを FAIL にできる。

## 親 brief の P1〜P4 に対する裁定

|案|裁定|反映方法|
|---|---|---|
|P1|修正して採用|三分は採用するが、`NOT_TRIGGERED_BY_RULING` は P4 のような「独立裁定で発火条件が否定される義務」だけに限定する。P6 には適用しない。通常の成功・失敗を表す `SATISFIED` / `FAIL` も加える。|
|P2|修正して採用|実装 path + 検査 ID は必要条件とするが、1 組だけの提示では足りない。義務を構成する閉じた実装面の各要素について、対象 revision に束縛した path・検査 ID・検査結果を要求する。|
|P3|そのまま採用|宣言欠落、根拠不足、依存裁定未了、未知状態はすべて `FAIL`。現状は P4=`FAIL`、P6=`NOT_IMPLEMENTED`→FAIL と記録する。|
|P4|修正して採用|抜け道の指摘は採るが、「残存義務だけで還流効果 > 0」を新条件にはしない。代わりに `NOT_TRIGGERED_BY_RULING` を P6 へ適用禁止とする。正の効果を別途必須化すると、U2 が明示的に残した `NOT_CLAIMED` 免責を実質無効化し、P1〜P10 の集合も変更するためである。|

P1〜P4 の原案は [brief.md:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/brief.md:20) 以降にあり、U2 の確定裁定は [docs/worklog.md:1110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:1110) にある。exact-only の限界効果がゼロである事実は [docs/decisions.md:6726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6726) に固定済みである。

## 1. decisions fragment

対象: `docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md`

### 予定レイアウト

- `:1-7`: frontmatter。`ledger: decisions`、`authored: 2026-08-04`、`wave: dev-wave-t244-u2-na-bifurcation`、`seq: 1`。
- `:9`: `## {{D:t244-u2-na-bifurcation}}. ...` の H2 を 1 件だけ置く。題末尾に日付は書かない。
- `:11-15`: 背景、U2 裁定、D138 決定 (5) との関係。
- `:17-40`: 次の決定 (1)〜(8)。
- `:42-50`: 理由と却下案。

### 新 D の決定条項骨格

1. **supersede 範囲を限定する。**  
   D121 決定 (7) の「P4 と P6 は条件付き義務」から「cap が永久に解除不能になる」までの一文だけを、本 D の決定 (2)〜(6) に置き換える。

2. **status 語彙を固定する。**  
   `SATISFIED`、`NOT_TRIGGERED_BY_RULING`、`NOT_CLAIMED`、`NOT_IMPLEMENTED`、`FAIL` の 5 値とし、前 3 値だけを cap-lift の失敗に数えない。

3. **判定者・時点・入力を固定する。**  
   cap-lift を承認する人間が、承認上限を 1 より大きくする前に、対象 revision、先行裁定参照、主張宣言、実装 witness、契約充足証拠から status を決める。

4. **自己申告だけでは免責しない。**  
   申請側の宣言は claim intent の入力にすぎず、status 自体は申請側に選ばせない。宣言欠落、証拠面の非閉包、宣言と proof/cut の矛盾は `FAIL` とする。

5. **P4 の評価順を固定する。**  
   軸 (iii) を採らないという事前のユーザー裁定があれば `NOT_TRIGGERED_BY_RULING` とし、batch-freeze 実装を要求しない。未裁定なら `FAIL`、採用裁定後の未実装は `NOT_IMPLEMENTED` とする。

6. **P6 の評価順を固定する。**  
   claim intent より先に実装 witness を評価し、不在なら常に `NOT_IMPLEMENTED`。実装済みかつ generalized cut を主張しない場合だけ `NOT_CLAIMED`、主張する場合は D138 契約を満たして初めて `SATISFIED` とする。

7. **現況を記録する。**  
   P6 は実装ゼロなので `NOT_IMPLEMENTED`、P4 は軸 (iii) が未裁定なので `FAIL`。いずれも現時点の cap-lift を許さない。

8. **変更しない境界を固定する。**  
   P1〜P10 の列挙、無条件義務集合、P8 の射程、D121 の他決定、D138 の P6 契約、承認上限 1 を変更せず、機械 gate や status field も新設しない。

D121 の置換対象は [docs/decisions.md:5851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5851) に限る。P1〜P10 の列挙は [docs/decisions.md:5842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5842)、P8 と無条件義務は [docs/decisions.md:5853](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5853) にあり、そのまま残す。

実際の D 本文では腐敗する行番号参照を使わず、上記一文の冒頭と末尾を引用アンカーとして supersede 範囲を示す。

### 判定規則

|義務|評価順|status と cap-lift 上の扱い|
|---|---|---|
|P4|先行する P10 の軸 (iii) 裁定を確認|不採用裁定=`NOT_TRIGGERED_BY_RULING`（免責）。未裁定・曖昧=`FAIL`。採用済みだが batch-freeze witness 不在=`NOT_IMPLEMENTED`（FAIL）。採用済みかつ契約充足=`SATISFIED`。|
|P6|実装 witness を最初に確認|不在・不足=`NOT_IMPLEMENTED`（FAIL）。実装済みかつ非主張=`NOT_CLAIMED`（免責）。実装済みかつ主張ありで D138 契約充足=`SATISFIED`。それ以外=`FAIL`。|

P4 の判別子は `trigger_basis = prior_user_ruling(axis_iii)`、P6 は `trigger_basis = claim_intent_after_implementation` とする。P4 の条件は D121 が軸 (iii) の採否へ明示的に結び付けている一方、P6 は「no-good cut を超える主張」の有無へ結び付けているためである。[docs/decisions.md:5794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5794) [docs/decisions.md:5846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5846)

実装 witness は次を要求する。

- P4: batch cardinality、全候補の事前 commit、batch seal までの結果非公開を覆う実装 path・検査 ID。[docs/decisions.md:5799](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5799)
- P6: handler、全 witness-kind adapter、正負 calibration、未知 kind の fail-closed を漏れなく覆う実装 path・検査 ID。[docs/decisions.md:6760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6760)
- P6 の意味的妥当性は D138 決定 (3) の明示的帰納契約へ委譲する。[docs/decisions.md:6744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6744)

cap-lift 申請 artifact や入力 field は現存しないため、上記は人間 gate の語彙であって機械 schema ではない。[brief.md:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/brief.md:33)

## 2. worklog fragment

対象: `docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md`

### 予定レイアウト

- `:1-8`: worklog 用 frontmatter。`title` を含め、`seq: 2` とする。
- `:10-16`: `## 本文`。U2 を `{{D:t244-u2-na-bifurcation}}` で確定したこと、docs-only、上限・実装・成果物が不変であることを記録する。
- `:18-25`: `## 次の一手差分` → `### 更新` のみを置く。
- `[T-244]` は完了にせず、U2 の「新 D で書く」を「新 D で確定済み」へ置換する。U1・U3・U4・U5と「本体未解決」は全文保持する。

現在の `[T-244]` item は [docs/worklog.md:1156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:1156) から始まる。現時点の base digest は次である。

```text
561133878fa793e7a5793ca544af03b85be0dcd49fe8b047c9f70159b917c9cf
```

fragment には `  base: 5611...c9cf` を付ける。ただし並行 fold で現本文が変わり得るため、作成直前に再計算し、不一致なら新しい本文から更新案を作り直す。`完了` にしない根拠は、P6 実装がゼロで T-244 本体が未解決だからである。[README.md:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-03_t244-p6-contract/README.md:474) [README.md:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-03_t244-p6-contract/README.md:496)

## supersede 後の参照関係

新 D には次を明記する。

- D121 決定 (7) の対象一文だけを supersede する。
- D121 決定 (1)〜(6)、P1〜P10 の内容、P8 の射程、無条件義務集合は残す。
- D138 決定 (5) を覆さず、U2 裁定によって確定した一般規則として採用する。D138 はすでに `NOT_IMPLEMENTED` と `NOT_CLAIMED` を定式化している。[docs/decisions.md:6760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6760)
- `MAX_APPROVED_GENERATIONS = 1`、cap-lift 非結線、実装ゼロを維持する。[docs/decisions.md:6774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6774)

「D121 全体を supersede」「D138 を supersede」とは書かない。

## 他文書への波及

更新が必要な追加ファイルは 0 件と判定する。

|対象|grep・読取結果|扱い|
|---|---|---|
|`docs/phase3.md`|D121 の設計、軸 (iii) 未裁定、前提未充足を要約するだけで、旧 NA 免責を再掲していない。[docs/phase3.md:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3.md:471)|変更なし。|
|`docs/phase3-8c-preregistration.md`|2 世代以上には T-244 裁定、D114 改訂、再事前登録が必要とするだけで、P4/P6 の免責規則を持たない。[docs/phase3-8c-preregistration.md:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-8c-preregistration.md:69)|変更なし。|
|`docs/phase3-main-experiment.md`|D39 の on/off ablation を固定している。[docs/phase3-main-experiment.md:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-main-experiment.md:40)|D121 自身も不変更を要求しているため報告のみ。[docs/decisions.md:5856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5856)|
|前 wave `README.md`|§3.11.2 はすでに `NOT_IMPLEMENTED`=FAIL、`NOT_CLAIMED`=免責を記述している。[README.md:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-03_t244-p6-contract/README.md:400)|変更なし。裁定待ちと書いた箇所も当時の凍結スナップショットである。[README.md:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-03_t244-p6-contract/README.md:6)|
|`s2-plan.md`|旧 `P6=NA` 規則を持つ。[s2-plan.md:361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-03_t244-p6-contract/s2-plan.md:361)|段 2 逐語であり、後続の敵対所見・裁定により棄却された履歴なので変更しない。|
|`s4-adjudication.md`|U2 を裁定パッケージとして提示している。[s4-adjudication.md:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-03_t244-p6-contract/s4-adjudication.md:117)|当時の裁定記録なので変更しない。新 D が採用記録を担う。|

## `check_docs.py` を通す条件

`check_docs.py` は `tools/spool_fold.py` の `validate_spool_tree()` を直接ロードし、失敗を finding 化する。[tools/check_docs.py:616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/check_docs.py:616) [tools/check_docs.py:647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/check_docs.py:647)

必要条件は次のとおり。

- UTF-8、LF、BOM なし、末尾 newline あり、regular file。[tools/spool_fold.py:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/spool_fold.py:260)
- frontmatter は `key: value` のみ、重複・空値・未知 key なし。[tools/spool_fold.py:286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/spool_fold.py:286)
- decision は `schema/ledger/authored/wave/seq`、worklog はそれに `title` を加えた完全一致集合。[tools/spool_fold.py:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/spool_fold.py:763)
- filename は frontmatter からの再構成と byte 一致。[tools/spool_fold.py:792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/spool_fold.py:792)
- decision の全 H2 は `## {{D:slug}}. title`。slug は小文字 kebab-case、題末尾の日付は禁止。[tools/spool_fold.py:658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/spool_fold.py:658)
- placeholder は同一 wave 内で定義済み、重複なし、未定義・壊れた `{{...}}` なし。[tools/spool_fold.py:912](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/spool_fold.py:912)
- worklog の H2 は `本文`、`次の一手差分` のちょうど 2 件。action H3 は規定順で、今回使うのは `更新` だけ。[tools/spool_fold.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/spool_fold.py:503)
- `更新` item には 64 桁 SHA の `base:` が 1 件必要。[tools/spool_fold.py:453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/spool_fold.py:453) 実本文との一致は fold 時に検査される。[tools/spool_fold.py:1334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/spool_fold.py:1334)
- 新 D は実番号を書かず `{{D:t244-u2-na-bifurcation}}` とする。fold が canonical 最大 D + 1 を割り当てる。[tools/spool_fold.py:1771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/spool_fold.py:1771)
- 実番号で参照するのは存在確認済みの D114、D121、D138だけとする。[docs/decisions.md:5319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5319) [docs/decisions.md:5781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5781) [docs/decisions.md:6718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6718)

注意点として、実在しない D 参照の lint は living docs が対象で、decisions/worklog/insights は明示的に対象外である。[tools/check_docs.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/check_docs.py:29) [tools/check_docs.py:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/check_docs.py:557) したがって fragment に架空の `D139` 等を書かないことは、pre-fold の checker 任せにせず手動で守る。

実装後は `python3 tools/check_docs.py` を実行する。結果を worklog に書く場合は、その追記後に再実行する。pytest は本 worker の検査対象外であり、緑とは記録しない。

## 却下すべき案

1. **単一の `NA` に戻す。**  
   未実装と実装済み非主張を区別できず、P6 を 1 行も実装しないまま cap-lift を通す恒真化が再発する。

2. **`NOT_CLAIMED` を宣言だけで認める。**  
   申請者が status を自己選択できるため恒真である。P6 実装 witness の独立確認を必ず先に置く。

3. **P4/P6 を一律の無条件実装義務にする。**  
   軸 (iii) を採らない裁定後も batch-freeze を要求し、D121 が避けた永久解除不能を再導入する。

4. **「座標 cut を採らない」という裁定を P6 の `NOT_TRIGGERED_BY_RULING` に使う。**  
   P6 未実装を裁定文だけで免責する別名の抜け道になる。P6 は実装判定を常に先行させる。

5. **この wave で「還流の実効性 > 0」を追加前提にする。**  
   証拠 field が存在せず自己申告か永久 FAIL のどちらかになり、P1〜P10 を変えない scopeと、`NOT_CLAIMED` を免責する U2 の両方を越える。必要なら別裁定として扱う。

6. **D121 本文を in-place 編集する。**  
   fragment/fold の追記契約に反する。新 D で置換対象を文言アンカー付きで明示する。

## 総括

新 D は、P4 を「先行する軸 (iii) 裁定」で、P6 を「実装 witness を先に確認してから claim intent」で判定する。この非対称な判別により、P4 の不要な batch-freeze 強制を避けながら、P6 の未実装免責だけを確実に FAIL にできる。

確信を持てなかった点は、「還流の限界効果 > 0」を cap-lift の別条件にすべきかである。D138 の中心定理と U3 はその必要性を示唆する一方、U2 は実装済み非主張を明示的に免責しており、本 wave の scope は P1〜P10 を変えない。このため本プランでは追加せず、必要なら別のユーザー裁定へ返す。なお静的なソース確認だけを行い、`check_docs.py` や pytest の成功は主張していない。