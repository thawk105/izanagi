## 総括

- **must-fix 1 件、nit 2 件**。書込み・pytest・受入 checker の実走なし。
- 層別件数は **A12 / B12 / C31 / D1 / E35 / F31 / G12**。134 path は両 TSV で一致し、分類訂正は **0 件**。
- 件数の誤りは **1 件**。§4.3 が registered 全体 **8 件**と検索集合内 **6 件**を混同している。
- 段 3 レンズ B の M1〜M6・N1・N2 は反映済み。全面未反映 **0 件**、M5 の可変状態回避だけ一部後退。
- fragment は**構造上可**。追記の禁止表記なし。本文の圧縮と可変状態の削除を推奨する。
- 保存 scan script の再実行結果は、既存 `pin-closure.tsv` と完全一致した。

## 1. §4.2 の層別表

**所見:** 件数・代表例の分類に誤りなし。

**根拠:** README §4.2、`verbatim/pin-impact.tsv` 全134行を再集計。`pin-closure.tsv` と path 集合が一致し、全 path が実在する。path 内にもコロンがあるため、行番号は末尾のコロンで分離して照合した。

| 分類 | 再集計 |
|---|---:|
| A | 12 |
| B | 12 |
| C | 31 |
| D | 1 |
| E | 35 |
| F | 31 |
| G | 12 |

`phase3-8b-restart-runbook.md` は TSV #24 の **G**、`buildcache.py` は #32 の **E**。README と一致する。

**区分:** 整合・実効性／指摘なし。

「保持」だけで閉じてはいけないのは、**A・B・C・D・F・G、および E 内の buildcache 再実測義務**。README はそれぞれ新系列への対応、契約更新、旧 control の保持、再実測を明記しており、M3 の欠落は解消している。

## 2. §4.1 の作業一覧10項

**所見:** 指定された根拠と矛盾する項目は確認しなかった。

**根拠:**

- 項1：`orchestrator/tests/test_s8b_approved.py:38` が gitlink を取得し、`:59` 以降で承認定数と照合する。
- 項2：`ident.py:214` が `ccbench_commit` を preimage に含め、`:379` が保存済み preimage との不一致を拒否する。
- 項3：`p3_s4_loop.py:111` の D1936 注記と独立 full OID、`pin.py:11` 以降の歴史的 driver 据置注記に一致する。
- 項4：`buildcache.py:1062` に pin 更新時の生成物形の再実測要求がある。
- 項5〜8：凍結物・較正・旧 pin control・事前登録を一律置換しない整理は、TSV の帰結と§4.3に整合する。
- 項9：`tools/pegasus/mocc_trace_v1_policy.json:20` の旧 base を候補へ置換した場合に自己比較となる説明は正しい。N2 は反映済み。
- 項10：`git show --stat fb5e74a17` の本文は「現用23箇所」「歴史据置」「校正pin 4件」「測定値不変・再測定なし」「16 context」を明記する。README は **pin と凍結証拠部分の要約として一致**する。

**区分:** 正しさ境界／指摘なし。是正不要。

## 3. §4.3 の境界表と規律7

### M1：registered 全体8件と検索集合内6件の混同

**所見:** README の「registered 6 件」に続く内訳は `2 + 2 + 2 + 2 = 8`。検索対象外の旧々 pin 2件まで内訳に含めている。

**根拠:** README §4.3、`README.md:155`。実在する registered JSON は8本。うち現 pin の6本が `pin-impact.tsv` #110〜115。残る次の2本は旧々 pin：

- `calibration-753f535a8d024727.json:40`
- `calibration-94a4b79fa31bba3c.json:40`

D2083 項6も「既存の較正 record 8 件」と記す（`docs/decisions.md:64012` 付近）。

**区分:** 整合・実効性／**must-fix**。

**是正案:** 行155の対象欄を次に置換する。

> 既存較正 record（registered 全8件：現pinのsilo・mocc・tictoc各2件＝検索集合内6件、旧々pinのsilo 2件＝集合外）

§4.2 の C「registered 6」は検索集合内の説明なので変更不要。

**境界判定:** その他の「保持／再取得＋新登録／再承認パッケージの一項」は妥当。`CLAUDE.md:100` 以降は過去事実の保持と較正等の前提条件の存続を分けている。D2083 は用途限定登録であり、reportへの自動接続を認めていない。

親の「既定は再取得」は**未決の推奨としてなら矛盾しない**。README は「pin差だけで一律再取得も導けない」と併記しており、規律7から再取得義務を直接導いてはいない。

