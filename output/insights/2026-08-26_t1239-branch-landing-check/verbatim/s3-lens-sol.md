## tip の net tree は branch 固有の中間内容を消す

**深刻度**: blocker

**成立条件**: branch が一度導入した内容を、後続 commit で別内容へ置き換え、その最終内容だけが main に存在する。

```bash
git init r && cd r
git config user.name test
git config user.email test@example.invalid

printf 'base\n' > f
git add f && git commit -m base
git branch topic

git switch topic
printf 'unique-secret\n' > f
git commit -am secret
printf 'final\n' > f
git commit -am final

git switch main
printf 'final\n' > f
git commit -am independently-final
```

`merge-base..topic` の net tree は `f=final` だけなので、プランの exact blob 層は `landed` を返す。しかし `unique-secret` の blob とそれを導入した commit は main に存在せず、topic 削除後に到達不能になり得る。net diff が空の場合の無条件 `landed` は、さらに直接この問題を起こす。

**成果物影響**: 判定表で topic が `landed`、削除候補に入り、中間 commit の固有内容が台帳に残らないまま失われる。

**提案**: `git rev-list <branch> --not <main>` で branch 削除により失われる commit closure を列挙し、最終 treeだけでなく各 commitが導入した状態を監査する。少なくとも branch-only commit が存在する net-empty branch は自動で `landed` にせず `indeterminate` とする。JSONにも audited commit数と、各固有状態の証明を表現する。

## merge commit を branch 内容の監査対象にしていない

**深刻度**: blocker

**成立条件**: main にない side commit を topic が mergeし、merge結果ではその内容を捨てる。

```bash
git init r && cd r
git config user.name test
git config user.email test@example.invalid

printf 'base\n' > f
git add f && git commit -m base
base=$(git rev-parse HEAD)

git switch -c side
printf 'side-only\n' > f
git commit -am side-only

git switch -c topic "$base"
git merge --no-ff --no-commit side
printf 'base\n' > f
git add f
git commit -m 'merge side but resolve to base'
git branch -D side
```

topic の net tree は main と同じなので現規則は `landed`。`git cherry` は merge commitを出力せず、side commitだけを1行出す。topic を削除すると merge commitと side commitの双方が最終的に到達不能になる。

実データでも、9本中 `t1484-backup-before-trailer-fix`、`worktree-t1458-side-ccbench-provenance-fix`、unitB/C に branch-only merge commitがある。t1458 は unique commitが2件なのに `git cherry` は1行である。

**成果物影響**: mergeを含む4 branchで、判定表の `patch_id.status=complete` と削除根拠が実際の commit closureより少なくなる。

**提案**: mergeを含む全 branch-only commitを列挙する。main reachable parentがある mergeは、その親との差分で branch固有の解決結果を監査する。該当 parentがない mergeは全 parentとの差分を保守的に監査し、証明できなければ `indeterminate`。`git cherry` の出力件数が branch-only commit数より少ない場合は `complete` と表示せず、merge省略数を明記する。

## receipt 不在を `not-landed` にする規則は実測と矛盾する

**深刻度**: blocker

**成立条件**: fragment が別 waveへ re-homeされた後に foldされた、または canonical worklogが archiveへローテーションされた。

```bash
git switch -c old-wave main
# docs/spool/decisions/...-old-wave-1.md を追加して commit

git switch -c new-wave main
git show old-wave:docs/spool/decisions/...-old-wave-1.md \
  > docs/spool/decisions/...-new-wave-1.md
# filename、frontmatter waveを new-waveへ変更
git add docs/spool
git commit -m rehome
# new-wave版を foldし、receiptとcanonical台帳をcommit
git switch main
git merge new-wave
```

old-wave版の whole-file SHA-256 は receiptにないが、本文は既に着地している。追加実測ではこの型が3本あり、`roadmap-workload-hint` の decisionは D568、worklogは archiveに存在する。

