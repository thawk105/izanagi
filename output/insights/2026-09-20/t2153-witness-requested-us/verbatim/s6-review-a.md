## 所見

**実装レビューは GO。must-fix の実装欠陥は見つかりませんでした。** 変異指定と検証報告には should が2件あります。編集・pytest・変異実走は行っていません。

以下、G＝[condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-requested-us/orchestrator/campaign/condition_meaning_gate.py)、T＝[test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-requested-us/orchestrator/tests/test_condition_meaning_gate.py)。両現物の Git blob hash は指定 patch の変更後 hash と一致しました。

1. **real／should：I1 比較ログ単独では「一時 path 由来だけ」を証明していません。**

   根拠：[compare_records.py:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/compare_records.py:19)、同:31、[login-after-summary.txt:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/login-after-summary.txt:20)。

   比較器は argv の値を除外し、list の形も各要素の key 集合の和へ潰します。ログ自体も digest 差で `DIFFERENT / rc=1` です。このログから未比較の argv 差を一時 path と断定できません。

   **今回、原本を配列 index を保持した全 leaf 比較で独立確認しました。** SORT／NOINLINE／RUNG1 の差は、一時 path を含む argv と派生 digest・ID・`record_ids` だけでした。identity の値に差はありません。結論は支持できますが、要約の「identity から派生」はこの3組には当たりません。

   **放置時の成果物影響：互換性台帳が、比較器の実際の検証範囲を過大に記録します。** 比較根拠と要約を修正すべきです。

2. **real／should：m8 は変異する行を限定しないと、裁定どおりの帰属になりません。**

   根拠：[ruling.md:60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/ruling.md:60)、G:3439、G:3450、G:3470、G:1157。

   現物の `if companion_sources:` は副 payload 挿入だけでなく個別観測も囲みます。これを単純に無条件化すると、単 file macro では site marker が未計装なので、**schema 到達前に `site-observation-mismatch`** になります。

   裁定の「副 key 混入を schema が拒否」を測るには、G:3470 の payload 構築・挿入だけを無条件化する必要があります。

   **放置時の成果物影響：変異台帳が、個別観測による拒否を schema の検出成果へ誤帰属します。**

3. **refuted／nit：総数相殺・同一 key の二重展開による誤 green。**

   根拠：G:3026、G:3048、G:3057、G:3249、G:3416、G:3441、T:1743。

   file 登録順と各 file 内の箇所順から `f0s0/f0s1/f1s0/f1s1` が生成され、現登録に collision はありません。計数は出力 token の行全体一致です。同じ key が二重展開されれば個別値が `(2,2,0,2)` となり拒否されます。

   指定の相殺入力は総数検査を通りますが、`f0s0=(0,0,0,0)` で拒否されます。T:1753 は `_assert_compile_time_branch_selection` の直接呼出しで、schema に依存しません。コメント内では展開が消え、raw string 内では未展開の呼出し文字列が残っても `_OBSERVED_…` と一致しません。既存 output token／site marker の直接混入も collision 検査対象です。

   **成果物影響：指定反例から未観測箇所を意味確立済みとする経路は塞がっています。**

4. **refuted／nit：shadow が元 header を上書きする、または中継 header の `..` が実木へ逃げる。**

   根拠：G:1171、G:3274、G:3280、G:3088、G:3113、G:3132、G:3174、G:3401、T:1762。

   主・副はともに no-follow capture を通り、2 file の mapping は深い鏡像へ進みます。全計装 file を symlink 作成から除外してから本文を書きます。通常の中継ディレクトリは実体なので `../../../include/backoff.hh` は shadow 内へ解決されます。

   両腕で同じ shadow と prefix-map を使用し、site define も同一です。対象 define 以外の comparable 一致検査も維持されています。

   **成果物影響：通常入力で元 source／supply digest を汚染する新経路は見つかりません。**

5. **refuted／nit：副 evidence が自己申告を信じる、または改竄テストが digest／issuer に遮られている。**

   根拠：G:4084、G:4139、G:4164、G:4188、G:4202、G:4210、T:129、T:1804、T:1870。

   required key と箇所集合は registry から導出しています。tuple の長さ・順序、row の key 集合、登録値、exact int による bool 拒否、capture 型・path・digest・三 identity の一致、個別値・総和、両腕の site define を検査しています。単 file の副 key は unexpected です。

   テストは改変後 payload から canonical digest を再計算し、`require_issuer=False` で検査します。片側 digest 改変、欠落・重複・余分 key・数値改変が古い digest に遮られる構造ではありません。整合した両側偽造まで検出するという主張はしていません。

   **成果物影響：指定された不整合 record が schema を通って意味確立表示へ入る穴は見つかりません。**

