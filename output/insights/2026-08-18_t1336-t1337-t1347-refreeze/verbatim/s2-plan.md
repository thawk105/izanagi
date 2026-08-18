## 総括

必読 8 資料はすべて読めた。行番号は現在の clean worktree で実測した。

結論は次のとおり。

- P1 は採用できる。8b §8 は「旧 freeze・変更理由・ユーザー承認記録」を要求しており、旧本文を残して新規 §10 から明示的に上書きする形が最も素直に満たす。
- 3 裁定は 8b §10、8c の規範改訂、g6 の 1 世代にまとめる。ただし g6 が発効させるのは条件契約の新世代であり、正式系列全体は前提条件未実装のため引き続き `NOT_EFFECTIVE` である。
- `DECIDER_VERSION` は本 wave では上げず `s8c-decider/v2` のままとする。コード・評価器・射影を変えないためである。後続実装で C04 / C07 等の意味を追随させる際は版上げと新世代 record が必要になる。
- 親 brief の生成 command は誤っている。実装上の subcommand は `prepare-revision` である。
- 親 brief の「構成対ごとに差分 summary」は広すぎる。現実装が直接出す差分 vector は「各非既定構成対既定構成」であり、全構成対にあるのは `joint_covariance` / `joint_correlation` である。off が既定構成固定なので今回の on/off 判定には使えるが、任意対へ一般化するなら後続実装が要る。

## 1. 編集アンカー表

8b は P1 に従い、既存行を直接書き換えない。表中の既存箇所は、新 §10 が明示的に supersede する意味アンカーである。8b の実 byte 追加位置は現行 422 行目の直後だけとなる。

