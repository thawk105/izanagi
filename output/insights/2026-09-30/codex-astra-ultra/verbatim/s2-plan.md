## 単位 A

静的確認のみ実施。ファイル変更・テスト・CLI 実走は行っていない。以下の行番号は投入先 worktree の現物基準。

**D2229 決定 2 の model 側は、次の 5 行で閉じる。**

| 箇所 | 変更 |
|---|---|
| `tools/check_docs.py:372` | DW-O01 literal の `gpt-6-sol` → `gpt-6-astra`。V2 書式は維持 |
| `orchestrator/tests/test_check_docs.py:9138` | drift 負例の置換元を `gpt-6-astra` にする。置換先は維持 |
| `orchestrator/tests/test_check_docs.py:9424` | literal 期待値を astra にする |
| `orchestrator/tests/test_dev_wave_launch_authority.py:261` | 全段導出 model の期待値を astra にする |
| `orchestrator/tests/test_dev_wave_launch_authority.py:377` | docs 独立照合の期待値を astra にする |

`docs/dev-wave/operations.md:14` は既に astra。過去形式を試す `_V1_MODEL_LINE`・`_V2_MODEL_LINE` の fixture は変更しない。

**effort 側の変更箇所は、brief の列挙より多い。**

| 箇所 | 変更 |
|---|---|
| `docs/dev-wave/workers.md:5,10,24,46,60` | 親担当。5 箇所の medium → ultra |
| `tools/check_docs.py:513,514,515,516` | 4 literal の medium → ultra |
| 同 `:518,521,524` | review・focus・author の必須文中 medium → ultra |
| 同 `:527,532,537,541,545` | 5 finding の表示値 medium → ultra |
| 同 `:5834,5840,5846,5852,5858` | `_check_dev_wave_reasoning_effort_pins()` の期待値 medium → ultra |
| `orchestrator/tests/test_check_docs.py:8241` | DW-S05-A の負例生成用置換元 medium → ultra |
| 同 `:8427–8431,8459–8462` | decoy・重複検査の「正しい値」役の medium → ultra |
| 同 `:8482,8485–8487,8518–8519` | 別キー・引用・コメント検査の medium → ultra。誤値 high は維持 |
| 同 `:8859` | 追加可視値を ultra にし、採用値の重複も引き続き拒否する検査にする |
| 同 `:8999` | production-path 負例内の採用値 medium → ultra |
| 同 `:9025,9030,9035,9039,9043,9046` | finding・必須文の独立 literal 期待値を ultra にする |
| `orchestrator/tests/test_dev_wave_launch_authority.py:70,74,78` | 合成 workers fixture の置換元 medium → ultra |
| 同 `:265,267` | 現行 docs からの author・fix 導出期待値 medium → ultra |

`test_dev_wave_launch_authority.py:71,368,369` の medium は、合成 fixture に意図的に設定する author 値として**維持できる**。`:70` を ultra → medium の置換にすると、review=high、focus=low とともに段別導出を検証できる。`:864,868,872` も合成された異なる値の検査なので変更不要。

`REASONING_XHIGH_*` という既存定数名は今回改名しない。値変更と無関係な参照変更を増やさない。

追加する負例は、5 節それぞれの旧値 `medium` を拒否するケース。既存の high 負例も残す。

**ultra 語彙と consumer。**

- `tools/dev_waves/effort_levels.py:24` の `"max",` の後へ `"ultra",` を追加。
- 同 `:7–11` の docstring は、既存の F56 の記述を残して次を追記する案：
  > `ultra` は luna 系では非対応である。この定数への収載は、全 model がその値を受理することを意味しない。model×reasoning の互換性や served model の identity は本 module では保証しない。
  
  luna 非対応は依頼で指定された事実として記述する。本段での独立実測ではない。
