# [T-244] 8c 世代予算 gate wave — 逐語と裁定パッケージ (2026-08-01)

本ディレクトリは dev-wave `[T-244]` の逐語成果物である。可変状態の正本は worklog 末尾と
現行 phase doc であり、ここには凍結した逐語だけを置く。

## ファイル

| file | 内容 |
|---|---|
| `brief.md` | 段 1 brief (親の provisional 裁定 (P1)〜(P4) を含む) |
| `s2-plan.md` | 段 2 プラン起草 (codex read-only, reasoning=max) |
| `s3-lensA.md` | 段 3 敵対相談 レンズ A = 受理集合・迂回路・恒真性 |
| `s3-lensB.md` | 段 3 敵対相談 レンズ B = リーク経路と規律 2/3 |
| `s4-adjudication.md` | **段 4 裁定 + plan v2 + 変異事前登録 (実装の正本)** |
| `s5-impl.md` | 段 5 実装子の報告 |
| `s6-revA.md` | 段 6 敵対レビュー レンズ A = 実装の正しさと迂回路 |
| `s6-revB.md` | 段 6 敵対レビュー レンズ B = 受理集合の過剰縮小と運用破壊 |
| `s6-fix-brief.md` | 段 6 所見の裁定と fix 指示 (1 巡目) |
| `s6-fix.md` | 1 巡目 fix 子の報告 |
| `s6-refocus.md` | 焦点再レビュー (所見別 closed/partial/regressed 表) |
| `s6-fix2.md` | 2 巡目 fix 子の報告 |
| `mutation-ledger.json` | 変異本走の台帳 (統合 commit 後の記録 commit で追加) |

## 実装した内容 (D112)

宣言済み禁止 `--max-generations >= 2` の機械 gate 化。承認上限 `MAX_APPROVED_GENERATIONS = 1` を
CLI・`run_trial()`・`_run_workload()` の 3 入口で強制し、`int` サブクラスによる予算偽装を exact 型検査で
塞ぎ、最初の provider 呼び出し前に campaign checkpoint の freshness を検査する。CLI 既定値を
literal `1` に是正した。詳細と保証の限界は D112。

---

# 裁定パッケージ — ユーザー判断待ち

## 1. T-244 本体 (規律 3 の還流設計) — **未解決のまま残す**

本 wave は禁止の機械化だけを行い、「機序を漏らさずに失敗理由だけを次世代へ還流させる」設計は
実装しなかった。段 2 が挙げた候補 A〜D はすべて不採用と裁定した。

| 候補 | 内容 | 不採用理由 |
|---|---|---|
| A | 現状維持 (還流を増やさない) | 規律 3 の設計解ではなく**封じ込め**。次の variant を作らないことで欠陥を発火させないだけ |
| B | `prior_failure_v1.class` (4 値) を planner のみへ | **recipient separation が情報フロー分離になっていない。** planner→coder の `direction × magnitude` は 9 記号 = `log2(9) ≈ 3.17 bit/世代` を運び、4-class = 2 bit を一世代で符号化できる。prompt の no-echo 規律はこの符号化を止めない (D45 は自然文 lint を唯一防壁にしない決定済み) |
| C | 非重複 window (3 件) の集合還流 | **padding 攻撃で匿名化が崩れる。** window の最初の 2 件に既知 class (禁止識別子で決定論的 reject) を詰めれば、3 件目の 2-bit class が一 window で完全復元される |
| D | planner/coder 双方へ 4-class | D39 が排除した勝ち筋逆算経路の直結。coder が accept/reject を oracle にして具体 predicate を探索できる |

**次の設計 wave の第一候補として、段 3 レンズ B が挙げた設計軸を推奨する。**

1. **trusted machine が failure を単調な safety constraint へ変換する** — generator は理由を見ず、
   制約違反候補が機械的に生成・受理されない形にする。規律 3 の reason は次 variant 生成の
   **制約入力**になり、規律 2 の gate 探索用 label は公開しない
2. **failure を post-run auditor だけへ戻す** — auditor は自由生成でなく機械検証可能な
   safety obligation / veto だけ返す。planner/coder は generic reject しか受けない
3. **verifier feedback 前に候補 batch を凍結する** — adaptive one-query-at-a-time oracle を弱める
4. **campaign-global な disclosure / query budget** — `--max-generations` でなく campaign state の
   総 iteration・公開 class 数を束縛する。別 run-root や programmatic 分割で回復させない

**どの候補を採るにせよ、決定には次を必ず含める必要がある** (現行の候補記述はこの水準を満たさない):
誰がどの field を見るか / 一世代・一 window あたりの最大 bit 数 / accept-reject query の総予算 /
producer は trusted machine か外部 role か / run・campaign の origin binding /
正式 report・WAL へ残す参照 / 受容する残余と、不採用案を再開できる条件。

## 2. scope 外だが real と裁定した所見 (実装せず返す)

