# [T-2791] mocc G2 観測の上流 (ccbench 本家) 向け報告案 — 英語 issue 本文案と、各文の一次資料対応表 (送信しない、修正 PR は見送り)

authority: none
default_effect: no-state-change

作成 2026-09-20 (wave `dev-wave-t2791-mocc-upstream-report`、着手時 local main `947fd160ab44e6ae82b6eab56ee8d70813fda31d`)。docs のみ・実装差分ゼロ。
job dir は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2791-mocc-upstream-report/` (brief・裁定・codex 逐語・静的検算の artifact)。

**還元判断: ユーザー確認待ち。** 上流への送信・push・issue 起票は人間の手番 (D2148 項 13、D16)。AI は本文案の準備まで。

## 0. 何のための資料か

D2148 項 13 の裁定 — 「上流向けには観測事実と限界を示す報告までとし、修正 PR は見送る。G2 signal の再現を根因確定とせず、witness on で読み値の出所照合が
未達であること、hook / verifier 仮定の分岐が残ることを明記する。AI は報告案の準備まで、送信は人間が行う。診断 patch の取り込み・pin 前進・certified 昇格は
本項で認可しない」 — に対する AI 側の成果物。

- `report-draft.md` — 英語の GitHub issue 本文案。各文に `[S-nn]` を振ってある (送信時に落とす)。
- `evidence-map.md` — `[S-nn]` ごとの一次資料 (path と SHA-256、該当節)。draft に書いた事実命題はすべてこの表に出所がある。
- 本 README — 位置づけ、書いたこと・書かなかったこと、段 6 レビューの所見と反映、送信者への注意。

## 1. 書いたこと (観測事実と限界だけ)

1. 4 つの観測 ([T-2774] torn-read probe 5 arm × 40 + 2 arm × 56、[T-2779] 3 arm × 120、[T-2780] pilot 1 cell、軽量 witness 4 arm × 60) と、経緯としての
   [T-1892] 5/42・[T-1943] 1 cell を、producer・計装・witness・`BACK_OFF` ごとに表 A〜C に分けて件数 / 分母 / Clopper–Pearson 区間で書いた。合算値は
   [T-2774] README が自ら計算した 7/120 (参考値) 以外置かない (規律 7)。
2. 「witness off の producer でだけ G2 signal が再現し (`BACK_OFF=0` でも `=1` でも: [T-2779] backoff arm 2/120、軽量 witness off-bo1 1/60)、witness on では
   0/40・0/40・0/56・0/56・0/60・0/60・0/1・0/1」の観測。依頼文の「`BACK_OFF=0` かつ witness off でだけ」は一次資料 (C §3.2、D §2.2) と食い違うので、
   一次資料に合わせて「witness off でだけ、BACK_OFF は 0 / 1 の両方」と書いた (段 6 レビュー must-fix 1、F1: docs は一次資料と一致するまで根拠にしない)。
3. trace-enabled build の条件 (pin `511c9538` は不変、候補 `e9e477ca`、producer `058d0c4e`、X/P 計装 patch の sha、configure define、workload argv、toolchain)。
4. 上流 master (local mirror `50c7946d`) と `e9e477ca` の `cc/mocc/transaction.cc` の差分が +141/−0 で非空の追加行が全部 `#if TRACE` 内であること (本 wave の静的検算、
   job dir `artifacts/mocc-transaction-master-to-e9e477ca.diff`)。上流 master そのもので走った走は無い、と明記。
5. signal 走 21 件 (5 + 7 + 7 + 2) の共通の形 (cycle 1・長さ 2・両辺 rw・integrity clean・commit 版が同 epoch で tid 差 1・key は小さい id)。
6. [T-2774] §3 の静的順序論証 (cold 読みの (i)、validation の 2 load の (ii))。「観測と整合する静的読解であって、実行順序の観測でも根因でもない」「分岐 (2)(3) を
   排除しない」を同じ節に置いた。行番号は `e9e477ca` の現物で照合済み。
7. 診断 patch の結果 ([T-2779] 診断 arm 0/120、未調整片側 Fisher p = 0.030) は「観測」として置き、「修正案として提案しない」「2 変更が束ねられ寄与を分離できない」
   「witness on かつ signal ありの条件で走らせていない」を同じ節に書いた。
8. 未達 2 点を明記: (a) hook / verifier 仮定の分離 (三分岐 = 実装 / hook の記録 / verifier の版順序仮定) が未達 (S-04、S-25、S-44)、(b) witness on の読み値の
   出所照合が未達 (S-28、S-45)。
9. 0 件を不在証明としない (S-46)、非有意を同等性としない (S-47、S-32、S-34)、性能値を書かない (S-09、S-49)、「同一 binary」と書かない (S-51)。

## 2. 書かなかったこと

- 根因の確定、修正提案、上流への依頼事項 (S-62 で「何も求めない」と明記)。
- 機体の CPU model・memory (一次資料の bindings に無い)。上流 master の後続 commit との差分、master 実走の結果 (どちらも無い)。
- 軽量 witness 2 走の thread id (一次資料に無い)。性能値。率の合算 (規律 7)。