6. **refuted／nit：既存21 macro／旧宣言経路の受理集合が広がる。**

   根拠：G:1037、G:3030、G:3065、G:3200、G:3438、T:2293、T:2338。

   変更前との AST 比較でも factory・DefineSpec・供給処理・旧 CLI は不変でした。既存21件では追加 marker は空文字、追加 argv は無し、副 payload は空です。総 N も従来の主 N と一致します。既存 dataclass／evidence key の追加はありません。

   REQUESTED_US の `1/None、1/1、0/0、0/1` は factory `None` のままです。BACKOFF_FIXED 固定の旧経路も維持されています。

   **成果物影響：REQUESTED_US 1/0 を未確立から観測結果に応じて green／red にする以外の受理拡大は見つかりません。** 全21件の実 record bytes 同一を実測したとは扱いません。

7. **refuted／nit：実 TU 要約・author 報告と実装が食い違う。**

   根拠：[実 TU 原本:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/login-after/requested-us-1v0.stdout.jsonl:2)、[BACK_OFF=0 原本:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/login-after/requested-us-1v0-backoff0.stdout.jsonl:2)、[focus-own1.log:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/focus-own1.log:31)。

   原本で `(4,4)/(0,4)`、4 site row の `(1,1)/(0,1)`、admitted、未確立 `[]` を確認しました。主・副 digest も実木と一致します。BACK_OFF=0 は `(3,3)/(0,3)` の red／admitted=False で期待どおりです。

   author の「pytest 未実走」は引継ぎ時点の記述です。親の request は所有 test を含む15 file 全体を指定し、計算ノードの焦点走は **1148 passed／2 skipped**。ただし集約ログには node 別結果・skip 理由がなく、各 node の個別実走証明まではありません。新設検査に説明だけの stub や恒真 assert は見つかりませんでした。

   **成果物影響：焦点走の緑は支持されますが、受入全走・正式変異・計算ノードの実 TU cell 完了へ読み替えることはできません。**

## 変異の帰属予測

以下は静的予測です。完全な失敗 node 集合は正式変異走で確定する必要があります。表中の短縮名は T の `test_requested_us_multifile_…` を指します。

| 変異 | 予測 | 主な失敗 node・帰属 |
|---|---|---|
| m0 | SURVIVED | 通常の行末 comment は意味上等価。module bytes 自体は変わるが、今回の意味・供給 record に module hash は入らない。 |
| m1 | KILLED | registry／patch 束縛 test の T:1096、正例、CLI、schema 各ケースの前提 green。独立 fixture は header 2箇所のままで、宣言1との不一致。複数 node であり schema 改竄検出とは数えない。 |
| m2 | KILLED | `supply_meaning_and_admission`、`shadow_instruments_all_files`、CLI 等。元 header を残せば観測は2/4、shadow test は本文不一致。include error による kill とは区別。 |
| m3 | KILLED | 正例、全 registry 正例の REQUESTED_US、CLI 等。正常な4箇所を期待2で拒否する**過剰拒否**。missing include は個別観測がなお拒否する。 |
| m4′ | KILLED | `rejects_compensated_missing_sites`。個別等値検査だけを除けば相殺入力の総和は一致し、直接呼出しが例外を出さず失敗。公開 evaluator の schema は二次防壁。 |
| m5 | KILLED | `green_schema[missing]`。required と後段副検証の双方を key 依存にした場合、両副 key 欠落 record が通る。片方の guard だけを変えた変異とは区別する。 |
| m6 | KILLED | registry 集合 pin、REQUESTED_US 正例、CLI、schema 前提等。fixture は registry 非依存なので、その構築時の KeyError ではなく factory None／unestablished に到達する。 |
| m7 | KILLED | `green_schema[digest]`。形式正しい片側 digest 改変が通り、`raises` が失敗。他の identity／digest 書式検査は通るため狙った項に帰属。 |
| m8 | KILLED | **payload 挿入だけ**を無条件化すれば既存単 file 正例・field/key pin 等が `_issue_arm_record` の unexpected-key 検査で失敗。G:3439 の guard 全体を外す形なら個別観測で先に失敗し、裁定の帰属にはならない。 |

## 判定

**GO — 次の正式変異・受入段へ進める実装です。**

全箇所性、shadow、schema、受理集合に must-fix は見つかりませんでした。I1 の報告根拠と m8 の変異箇所は補正してください。この判定は wave 全体の完了・land 承認を意味しません。

## 総括

主2＋副2の個別観測と再検証は、指定された相殺反例を拒否できる構造です。残る指摘は、I1 比較の説明と m8 の帰属精度です。本レビューは現物・既存ログの読み取りと静的比較のみで、書込み・テスト実走はしていません。