| # | 所見 | 影響 | 推奨 |
|---|---|---|---|
| X1 | `run_trial(drive=/providers=/preview=)` の注入 seam。1 callable 内で複数 iteration を回す `drive` を渡せば予算検査を素通りする | 機械保証の穴。ただし production 呼び出し元は `main()` だけ | 注入を internal test helper へ分離するか、保証対象外と明記したまま残す (本 wave は後者を採り D112 に明記) |
| X2 | `p3_s4_loop_trigger_gating.drive_iteration()` の直接反復 | 同上 | 8c 専用 wrapper か origin binding を作り、raw driver と 8c admission を区別する |
| X3 | **freshness 検査と state 生成の TOCTOU (並行 race)。** 同じ trial/config の 2 supervisor が同時に検査を通過しうる | 逐次連結は閉じたが並行は開いている | 原子的 campaign reservation の設計。stale lock 処理と異常終了時の解放が要る。並行実行は計測規律が既に禁じ、build 経路は `competing_bench_pids()` が部分的に覆う |
| X4 | `state_from_dict()` が `direction`/`magnitude`/`result` の**値**を無検証で通す。checkpoint は信頼境界の外 (規律 6) なので、任意の長文・機序・prompt injection を planner/coder payload へ流せる | 変異生成の入力汚染。report 表示漏れではない | exact enum / type / range 検査、entry count、iteration 整合、campaign/run origin を roles 呼び出し前に検査する |
| X5 | `delta_pct≡None` は planner 全体の性能リーク防壁**ではない**。絶対 throughput が `current_perf` で planner へ、`baseline` で coder へ渡る | 現行 contract 違反とは断定できない (D51 と role md は本 campaign の baseline を許可) が、`delta_pct≡None` を「planner へ性能値を渡さない保証」と説明してはならない | recipient matrix と世代間情報量を新 D で明示する |
| X6 | **単位の不整合 (real defect)。** `cache_miss_rate_pct` / `abort_rate_pct` には 0..1 の率がそのまま入る一方、planner-v4 の例示は percent 表記である | 100 倍の意味ずれ。proposal と台帳の受理 variant が変わりうる | multi-generation 開放前に修正する |
| X7 | `WhiteboardEntry.result` の閉 enum 化と、role-invalid / auditor-invalid / infrastructure failure を粗分類へ含めるか | S2 候補の入力前提が変わる | X4 と同じ変更単位で扱うのが自然 |

## 3. dev-wave 自己改善 — 予算に収まらず裁定へ返す 3 件

段 8 の自己改善で、本 wave が**実測した** 3 件を `docs/dev-wave/` の既存 leaf 節へ統合しようとしたが、
**予算に収まらなかった**ため契約 (`docs/skill-self-improvement.md`「予算のために安全義務を削除・
弱化してはならない。…意味等価にできなければ変更を止めてユーザー裁定へ返す」) に従い返す。

**予算の実態:** `docs/dev-wave/mutation.md` は 3747 bytes で予算 3750 bytes に対し**余裕 3 bytes**、
`docs/dev-wave/**` 合計は 23991 bytes で hard ceiling 24000 に対し**余裕 9 bytes**。
すなわち reference への追記は**どんな内容でも入らない**状態である。圧縮を 3 巡試したが、
安全義務を落とさずに 600 bytes 以上を空けることはできなかった。

**返す 3 件** (いずれも台帳側 = `docs/failures.md` には反映済みなので、情報は失われていない):

| # | 統合先 | 内容 | 実測した根拠 |
|---|---|---|---|
| I1 | `DW-M08` | 失敗 node の**抽出元を中継コンソールでなく実行体の stdout 成果物にする**。dispatch は行頭へ接頭辞を付けたうえ `omitted_bytes` で切り詰めるため `FAILED` 行が残らない。成果物が無い・`rc != 0` で 1 行も取れない場合は SURVIVED / AGREE にせず停止する。baseline にも同じ抽出を通す | F65 の再発。**独立 2 例** (本 wave と並行 [T-118] wave。後者は 16 変異すべてが偽 SURVIVED) で `DW-G03` の族一般化条件が成立している |
| I2 | `DW-M05` | harness は起動前に総所要を見積もる。台帳を 1 件ごとに flush して resume 可能にし、**起動時に対象ファイルが HEAD と一致するか検査して不一致なら停止する**。SIGKILL は捕捉できないのでこれが残留変異の唯一の機械防壁 | F32 の 3 度目の再発 (2026-07-27 / 07-30 / 08-01)。「background で起動する」規律だけでは 3 回とも止まらなかった |
| I3 | `DW-O09` | pin の列挙を**パス文字列だけで探さない**。pin が対象を role 名・key 名で参照する台帳 (`review_ledger.py` の `SOURCE_FILE_SHA256`) はパス検索で取りこぼす。対象の識別子でも検索する | 本 wave の親が実際にこれで brief の前提 9 を誤り、段 3 レンズ A が訂正した |

**ユーザー裁定が要るのは「何を空けるか」である。** 予算値の引上げは提案しない。選択肢:
(a) 既存節のうち陳腐化したものを削る (削除の実施はユーザー裁定に限る、という契約がある)、
(b) D110 の先例に倣い、条件付き reference として `docs/dev-wave/**` の外へ外出しする
(この場合 command 入口の条件 dispatch 表に 1 行増えるため、入口編集条件の判定も要る)、
(c) 3 件とも入れず failures 台帳のポインタ運用に留める (現状。`DW-M05` / `DW-M08` は既に
(F32) / (F65) を引いているので、レンズ設計時に台帳を読む運用なら到達はする)。

## 4. 本 wave で確定した事実 (再検討の起点)

- **還流はゼロではない。** `whiteboard` の `result` (`success|fail|rejected`) は既に世代を跨いで
  planner/coder へ届いている。欠けているのは「なぜ」である。「何も還流していない」という前提で
  設計を始めてはならない。ただし値域は閉じておらず (X4)、role-invalid・auditor-invalid・dry-pass は
  whiteboard result にならない。
- **cross-generation の critic チャネルは `prior_reverse` (bool) 1 本だけ**で、それは `drive()` と
  proposal 記録へ行き、次世代の planner/coder payload には入らない。
- **「1 generation/cell は還流が起きない」は fresh campaign の単一 invocation でのみ成立する。**
  これは D106 残余 3 に逐語で記録済みの既知事実であり、残余 1 を失効させる新事実ではない。
  D112 はこの経路を provider 呼び出し前に拒否することで閉じた (並行 race を除く)。
