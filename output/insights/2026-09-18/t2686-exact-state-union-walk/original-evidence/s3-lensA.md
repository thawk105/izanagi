## 判定表

`real` は主張を支持、`refuted` は反例・誤った推論あり、`判定不能` は一般成立を確認できない、の意味で使う。確認環境は Git 2.34.1。書込み・pytest 実走は行っていない。

**現案の候補列同一性は refuted。通常の rename だけで移動元の候補が落ちる実例を確認した。**

| id | 判定 | 根拠 |
|---|---|---|
| 1 包含規則 | **real（指定条件内）** | ローカル `git help log` の「`--full-history without parent rewriting`」は、両親に TREESAME な M を除外し、片親にだけ TREESAME な P・Q を含める。実例 `4a614a49` の `docs/archive/README.md` は第1親との差あり・第2親との差なしで、`git log --full-history --max-count=1 --format=%H 4a614a49 -- docs/archive/README.md` は merge 自身を返した。`--sparse` を追加すると全親同一の commit も対象になるため、この規則の適用外。 |
| 2 separate と走査 | **real（commit の重複を除いた列）** | `git help log` は親ごとの diff 表示指定と定義している。上記 merge は追加前後とも先頭に現れた。ただし「walk が同じ」から「name による派生列が同じ」は導けない。後述の rename が反例。 |
| 3 pathspec と順序 | **判定不能（一般保証）** | 全親を辿る説明と33件の一致は支持材料だが、同時刻・時刻逆転を含む DAG の順序不変を証明していない。また現行 `Git.run` は repo-local config を無効化しない（対象コード:218）。`git help log` の `log.follow` は単一 path のときだけ follow を有効にすると明記しており、これが true なら単一／複数 path の探索条件自体が異なる。今回の follow 確認 command は40秒で timeout したため、実測成立とは報告しない。 |
| 4 有界走査と再走査 | **real（走査の打切り判定）／refuted（同一性・時間保証への拡張）** | 正常終了し、出力 commit を漏れなく数え、同一 walk を使うなら、`n<K` は対象 commit の列を取り切ったことを示す。`n==K` でも全 path の必要 prefix が揃えば追加走査は不要。ただし名前派生が正しいことが前提で、現案は rename で破る。A1:11 の時間保証も不成立。 |
| 5 prefix 規則 | **refuted（任意の literal pathspec という主張）** | `GIT_LITERAL_PATHSPECS=1 git log --full-history --format=%H --max-count=1 HEAD -- tools/` と `-- tools` はともに `5ac36d66…`、`-- .` は `1809e666…` を返した。提示 predicate は `tools/` に対して `tools//`、`.` に対して `./` を要求するため一致しない。対象が Git tree 由来の正規化済み path だけなら、この反例は入力域外と明記できる。`-- TOOLS` は空で、大文字小文字の自動同一視は観測されなかった。 |
| 6 framing | **real（非空 name entry の byte 境界）** | 実出力は `NUL H NUL LF name NUL NUL H …`。合法名は NUL を含まず空でもないため、名前による header 偽装はできない。LF は**区切りとして1 byteだけ**取り除けば先頭LFを保存できる。ただし合法 Git 名には非UTF-8もあるので、A2 の strict UTF-8 parser は「任意の合法名を受理」するものではない。末尾 split に生じる空 field は EOF と区別する必要がある。 |
| 7 root | **real** | root `6ad3d7aa…` の `.claude/agents/calibrator.md` で確認。旧 command は `log.showRoot=true/false` の両方で root OID を返した。name-only 出力は true で名前あり、false では `NUL H NUL` のみ。名前出力のための強制は必要で妥当。 |
| 8 候補上限 | **refuted（現案全体）** | 同一無制限列を得られれば `[:limit+1]` は旧上限と一致する。しかし rename で列が変わるため現案では保証できない。対象コード:784、798、802 の「limit+1 件も正証拠照合し、その後 `>limit`」という順序は保持すべきで、これは D2123 と整合する。 |
| 9 親の一般化 | **refuted** | `measure-verify-union-559.json` は33 path の一致を示すだけで一般証明ではない。今回、その集合外の実在 rename で不一致を確認した。別12 path の検証結果は射影資料にないため独立確認できない。probe:25、33 は RS split と LF strip を使い、A2 parser の証拠にもならない。 |
| 10 D2106 との整合 | **refuted（現案を候補列同一として通すこと）** | brief:30 の根拠「候補列が完全一致」が実例で崩れる。実 tree 再確認を残すことで正証拠の受理述語は保てても、候補・candidate_count・matched_commit・上限判定の同一性は別問題。修正・再検証なしには D2106 の却下項に当たらないと言えない。 |

## 反例と要追加 test

### 1. rename による移動元候補の欠落 — 実測済み、必須修正

