# [T-338] 投入 gate の規模実測と切り直し wave — 逐語と裁定 (2026-08-18)

`authority: none` / `default_effect: no-state-change` — 可変状態の正本は `docs/worklog.md` 末尾、
設計判断の正本は `docs/decisions.md` の当該 D である。本 dir は wave の一次資料 (逐語) を置く。
branch `worktree-dev-wave-t338-submission-gate`。凍結記録であり、後から書き換えない。

- `package.md` — 裁定パッケージ (ユーザー裁定 3 問 Q-A / Q-B / Q-C と親の推奨)。
- `verbatim/s1-brief.md` — 段 1 brief (親)。規模の実測表と (P1)〜(P4) の provisional 裁定。
- `verbatim/s1-classification.md` — 親の独立 A/B 階級分類 (段 2 子の回答を見る前に確定)。
- `verbatim/s1-p3-measurement.md` — (P3) を決める親の実測。B1 を凍結 bytes 不変で閉じる経路。
- `verbatim/s1-reuse-inventory.md` — 再利用先の棚卸し (D500 決定 (6) の次 wave 段 1 要件)。
- `verbatim/s2-plan.md` — 段 2 プラン起草 (codex、read-only、reasoning=max)。総括 NO-GO。
- `verbatim/s3-lensA.md` — 段 3 敵対レンズ A (正しさ境界と受理集合)。総括 NO-GO。
- `verbatim/s3-lensB.md` — 段 3 敵対レンズ B (全層 scope と「完成」申告の実体)。総括 NO-GO。
- `verbatim/s4-adjudication.md` — 段 4 裁定 (親)。real 11 件 / refuted 1 件 + 部分 refuted 1 件。

## 結論

**投入 gate は実装していない。実装差分はゼロである。** 2026-08-18 のユーザー裁定
(T-338 Q1 = 択 (a)) は「投入 gate を 1 単位で完成」を命じたが、同じ裁定が
「着手前に規模の見積りを実測で出し、**D205 / D220 の水準に触れるなら同 wave 内で範囲を切り直す**」
という条件を付けていた。本 wave はその実測を行い、条件が発動することを確認し、
切り直しを 2 通り試みて、**どちらも承認済み受理述語の緩和になる**ことを独立 3 本の検証子から
突きつけられた。command は「規律 2 を緩める方向の変更は採らない」と明示している。

**pilot は依然として投入不可。** `pilot_submission = forbidden` と D292 の解除権威は 1 bit も
動いていない。D264 の 4 名前非 export も維持されている。

## この wave が確定させたこと

1. **規模。** 独立 3 見積りが揃った — 親 1,650〜3,450 行 (過小と判定された)、段 2 プラン
   2,570〜3,740 行、段 3 レンズ B 3,550〜6,200 行 (6 層接続込み)。いずれも production のみで
   tests を含まない。repo 実測の test/production 比 2.18 を掛けると総計 8,000〜19,700 行。
   D220 が D205 のプロトタイプ基準に照らして過大と判定したのは production 645〜816 行であり、
   本件は下限で 3.2 倍、上限で 7.6 倍。
2. **「階級で切る」戦略は実測で死んだ。** 承認済み要件 63 件 (§6 の箇条 41 + §7.1 の 20 項目 +
   §8 の否定検査を 1 群として数えた閉包) を段 2 プランが**全件独立に分類**した結果、
   D320 の見送り対象 (bytes 級 provenance にのみ効く) と判定されたのは §7.1(19) と
   conformance vector index の digest pin の **2 件だけ**である。しかもこの 2 件は
   manifest への sha256 1 field と既 land pin の読取 1 行で、切っても規模は動かない。
3. **B1 は凍結 bytes を 1 bit も変えずに閉じられる。** これが D500 の状態からの最大の前進である
   (下記「訂正した既存記録」)。
4. **再利用先が確定した** (D500 決定 (6) が次 wave の段 1 要件と定めたもの)。
   `verbatim/s1-reuse-inventory.md` と `verbatim/s4-adjudication.md` §5 が正本。
5. **6 単位の実装分割 (編集 path 素集合) が確定した。** 依存順 `1||2` → `3`,`4` → `5` → `6`。
   4 名前 export は単位 6 の最終 commit だけで行う。`verbatim/s2-plan.md` §7 が正本。