`rg head_sha orchestrator/campaign` の一致は `chain_head_sha256` 系だけで、較正 record の `head_sha` を直接読む consumer は見つからなかった。§4.3 の限定された主張を支持する。

## 4. §4.4 の集合外依存

**所見:** 13ファイルと gitlink の区別、役割、短縮pinの説明は正しい。

**根拠:** 列挙された13ファイルすべての実在と、134件の集合外であることを確認した。

- gitlink取得：`test_s8b_approved.py:38`
- preimage不一致拒否：`ident.py:379`
- source evidenceのcommit field：`source_digest.py:192`
- 較正path/hash・契約の束縛：`env_contract.py:454`、`calibration_verify.py`
- 凍結raw-manifest 3本：いずれも `current_pin` は **`511c953`、7文字**

**区分:** 正しさ境界／指摘なし。

M1・M2は反映済み。「13件以上」を完全な依存閉包と断定せず、「今回確認した最低数」とする提示も適切。

## 5. 取得条件と再現性

**所見:** README §4.2 は保存scriptの実際の処理と一致する。

**根拠:** `verbatim/pin_closure_scan.py.txt` を読取り専用で再実行し、**134行のTSV出力が保存版と完全一致**した。full40 を含むファイルは79、describeは0。

母集合は `git grep -l 511c953 -- .`。除外は git pathspec に渡す方式ではなく、その後の Python `startswith(excl)` によるフィルタである。README はその処理を正しく要約している。

形別regexは保存scriptにあり、排他的分類ではない。README も排他的とは主張せず、**「依存閉包でも更新対象の件数でもない」**を明記している。M6は反映済み。

**区分:** 整合・実効性／指摘なし。

日付・採取時HEAD・clean状態は記録された取得条件。今回の再実行一致は確認したが、採取時のclean状態を独立に遡及証明したものではない。

## 6. spool fragment案

**構造確認:** H2の順序、`完了`の末尾field、1物理行の`見送り追記`は規約どおり。`remaining: none`あり。`base:` は今回の作業木での読取り専用lookup結果と一致した。land先の最新値との一致は別途必要。

title先頭の `[T-2756]` は同fragmentで完了する既存項目なので適格。追記行に現pin literal、承認語、`.md:数字`、`状態:`はない。

### N1：採用したM5の文面へ可変状態を再追加している

**所見:** 追記末尾の「pin 更新の裁定待ち」は、参照追加に不要な可変状態。

**根拠:** `spool-fragment-draft.md:32`、`verbatim/consult-B.md` M5、`verbatim/s4-adjudication.md` M5。採用文は「判断材料の参照追加である」で閉じていた。

**区分:** 整合・実効性／**nit**。

**是正案:** 末尾を次に戻す。

> 本追記は判断材料の参照追加である】

### N2：fragment本文が成果物の内容を重複掲載している

**所見:** 材料1〜3の詳細説明は、索引としてのworklogに対して長い。

**根拠:** `spool-fragment-draft.md:14`〜`:17`、`docs/worklog.md:22` 以降の「gitに入り得ない情報だけ」「最重要1〜3件・一次資料ポインタ」の規約。

**区分:** 整合・実効性／**nit**。

**是正案:** 当該4段落を「候補確定、GCC2版pass・clang未確認、波及資料完成。詳細はinsight §2〜§4」の1段落へ圧縮し、協議の決着・残る裁定・工数を残す。

## 7. check_docs・三軸語・placeholder・NFC

**所見:** 現在の成果物に、この静的検査で検出した阻害要素はない。

**根拠・検査範囲:**

- READMEと`verbatim/`の読取り可能な全ファイルを検査し、**非NFCなし**。
- `tools/check_docs.py:206` の禁止placeholder 3種は**なし**。
- 三軸名が揃うのは `verbatim/plan.md:517` の注意書きだけ。値付き表記ではなく、三軸 conjunction の対象形ではない。
- 生report・TSVを含め、それ以外に三軸名が同一ファイル内で揃うものはない。
- insight README・verbatim は `LIVING_DOCS` のpin literal／行番号参照検査対象ではない。これらに値や行番号が存在すること自体を違反とは扱わない。
- fold先のphase3へ入る追記行には禁止表記がない。worklog本文のpin literalも、phase3向けの検査と混同しない。

**区分:** 整合・実効性／指摘なし。

`check_docs.py`全走・`s8b_holdout_freeze search`全走の合格は主張しない。README §7とfragmentの実走記録・段6所見は、親の最終実測と本レビュー反映後の状態に合わせて確定する必要がある。
