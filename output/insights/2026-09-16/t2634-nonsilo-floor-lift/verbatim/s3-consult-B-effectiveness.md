## 所見一覧 (番号、real / refuted / 判定不能、根拠、影響)

1. **real — F1/P3 は「照合可能」と「現物が探索対象になる」を混同している。**  
   `layer3_report.py:518-538` は calibration directory **直下**の JSON と contract pin の和集合だけを探索する。通常の呼出元は同 `:851-858`。今回の4件がある `registered/` は再帰探索しない。D1508 (`docs/decisions.md:46981` 以下) も「`registered/` 全体は走査しない」と明記する。**phase3 への追記だけでは4件が公式 layer3 report に流入するようにはならない。**

2. **refuted — 非 silo を一律拒否する within-run protocol 分岐がある、という疑い。**  
   `layer3_report.py:477-495,590-599` は canonical genome から protocol を取り、protocol・records・threads・workload を一致させる。非 silo 一律拒否はない。ただし探索対象になること、複数一致がないこと、既知不整合 pin による除外がないことが前提である。

3. **real — plan の mocc rr50 数値欠落扱いは修正が必要。**  
   README に詳細値がないという観察自体は正しい。しかし record 自体に LLC miss `0.14821268619041902`、CV `0.014348130441228051` がある。親の `1.4348%` は正しい。根拠は `calibration-449d0ad22f13e366.json:1582,1612` と射影された `parent-record-facts.txt`。推定ではなく一次値の転記で埋められる。

4. **refuted — phase3 への文書登録が code の受理集合を変える、という疑い。**  
   照合器は phase3・insight・spool を読まない。plan の変更だけなら受理集合は不変。ただしこれは所見1の未接続も不変という意味である。

5. **refuted — BASELINES に tictoc を追加すると既存指定 test が必ず赤になる、という疑い。**  
   `test_between_run_floor.py` に tictoc の引数拒否や BASELINES のキー集合を固定する assertion は見当たらない。既存の silo/mocc assertion は追加だけでは変わらない。静的判定であり、実走結果ではない。

6. **real — fragment 草案は `base:` 未確定のままでは受入不能。**  
   plan はこの点を明記済み。それ以外の指定された形式違反は見つからない。完了の意味は所見1と分けて確定する必要がある。

7. **判定不能 — F4 の他 worktree の未 commit 差分。**  
   この worktree の共有 Git refs から他 worktree の未 commit 状態は検算できない。committed 差分では、検査時の main に未統合な local branch の phase3 変更は検出しなかった。t2386 の committed 編集対象に phase3.md は含まれない。

## 保留の実体と登録先の判定

**「embargo という protocol 禁止スイッチはない」は支持する。「実体は未登録の散文だけ」は支持しない。** 政策上の保留と、公式 report までの接続条件を分ける必要がある。

tracked 内容への `git grep` で、`embargo`、`非 silo`、`silo 限定`、`silo にだけ`、`legacy`、`genome-absent`、`within_run`、`registered/` を検索した。関連する結果は次のとおり。

- `orchestrator/`・`tools/` に対する `embargo|silo 限定|silo にだけ` は **0件**。
- embargo の明文は `docs/archive/worklog-phase3-0909-1405.md:393`、`docs/archive/worklog-phase3-0915-1503-1504.md:5,34,681`、T-2224 README `:122-123` に存在する。
- **追加の未接続条件**は `docs/archive/worklog-phase3-0902-1206.md:8-10,42-43`、`output/insights/2026-09-02/t2136-within-run-floor-protocol/README.md:18-26` に存在する。後者は、取得後にも「環境契約世代の登録と活性化」「その契約を持つ v2 campaign」「層3レポート生成」が必要とする。
- **探索範囲の方針と実装**は D1508 と `layer3_report.py:518-538`。非 silo 専用禁止ではないが、今回の登録済み4件が自動採用されない直接の理由である。
- `genome-absent` の silo 仮定は同 `:493-494` と `test_layer3_report.py:3841` 以下。D1538 (`docs/decisions.md:47632`) の内容 hash allowlist 方針も genome 不在 record が対象で、今回の genome 付き4件を拒否する根拠ではない。
- 同 `:539-543,582-583` は既知不整合 contract pin の場合に within-run 候補全体を除外する。これも非 silo 専用 embargo ではない。

登録先の判定は以下とする。