`content_sha256` の厳密一致は「その exact whole-file bytes が fold入力だった」ことを保証する。一方、re-homeで frontmatterが変わった論理 fragmentや元 pathの identityまでは保証しない。プランのJSON厳密 parseは `grep -F` の部分文字列事故を避けられるが、hash不在を負証拠にすることはできない。

現規則を9本へ適用すると、概ね次になる。

- `landed`: 4本
- `not-landed`: 5本
- `indeterminate`: 0本

誤った `not-landed` は roadmap、floor-measurement、unitB/C の4 branchに及ぶ。追加実測を反映した file-level予測は、commit closure監査による追加降格を除けば `landed` 6本、`not-landed` 1本、`indeterminate` 2本である。

**成果物影響**: 既に着地した3 fragmentが未fold一覧へ再投入され、D568やworklogを二重に landする候補になる。

**提案**: receipt不在時は直ちに `not-landed` にせず本文照合へ落とす。receipt metadataから main履歴上の re-home後 fragmentを取得し、spool schemaで検証した上で frontmatterを除く構造化本文を比較する。canonical台帳と `docs/archive/` も探索する。意味変換を完全に復元できない場合は `indeterminate` とし、40文字の特徴行や一部行 hitを `landed` の十分条件にしない。

## whole-file subsequence でも頻出行の誤対応が残る

**深刻度**: blocker

**成立条件**: base部分が main内で複製され、branchの追加行が別の複製へ入っている。

```bash
printf '[prod]\nenabled=false\n' > config.ini
git add config.ini && git commit -m base
git branch topic

git switch topic
printf '[prod]\nallow_delete=true\nenabled=false\n' > config.ini
git commit -am topic-change

git switch main
printf '[prod]\nenabled=false\n[prod]\nallow_delete=true\nenabled=false\n' > config.ini
git commit -am duplicate-section
```

topic tipの全行は main tipの subsequenceであり、順序と重複数も満たす。しかし branchが変更した元の `[prod]` 節には行がなく、別の重複節に偶然存在するだけである。空行、コメント、`}`、重複した設定節では同型が生じる。

**成果物影響**: 実際の hunkが未着地でも fileとbranchが `landed` になり、削除候補へ混入する。

**提案**: 最も安全なのは逐語層を十分条件から外し、exact blobだけを `landed` 証拠にする。残す場合は merge-base行の対応を一意に固定し、各追加runが同じ gapへ連続して存在することを要求する。base alignmentが複数ある場合や contextが頻出する場合は `indeterminate` にする。

## content、mode、type の証拠を別時点から合成できる

**深刻度**: must-fix

**成立条件**: branchが内容とmodeを同時に変更し、mainでは必要なblobとmodeが別々のcommitにしか存在しない。

```bash
printf 'base\n' > tool
chmod 644 tool
git add tool && git commit -m base
git branch topic

git switch topic
printf 'payload\n' > tool
chmod 755 tool
git add tool && git commit -m 'payload executable'

git switch main
printf 'payload\n' > tool
chmod 644 tool
git add tool && git commit -m 'payload non-executable'
printf 'other\n' > tool
chmod 755 tool
git add tool && git commit -m 'other executable'
```

main履歴には `payload` blobとmode `100755` がそれぞれ存在するが、要求状態 `(100755, payload-oid)` は一度も存在しない。表の change分類が排他的に実装されたり、各証拠を独立合成すると偽の `landed` になる。

**成果物影響**: executable、symlink、gitlinkを含む branchが誤って削除候補へ入り、必要なtree entry状態が失われる。

**提案**: 証明単位を常に `(path, mode, object-type, oid/content)` の同時状態にする。内容とmodeが同時変更された場合も全次元を連言し、別commitの証拠を混ぜない。branch削除は次の行列を明文化する。

- branchが `D`、main tipも不在なら `landed`
- branchが `D`、mainに残り、完全履歴にも削除がなければ `not-landed`
- branchが `A/M`、main tipで不在なら、不在自体を `landed` 証拠にしない
- renameは `D+A` の双方を連言
- symlink、gitlink、type変更は同一時点の modeとOIDを要求