| file:line | 現行の文 | 改訂後の趣旨 |
|---|---|---|
| `docs/phase3-8b-descriptor-design.md:184-190` | 「選択は次の二層を混同しない」「採点 oracle」「対象別 between-run floor の算出基盤」 | 旧二層は履歴として残す。新 §10 では「生値から決まる順位・性能」と「予測との突合せによる選択評価」を新しい二層として定義し、公式性能主張を前者だけに置く。 |
| `docs/phase3-8b-descriptor-design.md:199-208` | 「### 5.2 gate・floor・予算」「対象別 between-run floor」「floor 未確定・欠測・hash 不一致は判定不能」 | correctness gate と build 分離は不変。最終判定から床値を外し、反復単位対比の規則と、後日記入する数値パラメータへ置換する。 |
| `docs/phase3-8b-descriptor-design.md:220-240` | `|oracle floor 超|...差が当該対象別 between-run floor を超える...|`、および「floor 再実測後に確定」 | 条件 3 と結論行を新 §10 で置換する。対比の平均と差分標本 SD、完全 block、三値判定を規範化し、床値再実測を解除条件から外す。 |
| `docs/phase3-8b-descriptor-design.md:255-267` | 「発効後に…変更する場合は、旧 freeze と変更理由を残し、再凍結 + ユーザー承認を要する」 | この本文は改変しない。新 §10 冒頭に変更理由、上書き対象、2026-08-18 ユーザー承認を記録して手続きを満たす。 |
| `docs/phase3-8b-descriptor-design.md:269-286` | 「項 8 は択 (a) = crash 後の再走なし」「途中 crash は当該実験全体を判定不能」 | 新 §10 が 2026-08-18 再裁定を明記し、事前割当 attempt registry を優先する。 |
| `docs/phase3-8b-descriptor-design.md:315-323` | 「oracle 集約規則 = … median of medians」「実走後の途中再開は拒否」「floor・budget・n…を…充填」 | median of medians は順位の記述事実として維持するが、公式性能主張にはしない。項 8 と床値充填部分を上書きし、数値保留対象を対比パラメータへ変える。 |
| `docs/phase3-8b-descriptor-design.md:422-422` | 現在の末尾「実行責任者・開始時刻 (floor 実走時)」 | 直後、現行換算 423 行目から新規 `## 10. 再凍結 2026-08-18` を追加する。 |
| `docs/phase3-8c-preregistration.md:80-87` | 「判定基準の表｜8b §6」「crash 時の扱い｜8b §9 項 8…再走なし」 | 判定行を「8b §6 を §10 が上書き」、crash 行を「8b §10 の事前割当 registry」に更新する。 |
| `docs/phase3-8c-preregistration.md:91-102` | generation 予算の直後に「世代間で運んでよいものの閉じた集合」 | 両者の間へ T-1347 の role payload 規範を 1 項追加する。真の作業種別名は全 arm の closed key set から除外し、特に off では値・識別子・path からも復元不能とする。 |
| `docs/phase3-8c-preregistration.md:110-115` | 「欠測 cell を補完・再走・除外しない」「対象別 floor が未再測定」「検定を加える改訂には floor の再実測」 | 再走全拒否を、事前割当 slot に限定した失敗構成だけの再測定へ変更する。床値依存を除去し、対比規則・数値・事前承認を再開条件にする。 |
| `docs/phase3-8c-preregistration.md:130-138` | 「規範にする文言は本節に置く」「説明文・条件…を値セルへ書いてはならない」 | 本文は維持し、今回の解除条件をすべてここへ置く。§5 へ規範文を移さない。 |
| `docs/phase3-8c-preregistration.md:142-147` | 「env_tag…同じ環境で対象別 floor を再実測した後」「対象別 between-run floor…」「検定 4 点…」 | env_tag は実行 site・環境契約・schedule が固定された時点で記入する。床値項を対比パラメータの解除条件へ置換し、検定再開条件から床値再実測を外す。 |
| `docs/phase3-8c-preregistration.md:157-159` | 「6 cell manifest…arm binding と registry…配線が揃うまで記入しない」 | 条件 4 の freeze-wide attempt registry と、その slot 消費・差替え拒否 consumer も解除条件へ加える。 |
| `docs/phase3-8c-preregistration.md:164-174` | 「対象別 between-run floor (H1 / H2)｜未記入」、検定 JSON 内の `reopen_requires` / `reporting` | 欄名を「反復単位対比の判定パラメータ」に置換する。検定 JSON から規範的な解除条件・説明を除き、no-test の値だけを残す。 |
| `docs/phase3-8c-preregistration.md:189-197` | 条件 4「実験全体を判定不能、再走なし」、条件 7「対象別 between-run floor…floor consumer」 | 条件 4 を事前割当 attempt registry、条件 7 を完全 block・対比 summary・二層結果表を消費する judge へ置換する。 |
| `docs/phase3-8c-preregistration.md:261-275` | 「6 評価器…充足を返す経路は 1 本も無い」「負の対照が初めて拒否能力を持つ」 | C04 / C07 の既存証拠契約・評価器が旧意味のままで、新規規範の充足証拠にはならないことを追記する。NOT_EFFECTIVE を維持する。 |
| `docs/phase3-8c-preregistration.md:402-416` | 起動形の「対象別 floor、判定…すべての consumer」 | 床値 consumer を反復単位対比・分散・二層結果表 consumer に置換する。 |

## 2. 8b の再凍結の書き方

§8 を満たす条件は、新 §10 に次を明記することである。

1. 変更理由: 過去の凍結値との比較を廃し、同じ campaign 内の対測定へ移す。
2. 旧 freeze の所在: §5.2、§6、§9 は履歴として残す。
3. 上書き範囲: §5.2 の床値 bullet、§6 条件 3・結論・数値保留理由、§9 項 8 と数値充填列挙。
4. 優先順位: 矛盾時は 2026-08-18 承認済みの §10 が勝つ。
5. 承認記録: T-1336 / T-1337 のユーザー裁定日と D496 を記す。

したがって P1 は妥当である。§6 表だけを直接書き換える案は、旧 freeze を文書内に残さず、§8 の要求を満たしたかが git 履歴依存になるため採らない。

新 §10 の置換行は次の内容にする。