| 候補 | 判定 | 根拠・意味 |
|---|---|---|
| `docs/phase3.md` 8b | **入れるべき** | `:537-550` の較正取得記録と同じ位置に、解除対象と用途限定を残せる。ただし「公式文書への登録」であり、report 消費の開通ではない。 |
| paper-story 現行版 | **入れるべきでない／次版は別 wave** | `docs/paper-story/README.md` の「このディレクトリの位置づけ」は既存版を凍結し、新版は正典全体から再導出すると定める。 |
| `docs/pegasus-runbook.md` | **主登録先にすべきでない** | 運用・環境契約の手順書である。ただし `:1373` の「登録済み calibration は2件」は無限定だと現物8件と不一致。「環境契約が pin する較正2件」への限定訂正は候補になる。 |
| env_contract registry | **文書解除だけなら変更しない。report 接続なら別 wave** | `env_contract.py:248-289` は契約値と較正 bytes を世代として束縛し、g2 の contract hash も golden と照合する。成果物一覧ではない。しかし「登録先ではないから不要」と全面否定するのも誤り。認定 record を通常の report 候補へ加える既存経路の一つである。 |
| `output/` の registry | **追加しない** | 4件は既に `calibration/registered/` に存在する。`output/registry/` の tracked file は T139 の予約台帳2件で、較正採用台帳ではない。新台帳を作る根拠はない。 |

## 4 record の照合結果 (食い違い一覧)

共通 directory は `output/env/pegasus/calibration/registered/`。以下のファイル名先頭16桁は、実際の `sha256sum` の先頭とも全件一致した。

| 対象 | record ファイル名 | request / node | records | LLC miss | within-run CV |
|---|---|---|---:|---:|---:|
| tictoc rr50 | `calibration-9b49335d02ad4d2e.json` | `998860.nqsv` / `bnode093` | 1,000,000 | 7.969% | 2.2160% |
| tictoc rr95 | `calibration-cb98513996e5ae35.json` | `998863.nqsv` / `bnode103` | 1,000,000 | 9.557% | 0.8336% |
| mocc rr50 | `calibration-449d0ad22f13e366.json` | `989271.nqsv` / `bnode020` | 1,000,000 | **14.821%** | **1.4348%** |
| mocc rr95 | `calibration-b3329d93417c76ad.json` | `998864.nqsv` / `bnode016` | 1,000,000 | 17.008% | 1.7204% |

照合根拠：

- tictoc 2件・mocc rr95：T-2224 README `:17-19,33-35,131-141`。plan の request、node、records、丸めた数値、path は一致。
- mocc rr50：T-2535 README `:25,29-38`。request、node、records、ファイル名、CV 原表記 `0.0143` は一致。詳細 LLC miss と CV の追加桁は同 README にはない。
- その詳細は record `:1582,1612` に存在する。plan の phase3 案・decisions 案・worklog 案・検査計画の「欠けた値を補わない」は、**record を出典に転記する**へ訂正すべきである。
- `parent-record-facts.txt` は全件 `n=10`、threads 48、accepted、同じ CCBench head `511c9538e4e8efa54b45cda62e72389ed3b706ec` を示す。plan の「mocc rr50 の reps を断言できない」は README 単独の限界であり、利用可能な一次証拠全体の限界ではない。
- record hash と binary hash は別物。plan の path の16桁は record hash と一致し、取り違えはない。

**数値の誤転記は見つからない。実在する mocc rr50 の詳細値を欠落扱いする点が問題である。**

## P4 の判定 (足す / 足さない)

**足さない。** 今回の較正文書登録には不要で、追加しても現行 pin で測定は開通しない。

`between_run_floor.py:285-298` が baseline 未登録を拒否し、登録後も `:303-307` が source の hook 証拠不在を build 前に拒否する。親 probe は tictoc の hook 判定 False を示す。

足さないことによる確認できた影響は、将来 hook を移植した際にも baseline 対応が必要なことと、現在の CLI が hook 不在より先に unknown protocol を報告すること。既取得較正や現在の silo/mocc 経路への追加の害は見つからない。

追加だけで `test_between_run_floor.py` の既存期待値が赤になる根拠はない。同 `:251-253,440-483,486-552` は silo/mocc の hook 判定と経路を検査する。**「既存 test が赤になるから追加しない」ではない。**

将来追加する stock genome は、T-2224 README `:48-50` の実測値に合わせる。

```text
tictoc|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,PREEMPTIVE_ABORTS=1,TIMESTAMP_HISTORY=1
```

`genome.py:147-156` の5軸を満たし、`:74-89` の制約が排除する no-wait 両1にも該当しない。

