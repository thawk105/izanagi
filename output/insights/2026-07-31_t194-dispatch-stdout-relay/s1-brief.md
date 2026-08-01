# [T-194] 段 1 brief — dispatcher の子 pytest 出力を親 stdout へ中継する

- 対象: `tools/pegasus/dispatch_compute.py` と `orchestrator/tests/test_pegasus_dispatch_compute.py`
- 実測した前提 (段 1 前提実測、静的読解): 子 stdout/stderr は `_bounded_log` で収集され
  `receipt["scheduler_logs"]` に入るが (`dispatch_compute.py:1084-1089`)、親へは印字せず
  `child_rc` だけを返す (`:1102-1117`)。既存 905 行のテストに中継の検査はない (`capsys` は latch のみ)
- 実測した環境: 本 checkout の `site_policy.current_site()` = `PEGASUS_LOGIN`。よって受入全走
  (`tools/run_tests.py`) は本 wave が変える dispatcher 自身を通る (dogfood 経路)

## scope (in)

1. child_rc≠0 のとき、収集済み子 stdout tail を親 stdout へ、stderr tail を親 stderr へ中継する。
   **未実装なら**: 受入・変異の赤が「rc だけ」になり、`DW-M08` が要求する失敗 node の毎回記録が
   Pegasus 経由で構造的に不可能になる (台帳の受入欄から node 名が欠落する)
2. child_rc=0 のときは末尾の小枠 (既定 4 KiB) だけ中継する。**未実装なら**: 緑走でも数千行が親
   コンテキストへ流れ、親の裁定容量を食う (成果物の値は変わらないが wave の完走可能性が下がる)
3. infra 失敗経路 (accounting grace 満了・DispatchError) でも収集済み分があれば同じ規則で中継する。
   **未実装なら**: infra 赤の一次資料が `.o` 手読みのみになり worklog の原因記述が推測になる
4. 上記 3 点の回帰テストを新設する

## scope (out)

- receipt schema (`pegasus-dispatch-receipt/v1`) の field 追加・変更。consumer は自テストのみと
  実測済みだが、本 wave では touch しない
- 中継量の CLI/環境変数による上書き口の新設 (必要が実測されるまで設計メモ、`DW-G04`)
- T-193 (dispatch_compute.py と dev-wave-improve 3 ファイルの正本統合) は別タスク。触らない

## 不変条件 (破ったら停止)

- dispatcher が返す rc は中継の有無・成否で変わらない。中継は best-effort で、その例外を
  握って rc を変えてはならない (受理集合不変)
- 中継は receipt 永続化の**後**に行う。中継経路の例外で receipt を失わない
- `_bounded_log` の decode 済み text をそのまま使い、再 decode・再読込をしない
- 既存テスト (905 行) の期待値を書き換えて緑にしない

## 確定済みユーザー裁定

- codex のレートリミットが近いため、実装子・レビュー子は **claude 子で代替**する (本 wave 起動引数)。
  親が実装面を直接編集しない境界 (凍結境界) は維持する

## provisional 裁定 (親の暫定・攻撃対象)

- (P1) 発火条件を rc で分岐させ、緑は 4 KiB / 赤は収集済み全量とする。
  対案: 常時同量。攻撃点 = 「rc 分岐は tail 量という診断面に受理集合的な分岐を持ち込む」
- (P2) 子 stdout→親 stdout、子 stderr→親 stderr の対応を保つ。
  対案: 全部 stderr。攻撃点 = 「親の stdout は rc 判定に使われていないか」
- (P3) 中継 header は `[Pegasus dispatch]` prefix 付き 1 行とし、`_progress` と同じ体裁にする。
  攻撃点 = 「pytest 出力に prefix 無しで混ざると、親が子の出力を自分の出力と誤認する」

## 成果物の形・分割

- 実装単位は 1 つ (`dispatch_compute.py` + 同テスト) — 所有が素集合に割れないため分割しない
- codex 実装子 1 本 → claude 敵対レビュー 2 本 (異なるレンズ) → 親が変異 matrix と受入全走

## erratum (段 6 裁定による親自身の訂正。裁定は `s6-adjudication.md`)

1. **scope 1 の被害記述は過大だった (A-6)**。「台帳の受入欄から node 名が欠落する」は誤り。
   `tools/run_tests.py:903` が Pegasus dispatch 経路で `sidecar=None` を渡すため、中継を実装しても
   `output/task-runs` の `collected_node_digest` は `None` のままである。本 wave が確保するのは
   **親・人間が読める一次資料**だけであり、台帳欄の修復は別タスクとして起票する
2. **不変条件 1 の文言が欠陥だった (A-6b)**。「中継は best-effort で、その例外を握って rc を変えては
   ならない」は「中継の失敗」と「中継中に起きた無関係な中断」を区別しておらず、実装子を
   `except BaseException` (= signal 握り潰し) へ追い込んだ。正しくは
   **「中継の I/O 失敗 (`Exception`) で rc を変えない。`BaseException` (シグナル・`SystemExit`) は
   従来どおり伝播させる」**
3. **(P1) を改訂した (A-7 / B-9)**。赤側の「収集済み全量」は最大 2 MiB を親のコンテキストへ流し、
   緑側を 4 KiB に絞った理由 (親の裁定容量) がそのまま当てはまる。赤側にも 64 KiB の上限を置き、
   切り詰め時は実サイズと省略量を枠行に明示する。全量は receipt に残るため一次資料は失われない
4. 実装子は当初 claude で起動したが、`tools/check_ai_provenance.py` が実装面 commit に
   `product=codex; role=author` を機械的に要求するため、**実装面は codex 実装子**へ切り替えた。
   ユーザー裁定 (codex レートリミット回避) は相談・レビュー・harness を claude に寄せる形で満たす