| 条件 | 成立 | 不成立 | 判定不能 |
|---|---|---|---|
| 反復単位の生値対比と分散 | holdout ごとに、on の予測構成と off の固定構成を同じ replicate で対にし、correctness gate を通った trace-disabled の `outer_median` から `absolute_difference.raw` を作る。事前記入済みの `delta_min` / `sd_max` に対し、`mean > delta_min` かつ `sample_sd <= sd_max` が成立する | 完全 block、2 反復以上、数値パラメータ確定、gate 通過という判定可能条件が揃い、同一構成の選択、`mean <= delta_min`、または `sample_sd > sd_max` のいずれかである | selector 出力不正、gate 不通過、欠測・重複・不連続 replicate、不完全 block、2 反復未満、非有限値、数値パラメータ未記入または hash 不一致。unpaired 推定へ fallback しない |
| 選択評価の結論 | on/off 予測差、swapped 追従、上記の生値対比が成立し、「予測選択が生値順位と整合した」と報告できる | 完全なデータがあり、いずれかが不成立 | いずれかが判定不能 |

`delta_min` と `sd_max` の値は本 wave では書かない。

二層化は新 §10 内で次のように分ける。

- 生値層: 構成ごとの `raw_outer_trials` と median of medians による順位を全件報告する。公式性能主張は、対になった生値の差とその標本分散だけから出す。
- 選択層: on/off 予測差、swapped 追従、予測構成と生値順位の整合を扱う。「選択が当たった」という主張であり、これ自体を性能向上の証明と呼ばない。
- 同順位、欠測、gate 不通過も生値表から落とさない。順位の事実は、複合結論が判定不能でも報告する。

## 3. 反復単位の対比と分散

### 対の作り方

`orchestrator/campaign/s8b_oracle_manifest.py:221-270` の schedule row は `schedule_index` と `replicate_index` を持つ。`s8b_oracle_n_pilot.py:870-894` は前者を observation の `seq`、後者を `pilot_round = replicate_index + 1` へ写す。

したがって、

- `schedule_index` で manifest row と observation の同一性・順序を照合する。
- 対そのものは同一 `holdout_id`・同一 `replicate_index` の 2 構成で作る。
- schedule 上で隣接した行を対と見なしてはならない。
- 各 replicate が全 `(holdout, configuration)` を 1 度ずつ持つ完全 block でなければならない。
- 欠測、重複、1 始まり連続でない round、cell 間の round 集合不一致は判定不能とし、行削除や unpaired fallback をしない。

これは manifest validator の `orchestrator/campaign/s8b_oracle_manifest.py:309-347` と `_observation_matrix` の `orchestrator/campaign/s8b_oracle_n_pilot.py:1152-1172` に一致する。

### 推定量

holdout `h`、構成 `a` と `b`、replicate `r` の `outer_median` を `x[a,r]`、`x[b,r]` とする。

- 絶対差: `d[r] = x[a,r] - x[b,r]`
- 相対差: `q[r] = (x[a,r] - x[b,r]) / x[b,r]`
- `_difference_summary` は各 vector について `mean`、`median`、`sample_sd`、`dispersion_ratio` を返す。
- 差の標本分散は `sample_sd ** 2` で、分母は `n-1`。
- 絶対差については `Var(a-b) = Var(a) + Var(b) - 2 Cov(a,b)` であり、`_sample_covariance` は同じ `n-1` 標本共分散を返す。
- `_sample_correlation` は共分散を両構成の標本 SD で規格化する。2 反復未満または一方がゼロ分散なら null 理由を返す。

判定の主量は絶対差の `mean` と `sample_sd` とする。`median`、相対差、`dispersion_ratio`、共分散、相関は必ず併記するが、後から主量へ昇格させない。

現実装で直接 `absolute_difference` / `relative_difference` が出るのは各非既定構成対既定構成だけである。off は既定構成固定なので今回の対比に合う。on も同じ既定構成を選んだ場合は、ゼロ差として「不成立」であり、判定不能ではない。

### 走行内変動係数を閾値にしない担保

判定表に次を明記する。

