---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2724-ax-delegated
seq: 1
---

## {{D:t2724-ax-delegated}}. 凍結 v2 g1 の承認 A と active pointer X は AI が作る — 批准 attestation を「`AI-Agent: none` 逐語」から「記録済みの委任裁定 + 構造化 AI trailer ちょうど 1 行」へ改める (D2120 項 2 (b) と D2174 項 4 を supersede)

**決定 (ユーザー裁定 2026-09-20 13:2x JST、本 wave が履行):**

- 承認 A (`output/s8b-freeze/approvals/<世代 sha256>.json`) と active pointer X (`output/s8b-freeze/active/<自身の sha256>.json`) は
  AI が作る。D2120 項 2 (b) の「いずれも逐語 `AI-Agent: none` の人間 commit」と D2174 項 4 の「ユーザーが実施する。AI は作らない」は
  本決定で supersede する。record の bytes は Codex author (D95) が `output/insights/2026-09-18/t2724-freeze-g1-gen/README.md` §5
  手順 2〜5 と同じ形 (canonical JSON、keys ちょうど 4 / 5、filename 規則、create-only) で書き、commit は親 (Claude manager) が機械的に
  代行する。A / X の commit は非 merge・diff 1 file・X^ == A・A と X の間に他 commit を挟まない、を保つ。
- 批准側 `orchestrator/campaign/s8b_ratified_freeze.py` の `_assert_user_commit` (approval / pointer / revocation / cancellation の
  導入 commit 検査、C1-6) は「非 merge・H ancestry・`AI-Agent` trailer が**ちょうど 1 行**で、その 1 行が逐語 `AI-Agent: none`
  または `docs/ai-provenance.md` の必須形式に適合する構造化 trailer」を要求する。none と構造化の併記、2 行以上、trailer 無し、
  規約非適合の構造化行 (product / model / reasoning / role の順と許可値、予約語 product、`model` / `reasoning` の `none`)、
  key の大小文字違い・末尾空白 (raw 行の byte-for-byte 検査) は従来どおり拒否する。
- attestation の意味: 発効 commit の真正性は「本決定 (記録済みの委任裁定) + 構造化 AI trailer + 導入 commit topology」が担う。
  `AI-Agent: none` 逐語は人間 commit の証明ではなく (hooks README F6a)、本決定以後は「人間が commit 操作を行った」ことを主張しない
  (承認の主体はユーザー、record の作成と commit の実行は委任された AI)。論文で g1 の批准をどう記すか (呼称・独立性・主張への影響)
  は本決定の対象外で、必要なら別途諮る (10:2x の裁定控えには、提示時に AI が明示しユーザーが承知した帰結として「AI が自己承認した
  世代になる」の記録がある)。
- 不変: 世代導入 G の `generation-commit-none` 拒否、diff 1 file (`approval-commit-diff` / `pointer-commit-diff`)、X^ == A
  (`pointer-approval-parent`)、`user-commit-merge`、`user-commit-ancestry`、`_unique_introduction`、`history-mutated`。
  hook (`hooks/guard_write.py` の `output/s8b-freeze/` Write 拒否) は変えない (誤操作抑止のまま。bytes は Bash 経路で書く、G と同じ)。
  鍵署名・床値・certification・W-4 / W-5 は本決定の対象外。規律 2 は緩めない。
- `approver` は「ユーザーの委任と裁定日」を記す文字列とし、批准側は値の書式を検査しない (従来どおり)。
- 帰結: A / X の 2 file は B-10 の freeze-tree pin (`EXPECTED_FREEZE_TREES_SHA256`、D2166) の対象 dir に入るので、pin を A / X 込みの
  値へ更新する。扱いは D2166 を引き継ぐ (旧 cohort の記録は不変、新 phase の事前登録成立でも本走許可でもない) が、手続は同一ではない:
  本 wave では A / X 導入の事前授権から必然となる期待変更として、赤を見る前に更新対象 3 literal を固定し、独立レビュー・変異 2 件
  (test literal だけ旧値 / job 定数だけ旧値)・負例 4 件 (別 file 追加 / 1 byte 変更 / A 欠落 / X 欠落) を条件に同 wave で更新する。
  未実施の検証は未実施と記録する。実 repo を root にする consumer test (growth hold 下の 6 node) の「`no-active`」期待値は発効後の
  実測値へ書き直す (弱体化ではなく新しい真値。tmp repo 側の `no-active` 負例は残す。hold の登録は不変だが通常受入の所要は未検証)。

**理由・採らない案:** 人間 commit を待つ形 (D2174 項 4) は、`git status` 空の前提が未追跡 dir で成立せず、承認の内容 (床の採用、
候補 bytes、世代導入) はすべて D2120 項 2 で裁定済みで人間が新たに判断する事項が無い。AI が `AI-Agent: none` を書く案は
provenance 虚偽 (規約 35 行) で採らない。構造化 trailer を「1 行以上」で受理する案 (10:2x の控え) は、A / X が単一の author 構成で
作られる事実と合わず、ちょうど 1 行の方が受理集合が狭い。hook の Write 拒否を正規経路に限って解除する案 (同控え) は hook が
認証防壁でない以上、発効の真正性に寄与せず変更面を増やすだけで採らない。`role=author` / `product=codex` を必須にする案は、
裁定の文言 (規約に適合する構造化 trailer) より狭く、revocation / cancellation を将来別構成が作る余地を無くすので採らない。
