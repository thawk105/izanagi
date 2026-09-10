# 段 1 brief — dev-wave-t181-stage6-high

## 依頼 (ユーザー逐語)

> t181で、段6がmax, highでもあまりパフォーマンス変わらずという過去があったと思う。
> それならばhighにしてほしい。

## scope

段 6 の codex review 子の reasoning effort を `high` に確定し、契約 (`docs/dev-wave/workers.md`) と
機械 pin (`tools/check_docs.py`) を同時に更新する。段 2・3・5 の effort は一切触らない。

## 確定済みユーザー裁定

- 段 6 を `high` にする (本 wave の起動指示そのもの)。
- 親は evidence の欠落を承知のうえで進める。証拠を「非劣性を証明した」とは記録しない。

## 段 1 前の実測 (DW-S01。裁定前提の再測)

1. T-181 が測ったのは **段 6 focused review の `max` 対 `high`**。名指し R-1 正例 high 3/3・max 3/3、
   限定負例で偽 R-1 は両 arm 0、資源は max が一貫して大 (`output/insights/2026-07-30_t181-reasoning-ab/`)。
2. **未認証。** `aggregate-uncertified.json` / `verify-uncertified.json` = `experiment_complete:false`,
   `decision:null`、失敗理由は全 10 run の `snapshot oracle replay mismatch`。insight 自身が
   「許される裁定は『この 6 run で劣化を観測しなかった』だけ。非劣性・同等・採用の証明にはしない」
   と明記。`docs/phase3.md` [T-181] も「再走せずに [T-184] の根拠にしてはならない」。
3. **D207 が pin するのは段 2・3=max、段 5=high のみ。段 6 は pin 対象外。**
   `_check_dev_wave_reasoning_effort_pins()` も DW-S02 / DW-S03 だけを exact pin する。
   よって本 wave は「pin 値の引き下げ」ではなく「未規定の段 6 を high に確定する」。
4. 段 6 の現行契約に effort の記載なし。`DW-S06-A` 無記載、`DW-S06-B` は `DW-S05-A` 継承で既に high、
   `DW-S06-C` / `DW-O16` 無記載。T-595 段 3 lens B が既に「現 DW-S06-A は reasoning を規定していない」
   と指摘済み。
5. **docs byte 予算の余地は 4 bytes** (dev-wave 4 文書 aggregate 上限 25,200 / 現在 25,196)。
   workers.md 単体は 5,000 / 4,575。追加には同 4 文書内の削減が必須。上限引き上げは提案しない。
6. 並行 wave `dev-wave-t182-luna-stage3` が同じ workers.md の `DW-S03` を編集予定。節は素だが
   同一ファイル・同一 byte 予算を奪い合う。land 順で片方は必ず再走要。

## DW-O09 pin 閉包 (workers.md の bytes を pin する全経路)

`tools/check_docs.py`: `REFERENCE_LIMITS`(178, 5_000) / `DEV_WAVE_AGGREGATE_BYTES`(254, 25_200) /
reasoning pin literal・finding(264-275) / `CODEX_DEV_WAVE_SKILL_LITERALS`(286) / 節閉包(401,437,473)。
`orchestrator/tests/test_check_docs.py`: 466, 569-571, 1619, 1777, 2205, 4400, 4970, 5007, 5044-5063。
`.agents/skills/dev-wave/SKILL.md:30`、`.claude/commands/dev-wave.md:62-71`。
DW-O10 は不成立 (workers.md は producer 出力ではない)。

## 不変条件

- 段 2・3 の `reasoning=max` と、その exact pin を変更しない。D207 の当該部分は不変。
- 段 5 の `reasoning=high` を変更しない。
- byte 予算 (25,200 / 5,000) を引き上げない。削減で吸収できないなら停止して裁定へ返す。
- 削減先が安全義務 (テスト弱体化禁止・期待赤・波及報告・復元規律など) を削る形なら採用しない。
- 記録に「非劣性が示された」と書かない。「未認証、方向は支持、ユーザー裁定で採用」と書く。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 適用範囲は段 6 の review 子すべて** — `DW-S06-A` の敵対レビュー 2 本と
  `DW-S06-C`/`DW-O16` の焦点再レビュー。T-181 が実測したのは焦点再レビュー prompt 由来の
  benchmark のみで敵対レビュー 2 本は未実測だが、ユーザーの「段 6」を素直に読む。
  代案 = 焦点再レビューだけ high。
- **(P2) 機械 pin を段 6 側にも張る** — D207/T-595 と同型に `DW-S06-A` = `high` を exact pin する。
  代案 = docs 文言のみで pin なし。
- **(P3) byte は同 4 文書内の stale 記述の削除で捻出する** — 候補は F (failures.md:3415) が
  「stale になった」と明記する記述群。安全義務の削除では捻出しない。
- **(P4) 新規 decision を 1 本起票する** — D207 を上書きせず「段 6 は未 pin だったので新規に確定」と
  範囲を限定して記録する。

## DW-G05 成果物影響

- 段 6 レビューの effort 固定は、must-fix へ昇格する所見集合を変えうる → worklog / insights /
  decisions に載る所見と land する実装差分が変わる。
- 機械 pin 新設は `check_docs.py` の受理集合を変える → `DW-S06-A` に `high` 以外の effort 値を
  書いた docs を新たに拒否する。
- (P3) の削除は、削除した規範が指す再発検知を失わせうる → 削除対象は「既に別節が担い手」と
  実測できるものに限る。

## 成果物

- `docs/dev-wave/workers.md` の `DW-S06-A` (+ 必要なら `DW-S06-C`) に `reasoning=high`。
- `tools/check_docs.py` の段 6 exact pin と `orchestrator/tests/test_check_docs.py` の正例・負例。
- spool fragment: decisions 1 本、worklog 1 本。
- insight `output/insights/2026-08-08_t181-stage6-high/`。

## 分割方針

編集面は `docs/dev-wave/workers.md` (親が docs 本文として編集) と
`tools/check_docs.py` + `orchestrator/tests/test_check_docs.py` (Codex `role=author` 実装子 1 単位)。
docs 本文と実装面は所有が素なので単位 1 本で足りる。

## 環境

受入全走は Pegasus の `python3 tools/run_tests.py` (追加 flag なし、dispatch recipe)。
親が repo root で実行する。