> 単独構成の `summary.cv`、session 内反復の変動係数、および 2 構成それぞれの SD の単純加算は、条件 3 の成立・不成立を決める入力にしない。条件 3 が消費する分散は、同一 replicate の差 vector から得た `sample_sd` とその二乗だけである。

既存の走行内異常検出は fail-closed の測定衛生として残せるが、性能差の成立根拠には使わない。`dispersion_ratio` は平均差が 0 なら null、0 に近ければ不安定になるため、判定閾値にはしない。

### 数値欄と解除条件

8c §5 の欄名を次へ置換する。

> 反復単位対比の判定パラメータ (H1 / H2: n・平均絶対差の下限・差分標本 SD の上限)

本 wave では値を `未記入` のまま残す。凍結するのは、対の作り方、主量、三値判定、比較演算子、fallback 禁止である。

値を埋める解除条件は §4 に置き、次の全件成立とする。

- schedule generator、manifest、replicate binding が固定済み。
- formal 結果とは別の事前計画用 paired pilot が完全 block として成立。
- 対比・共分散・結果表を実際に消費する judge が実装済み。
- `n`、`delta_min`、`sd_max` を結果閲覧前に決定。
- 8b §8 の再凍結とユーザー承認を完了。
- 正式実走前の 8c commit に §5 値と schedule hash を同時に記録。

## 4. 8c 側の波及

- §3 の判定行は `8b §6（§10 による 2026-08-18 上書きを含む）` を正本とする。
- §3 の crash 行は、再走全拒否ではなく 8b §10 の attempt registry を指す。
- T-1347 の規範は §4 の generation 予算 bullet と「世代間で運んでよいもの」の間へ置く。後者は世代間還流の契約であり、T-1347 は各 role invocation の入力面契約なので、同じ bullet に混ぜない。
- §4 の標本設計は「再走しない」を削り、失敗構成の事前割当 slot だけを使える形にする。正常な観測値は保持し、成功済み構成を巻き込まない。
- §4 記入規約の env_tag は床値測定から切り離す。実行 site、環境契約、schedule、実行責任者が確定した時点で埋める。
- §5 の旧床値欄を対比パラメータ欄へ置換する。
- §5 の検定 JSON から `reopen_requires` と `reporting` を除く。解除条件と報告義務は §4 に残す。
- §7 の受入順序も床値 consumer から対比・分散 judge へ更新する。

条件 4 の文言案は次である。

> freeze 全体の全 `(holdout, configuration, replicate, attempt)` slot を最初の観測前に閉じた集合として割り当て、追記専用 registry へ束縛する。失敗した構成の同じ replicate についてのみ次の事前割当 slot を消費できる。slot の後出し追加、成績を見た後の再走選択、正常な観測値の差替え、成功済み構成の再測定を拒否する。割当枯渇は該当対比を判定不能にする。

条件 7 の文言案は次である。

> §5 の反復単位対比パラメータが記入され、manifest の `schedule_index` / `replicate_index` と observations の対応から完全 block を復元できる。consumer は `absolute_difference` / `relative_difference`、`_difference_summary`、`joint_covariance` / `joint_correlation` を計算し、順位事実表・公式性能表・選択評価表を分離して全 6 cell を出力する。床値 artifact は本条件の入力にしない。

## 5. 凍結 record

### `prepare_revision` の前提

コード実測は次のとおり。

- `SOURCE_PATH` は `docs/phase3-8c-preregistration.md`。
- 過去世代は HEAD から読むが、新しい markdown と evidence contract は worktree bytes から読む。
- `ruling_reference` は `D[1-9][0-9]*\Z`。D496 は適合する。
- introduction commit の `docs/decisions.md` に `^## D496\.` が実在し、fence や comment 内でないことも検査される。
- g1〜g5 は連番かつ不変でなければならない。現 g5 の SHA-256 は `8980803794d858d81e69325e98a8bce6ef9c4da7d65cbab89680dbfd09b7466b`。
- §1〜§4・§6・§7、§5 欄名、evidence contract から導く protected hash が g5 と同じなら `spurious-revision` で停止する。
- destination は exclusive-create。既存 g6、未知ファイル、symlink parent は停止条件である。

