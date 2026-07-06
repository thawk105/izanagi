# 後続段 4: coder 自律期 (diff 検疫 / リーク制御 / planner) — 継続 WAL

- 状態: **設計基盤 + コア設計方針まで確定・実装未着手** (基準 833671c、後続段 3 完了済み・作業ツリー clean)。
  着手時は新しいセッションで (このセッションは長く、load-bearing な段の実装を末尾劣化から守るため区切った)。
- スコープ (phase3.md 後続段 4): coder が初めて変異の値・方向を**自律生成**する段 = reward hacking 圧力が最も高い。
  リーク制御が airtight でないと主実験の「合成 vs 答えを読んだ」の区別が崩れる。
- **設計基盤 = docs/phase3-s4-design-foundation.md** (調査 5 レンズ wf_e2036fe9-dc2 を統合、commit 0232101)。

## このセッションで進んだ分 (design-foundation の先・未コミット = 記憶のみ、要再構築)

- **重要発見: 4a (diff 検疫) と 4b (リーク制御) は密結合。** coder の**出力インタフェース**が diff 検疫の役割を
  決める。よって「4a を先に単独実装」の順序は誤り — 一体で設計する。
- **Model X vs Y の裁定 → Model Y を採る:**
  - Model X = coder が filesystem を Edit → diff 検疫が git diff のフレーム byte 同値を検証 (主 gate)。だが coder は
    Read tool で output/docs/WAL を徘徊でき勝ち筋 literal を読める = リーク (急所)。
  - **Model Y (採用) = coder は fresh subagent・filesystem browse なし。合成枝 (hole) のコードを構造化出力で返し、
    harness がテンプレフレームに挿入。** フレームは構成上保存。browse 経路が構造的に無い = リーク閉
    (critic-experiment が tools=Bash のみで guided.py 出力だけ見るのと同型)。
  - harness が context を射影して渡す: フレーム + hole 位置 / coder が呼んでよい silo API surface の curated snippet /
    planner の変異方向 (値でなく方向)。遮断 = 勝ち筋 VALUE(0-10us)・機序・利得(+38/+11%)・grid fitness
    (所在 = decisions.md:319/338・output/insights/2026-06-22_p2-case-study-*・backoff-sweep WAL・main-experiment §24/59)。
- **diff 検疫の役割 (Model Y では):** フレーム byte 同値 = defense-in-depth (構成上保存されるため)。**主 gate 価値は
  hole エスケープ検査** (hole 内の生 #if/#else/#endif 指令・マーカー文字列を reject = フレームを壊す挿入を止める)。
  唯一防壁にしない (構造破れは Tier0 compile が、binary 差は source_digest identity が二重に捕らえる)。content 逸脱
  (straight-line か・computed include・環境判別述語) は auditor + 規律6 に advisory (text-gate しない、D30/D33)。
  配置 = 新規 orchestrator/campaign/diff_quarantine.py (guard_write には入れない — caller 非識別・D33)。
- **段 4 の変異題材:** 同じ backoff 軸で coder が値・方向を自律発案 (kickoff は人間が値 50 を与えた。sort/lock は段 5)。
  planner が方向を提案・coder が具体コード合成 → diff 検疫 → verify+bench → critic 帰属の閉ループを最小軸で実証。
- **diff-reject は S4 rejection の新型** (frame-altered/hole-escape/outside-region)。片肺を作らない (規律3・D37 型5)。
- **D38 残:** auditor 直接 Write は read-only 据え置きが正解 (path-scoped 執行は原理的に不能・guard_write caller 非識別)。
  検証相 (seed×N/長 extime) は main-experiment §65-66 が明示的に段 6。

## 次セッションの入口 (推奨フロー)

1. 上記コア設計方針を design v1 に再構築 (このセッションの design v1 Write はユーザー中断で未保存 = 記憶から復元)。
2. **敵対検証 (段 3 と同型) — Open Questions を検証:** (a) Model Y の hole エスケープ検査の robust 性 (backslash-newline
   splice で #endif を隠す GW2R-1 同型攻撃が効くか・効くなら Tier0/identity の二重で十分か hole を preprocess すべきか)。
   (b) coder に tools を全く与えないか限定 Read か (browse 閉じつつ API 確認を成立させる形・限定 Read の徘徊経路)。
   (c) フレーム byte 同値の template baseline 定義・マーカー複数化。(d) リーク実効性 (planner もリーク制御要か・
   planner→coder リーク経路・fresh context の「本会話を見ない」保証)。(e) diff-reject 新型の形 (build 前 reject は
   verdict 軸に乗らない)。(f) Model Y で diff 検疫が defense-in-depth 降格 → 規律5 的に過剰か backstop として正当か。
3. 実装 → 実走 → docs (D39)。実装順 = coder 出力インタフェース(4b) + diff 検疫(4a) をコアに、planner.md(4c)・
   mutation-red ゲート(4d) を後続。段 4 の中間結果は主実験の事前登録に従い「暫定」報告 (headline は段 6)。

## 人間待ち
- submodule izanagi-trace 028f34d (後続段 3 の write_set 被覆 assert) の push — この環境に認証なし (D16)。
  push まで gitlink 028f34d は clone 不能。