## 3. 段 6 レビュー (read-only、Codex gpt-6-astra、レンズ = 上流の読者に誤読させる文・禁止された主張の混入・数値の一致・静的読解の行番号・英語の定義順)

軽量版 (DW-C00: 一次資料から事実を再抽出する docs-only) なので段 2・3 は省略し、段 6 の独立 read-only レビュー 1 本 + 焦点再レビュー 2 巡で閉じた。
逐語は `verbatim/` (s6-review-1 / s6-focus-1 / s6-focus-2 と各 prompt、所見ごとの対応表 s6-fix-table)。

- **1 巡目 (review):** must-fix 8・should 5・nit 1、NO-GO。全件 real として親が本文を直した。主な訂正: (1) S-03「BACK_OFF=0 のみ」→ witness off なら
  BACK_OFF 0 / 1 の両方で signal (§1 項 2)。(2) 「21 件全部 commit tid 差 1」→ 20 件、[T-2779] B2/069 は差 2 (`v_ver` (59,2577) / (59,2575))。(3) 「これまでの全走で
  21 件」→ 表にした 4 実験の合計に限定 ([T-1892] 記録の先行 pilot 1 件は含めない)。(4) 計装 patch の 3/40 対 2/40 を「率を変えなかった」と書かない (p = 0.500)。
  (5) 静的読解 (ii) の前提の英訳を原典で確定できない → 2 巡目へ。(6) S-05 の「master と TRACE 追加だけの差」を e9e477ca の 1 file に限定。(7) 軽量 witness で
  lock 保持中に残る処理 (decode・abort・push・reserve) を明記。(8) 0 件 arm の説明から「率 0.02–0.06」を削除し CP 上限だけに。
- **親の再計算 (DW-O16):** 21 走の verifier.json を機械集計 (`artifacts/recheck_21_cycles.{py,log}`、evidence-map R1)。同 epoch 21/21、tid 差 1 = 20、差 2 = 1、最大 key
  0x55、2 reason 辺 2 件は draft と一致。**追加発見: `integrity.clean` は true 16 / false 5** — false 5 は [T-2774] の計装 patch 無し 2 arm の走で、違反 counter は
  全 0 だが verifier の `clean()` が X/P の text evidence の存在も要求する (model.py `Integrity.clean()` / `certification_gate_satisfied()`)。draft の「integrity checks clean」を
  「counter 全 0、`clean` flag は 16 / 5」へ訂正した。
- **焦点再レビュー 1 巡目 (focus):** closed 11 / partial 3 / regressed 1、残 must-fix 2、NO-GO。(a) S-55 の前提を「同義の英訳」と確定できない (plan 24 行の「互いの read
  key」は一義的でなく、README §3 の「相手の read key」は操作指定と矛盾) → plan の操作指定 (W は y を読み x だけ書く、R は x を読み y だけ書く、x ≠ y、旧 payload 読取は
  相手の更新前に終了、cold・RLL 空、validation の順序) からの条件付き再構成として書き直し、evidence-map に文言の不一致を記録。(b) 親の S-40「true 16 = 計装あり」が誤り
  (true 16 = 計装あり 11 + [T-1892] の計装なし 5、後者は X/P evidence 要件の導入 `e4c949f08` (09-03) より前の verifier 出力)、再計算 script が counter を検査していなかった →
  script v2 (counter 11 個を全走で検査) に改版し再実行、S-40 を「archive された flag は単一 verifier 版の再評価ではない」に書き換え。
- **焦点再レビュー 2 巡目 (focus):** closed 4 / partial 0 / regressed 0、残 must-fix 0、**GO**。
- 実装差分ゼロ (probe・runner・verifier・patch に触れていない)。変異 matrix は DW-S04 により免除。

## 4. 送信者への注意 (人間手番)

- `[S-nn]` の tag を落としてから貼る。文を直すときは `evidence-map.md` の出所へ再照合し、事実命題を足さない。
- 本文案は「これらの commit は執筆時点で GitHub 未 push」と書いている (S-13)。送信前に、参照する commit (`e9e477ca`、`5b02546f`、`058d0c4e`) の公開状態を
  確認し、公開していないなら S-13 の記述のまま送るか、先に push するかを決める (push は D2150 項 1 / D16 の人間手番)。
- 上流 master との差分 (S-14) は local mirror の `origin/master` = `50c7946d` (2026-06-28) に対する値である。送信時点の master が進んでいれば「as of 50c7946d」の
  限定のまま送るか、再計算する (再計算は `git diff <master> e9e477ca -- cc/mocc/transaction.cc` の 1 回)。
- 生 trace や verifier JSON を添付する場合は job dir から取る (evidence-map §0.3)。repo 内の verbatim は行末空白の正規化で原本と bytes が異なる場合がある
  ([T-2779] insight の `whitespace-errata.json`、witlight insight の `NORMALIZATION.md`)。

## 5. 一次資料

`evidence-map.md` §0 に全部 (repo tracked 15 file の SHA-256、ccbench submodule の blob / commit、job dir 原本 6 種の SHA-256)。