## 合成テストが追加実測と commit closure を再現しない

**深刻度**: must-fix

**成立条件**: 現在列挙された5必須ケースだけを実装する。これらは tipの最終blobを中心にしており、次を検出できない。

```bash
# 中間blob消失
git switch topic
printf secret > f && git commit -am secret
printf final > f && git commit -am final

# path取り違え
git switch topic
printf same > wanted && git add wanted && git commit -m wanted
git switch main
printf same > other && git add other && git commit -m other
```

さらに re-home、archive、merge-only commit、net-empty branch、content+mode同時変更、main側削除、branch側削除、FOLDED本文中にhash文字列があるだけのケースが不足している。

**成果物影響**: テストが緑でも、判定表の偽 `landed` と偽 `not-landed` の主要経路が残る。

**提案**: 上記反例を必須 fixtureへ追加する。各負の対照は単に「`landed` ではない」ではなく、期待する `not-landed` または `indeterminate` と reason codeを厳密にassertする。特に以下を独立testにする。

- 同じblobが別pathにあるだけでは一致しない
- receipt hashはJSON fieldの完全一致だけを認める
- merge commit数と `git cherry` 行数の差を記録する
- branch tipが同じでも中間blobがmainにない
- mainがfileを削除した `A/M` と、branchがfileを削除した `D` を区別する
- re-homeとarchive済みは `not-landed` にしない

## `--find-object` の1秒観測は探索上限にならない

**深刻度**: nit

**成立条件**: 対象OIDが存在しない長い履歴を作る。

```bash
for i in $(seq 1 100000); do
  printf '%s\n' "$i" >> unrelated
  git add unrelated
  git commit -q -m "$i"
done
```

`--max-count=N+1` は出力commit数を制限するが、hitがない場合に調べる履歴量は制限しない。選択された3 pathが1秒未満だった観測は、全file、全branch、cold packへ一般化できない。プランの5秒 timeoutは偽 `landed` を防ぐので正しさ上の blockerではない。

**成果物影響**: 実データやcold cacheで `history-timeout` が増え、判定表の `indeterminate` と削除候補減少につながる。

**提案**: timeoutは維持し、履歴走査時間と候補数をJSONへ出す。同じpath/OID照合をcacheし、可能なら複数pathをまとめた一回の履歴走査へ寄せる。「候補上限」と「走査量上限」を別概念として文書化する。

## task index が failures 台帳を検索しない

**深刻度**: nit

**成立条件**: branch名が `worktree-t1239-*` で、`T-1239` の記録が `docs/failures.md` にだけ存在する。

```bash
printf '\n- [T-1239] failure record\n' >> docs/failures.md
git add docs/failures.md
git commit -m 'record T-1239 only in failures'
```

計画の `git grep` は worklog、decisions、archiveだけなので、補助証拠はhitなしになる。

**成果物影響**: verdictは変わらないが、判定表と削除候補一覧の台帳根拠が不完全になる。

**提案**: `docs/failures.md` も検索対象へ加え、hit上限とtruncationを同じschemaで扱う。

## 総括

blocker:

- tipの net treeだけでは branch固有の中間内容を保存できない
- merge commitとその親closureが監査対象になっていない
- receipt不在を `not-landed` とする規則がre-home/archive実測に反する
- whole-file subsequenceでも頻出行や重複contextによる偽 `landed` が作れる

must-fix:

- content、mode、typeを同一tree状態として照合する
- 追加実測、commit closure、merge、path、hash、削除行列を合成testへ追加する

このプランをこのまま実装してはいけない。まず判定対象を「tipのnet変更」から「branch削除で失われるcommit closureの内容」へ改め、spool不一致と逐語照合を `indeterminate` 側へ倒す必要がある。

最も見落とされやすい点は、tip同士が完全一致しても、branch途中の固有blobはmainへ一度も着地していない場合があることだ。net diffが空という事実は、不可逆削除の十分条件ではない。