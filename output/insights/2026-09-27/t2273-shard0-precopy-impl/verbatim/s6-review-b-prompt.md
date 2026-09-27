単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/verbatim/T-2273-origin.md — 依頼の逐語 (本題の実装だけ、仮想リスク向けの gate・検査・台帳・一般化は scope 外)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s4-ruling.md — 段 4 裁定 (プラン v2、変異、計測の事前登録)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s5-author-l.patch — レビュー対象の実装差分 (wave 木の commit `677ea17b6`)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s5-author-l-out.md — 実装子の報告。
- wave 木 /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy の orchestrator/tests/conftest.py、orchestrator/tests/test_s8b_oracle_driver.py の該当範囲。

書込可能な tmp は無い。静的検査だけでよい (test の実走は親が行う)。予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終われ。

## レンズ B — 過剰・削除 (DW-S03 と同じ)

実装を守らず、削れるもの・足りないものを探せ。特に:

1. 本題 (D2253 項 2 の形) を超える機構・検査・分岐・例外経路・test assert は無いか。より短い等価な実装を示せ (行数・分岐数)。`module.ROOT != repo_root` の検査、`result.json` の失敗記録、`_T080_VISIBLE_OUTPUT_JOB_ATTR` の 1 回性 guard、helper の待ち loop は、それぞれ本題に必要か。
2. identity の式が conftest と test module に二重にある点: 片方に寄せられるか (寄せると import 関係が増えるなら現状でよいか)。
3. T1 は最小か: assert の冗長、setup の過剰 (conftest の tmp 複写・`importlib.util` 読込み) に、より短い等価な形があるか。既存 test 基盤 (`_load_suite_conftest` 等) で置き換えられるか。
4. 逆に足りないもの: 裁定 v2 の要求 (hook での起動、1 回性、写しからの複製、終了時削除、既存模擬 hook fixture の no-op 化) の取りこぼし。本物の hook を shard spec 付きで呼ぶ既存 test が他に残っていないか (grep で全列挙)。
5. 放置時に成果物 (受入の緑・所要、fixture の中身) の値がどう変わるかを 1 行で示せない所見は nit とせよ。

## 出力形式

見出し「## 所見」(各所見に ID B1〜、重大度 must-fix / should / nit、file:line、根拠、修正案)、「## 削れるもの」、「## GO 判定」(GO / 修正後 GO / NO-GO と 1 行理由)、「## 総括」(5 行以内)。
