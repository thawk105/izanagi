---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t822-evidence-gaps
seq: 3
---

## 新規

### {{F:call-site-mistaken-for-guarantee}}. 親が呼び出しの存在を保証の発火と取り違えた [防壁の射程誤認] [誤前提]

- 事象: 段 1 brief で親は「D863 の証拠欠落 3 件は既に実装済みで閉じている」と結論し、
  wave の実装 scope を 1 件へ絞った。段 3 レンズ A が 3 件すべてを原典で反証し、
  親が逐語で裏取りして brief を撤回した。段 3 を省いていれば、閉じていない条件を
  閉じたと台帳へ書き、正式系列の起動条件を誤って解除していた。
- 根本原因: 親は grep で呼び出し箇所を見つけ、判定器で当該条件が合格終端に達していることを
  確認し、それを「保証が発火する」と読んだ。実際には (a) 呼び出しは `do_build=False` と
  campaignless failure cell で迂回でき、(b) 契約が謳う「no-build を certify しない」保証は
  受領証が構造上つねに非 certifying であるため恒真で、(c) 6 report の commit 一致は
  計測対象の一致ではなかった。**呼び出しの存在・判定器の合格終端・条件の見た目の充足は、
  いずれも保証が発火する証拠ではない。**
- 恒久対応: `docs/dev-wave/core.md` の `DW-C00` が「設計択一が割れる・正しさ防壁に触る・
  受理集合が変わる段では独立の敵対検証子を省かない」と定めている。本件はこの規定が
  実際に機能した事例であり、規定を緩める提案 (軽量版で段 3 を省く) を
  正しさ防壁に触る wave へ適用してはならない。加えて、既裁定の前提が古いと親が判断した
  場合でも、**その判断自体を反証させるレンズを段 3 へ立てる**ことを本 wave で実施し有効だった。
- 再発検知: 段 1 brief で「既に閉じている」と結論した項目があるとき、段 3 の 1 レンズを
  その結論の反証専任にする。反証できなければ「反証できなかった」と、
  何をどこまで確かめたかを添えて書かせる。

### {{F:mutation-harness-preflight-serial-rejects}}. 変異 harness の起動条件で 5 回連続ではじかれた [手順漏れ]

- 事象: `tools/mutation_harness.py` の起動が 5 回連続で rc=2 停止した。停止理由は
  (1) 走行 argv に `-rf` が必須、(2) `--spec` は試験対象 checkout の外に置く、
  (3) spec の key は `schema` + `timeout_seconds` (`schema_version` ではない)、
  (4) 作業ツリーが固定 HEAD blob と一致していること = 実装 commit が先、
  (5) untracked file が 1 つでもあると停止。各回とも 1 往復を要した。
- 根本原因: 起動条件が `--help` にも既存 spec の例にも現れず、実行して初めて分かる。
  とくに (4) は「変異は段 6、commit は段 7」という段順と衝突するため、
  手順どおり進めると必ず踏む。
- 恒久対応: 起動前に `--plan-only` で preflight だけを走らせて全条件を一度に出す。
  本 wave の spec (`output/insights/2026-08-25_t822-evidence-gaps/mutation-spec.json`) は
  5 条件すべてを満たした実例として参照できる。
- 再発検知: 変異 spec を書いたら `--plan-only` を 1 回通す。通らなければ本走を投入しない。
- 付記 (別事象、同 wave 内): 最終巡は M02 が `PARSE_ERROR`
  (`rc=1 だが canonical stdout から failed node を確実に抽出できないため停止`) で止まった。
  同一の変異内容が直前の probe 巡では node 1 件の `KILLED` になっており、
  変異でなく捕捉側の一過性の失敗である。既存の同署名エントリ (F149 は runner の
  local 実行へのドリフト、F194 は parametrize の自動 id) とは根本原因が異なるため、
  それらの再発としては記録しない。`--resume` で続きから再開して完走した。
