# 段 4 裁定 (親) — [T-2756] pin 更新項の再承認材料 3 点

裁定 inbox 再走査: local main は wave 開始時と同じ `38353207f` (新 commit なし)。段 1 以降に効く新裁定は無い。

## 段 2 plan の訂正 6 点 → すべて real・採用
1. D986 全件閉塞の断定を削る (残余 = 解決不能な CMake 間接値は拒否しない。親の検算: D774 (2026-08-25) がこれを裁定、T-1584 §6 R5 が留保、[T-1644] が見送り台帳で据え置き)。
2. preprocess 引数の正確な記述 (`-E -P -dD -nostdinc -Werror=undef` + BUILD_FLAGS + defines、空入力の環境 prefix 剥がし)。
3. report の合否表現 (拒否時は report JSON が出ない → `runs.json` に rc / stderr / `report_emitted` を親が記録)。
4. 134 file は文字列検索集合であって依存閉包ではない。
5. F (テスト) は機械的更新ではない (旧 pin control を保つ)。
6. P5 の追記は spool `### 見送り追記` で行い phase3.md を直接編集しない。

## レンズ A (正しさ境界) — must-fix 8 / nit 2
| # | 判定 | 採否 | scope | 裁定内容 |
|---|---|---|---|---|
| F1 clang の分類と「3 本すべて成功」未達 | real | 採用 | 内 | 材料 (2) の書き方 = 「GCC 11.4 / 12.3 は各 16 context で pass。clang 14 は環境 prefix 不一致で rc=1、比較未完了。候補差分の不一致を検出した結果ではないが clang での同一性は未確認。事前計画 (P2) の『3 本すべて成功』は未達」。総合合格へ置換しない。P2 を訂正 |
| F2 login g++ の version body digest | real (親が実測: `/usr/bin/g++` と `/usr/bin/gcc` の `--version` 全文 body の sha256 = `b713e6ab…` で policy と一致、g++-12 = `75f4ea26…`、clang++ = `4b53fd45…` は不一致) | 採用 | 内 | 「login GCC 11.4 の version-body digest は mocc pilot policy の期待値 (D1487、pilot receipt 37 件と同じ) と一致するが、admission toolchain 全体の同一性は主張しない」 |
| F3 16 context の分岐被覆表 | real (親が検算: 候補の条件付き指令は `#if TRACE` 8・`#if ADD_ANALYSIS` 17・`#ifdef RWLOCK` 15・`#ifdef MQLOCK` 11・`#if TEMPERATURE_RESET_OPT` 1・`#if BACK_OFF` 2、`#else`/`#elif`/`#ifndef` は無し (行 616 の `// #else` はコメント)) | 採用 | 内 | 表を材料 (2) に載せ「16 件・実効 4 構成・出力 2 種、両枝を検査したのは BACK_OFF だけ」と併記 |
| F4 D986 全面閉塞は断定不可・裁定と実装の関係 | real | 採用 (文言) / 修理・許容判断は scope 外 | 内 (記載) | 「D986 の 3 穴のうち単純形は T-1584 が修理。解決不能な間接値は D774 で『供給と主張しない・拒否しない』、[T-1644] で据え置き。本資料は D986 全面閉塞を主張しない」。新しい許容判断も修理もしない。裁定パッケージは新設せず、既存の [T-1644] (再訪条件つき見送り) を指す |
| F5 保証範囲 8 点 | real | 採用 | 内 | plan の 9 点・T-1584 §6 の留保 (`#undef TRACE`/`#define TRACE 1` を両 commit に置けば pass する = 完全除去の証明ではない、report は proof chain 外 (R1)、`__has_include` と `-nostdinc` (R3)) と統合した逐語を材料 (2) に置く |
| F6 候補の来歴 | real | 採用 | 内 | 4 commit の本文・trailer を逐語で載せ「全部ユーザー作成」「provenance 監査済み」と書かない。witness は TRACE-only の payload watermark (G2 discriminator 用)、D18 の性能 variant 昇格候補ではない、TRACE=0 一致から TRACE=1 の意味的無影響・正しさを導かない、unknown は補完しない |
| F7 「mocc 単独」「未 push」の対象限定 | nit | 採用 | 内 | 「mocc 単独 = 現 pin から候補までの追加変更範囲」。共有 `include/trace.hh` は両端で同一 blob `570e35e3…`。GitHub 到達性は親が `ls-remote` で実測 (候補 OID・branch とも不在、現 pin は `izanagi-trace-pin-t816` / `izanagi-trace-t816-fn2` として存在)。worktree の origin は primary の module store |
| F8 検査結果と裁定の分離 (冒頭) | real | 採用 | 内 | 冒頭と材料 (2) 直後に「本資料は判断材料であり承認・実行ではない」の段落 |
| F9 検査器の版の束縛 | real (親が検算: checker blob `79dc9bbd…`、source_digest blob `0f062df9…`、worktree は clean で HEAD と一致) | 採用 | 内 | `runs.json` に時刻・argv・cwd・host・HEAD・submodule HEAD・blob sha・requested/resolved compiler・rc・stdout/stderr の bytes と sha256 |
| F10 wall / bytes の用途 | nit | 採用 | 内 | wall は索引のみ、本文の結論に使わない |

