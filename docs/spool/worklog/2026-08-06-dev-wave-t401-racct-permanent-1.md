---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t401-racct-permanent
seq: 1
title: [T-401] racct 欠測の恒久対応を設計まで詰めた — 段 2 の推奨案が受理集合を広げると段 3 の 2 レンズが独立に実証し、親は取得回数を保つ案 A′ へ差し替えて裁定 4 点を返す (docs のみ、branch worktree-dev-wave-t401-racct-permanent、実装差分がないため変異 matrix と受入全走は対象外)
---

## 本文

- **ユーザー引数が「設計案まで」だったので段 4 で「実装しない」と裁定し、`4→7→8→9` で終えた。**
  実装差分が無いため変異 matrix と受入全走は対象外である。案 A′ の実装、scope 外所見の是正、
  不変条件 I1–I4 の機械化はいずれも次 wave 以降に属し、着手は裁定 U-1〜U-4 の後とする。
- **段 2 が推奨した案 (権限の壁を見た command の retry を 1 回で打ち切る) を親が却下した。**
  段 3 の 2 レンズが**独立に同じ反例列**へ到達した — 1 回目が権限の壁、2〜5 回目に record が
  出るが壊れている応答列で、現行実装は最後の snapshot を採るため `available=true,
  integrity=false` (観測無効) になるのに対し、打切り案は `available=false, integrity=null`
  (観測有効) になる。危険側の attempt でも同じで、非 authoritative が authoritative へ反転する。
  親はコードで再照合して real とし、**取得 5 回は保ったまま固定待ち 16 秒だけを落とす案 A′**
  へ差し替えた。減るのは待ち時間であって観測の情報量ではない。
- **最も重い所見は「案 C は危険な job に自己拒否権を与える」だった。** `.e` は `qsub -e` によって
  job の標準エラーと scheduler 出力が合流するファイルで、job body 自身が書ける。これを会計
  integrity の producer にすると、危険な job body が `Request ID: <期待値>` を 1 行足すだけで
  exact-one 検査を落とし、自分の危険観測を台帳から排除できる。F93 の fail-blind の再発であり、
  D161 が会計 integrity をゲートに残した理由と正反対になる。案 C はこれで落とした。
- **親 brief の一次事実に誤りが 3 件あり、段 3 が全部拾った。** (a) 固定待ちを 8 秒と書いたが
  正しくは 16 秒で、同じ brief の (P3) と矛盾していた。(b) 「`.e` は manifest 束縛付き」と
  一般化したが、判定に使う `valid` は manifest 束縛を要求しない。(c) `rbudgetcheck` を
  「唯一の外部会計信号」と書いたが `qstat` にも scheduler 由来の counter がある。
  brief 本文は書き換えず erratum として残した。
- **成果物影響の射程も段 3 が狭めた。** 親は「certified 選択・材料レポートへは一切流れない」と
  書いたが、直接の schema consumer が閉じていることは因果的独立の証明ではない。T-399 の
  authoritative attempt が D130 条件 3 を前進させ [T-360] の着手前提として明記されている経路が
  ある。主張は「直接の schema consumer は存在しない。研究状態の依存は残る」まで狭めた。
- **段 3 の 18 件はすべて real で、refuted はゼロだった。** 親が狭めたのは 2 件の例示・帰属の
  射程だけである。重複を畳んで R-01〜R-14 に整理した。
- 逐語と根拠は `output/insights/2026-08-06_t401-racct-permanent/`。
- 段 1 の前提実測を 5 件行い、うち 1 件で `rbudgetcheck` が sudo 無しで通ることを発見して
  設計の選択肢が 1 本増えた。racct 系が恒久的に rc=1 になることは本 wave でも再現した。
- **段 8 の自己改善は候補 1 件で、記録に留めた。** worktree 隔離セッションで redirect / pipe を
  含む複合 Bash が guard に拒まれる既知候補が本 wave でも 3 回発火した。置き場である条件節の
  予算が塞がったままで前 wave と状況が変わらないため、[T-432] へ発火実績として記録する。

## 次の一手差分

### 更新

- [T-401] **P2・ユーザー裁定待ち**: 設計は詰め終えた。racct を正式源に据え置き、権限の壁のときは
  取得 5 回を保ったまま固定待ちだけ落とす案 A′ を推奨する。`.e` を会計証拠へ昇格させる案は、
  job が書けるストリームを integrity の producer にするため却下した。裁定は U-1 (正式な会計源)、
  U-2 (「恒久対応」の成功条件を死荷重削減に置くか)、U-3 (権限の壁のときの retry)、U-4 (着手時期)
  の 4 点。一次資料は `output/insights/2026-08-06_t401-racct-permanent/RESULT.md`。
  base: 6e3a0cf66eb7dce52f72bbd1ef13ecea85b4e962188a44310cad24ec7cbadda9

### 新規

- {{T:probe-terminal-proof-provenance}} **P2・新規**: probe controller の終端実証 第 3 経路が、
  manifest 束縛のない未改名 `.e` を受け入れる。`_saved_nqsv_stderr_accounting` の `valid` は
  `bool(matching_blocks) and not errors` で束縛を要求せず、`glob("*.e")` が未改名ファイルも
  候補にする。qsub template・展開後ファイル名・期待ファイル数の照合を必須化する是正は
  受理集合を縮めるだけである。評価器テストの fixture 既定が production の値域
  (欠測時は `null`) を代表していない件も同じ単位で扱う。
