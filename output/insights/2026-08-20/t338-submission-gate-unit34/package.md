# [T-338] 投入gate 単位3 (semantic validator)・単位4 (全履歴検査 + attempt authority) 実装 — 一次資料

## 対象

D509 決定(7)の6分割 (`docs/decisions.md:21151`付近) のうち、依存充足済みの単位3 (semantic
validator と申告値の拒否専用化)・単位4 (全履歴検査と attempt authority) の実装。単位1/2は
`orchestrator/submission_gate/` に実装済み (commit `94aa3a54`→fix `6bd9e724`→`ad828076`)。
単位5(writer+conformance vectors)・単位6(統合+4名前export)は依存未充足のため対象外。

確定済みユーザー裁定 (`docs/archive/worklog-phase3-0819-676.md`、D509決定8): Q-A=択(a)計画通り
最後まで実装、Q-B=D229決定(8)必須kill3件はvalidator/consumer段の受入条件、Q-C=B1は`cmake_cache`
申告値の拒否専用化で閉じる。

## 段2 codex plan

`s2-plan.md` (単位3/4の実装地図)。P1(`_git.py`拡張)・P2(attempt authority=a13台帳限定、
family_root↔series_id対応式は作らない)・P3(単位3が汎用pointer helperを持つ)いずれも採用。
規模再見積り: 単位3 production 1,650-1,950行・test 1,250-1,650行、単位4 production
870-1,160行・test 700-1,000行 (旧見積り [`output/insights/2026-08-18_t338-submission-gate-sizing/`]
は旧ファイルレイアウト前提で陳腐化と判定)。ただし段5 authorへ条件付きNO-GO
(受領証`preregistration`の8key/9key不一致、a13 JSONL row schema未確定、family_root↔series_id
対応未確定)。

## 段3 敵対相談2レンズ

レンズA(正しさ境界)・レンズB(整合・実効性)ともNO-GO。レンズAが5系統のmust-fix
(8key/9key adapter比較不足、深凍結漏れ、canonical bytes未照合、root identity pin欠如、
DW-M01単一理由性不成立4件、存在しない関数名`_require_commit_object`)を発見。レンズBが
D509上限6,200行への予算接近リスク (単位1-4累計4,667-5,257行、残り943-1,533行) と報告規律
(「投入gate完成」と報告しない)を発見。

## 段4 親裁定 — 一次資料検索でNO-GO理由2/3件を解消

段2/3のNO-GO理由3件のうち2件を、**親が`docs/decisions.md`のD282を直接検索して解決した**
(`s4-adjudication.md`)。record-items-v2.md自身は「a13台帳のrow schemaはvalidatorが行う検査を
定めるだけで台帳自身のschemaは定めない」と明記しており、その定義はD282
(`docs/decisions.md:12941-12958`)の`alpha_reservation`blockにあった: `ledger_path =
"output/registry/t139-alpha-reservations.jsonl"`、`family_root =
"dce4ae4fed6f4fb33747165c5b92c16d01822850"`(D262 fold commit、固定literal)、row schema
(exact4key: family_root/kind/ordinal/schema_version)、canonical serialization全定義。現物
`output/registry/t139-alpha-reservations.jsonl`のsha256がD282の`ledger_blob_sha256`と一致する
ことも確認した(commit `87cd8d4a`で導入済み)。

**family_root↔series_id対応は不要と判明した。** family_rootはD282の固定literalであり、
producerが選べない。kill2(D229決定8、親系列ID自己申告によるα累積有意水準リセット)の防御は
「①family_rootの固定literal reject-only比較、②(family_root, ordinal)の全履歴一意性」の2点だけで
完結し、series_id/parent_series_idは一切関与しない。対応式が無いことがP2設計の意図そのものである。

残る1件 (8key/9key不一致) はadapter設計の拘束強化 (binding.recordとの全field比較 +
`assert_intact`呼出しを必須化) で解消し、**段5 authorをGOと裁定した**。

## 段5 実装

2並列codex author (専用worktree、`dev-wave-t338-unit34-u3`/`-u4`)。単位3: production 2,386行・
test 868行 (統合commit `1fda2045`時点)。単位4: production 813+255(`_git.py`追加)行・test 587行。
**この段でT-1362着地後の`--stage author/fix`が`--reasoning`明示指定を拒否するargv変更を実地で
発見・修正した** (旧memory `dev-wave-codex-argv-stage-constraints`を訂正)。

## 段6 敵対レビュー・fix (3巡+baseline修正)

- レビュー2本 (裁定準拠監査・独立コードレビュー) がいずれもNO-GO。実所見: correctness raw検査の
  fail-open (D229決定8 kill3に直結、blocker)、kill2 fixtureが検査対象へ未接続 (両レンズ独立指摘)、
  `replaces_attempt_id`循環未検査、A03失敗のstring prefix帰属、authority/IO非同一snapshot(TOCTOU
  2箇所)、translation_units検証不足、CCBench対象プロトコル誤り(`cc/mocc/util.cc`ではなく
  `cc/silo/util.cc`が正、`ShowOptParameters()`の実出力で確認)、event directory容量上限なし、
  テスト空証明複数件。
- fix1 (`643aee9f`) で上記を解消。焦点再レビューがNO-GOを継続し、新規に`translation_units`の
  fail-open fallback (producer完全制御データだけからdigestを合成でき非存在ファイルでも受理される)
  を発見。fix2 (`7fb6e0c9`) で該当fallback関数を削除しfail-closed化。
- 変異harnessのbaseline走行が**単位3/4に対する本wave初の実pytest実行**となり、production非関与の
  test fixtureバグ4件 (`test_t338_submission_gate_unit4.py`のみ) を検出。fix3 (`f8821148`) で解消。
- 変異matrix (11変異、`mutation-spec.json`) 最終結果: **baseline PASSED、11/11 KILLED、
  SURVIVED 0、MISMATCH 0**。D229決定8のkill2(M1/M2)・kill3(M3/M4)を含む全項目を実地KILLEDで確認。

## 成果物影響

certified選択・材料レポート・proof chain・凍結bytes・受理集合は不変。単位3/4は単位6の統合commit
まで`verify_receipt`等のtop-level APIへ配線されない非公開の構造的検査部品であり (D264の4名前は
引き続き非export)、「投入gate完成」ではない。`pilot_submission = forbidden`/D292は1bitも動いていない。

**規模の申し送り (重要):** `orchestrator/submission_gate/*.py`の実測production合計は**5,608行**
(`__init__.py`含む、`wc -l`実測)。D509決定(2)の上限6,200行に対し残余592行のみ。単位5(writer+
conformance vectors)・単位6(統合+4名前export)のbrief起草時に規模の再実測と、必要ならユーザーへの
中間報告が要る。

## dev-wave改善候補 (段8で裁定、詳細はhandoff参照)

1. codex子への必読射影リストは、規範文書が「別文書が定める」と明言する項目について
   関連決定 (`docs/decisions.md`の該当D) も射影に含めるべき。
2. 変異harnessのbaseline走行が本waveで初めての実pytest実行だった。py_compile+直接コード確認を
   「実質green」と扱いかけたことをfailures {{F:...}} (F80の再発扱い) として記録する。