### 正確な argv

親 brief の `prepare` ではなく、次を使う。

```text
["python3", "-m", "orchestrator.campaign.s8c_preregistration",
 "prepare-revision",
 "--repo-root", ".",
 "--commit", "HEAD",
 "--ruling-reference", "D496",
 "--revision-reason",
 "2026-08-18 の T-1336/T-1337/T-1347 ユーザー裁定を一括反映し、床値比較を反復単位の対比と分散へ、再走全拒否を事前割当 attempt registry へ、role payload を真の作業種別名を含まない契約へ改訂した。"]
```

shell 表記は次となる。

```bash
python3 -m orchestrator.campaign.s8c_preregistration prepare-revision \
  --repo-root . \
  --commit HEAD \
  --ruling-reference D496 \
  --revision-reason '2026-08-18 の T-1336/T-1337/T-1347 ユーザー裁定を一括反映し、床値比較を反復単位の対比と分散へ、再走全拒否を事前割当 attempt registry へ、role payload を真の作業種別名を含まない契約へ改訂した。'
```

最終的な 8c bytes が確定してから 1 回だけ実行する。生成後に markdown を変えたり、g6 を手編集したりしない。

### `DECIDER_VERSION`

本 wave では bump しない。

理由は、変更するのが protected markdown とその世代 record だけで、core・evaluator・projection・evidence contract を変更しないためである。`_record_document` は自動的に現行 `s8c-decider/v2` を書く。先に v3 を名乗ると、未実装の意味へ版だけ進めることになる。

ただし C04 の現評価器は「実験全体を判定不能 + restart 禁止」、C07 の証拠契約は床値 consumer を記述したままである。g6 はこれらを新規規範の充足証拠として数えず、正式系列を未発効のまま保つ必要がある。後続 wave が評価器・証拠契約を追随させる commit では v3 への bump と次世代 record が必須である。

### commit に含める集合

最低限の atomic 集合は次である。

```text
docs/phase3-8b-descriptor-design.md
docs/phase3-8c-preregistration.md
output/s8c-preregistration/condition-freeze/condition-freeze.v1.g6.json
docs/spool/worklog/2026-08-18-dev-wave-t1336-t1337-t1347-refreeze-1.md
docs/spool/decisions/2026-08-18-dev-wave-t1336-t1337-t1347-refreeze-2.md
output/insights/2026-08-18_t1336-t1337-t1347-refreeze/README.md
```

コード、テスト、evidence contract、g1〜g5、canonical worklog / decisions は含めない。

g6 は 8b bytes を直接 hash しないため、8b・8c・g6 を同一 commit に置くことが 3 改訂の atomic binding になる。

### 検査

read-only worker では pytest を実走しない。親は次を行う。

1. 生成前に変更文書の禁止綴り 0 件、結合文字 0 件、`git diff --check`。
2. g6 生成後、`jq` で generation 6、D496、schema v2、decider v2、g5 の SHA-256 を指す `supersedes_sha256` を確認。
3. `git diff --name-only` が上の allowlist と一致。
4. `python3 tools/check_docs.py`。
5. `python3 tools/spool_fold.py --dry-run --show-diff`。
6. commit 後に `validate_condition_freeze_at(".", "HEAD")` が generation 6、decider v2 を返すことを確認。
7. `check --json` は条件契約 valid かつ `effective=false` を期待する。CLI rc=1 は正式系列未発効を示す想定値であり、freeze invalid と混同しない。
8. 親だけが `python3 tools/run_tests.py`、`python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py` を実行する。
9. commit 後に `python3 tools/check_ai_provenance.py`。

## 6. 不変条件

