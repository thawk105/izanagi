**real は「critic 還流の欠落」と「不在主張の過大化」です。正しさゲートの受理集合を広げる手順は確認できませんでした。**

以下、`brief.md`・`plan.md` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2588-k2-loop-roundtrip/` 配下、その他は指定 repo root 基準です。検査は静的読解のみで、テスト・role 生成・評価 job は実行していません。

### 1. real — critic を保存するだけで「診断を次提案へ還流した」と書ける

**根拠:** `brief.md:11,80`、`plan.md:199–209`、`orchestrator/campaign/p3_s4_loop.py:1217,1237`。

plan は critic 診断を保存した後、測定値・既存 whiteboard・同じ knowledge projection で planner-2/coder-2 を起動します。しかし whiteboard は5 fieldだけで診断本文を含まず、`prior_critic_reverse` も方向生成器へ渡りません。proposal-2 は評価しないため、その bool の機械的消費もありません。

**通ってしまう正例:** proposal-1 が certified → critic が逆方向を推奨 → 診断を保存 → 診断を含まない更新測定入力から proposal-2 を生成・保存。plan の列挙手順は終わりますが、brief の「その診断を入力にした」は満たしません。

**放置時の変化:** 成果物が証明する「測定結果の還流」が、「critic 診断まで還流した」へ拡大されます。

既存契約に沿った診断の受け渡しを具体化できなければ、完了条件(c)は未達と記録してください。新 field や機構の追加は本 wave では不要です。

### 2. refuted — 本 plan が正しさの受理集合を広げるという疑い

**根拠:** `brief.md:54–66`、`plan.md:58–85,199–205`、`orchestrator/campaign/p3_s4_loop.py:2226`、`orchestrator/codex_roles/policy.py:487–545`、`orchestrator/campaign/pipeline.py:655`。

確認した経路では、自己申告を保持して K2 loader を通し、指示検出・完全文法・literal/value 一致・source index を検査します。verifier 不通過は reject です。拒否候補の再抽選や入力再構成も scope 外です。

**受理形の正例〔静的確認、実走未確認〕:** planner が `decrease/medium`、coder が `value=20`、`implementation="double now_backoff = 20;"`、`confidence="medium"`、有効な source index、指示検出 `false` を本人の envelope で返す場合。この正例にも計算ノードの帰属照合・検疫・verifier が別途必要です。

`stop=continue` は terminal verdict ではありません。`check_stop()` は予算・収束等を判定する関数です (`p3_s4_loop.py:1253`)。また、reject 済み候補の診断を次候補へ渡すこと自体は、その候補を受理することではありません。

**放置時の変化:** 確認した手順どおりなら受理集合は変わりません。

`plan.md:65` の代筆禁止の列挙に `confidence` がない点は **nit** です。「envelope 全体を保存」が既にあり、補完を指示する経路は示せませんでした。

### 3. refuted — 指定 WAL が前回と同じ指示検出を必然的に起こすという疑い

**根拠:** 指定 commit の `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl:1–15`、前例 `output/insights/2026-09-09/t2182-k2-eval-run/README.md:93–109,219–221`。

**15行の本文を実際に読み、SHA-256 が指定値 `2163b794…0a611` と一致することを確認しました。**

内容は値40・30・40の build、verify、bench、commit 記録です。2・7・12行には build コマンド、4・9・14行には測定コマンドがありますが、過去の実行記録として格納されています。role に実行・検証省略・参照制限を求める文字列は見当たりません。過去の `certified=true` も今回の判定への指示ではありません。

**予測:** 前回の campaign.lock による停止と同じ原因では止まらないと予測します。ただし、同じ bytes への role 判定が揺れた前例があり、通過保証はできません。

**放置時の変化:** 本文を履歴データとして扱う限り受理集合は不変です。歴史的 certified を今回へ移すと判定の参照先が変わります。

今回 `true` が返った場合はそこで停止し、該当文字列を保存してください。送り手側の source 選定は後続の判断対象とし、本 wave の再抽選や自己申告の書換えで処理してはいけません。

### 4. real — 「主張しない」の列挙だけでは往復成立と効果実証を分離し切れない

**根拠:** `brief.md:8–11,44–45,62–65`、`plan.md:186–195,209`、K2 role 本文 `:23,124–137`。

既に因果・de novo・headline 性能等は除外されています。成果物では、さらに次の区別が必要です。

- 往復の成立は、合成による改善や探索の有効性の実証ではない。
- 新しい数値も、固定 backoff の初期値変更であり、新しい CC 構造ではない。
- proposal-1 の限定条件での certified は、候補間の certified な選択ではない。proposal-2 は未評価である。
- `knowledge_use` は自己申告であり、K2 の利用因果を証明しない。
- critic 診断の保存・入力への投入・改善効果はそれぞれ別である。
- 歴史測定と今回1走の差は性能優越の根拠にならない。`last_delta_pct=null` を維持する。

**放置時の変化:** 同じ測定値から導く結論が、配線成立から性能・構造・因果の主張へ拡大されます。

### 5. refuted — repo 内の新規実装ファイルが必須という疑い

**根拠:** `brief.md:56–57`、`plan.md:7–14,73–85,91–96,138–140,170–174`。

射影、検査、投入、digest 読出しには既存関数・CLI が示されています。repo 内へ新しいコード・script・設定を書かなければ実行できない手順は特定できませんでした。repo 外 launcher と、既存評価経路による候補の生成・build は、親による新機構の実装とは区別できます。

**放置時の変化:** 記載手順では実装面の変更は不要です。実際に追加実装が必要になった時点で brief の停止条件が適用されます。

### 6. refuted — T-304 の所有侵犯・改名後 schema への依存

**根拠:** `brief.md:58–60`、`plan.md:26,29,54,186`、`.claude/agents/coder-v4-autonomous-k2.md:75–77`。

2つの owned-path は契約の参照先で、編集手順はありません。`plan.md:186` は WAL の `throughput_tps` を現 role の `throughput_ops_sec` へ写すもので、改名完了を前提にしていません。

**放置時の変化:** 所有ファイルも role 入力の field 名も変わりません。

### 7. real — 「どこにも残っていない」は確認範囲を超える

**根拠:** job dir の `handoff.md:63–70`、`brief.md:70–77`、T-2581 の `evidence/attempt-0001/job.stdout:223–229`。

まず、現在の brief にその断定はありません。断定の所在は **handoff:64** です。

T-2581 の job rootを hidden file・段階ログを含めて検索し、repo の insight、主 checkout と今回 checkout の WAL/digest 候補も走査しました。**今回の走査では、T-2581 の LLC miss/IPC の実測値を復元できる反証は見つかりませんでした。** 段階ログの語句一致はテストや過去入力で、当該実測ではありません。

一方、「leading indicators 全般がない」と読むなら、stdout:224 に throughput **713,068 tps** が残るため反証されます。狭く「LLC miss/IPC がない」と読む場合も、探索した場所で未発見という結論までです。「唯一の完全な組」「構築不能」まで断定する証拠にはなりません。

**放置時の変化:** 歴史測定を選ぶ理由が、探索範囲に依存する判断から、代替入力が存在しないという事実へ変わります。

最小修正は「確認した保存先では LLC miss/IPC を発見できず、本 wave では歴史測定の完全な組を使う」です。

## 総括

優先して直す点は、**critic 診断の実際の受け渡しと完了条件の対応**です。不在主張も確認範囲へ限定してください。指定 WAL に指示誘導は認めず、ゲート緩和・実装必須箇所・T-304 所有侵犯は確認できませんでした。実走成立・terminal 取得・テストの緑は未確認です。