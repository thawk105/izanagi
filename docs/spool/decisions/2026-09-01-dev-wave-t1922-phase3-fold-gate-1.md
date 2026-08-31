---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t1922-phase3-fold-gate
seq: 1
---

## {{D:phase3-generated-canonical-duplicate-gate}}. 生成後 canonical の見送り重複は計画時に拒否し、land 前 dry-run を義務にする

**決定:** `spool_fold.plan_fold()` が、全 worklog fragment を反映し終えた `docs/phase3.md` に対して
見送り台帳 ID の一意性を検査し、重複があれば `deferred-duplicate` で `FoldPlan` を返さず拒否する。
検査は既存の `_deferred_items()` を使い、新しい parser を作らない。あわせて `DW-O23` へ
「land 前に `spool_fold.py --dry-run` を通す」義務を書く。

**理由:**

- 重複の検出器は `check_docs.py` に元から在ったが、fold を**適用した後**の canonical にしか当たらない。
  land は協調 lock を取ってから `plan_fold()` を呼ぶため、初回検出が lock の中になっていた。
  実測では `--dry-run` が `status: planned` を返し、適用後に初めて
  `見送り台帳の ID が重複` が出た。
- `plan_fold()` は `--dry-run` と apply の両方が必ず通る唯一の場所である。ここに置くことで、
  親が land 前に走らせる `--dry-run` が lock の外での初回検出になる。fold gate 側にだけ置くと
  `--dry-run` は緑のままになり、依頼が名指しした 2 つの欠陥の片方が閉じない。
- 検査の置き場だけでは lock 外検出は保証されない。`DW-O23` にも `DW-S09` にも land 前 dry-run の
  義務が無く、親が走らせるかどうかに依存していた。義務化して初めて閉じる。
- 検出の意味を書き起こさず既存 `_deferred_items()` を使うのは、二重定義が drift するためである。
  同関数は fence・HTML コメントを除外し、完了記録の手前で範囲を切る。実測では継続行に ID が
  31 行、完了記録側に 10 件あり、素朴な行走査は偽の重複を作る。

**あわせて決めたこと:** fold gate の `phase3` family を被覆済みにする。実 canonical を読む node を
1 本登録し、`FOLD_GATE_UNCOVERED_FAMILY_ALLOWLIST` から `phase3` を外す。node の正例は
実 canonical に対して述語を直接行使し、実在項目を走査して複製した負例と対にする。
**実在 ID・件数・特定の ID を期待値へ pin しない** (D316)。

**却下した選択肢:**

- land の plan 作成を協調 lock の外へ移す — lock 内検出を機械的に断てるが land 状態機械の変更であり、
  本題を超える。`--dry-run` の義務化で同じ実害を塞げる。裁定パッケージへ送る。
- `check_docs.py` の見送り台帳検査を `spool_fold` から呼ぶ — 当該検出は独立した述語ではなく、
  worklog 読取と保存則検査を併せ持つ `_check_backlog_guard()` の中に埋まっており、
  返り値も重複 findings ではない。純粋な述語として再利用できない。
- 新しい重複判定を `spool_fold` 側へ書き起こす — 範囲抽出と ID 規則が二重定義になり drift する。
- 所要時間台帳へ新 node の値を足す — 台帳の exact 固定対象 suite に本 wave の file は含まれず、
  被覆条件も完全一致でないため不要。足せば性能台帳への scope 逸脱になる。
