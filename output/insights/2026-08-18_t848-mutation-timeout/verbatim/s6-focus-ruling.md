# 焦点再レビュー (NO-GO) への親の裁定 — 2026-08-18 00:53 JST

## 最優先の NO-GO 根拠は refuted

**レビューの主張:** 「nonce が欠落した実 submission が terminal `TIMEOUT` へ落ちる偽の緑」。

**親の実測 (1 段ずつ実コードで確認):**

1. harness は runner の環境へ nonce を置く (`tools/mutation_harness.py:1776-1780`)。
2. `tools/run_tests.py` は `PYTHONDONTWRITEBYTECODE` に一切触れない
   (`grep -n "PYTHONDONTWRITEBYTECODE" tools/run_tests.py` は **hit 0 件**)。
3. `_dispatch_environment()` (`tools/run_tests.py:930-938`) は `os.environ` を複製し、
   task-run 台帳の 3 変数だけを除く。それ以外は素通しする。
4. dispatch は `tests` task の `env_allowlist` に `PYTHONDONTWRITEBYTECODE` を持つ
   (`tools/pegasus/dispatch_compute.py:79-85`) ので、値は `request_env` (`:1508-1511`) を経て
   `request.json["environment"]` (`:1561`) に載る。

したがって **nonce の運び屋は実運用で end-to-end に成立する。** NO-GO の主根拠は成立しない。

## ただし正当な残件 (後続タスクとして記録する)

**テストがこの連鎖の 1 段を固定していない。** fixture は `request.json` を自分で書くため、
「run_tests → dispatch が nonce を実際に運ぶ」ことをテストが pin していない。
carrier が将来壊れてもテストは緑のままになる。
**挙動の欠陥ではなくテスト強度の穴**であり、本 wave の受理を止める理由にはしないが、
後続タスクとして worklog へ残す。

## 他の未 closed の裁定

| 所見 | 判定 | 根拠 |
|---|---|---|
| A-2 (submission dir は qsub 前に作られる) | real / 受容 | 停止の結果は「sidecar を書いて rc=2、latch は張らない」。runner が dispatch 経路へ入った以上、その timeout は実行 timeout ではない。保守側へ倒すのが正しい |
| A-3 / B-1 (nonce の誤共有) | refuted | nonce は走行ごとの 128 bit 乱数。他 process が我々の環境を複製しない限り一致しない |
| A must-fix / B-7 (wrapper receipt の failure が null) | real / scope 外 | wrapper は `_select_return_code` (`tools/mutation_worktree.py:967`) で child の rc=2 を返すため偽の緑にはならない。診断欄の改善は後続タスク |
| B-2 (fanout の `--force-dispatch` 検証) | real / scope 外 | 本 wave は fanout を触らない (段 4 裁定) |
| B-3 / B-4 / B-5 (変異の帰属と期待 node) | closed | 親が probe 実走で期待 node を実測導出した。5 変異が別々の実効ゲートを撃つことを観測済み |
| B-6 (DW-M06 の逐語) | 段 7 で判定 | docs 予算に入らなければユーザー裁定へ返す |

## 結論

**GO。** ただし後続タスク 2 件 (carrier 連鎖の pin、wrapper receipt の診断欄) を worklog へ残す。