- `orchestrator/tests/test_effort_levels.py:40–42`：共通 `expected` をそのまま拡張すると Claude 側も変えてしまう。Claude の期待 tuple は維持し、Codex だけ `expected + ("ultra",)` にする。
- `tools/codex_worker_launch.py:51,4857`：実行コードの import・argparse choices は定数に追随するため変更不要。
- `orchestrator/tests/test_codex_worker_launch.py:3667`：許可語彙の parametrize に ultra を追加。単位 A/B の所有境界上、この 1 行は B 担当に渡す。
- `orchestrator/tests/test_effort_levels.py:28,34,48–52`：subset・import 同一性検査は変更不要。role adapter の受理集合は拡張しない。
- `orchestrator/tests/test_codex_worker_launch.py:6590`：定数から代替値を選ぶため変更不要。
- `tools/dev_wave_codex.py:72,285`：文字列を受け取り転送するだけ。追加語彙の実装変更は不要。`orchestrator/tests/test_dev_wave_codex.py:99–101` の plan/consult matrix は ultra にして転送確認に使える。

**supervisor digest。**

`tools/dev_waves/daemon.py:179–186` は同ディレクトリ直下の Python/JSON の名前と内容を hash するため、effort_levels の本文・docstring のどちらを変えても digest は変わる。`:1114,1211` の前後比較には影響する。

grep では `_supervisor_digest()` の実値を固定するテストは見つからなかった。`orchestrator/tests/test_dev_waves_receipt.py:383` の固定 digest は別物の receipt schema であり、更新不要。稼働 daemon 0 件は brief の L9 に依拠し、本段では再確認していない。

## 単位 B

**P1 は単なる発見追加では閉じない。usage 照合、終了後の証跡回収、receipt 再検証、ledger の接続まで必要。**

推奨する設計は、stdout で得る root ID と、rollout を識別する thread ID を分ける方式。

| 箇所 | 変更前 → 変更後 |
|---|---|
| `tools/codex_worker_launch.py:389` | `RolloutState.session_id` だけ → thread ID に加え、root ID・parent thread ID を保持 |
| 同 `:412` | root の session IDs と rollout map → root IDs は維持し、子候補・親子関係・未解決候補を別管理 |
| 同 `:1445` | stdout ID に一致するファイルだけ探索 → root 探索＋session_meta による子探索、親子連鎖の固定点まで解決 |
| 同 `:1497` | 一律 `meta_id == rollout.session_id` → root は現行条件、子は後述の厳密な別条件 |
| 同 `:1518` | turn_context の model/effort 照合 → cwd も要求値と照合 |
| 同 `:1634` | 全登録 rollout を合算 → この構造は維持し、子・孫を同じ map に登録 |
| 同 `:1653` | 全 rollout 合計と root stdout usage を比較 → root の比較と子の証跡完全性を分ける。実測後に固定 |
| 同 `:470` | rollout ごとの issue 集計 → 親子関係不正・未解決・探索失敗も致命的 issue として集約 |
| 同 `:2100,2113` | 発見・tail・root manifest 登録 → 子も検証後に manifest 登録 |
| 同 `:2203,2214,2294` | spawn 後の root 欠落 grace、終了時は即 break → 終了後の子証跡回収を追加 |
| 同 `:1992,2018` | root 中心の attempt 記録 → 全 rollout、親子関係、委任 session 数を記録 |
| 同 `:2539` | 全 sealed rollout から recorded summary → 子も含む現行ループを活用 |
| 同 `:4384,4499,4700` | sealed evidence 再計算 → stdout root と sealed session_meta から同じ親子関係・集計を再構築 |

子の登録条件は次のすべてとする。

- ファイル名の ID と `session_meta.id` が一致する。
- `session_meta.session_id` が、その attempt の stdout root ID と一致する。
- `source.subagent.thread_spawn.parent_thread_id` が同じ root の既知 thread に到達する。
- root と子の取り違え、自己参照、循環、別 root への接続、同一 ID の複数ファイルを拒否する。
- 孫が先に見つかった場合は候補に保持し、親発見後に解決する。期限後の未解決候補を黙って捨てない。

`:1497` を単に「既知 ID のどれかならよい」にする変更は不可。root の同一性検査は維持する。

**探索範囲・費用。**

最小で取りこぼしを避ける案は、`args.sessions_root` 配下の通常 `rollout-*.jsonl` を列挙し、各候補の session_meta 行だけを上限付きで読む方式。mtime・日付ディレクトリだけで排除すると、遅延書込みや時計差による欠落を受理しかねないため、初版の正しさ条件にはしない。