- legacy + S2 の correctness gate、trace-enabled verify と trace-disabled bench の分離は一切変更しない。
- correctness-red を再測定で救済しない。attempt slot は機械的な測定失敗だけを対象とし、性能値を見た後の retry を許さない。
- T-1337 は許される実行履歴を事前割当 slot の範囲で増やすが、variant・観測値の受理基準は広げない。正常な観測値は immutable とする。
- 欠測、不完全 block、数値未記入、consumer 不在はすべて判定不能へ倒す。
- 過去の凍結値を公式性能比較へ戻さない。
- 三軸の canonical 綴りは、8b、8c、spool、insight、生成理由のいずれにも書かない。
- §5 の値セルには canonical JSON の値だけを置く。規範、解除条件、説明、空 container を置かない。
- g6 は 3 裁定を一括で記録する 1 本だけとし、中間世代を作らない。

## 7. 危険箇所

1. §10 に「矛盾時は §10 が勝つ」を書かず、旧 §6 表が引き続き読まれる。
2. median of medians の順位を、そのまま「性能差が成立した」と言い換える。
3. 後日の §5 記入時に、平均か中央値、絶対差か相対差を選べる余地を残す。
4. 単独構成の走行内 CV を条件 3 の閾値にして、正の共分散を失う。
5. `dispersion_ratio` を閾値化し、平均差が 0 付近で恒常的に発散または null になる。
6. `schedule_index` が近い行を対とし、`replicate_index` を見ない。
7. 不完全 block を `zip` の短い側へ黙って切り詰める。
8. 同一構成を on/off が選んだ場合を判定不能にして、明確なゼロ差を隠す。
9. attempt registry の slot を観測後に追加する、成功値を新 attempt で差し替える、許可理由を性能値から決める。
10. 「失敗構成だけ」を campaign 全体または成功済み replicate の再測定へ拡大する。
11. role payload の key だけを消して、値、path、invocation ID、provider envelope に真の作業種別名を残す。
12. §4 に T-1347 を書いただけで、production payload consumer が強制したと報告する。
13. C04 / C07 の旧 evidence contract と evaluator を、新しい規範の充足証拠として流用する。
14. §5 parser が非空 JSONしか検査しない点を利用し、型・単位・範囲を消費しない恒真欄を作る。
15. g6 の `ruling_reference=D496` が heading の実在しか検査しないことを、人間裁定の全内容まで照合した保証と呼ぶ。現 D496 の決定 3 は旧測り直し単位なので、revision reason と裁定記録で改訂内容を全文識別できる必要がある。
16. `prepare` という存在しない subcommand を使う、または docs 確定前に g6 を生成する。
17. `check` の rc=1 を隠して「正式事前登録が発効した」と報告する。

## 8. 後続 wave へ送る実装項目

- T-1336:
  - manifest / observations から完全 block を復元する正式 result judge。
  - 差 vector、`_difference_summary`、全構成対共分散・相関の production 消費。
  - 順位事実表、公式性能表、選択評価表の分離。
  - 同一構成対のゼロ差処理、欠測時の三値判定。
  - 後日決定する `n` / `delta_min` / `sd_max` の schema、consumer、負の対照。

- T-1337:
  - freeze-wide attempt registry の schema、exclusive-create、append-only ledger。
  - `(holdout, configuration, replicate, attempt)` slot の事前割当と有限枠。
  - 失敗構成だけが同じ replicate の次 slot を消費する resume。
  - 正常観測の差替え、slot 後出し追加、成績依存 retry の拒否。
  - crash handler、run-start、terminal report、manifest、commit binding との結線。

- T-1347:
  - `p3_autonomous_workload_trial.py:264-291` の closed key set と allowlist hash の改訂。
  - `_common_payload` の真の作業種別名 field 撤去。
  - 全 role、全 7 sink、path・ID・provider bytes を含む間接漏洩検査。
  - off arm の neutral payload が role-visible な作業種別を持たないことの負の対照と変異検査。

- 8c 条件契約:
  - evidence contract C04 / C07 と評価器・reason code・negative control の改訂。
  - T-1347 を実際に強制する condition / consumer の追随。
  - `DECIDER_VERSION` の v3 bump、対応世代 record、関連テスト。
  - formal launcher と acceptance への発効判定・judge 結線。

本 worker は read-only のため、ファイル編集と pytest 実走は行っていない。