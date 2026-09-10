単独段 dispatch: stage=consult; lane=sol; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **親の段 1 brief (攻撃対象)**: `/home/SFC/tanab/.claude/jobs/c311da24/tmp/dev-wave-t1851-unit-c3b/s1-brief.md`
- **段 2 の plan (攻撃対象)**: `/home/SFC/tanab/.claude/jobs/c311da24/tmp/dev-wave-t1851-unit-c3b/out-s2-plan.md`
- 直前単位 C3a の記録: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-09_t1851-unit-c3a-wiring/README.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 契約の追記訂正 2: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-09_t1851-unit-c3a-wiring/contract-v3.1-erratum-2.md`
- 床値実走の runbook (W-2 節と復旧判定手順): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/phase3-8b-restart-runbook.md`
- 投入手順の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/README.md`
- 裁定台帳: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md`
- 失敗台帳: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/failures.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 3 レンズ A — 正しさ境界と proof chain から攻撃する

作業 root は read-only である。**書込み可能な tmp は無い。** pytest 緑を要求しない。
静的読解と grep による実測だけで結論を出す。**走らせていないものを緑と書かないこと。**

**file を 1 つも作れない。** 成果物は**最終メッセージの本文へ全文を書く**こと。

予算が尽きそうなら、**途中結論を下の出力形式どおりに書いて終わること** (無出力が最悪)。

この段では commit を作らない。git の状態を変えない。plan を守る義務は無い — **壊しに行くこと。**

## 攻撃対象

親 brief と段 2 plan の**両方**が対象である。親自身の実測値とその一般化も疑うこと。
親は次の 4 件を provisional に裁定しており、これが主たる的である。

- **(P1-1)** official 走行を wave branch の**未 land commit** `8fbcb70a5` で行う。
- **(P1-2)** receipt は `output/insights/` の `.md` 1 本とし、抽出 producer を新設しない。
- **(P1-3)** gate 入力の集合は C3a が新設した述語の消費 field に限る。
- **(P1-4)** 1 job・1 ノード直列でよい (pilot 実績 約 48 分)。

## このレンズで必ず見ること

1. **未 land commit で採った official 床値の証拠としての立場。** `eligible_for_refreeze` が真に
   なりうる走行を、main に着地していない commit で行うことの含意を追う。
   - D811 の逐語 (`## D811` 見出しで引く) は「別の source commit と script blob hash で
     再投入する」と述べる。この commit が main の祖先である必要はあるか。
   - **D811 には着手条件がある** — 「pilot 走行が消費した使い捨て入場鍵 (admission root 配下に
     118 件) の状態を実測し、official 走行が同じ cell を claim できることを確かめる。
     claim できないと判明した場合は着手せずユーザーへ返す」。**親はこれが D1124 (2026-08-27) の
     決定 3 「既に消費済みの key は以後の再測定を妨げない」で解けていると読んだ。**
     この読みを検査せよ。D1124 が撤廃した関門と、D811 が心配した関門が同一かを現物で確かめる。
   - 走行が emit する成果物のどこに commit が pin され、その commit が消えた (branch 削除・
     rebase) ときに証拠が dangling にならないかを追う。
2. **absolute 規律 6 (信頼境界) と規律 2 の観点。** 走行の入力・出力のどれが外部由来か。
   走行の成果物を後段が「指示」として読む経路はないか。
   正しさゲートを緩める向きの変更が plan に紛れていないか。
3. **receipt の主張の射程。** 親が載せる予定の限界文言は次である。逐語で検査せよ。

   > 本 receipt は、記載した commit、Pegasus job、環境 tag、mode、protocol および freeze による
   > fresh default production campaign 1 回で、実際に観測された入力値だけを記録する。
   > 列挙値と min/max はこの run の観測集合および標本極値であり、launcher または consumer が
   > 受理しうる全値域、未発火分岐、他環境、他 mode、他 commit、将来 campaign の母集合または
   > 許容 bound を示さない。

   この文言で守り切れない過大読みがまだ残るか。とくに **`DW-O13` が要求するのは
   「要求する値が到達可能か」の確認**である。1 run で観測されなかった値を「到達不能」と
   読み替える誤りが起きうる箇所を指摘せよ。
4. **未発火分岐の扱い。** C3a が新設した述語のうち、default production campaign では
   **原理的に発火しない**枝はどれか (例: 競合 pre-probe、cut-6 replay、retry ordinal の `1..N`)。
   それらを「実値域を測った」と書くと何が嘘になるか。receipt はどう書き分けるべきか。
5. **失敗台帳の型タグを攻撃面に入れる** (`docs/failures.md`)。過去に起きた型の再発検査。
   とくに「説明と実装の食い違い」「consumer 取り残し」「恒真な保証」を疑うこと。
   **親は `s8b_floor_contract.py:30-31` の comment 「現 producer は v4 のまま」が
   C3a 後に陳腐化していると実測した。同型の陳腐化が他にないか探せ。**

## 出力形式

次の H2 だけを使い、この順で書く。所見は 1 件ずつ `A-<番号>` で採番し、
**real か refuted か自分の判定を書き**、根拠を file:line か逐語で示す。

## 総括
## 所見
## 親の実測値への反証
## receipt 文言への修正案
## 未解決の問い

結合文字 U+0300〜U+036F を出力に使わないこと。