- 初回は `N` ファイルの列挙と bounded header read。
- 以降は既読の無関係ファイルを cache し、新規・変更された候補だけ読む。未完成 header は再試行。
- directory 列挙自体は単純実装では各周期 O(N)。現行も未発見 root ごとに全 `rglob` を繰り返している。
- 探索・読取が上限や期限を超えた場合は incomplete/invalid として拒否し、探索の打切りを「子なし」と扱わない。
- 時刻窓を使う最適化は、実環境の配置規約とファイル数を測った後に限定する。

**実ファイル数と所要時間は未測定。** 必読射影に sessions_root の具体値・件数がなく、本段は指定資料の静的検査に限定した。親は実走の sessions_root について、総候補数・新規候補数・header 読取量・1 scan の所要を記録する必要がある。

**終了競合。**

現行の `evidence_grace_s` は spawn 起点の root 欠落猶予であり、終了後の子発見猶予ではない。`:2214` で root process 終了を見た直後に break するため、既存値を変えるだけでは直らない。

root 終了後も、固定した終了時刻＋grace まで bounded な発見・tail を続ける。待機中も既存 wall-clock・token・call 制限を適用し、grace ごとの無期限延長はしない。seal 直前に再走査し、未解決候補・部分行・欠落 context/usage は拒否する。

ただし、**grace 経過だけでは、まだ出現していない子の不存在を証明できない**。root rollout の spawn 成功結果等から期待する子 ID を得られるなら、その集合との完全一致が必要。L4 の「stdout に ID がない」は root rollout にも ID がないことを意味しない。親の実測でここを確定する。

**会計・予算。**

`:1634` の合算を活用すれば、`:1956` の seal 判定、`:2211` の監視、`:2530` 付近の attempt 合算へ子の call/token が流れる。既存の実行中 `>=`／自然終了時 `>` の境界は変更しない。

一方、`:1667` は全 rollout usage と root stdout usage を等値比較している。親実測で stdout usage が root 単独なのか子込みなのかを先に確定する。root 単独なら、root stdout は root rollout と引き続き厳密照合し、子はそれぞれの terminal/cumulative usage の整合性を検査して別途合算する。差を許容する、比較を削る、といった変更は提案しない。

fork による履歴複製や初期 token 累積値も未確認。複製済みの履歴を再計上しない根拠が必要で、推測による差引きはしない。

**receipt と consumer。**

新しい明示 field を足すなら、閉じた V5 を変更せず V6 を作る。

- `tools/codex_worker_launch.py:149,172,275`：V6 attempt/rollout/top-level field 定義。attempt に `delegated_session_count`、rollout に root/parent ID を追加する案。
- 同 `:2637,3777,3960`：writer、attempt validator、receipt validator を世代別に対応。既存 V1–V5 は維持。
- 同 `:4384,4722`：記録された count・親子関係を信用せず sealed evidence から再導出し、manifest 全件と照合。
- 新しい fatal issue は `:150` の理由集合と `:470` の集計へ接続。既存 `duplicate_key` の扱いは変更しない。

grep で確認した接続先：

| consumer | 影響 |
|---|---|
| `tools/codex_worker_ledger.py:492,667,1123–1140` | receipt 本体ではなく manifest＋rollout を読む。現行は `session_meta.session_id == ファイル名ID` を選ぶため、子を manifest に足すだけでは会計漏れ。子の identity と親子連鎖を厳密に検証する変更が必要 |
| `orchestrator/tests/test_codex_worker_ledger.py:1337` | V2 manifest fixture に root・子・孫、別 root、偽 parent の回帰を追加 |
| `tools/collect_wave_usage.py:22,90` | Claude ledger 専用。Codex receipt schema の consumer ではなく変更不要 |
| `tools/t1434_t1222_science_slice.py:940` | recorded/requested effort を読む。既存 field を維持する設計なら変更不要 |
| `orchestrator/tests/test_dev_waves_git_state.py:1379` | receipt 値から provenance 表記を作る検査。既存 field 維持なら変更不要 |
| `orchestrator/tests/test_codex_worker_launch.py:1330,3300,4201,4370,6890,7218` | fake rollout、受理、context、欠落、再計算、usage 不一致の回帰を拡張 |
| `orchestrator/tests/test_codex_worker_launch_budget.py` | schema 世代互換と累積予算の回帰対象 |