## 訂正した既存記録

**T-139 裁定パッケージ V1 の「回避経路が無いことの実証」を反証した。** 同 package は
「イ (新 exact-byte approval payload) を作らずに B1 を閉じる案は
(a) semantic validator を常時拒否 (受理集合が空) か (b) §7.1(12) の CMakeCache leg を落とす (弱化)
の 2 つしかない」と書いていた。本 wave は**第 3 の経路**を実測した。

- CCBench の `external/ccbench/cmake/Options.cmake:59-67` の `ccbench_universal_definitions` は
  `ADD_ANALYSIS` / `TRACE` を target_compile_definitions として吐く。よって CMakeCache の 2 値は
  各翻訳単位の compile argv として `compile_commands.json` に必ず現れる。
- 凍結済み受領証 schema は `compile_commands` を `fileRecord` (path/size/sha256) として既に持つ。
  validator が bytes を再読できる実体である。
- §6.3 の逐語は第 3 脚を「`cmake_cache` の**申告値** (`CMakeCache.txt` 由来)」と定義しており、
  raw `CMakeCache.txt` の再読を要求していない。
- 承認済み記録項目 §0 が「producer が申告した派生値は、受理集合を狭める方向にだけ使う。
  不一致を拒否理由にし、一致は受理の正の根拠にしない」を既に定めている。

**したがって V1 の イ は不要であり、D320 との衝突は消える。** これは D500 が
「producer を止めている閂」と同定した箇所の直接の解除である。

## 親が訂正した自分の実測

- **(P2)** — 「述語を保存して機構だけ粗くする」は不成立。台帳を truncate / 削除して過去の使用を
  現在集合から外し同じ `(family_root, ordinal)` を再作成すれば、現 tip の `k = 1` も
  初出 commit の祖先性も成立する。段 2 プラン・レンズ A・レンズ B が**独立に 3 本とも**到達した。
  さらに承認済み記録項目 §0.2 が同じ穴を既知として逐語で記録していた
  (「前版の現 tip 検査は過去行を削除して同じ `(family_root, ordinal)` を再利用した履歴を受理した」)
  — 親はこれを読まずに (P2) を書いた。
- **(P1)** — §6.7 / §6.10 / §7.1(14)(17) を B 級としたのは誤り。いずれも raw 証拠のすり替えと
  attempt 脱落を直接防ぐ A 級である。
- **「§6.10 の hardening は既存実装で無料」は誤り。** 承認済み要件は「path の**各 component** を
  `O_NOFOLLOW` で辿る」だが、`orchestrator/qualification/artifacts.py:89` は
  `os.open(path, O_RDONLY|O_NOFOLLOW)` で**最終 component だけ**を守る。component ごとの走査は
  同 file の `_mkdir_parents` (`:360-375`、書込経路) にしかない。親が直接照合して確認した。
- **「duplicate key 拒否は `load_json_strict` で無料」は誤り。** 同関数 (`:541-555`) は
  duplicate key 拒否に加えて canonical bytes と末尾 LF を要求する。承認済み T-139 契約が
  canonical bytes を要求するのは `schedule_table` (§6.6) / `argv_raw` / a13 台帳の JSONL 行
  (§6.7 脚 5) だけで、受領証本体には無い。流用すると受理集合を承認なしに狭める。
  親が `grep -n canonical` の全 11 hit を確認した。
- **「Q2 は producer 段でないため非閂」は誤り。** D500 は必須 kill 2 件目
  (親系列 ID の自己申告による累積有意水準のリセット) の kill を全履歴 validator の責務とする。
  本 wave はその validator を作る wave なので、Q2 は直接の受入条件である。

## この wave が主張しないこと

- 投入 gate の実装。コード・テスト・schema・凍結 artifact の変更はゼロである。
- pilot 投入の解禁。解除条件の中身も定めていない (D292 の境界を動かさない)。
- certified 選択の値、材料レポート、proof chain、既存 gate、受理集合の変更。いずれも不変である。
- D229 決定 (8) の必須 kill が達成されたこと。Q2 は未裁定のままユーザーへ返す。
- B1 の閉じ方の確定。Q-C としてユーザー裁定へ返す (親の推奨は (P3) の採用)。
