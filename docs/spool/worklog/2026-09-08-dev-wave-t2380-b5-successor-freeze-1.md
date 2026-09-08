---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2380-b5-successor-freeze
seq: 1
title: [T-2380] 軸 B5 の後継凍結物 2 本と catalog で、部分登録が閉じられなかった 3 点 (候補主キー / catalog の seal / 引用・著者経路の起点) を閉じた — DBLP は anti-bot challenge で不達 (docs + 生成器 + test + catalog、branch worktree-dev-wave-t2380-b5-successor-freeze、変異 12/12 KILLED・等価変異 1 件 SURVIVED・MISMATCH 0・期待 node 完全一致 13/13)
---

## 本文

- ユーザー裁定: 引数で「凍結物なので、閉じる 3 点を先に事前登録へ書いてから内容を確定する順序を守り、commit 順が凍結の順序になるようにする」「既に凍結済みの部分は erratum でしか直さない」「本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外」「規律 2 を緩めない」「Codex author = D95」と限定された。
  commit 順は 1/2 (手順の事前登録、docs) → 生成器 + test + catalog (Codex author) → 2/2 (値の記録、docs) とし、**1/2 の commit より前に anchor の識別子を索引へ 1 本も照会していない。**
- **3 点はすべて閉じた。** 16 anchor の DOI を一次資料 (doi.org 解決 + Crossref record) で固定し (記憶していた識別子は 16/16 正しかった、`要裁定` 0 件)、OpenAlex 16/16 `収録`・arXiv は member `G2-08` が `収録`、catalog (1622 主 query + control 14 + venue 272) の file bytes の SHA-256 を seal し、補助探索 3 経路の起点 (W-ID 16、第一・最終著者 A-ID 延べ 29 / 異なり 24) と stream 61 本を確定した。
  **軸 B5 は `RW0` のまま。実行は認可していない** — registration preflight (実行器は未実装)、live preflight、人間認可が残る。
- **新事実 (環境): DBLP は本ホストから全入口が Anubis の anti-bot challenge を返し `不達`。** 2026-08-27 の軸 3 索引実測は到達していた。challenge の JS は模倣せず ({{D:dblp-anti-bot-challenge-is-unreachable}})、anchor 固有の DBLP request は未送信と記録した。**live preflight で DBLP が `不達` のままなら軸 B5 は走行を開始できない。** 軸 1 / 軸 3 の DBLP 経路にも同じ影響が及ぶ。
- 段 3 の敵対相談が親 brief の erratum 案を倒した (A-1、real)。当初案「`非収録` を見てから当該索引の control から外す」は positive control を結果依存で空集合化できる。裁定は「索引別 member 集合を lookup 前に鍵型と収録範囲で固定し、member の `不達`・`非収録` は `未完走`」({{D:b5-anchor-control-sets-fixed-before-lookup}}、1/2 の E-1)。受理集合の拡大は「member でない (slot, 索引) に control が無い」の 1 点に限る。
- 棄却 finding: A-2 (通りやすい anchor を選んだ)、A-5 (名称を主キーにした)、A-7 (実行前 = live preflight の読み)、A-10 (全頁取得後の辞書順)、B-1 / B-6 / B-9 / B-11、RA-01〜03 / 06 / 07 / 09、RB-02〜04、RB-16 / 17 — いずれも凍結文と実装・草稿が一致していると親が確認した。
- 採用した所見のうち親裁定を要したもの: RA-04 / RA-05 (`index` の小文字 token と `year` の JSON number は凍結文から一意に読めない) — 実装のとおりに裁定し bytes は変えず、2/2 に erratum E-4 として記録。RA-08 / RB-01 (test の自己参照と受理集合の穴) — fix 子が test だけを直し、凍結 catalog の SHA-256 literal と全 entry の完全列照合を既存 17 node に入れた。
- **裁定パッケージ (ユーザーへ):** (1) `G2-SA` の包含枝 (`B5-Q3` / `Q6` / `Q7` / `Q8`) はすべて C block を要求するが、`G2` の既知メンバー (Robbins–Monro、Kiefer–Wolfowitz、Kesten、SPSA、適応 sampling) の題名・要旨に登録 C 語の想定が無い。現行のまま実行すると `G2` の包含 control が不発 → 軸 `未完走` → §5.4 の語彙 amendment、が既定の経路。実行前に語彙 amendment (別 wave) を選ぶ余地がある (A-3)。(2) control の上限日 (2023 / 2026) が catalog に構造化されておらず、将来の実行器は `control_id` から割り当てる必要がある (RB-18)。後継 schema で `upper_date` 相当を足すかは裁定待ち。
- 変異 matrix: 13 件を事前登録し probe → 本走の 2 段で走らせた。12/12 KILLED・等価変異 1 件 SURVIVED・MISMATCH 0・期待 node 完全一致 13/13。逐語・台帳は `output/insights/2026-09-08_t2380-b5-closure/`。
- エージェント工数 (codex receipt、`gpt-5.6-sol` / xhigh、8 本すべて `accepted`、attempt 1): 段 2 plan 18 call / 1,055,922 token / 777 秒、段 3 相談 13 call / 770,050 / 836 秒と 21 call / 2,262,145 / 963 秒、段 5 author 29 call / 2,271,296 / 920 秒、段 6 レビュー 13 call / 758,250 / 943 秒と 32 call / 2,865,667 / 995 秒、fix 15 call / 833,192 / 429 秒、焦点 9 call / 462,461 / 587 秒。
- 親の実測: 自走 harness 17 passed (fix 前後とも)、生成器の再生成 bytes 一致、`--verify` 正例 rc=0 / 負例 rc=1、`check_docs.py` 違反なし、`git diff --check` rc=0、commit 1・2 の full provenance 監査 rc=0。外部 request は 1/2 §5 の範囲 (書誌解決 + OpenAlex / arXiv lookup + 非 anchor の応答形観測) だけで、catalog の query は 1 本も送っていない。

## 次の一手差分

### 完了

- [T-2380] 軸 B5 の後継凍結物 2 本 (`2026-09-08-backoff-axis-b5-closure-preregistration.md`、`2026-09-08-backoff-axis-b5-closure-record.md`) と catalog (`2026-09-08-backoff-axis-b5-search-catalog.json`、生成器 `orchestrator/axis_b5_search/catalog.py`) で 3 点を閉じた。軸 B5 は `RW0` のまま、実行は未認可。
  remaining: none
  base: e5f6276fcf4df77fbecb96fd46be67be10c84ea7618a5e434c807d1e2efab3ab

### 新規

- {{T:b5-registration-preflight-and-executor}} **P2・新規**: 軸 B5 の実行器 (parser・fixture・schema・runner) を作り、部分登録 §5.3 の registration preflight で catalog と実行器の bytes を束縛する。live preflight では 3 索引すべての member について ID lookup を再実施し、**DBLP が anti-bot challenge で `不達` なら走行を開始しない**。実行前に、`G2-SA` の包含枝がすべて C を要求する構造 (1/2 §2.2、§7) をユーザーが語彙 amendment で解くか現行のまま走らせるかの裁定を要する。