親 P4 の「起動できない baseline を置くこと自体が規律違反」という一般論は撤回すべきである。現行 mocc がその反例である。

## fragment の形の指摘

**指定された構造は、base の仮値を除いて適合する。**

- 共通 frontmatter、ledger、ファイル名、wave、seq は対応している。
- worklog の H2 は `## 本文`、`## 次の一手差分` の2つで順序も正しい。
- `title:` の `[T-2634]` は既存 active item を同 fragment の完了で扱うため許容される。独自 parser なので YAML 風の引用符を追加しない。
- `remaining: none` と `base:` は item 末尾の連続した機械 field になっている。
- decisions は `## {{D:nonsilo-within-run-floor-lift}}. 題` の形で、題に日付を付けていない。有効な `[T-数字]` の例示もない。
- **`base: <…>` は未受入。** land 先 local main の実体 item の digest に置換し、dry-run で一致を確認する必要がある。LF・末尾改行は実ファイル作成前なので未判定。

`完了`／`更新` は次のように判定する。

**between-run 未実測という理由だけで `更新` にする必要はない。** 起票逐語は「公式成果物へ入れてよいかを裁定する」、裁定逐語は「保留を解除する」「較正が取れたことを性能比較や床値本走の完了とは扱わない」である。between-run 完走を T-2634 の終端条件にはしていない。

一方、親が「公式成果物」を **layer3 report での実消費まで含む**と確定するなら、所見1の未接続が残るので `完了` は不適切であり `更新` にする。完了可否を左右するのは、この登録の意味である。

## 親 brief への訂正

1. **F1/P3：未登録状態だけという説明を撤回する。** D1508 の探索範囲と T-2136 の未接続条件を記載し、文書登録と report 接続を分ける。
2. **F3：親の mocc rr50 `1.4348%` は正しい。** plan 側の訂正要求を採らず、LLC miss `14.821%` も record 出典で追加する。
3. **F2：実測と静的帰結を分ける。** probe は hook 述語、BASELINES、argv 判定まで。CLI rc=2 と main の build 前例外はコードからの帰結である。
4. **P1：tictoc の再開条件に baseline 対応を加える。** hook 移植だけでは argv gate を通らない。
5. **P2：全4件の n=10 は record 証拠がある。** ただし producer・実行条件が同一、between-run を代替可能、とは広げない。
6. **不変条件：「output/ を書かない」は新規 insight 作成と矛盾する。** 既存較正・凍結成果物の bytes を変えず、新規 insight は作る、と限定する。
7. **F4：確認範囲を限定する。** `git log --all --since=2026-09-10 -- docs/phase3.md` と未統合 local branch の merge-base 差分では8b変更を検出しなかった。t2386 の committed 差分も非重複。他 worktree の未 commit 差分と `t548-a-procure:1547` の1行は、親の観測として区別する。

## 裁定パッケージ候補 (親が段 4 で決めるべき二択以上の争点)

1. **「公式成果物へ入れる」の完了範囲**
   - **A：用途限定の文書登録として完了。推奨。** phase3・decision・insight に4件を登録し、「layer3 の探索・契約・report 接続は変更していない」と明記する。T-2634 は完了扱い。
   - **B：公式 layer3 report への接続まで要求。** 現 plan は未完。契約世代・活性化・campaign 生産を含む実装範囲を別途設計し、T-2634 は更新扱いにする。

2. **mocc rr50 の表記**
   - **A：record 出典で 14.821%／1.4348% を記載。推奨。**
   - B：README の丸め値だけを保持。ただし「一次資料に値がない」とは書けず、既知の詳細値を省く理由が必要。

3. **runbook の「登録済み2件」**
   - **A：「環境契約が pin する較正2件」へ限定する最小訂正を含める。推奨。**
   - B：本 wave では触らず、別 wave の訂正事項として引き継ぐ。全 registered が2件という意味では引用しない。

4. **tictoc baseline**
   - **A：今回は追加せず、hook 移植と合わせた将来対応を明記。推奨。**
   - B：将来用に追加する。測定開通にはならず、今回の裁定実装に必要な変更でもない。

## 総括

**docs-only 方針は採れるが、現 plan をそのまま承認するのは不適切である。** 必須修正は、mocc rr50 の一次値を採用することと、**phase3 への登録では registered の4件が layer3 report に自動接続されない**ことの明記である。

T-2634 を用途限定の文書登録として閉じるなら `完了` は妥当。report 接続まで閉じたとは書かない。BASELINES は変更不要。静的検査のみで、pytest・測定・fold は実行していない。