単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、それを理由に検査全体を打ち切らない。

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/paper-methods-ja/methods.md (**再レビュー対象 1**、fix 後)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/paper-methods-ja/implementation.md (**再レビュー対象 2**、fix 後)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/paper-methods-ja/README.md (親の wave 記録。§5 が 1 巡目の所見 9 件と親の対応表、§6 が pin 前進の取り込み)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-methods-ja-2026-09-20/codex/review-out.md (1 巡目レビューの逐語。所見 1〜9 の原文)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-methods-ja-2026-09-20/brief-s1.md (親の段 1 brief)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/t2304-pin-advance/README.md (**1 巡目の後に main へ着地した pin 前進 [T-2304] の一次資料**。§0・§1・§4 が要点)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/t2795-pair-launcher/README.md (所見 1 の一次資料)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-05/t1905-b10-report/README.md (所見 5 の一次資料、§0)

**巨大 file の扱い:** `docs/decisions.md` (約 5.8 MB) は `grep -n "^## D<番号>\. "` で位置を出し `sed -n` で 60 行以内ずつ読め。要るのは
D1257、D1408、D1936 項 9、D2016、D2134 項 9、D2150 項 1、D2159 項 8・9、D2183。`docs/paper-story/2026-09-20.md` (約 489 KB) は §8 の
exact claim (行 2723〜2807) だけでよい。コードは `grep -n` と `sed -n` で必要な関数だけ読め。

**worktree の状態 (親が 1 巡目の後に変えた):** HEAD は `482f19b88` (1 巡目は `fec4a8187`)。差は [T-2304] の着地 (CCBench pin
`511c9538` → `e9e477ca`、gitlink・`orchestrator/campaign/pin.py` `CURRENT_PIN`・`s8b_approved.py` `CCBENCH_FULL_SHA`、admission policy epoch
の golden 追随) だけで、稿の側の変更は本 dir の 3 file だけ (`git status --short` は新規 dir 1 つ)。submodule は `e9e477ca` に揃っている。
親が実測した点: submodule の `cc/mocc/transaction.cc` に `IZANAGI_MOCC_G2_WITNESS` 系の環境変数参照 4 箇所 (`#if TRACE` 内)、
`patches/instr-mocc-lock-coverage.patch` は同 file への追加 hunk (X / P 計装は pin の tree に無い)、`orchestrator/campaign/p3_s4_loop.py` の
`PIN = "511c9538…"` と `patchharness.assert_pinned_clean(fixed_sub, PIN)`、`axis_mocc_temperature.py` の `PIN = pin.CURRENT_PIN` と
`PROOF_PIN = e9e477ca…`、`s8b_floor_campaign.py` の `resolve_current_floor_protocol`。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す (read-only sandbox では `-o` の file を
書けない。**出力は file に書かず、最終メッセージの本文に全文を書け**)。pytest・build・測定は走らせない (静的検査でよい)。
予算が尽きそうなら途中までの結論を出力形式どおりに書いて終われ。

## これは何のレビューか

自分たちのプロジェクト (izanagi) の論文用文書 2 本 (方法節草稿と実装対応メモ) の、fix 後の焦点再レビューである。1 巡目
(`review-out.md`) が must-fix 4 / should-fix 3 / refuted 2 を出し、親が README §5 の表のとおり反映し、さらに 1 巡目の後に main へ
着地した pin 前進 [T-2304] を取り込んで pin に触れる記述を直した (README §6)。お前の仕事は次の 2 つ。

1. **所見ごとの closed / partial / regressed の対応表** (1 巡目の 1〜7。8・9 は refuted で変更なし、現文が維持されているかだけ見る)。
   親の対応が一次資料と合っているかを、対応文を実際に読んで判定せよ。表なしで「閉じた」と判定しない。
2. **pin 前進の反映の検査。** 次を [T-2304] の README・現行 code と照合せよ。
   - methods 冒頭 / implementation 冒頭の基準 SHA (`482f19b88`、起草時 `fec4a8187`) の書き方。
   - methods §1 末尾 (pin 前進の実施、「探索の解禁を含まない」)。
   - methods §2 の新段落 (pin が動かす identity の層 = campaign ID・cache key・builder bytes・受領証 / 動かさない層 = 較正 record・凍結
     protocol・比較 policy・歴史 golden。旧系列 = K2 の巡・A-1 sized・凍結 v2 g1 の launch・B-4 床値 は前進前の固定 checkout から走る。
     新 main からの再開には系列ごとの整合が要る)。[T-2304] README §1「据え置いたもの」と §4 A・B・「止まる作業」と一致するか。
   - methods §3 の MoCC 段落 (X / P 計装は pin の tree に無く patch。G2 witness は `e9e477ca` の trace 有効ビルドに環境変数で切り替える形で
     含まれる。軽量 witness は hook branch)。「witness」の 2 種 (G2 witness / 軽量 witness) の書き分けが一次資料 (`mocc-witlight-arm-run`、
     `t2774` の arm 名 `e9-instr-wit` = witness on) と矛盾しないか。
   - implementation の MoCC 2 行 (trace-hook 行、温度述語 template 行) と「story 未反映の着地」段落の pin 前進の記述 (fail-closed になる
     経路の名指し、旧系列の固定 checkout)。
   - **pin 前進を「探索の解禁」「mocc の certified 系列の開始」「性能比較の開始」と読ませる文が無いこと。** 逆に、承認済み・実施済みの
     事実を「未承認」「未実施」へ戻していないこと。
3. **fix が新しい誤りを持ち込んでいないか** (regressed)。特に: 所見 1 の対案どおり「内蔵の適応 backoff (`BACK_OFF=1`、`BACKOFF_FIXED=-1`)」
   と書けているか、所見 2 の admission record の field 名 (`admitted` / `use_class` / `unestablished_meaning_macros` / `record_ids`) が
   `paper_story_a2_certification.py` の `_CONDITION_ADMISSION_KEYS` と合うか、所見 3 の B-4 3 点の code 参照 (`p3_b4_raw_record_producer.py`
   の `O_EXCL`、`p3_b4_material_report.py` の `section_7_1_four_classifications_operationalized`、`p3_b4_launcher.py` の `--arm`) と D1408 の
   引用が正しいか、所見 5 の日付 (実行 2026-09-05 / 記録・裁定 2026-09-07)、所見 7 の `workload_argv_observation` の値。
4. **量化と件数の再確認**: README §4 の「D 37 件」「entry 19 件」、implementation の表の行数に触れる文、methods の「6 節」。

## 守らせる不変条件 (これを緩める所見は refuted として扱う)

- 凍結物 (前稿 2 本・story・results 稿・事前登録) は 1 byte も変えない。旧 attempt の判定を取り消さない。protocol status は成否宣告
  ではない。規律 7。方法節に性能値・図を転載しない。pool しない (D1993 項 6)。2 cohort を合成しない (D2157)。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。英訳・新規実験は scope 外。

## 出力形式 (この見出しをそのまま使う。見出しはすべて `##` の階層で書き、`###` を使わない)

## 対応表

1 巡目の所見 1〜9 について、番号 / closed・partial・regressed / 根拠 (file と節、一次資料) / 残るなら対案。

## pin 前進の反映の検査

項目ごとに 一致 / 不一致 / 過大 / 過小 と根拠。

## 新規所見

fix で持ち込まれた誤りや、1 巡目が見落とした must-fix 相当があれば番号付きで (real / refuted、must-fix / should-fix / nit、放置時の
影響 1 行、対案)。無ければ「無し」と書く。

## GO / NO-GO

稿 2 本をこのまま凍結してよいか。

## 総括

10 行以内。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