実在 commit:

```text
C = 8e0aadc14ab1229374ef11d64705c07b708ed29a
A = output/insights/2026-09-16/t2671-layer3-screening/s6-adjudication.md
B = output/insights/2026-09-16/layer3-screening-currency/s6-adjudication.md
```

`GIT_LITERAL_PATHSPECS=1`、global/system config 無効の環境で確認した。

```bash
git log --full-history --max-count=1 --format=%H "$C" -- "$A"

git -c log.showRoot=true log --full-history --max-count=1 \
  --diff-merges=separate --name-only -z --format=%x00%H \
  "$C" -- "$A" "$B"
```

観測:

- 旧 per-path は **C を返す**。
- union は **C の header と B の名前だけ**を返す。
- したがって提示 predicate は A の候補から C を落とす。
- union に `--no-renames` を追加すると **A・B 両方の名前が出る**。

合成 repo は `root: a=X → rename a→b → a=Y を再追加` でよい。`P={a,b}` とし、候補列だけでなく `a` の missing state の探索結果も旧版と比較する。完全一致 rename と内容変更付き rename の両方を入れる。

**提案:** union の差分抽出に `--no-renames` を明示し、その削除を変異 test に追加する。

### 2. 順序・merge

plan:124–131 に次を追加する。

- 親子の committer timestamp 逆転、両枝の同一 timestamp、親順を入れ替えた merge。
- 全親同一 merge、片親だけ同一 merge、全親と異なる evil merge。
- 3親以上の octopus merge。
- path 内の削除だけを行う merge。
- 各構成で旧単独列と union 派生列を**順序付き list**で比較する。
- repo-local `log.follow=true` の rename 履歴。旧挙動を保つ必要があるなら、この設定では旧 per-path fallback を検討する。新版だけ false に固定すると旧版との同一性を変更する。

### 3. A1 の境界

小さい limit で次を独立に検査する。

- `n<K`、`n==K` かつ全 path 飽和、`n==K` かつ未飽和。
- 実際の履歴末尾がちょうど K 件で未飽和。
- 同一 merge の複数親 entry を1 commitとして数えること。
- 更新頻度の高い path と候補ゼロの path の併存。後者によって無制限再走査になる場合。
- 再走査結果で置換し、最初の走査との連結・重複計上をしないこと。

`n==K` かつ全 path 飽和は「全履歴完走」ではなく「必要候補 prefix 取得済み」と記録すべきである。

### 4. path・framing・上限

- `f → f/child → gitlink f → f/child` の遷移。gitlink 内部へ履歴探索しないこと。
- `dir`、`dir/`、`.` の入力域を明文化。正規化済み tree path だけなら、その由来を確認する。
- 名前が LF のみ、先頭／末尾LF、RS、40桁hex、TAB、CR。`core.quotePath=true/false` 両方で byte 列を比較する。
- 正常な複数 entry、merge entry、最終NULによる EOF 空 field。
- prefix 配下の非UTF-8名。旧OID列の取得成功と新parser失敗を区別して記録する。
- 正証拠がちょうど `limit+1` 番目にある場合と、そこまで正証拠がない場合。前者 matched、後者 truncated を確認する。

これらは必要な回帰 test であり、任意の DAG・config に対する一般証明の代替ではない。

## 親 brief / addendum の誤り

1. **brief:18、30–31 の「親別 name の和集合＝候補列」は rename detection を落としている。**
   親との tree 差があっても `--name-only` が移動元名を出すとは限らない。今回の実例は通常 commit で成立する。

2. **A1:11 の「時間内に集め切れる入力集合を縮めない」は導けない。**
   仮に `新版合計 ≤ 旧版合計 + 有界走査1本` が成立しても、追加分で deadline を超え得る。また複数 command を45秒以内で処理できることは、束ねた1 command が45秒以内になることを保証しない。A5 の限定された主張と区別する必要がある。

3. **literal 指定は pathspec の正規化を無効にしない。**
   brief:18 の predicate は、正規化済み tree path という入力制約付きで述べる必要がある。

4. **既存 probe は新設計を検証していない。**
   probe:19–20 は無制限・RS形式、25・33 は特殊名を壊し得る parser である。33件一致を A1/A2 の検証結果として扱えない。

5. **plan の test 表は addendum に追随していない。**
   「常に1本」「stdin混在」を、A1 の0/1/2本・A3 の旧経路 fallback に更新し、rename と config 差の検査を追加する必要がある。

## 総括

現案の候補列同一性は、実在 rename commit によって否定された。
union に `--no-renames` を追加することが最優先の修正候補。
root 強制と NUL framing の基本構造は妥当。
順序の一般保証、repo-local config、A1 の時間保証は別途解決が必要。
現状のまま「受理集合に触れない」として author 段へ渡すことは支持しない。