したがって、P1 採用時の B 所有には **ledger とそのテストも追加**する必要がある。

**P1′との比較。**

P1′は prompt で委任禁止を伝え、実証拠で委任が見えたら fatal issue にする。発見・終了競合への対策は共通だが、子の usage 合成・V6 の詳細会計・ledger 対応は不要になるため小さい。

ただし、同等の探索完全性を満たす場合に限って「未会計の委任を受理しない」という安全性は同等。P1′では拒否までに消費した子 token の正確な予算会計は得られず、brief の「委任を許して合算」という完了条件も満たさない。prompt 禁止だけでは L6 の代替にならない。

## P2 rulings

**P2 の「command は変更不要」は支持できない。**

- `.claude/commands/rulings.md:58` は `dev_wave_codex.py --stage consult --sandbox read-only` と DW-O01/O02 だけを記載している。
- `tools/dev_wave_codex.py:214–218` と `tools/codex_worker_launch.py:2853–2863` は、plan/consult の `--reasoning` を必須の呼出側入力として扱う。DW-S03 から自動導出しない。

改訂案は `.claude/commands/rulings.md:58` の起動例へ `--reasoning ultra` を追加し、DW-S03 を参照に含めること。model の直書きはせず DW-O01 導出を維持する。

repo 全体の `--reasoning` 検索で、過去記録を除き変更すべき運用上の固定値は他に見つからなかった。plan/consult の規範値は `docs/dev-wave/workers.md:5,10` の変更で揃える。`.agents/skills/` に直接の固定値はない。

テスト内の high/max は任意入力・転送・拒否条件の fixture なので一括置換しない。ultra の正例は単位 A の matrix に追加する。

## P3 next-tasks

`/work/1/SFC/tanab/scripts/next_tasks_consult.sh`：

- `:24`：`effort=${CONSULT_EFFORT:-high}` → `effort=${CONSULT_EFFORT:-ultra}`。コメントも「Codex 相談の既定 ultra、2026-09-30 ユーザー裁定」に更新。
- `:76`：`codex exec` に `-m gpt-6-astra` を追加。
- `:77`：`model_reasoning_effort="$effort"` は維持。明示された環境変数 override の意味を変えない。
- `:83–84`：Claude 分岐は effort 変数を使っておらず変更不要。
- `:23`：締切 1800 秒は維持し、疎通の実所要から評価する。

P3 の受渡し方式は妥当。author が worktree 内の未 commit 一時 path に改訂全文を作り、親が原本を job dir に退避した後、byte 一致で設置する。親は差分と疎通結果を fragment に記録する。

## 未確定・親への質問

実装を確定する前に必要な証拠は以下。

1. root stdout usage は子込みか。子・孫の token 累積値は fork 履歴を含むか。
2. root rollout の spawn 成功結果から、期待する子 ID を漏れなく抽出できるか。孫の `session_meta.session_id` も root ID か。
3. root process 終了時に子 rollout が flush 済みとなる契約があるか。なければ期待 ID と grace の両方で閉じる。
4. 実 sessions_root のファイル数と探索所要。静的検査では実コストを確定していない。
5. 子の guard 発火は L8 で未確認。受領証の model/effort/cwd 照合は guard 有効性の証明を代替しない。

これらが閉じなければ P1 の accepted 実装は未確定と報告する。P1′や権威段 max への変更は、このプランで勝手に採用しない。

## 総括

変更行数は追加・削除を合わせた概算。

| 単位 | 見積もり |
|---|---:|
| A：値、literal、fixture、語彙テスト | 120–190 行 |
| 親担当 workers docs | 約 10 行 |
| B：P1、V6、再検証、ledger、回帰 | 700–1,100 行 |
| B 対案：P1′、検出・拒否・回帰 | 180–320 行 |
| P2：rulings の起動例 | 2–6 行 |
| P3：外部 script | 4–8 行 |

brief の修正点は、**P2 の自動追随前提が誤り**、**B を launcher とそのテストだけに限定すると ledger が漏れる**、**既存 evidence grace は終了後の子発見を扱わない**、の 3 点。さらに P1 の usage 照合・fork 会計・探索完全性は実測待ちであり、現段階で安全に受理できると断定できない。