## レンズ B (波及表) — must-fix 6 / nit 2
| # | 判定 | 採否 | scope | 裁定内容 |
|---|---|---|---|---|
| M1 134 は文字列集合、集合外の依存 ≥13 | real | 採用 | 内 | 「集合外の判断根拠・間接依存」表を材料 (3) に追加 (decisions.md、raw-manifest 3 本、artifact-manifest、completion-receipt、ident.py、source_digest.py、paper_story_a2_certification.py、env_contract.py、calibration_verify.py、s8b_floor_campaign.py、test_s8b_approved.py (gitlink を `ls-tree` で読む、親が検算)、gitlink 自体) |
| M2 凍結 raw-manifest の `current_pin` は 7 桁 | real (親が検算: `"current_pin":"511c953"`) | 採用 | 内 | 骨格行を「短縮 pin + manifest 内 file hash による束縛」に訂正 |
| N1 patch 適用性と適格性 | nit | 採用 | 内 | 文言追加 |
| N2 mocc policy は追随置換で自己比較になる | nit | 採用 | 内 | 「旧比較を保持、新命題は別 policy」 |
| M3 P4 の結論置換 | real | 採用 | 内 | 「pin 前進だけを理由に旧 pin・旧 identity で得た測定事実と当時の判定を無効化しない。新 pin で継続する系列は登録・identity・凍結・consumer・テスト契約を整合させ、明示された再実測を行う。旧証拠の保持は新 pin への保証の移転を意味しない」 |
| M4 較正・floor の境界表 | real | 採用 (表) / 流用の可否は親が既定を推奨し裁定は再承認パッケージに含める | 内 | 既定 = 新 pin 系列で較正値を主張するなら再取得 + 新登録 (規律 7 の「較正」は同一性と無関係な前提条件として残る、D297 合格は TU の binary 同一性を証明しない)。旧 record の流用を認めるかは pin 再承認の一項として提示 (本 wave は決めない、needs input にはしない) |
| M5 追記文 | real | 採用 (レンズ B 案を使用) | 内 | `- [T-167] 【2026-09-17 追記: [T-2756] の候補 commit・直接区間検査の結果と保証限界・pin 更新の波及資料を \`output/insights/2026-09-17/t2756-pin-evidence/README.md\` に記録。本追記は判断材料の参照追加である】` |
| M6 134 / 79 の再現条件 | real | 採用 | 内 | 数値と同じ場所に取得条件 (日付・HEAD・working tree・除外 pathspec・`git grep -l 511c953` が母集合、形別は regex) を書き、script を verbatim に置く |

## 確定した plan v2
- 成果物: `output/insights/2026-09-17/t2756-pin-evidence/README.md` (節順 = 提示目的と現在の結論 / 判定しないこと / 材料 1 / 材料 2 (結果 → 保証範囲 → 分岐被覆 → clang → 過去区間) / 材料 3 (必要作業の一覧 → 層別表 → 集合外の依存 → 134 行は verbatim) / 裁定に残す論点 / 再現情報と証拠索引) + `verbatim/` (report ×2、clang stderr/stdout、runs.json、pin-closure.tsv、pin-impact.tsv、closure script、candidate-commits.txt、candidate-diff.txt、github-ls-remote.txt、clang-probe.txt、parent-brief.md、plan.md、consult-A/B.md、s4-adjudication.md、review-A/B.md、MANIFEST.sha256)。
- spool: worklog fragment 1 本 (`完了` [T-2756] remaining: none、`見送り追記` [T-167] 1 行)。decisions fragment 無し (新しい設計判断なし; 両レンズ・plan とも同意)。
- 実装面差分ゼロ → 変異 matrix 免除。受入全走は実施。
- 不変: gitlink・pin.py・s8b_approved.py・checker・凍結物・事前登録。gate/検査/台帳の新設なし。
- 段 6: レビュー 2 レンズ (A: 正しさ境界 — 保証範囲・候補来歴・判定しないことの逐語; B: 波及表・集合外依存・追記文・再現条件) を書き上がった insight に対して起動。
