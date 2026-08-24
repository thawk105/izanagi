# 段 1 brief — [T-1263] 認証水準の明記と材料レポート側 1 箇所の検査

## scope

`tools/codex_reasoning_ab.py` の A/B 装置について、
(1) 「aggregate の `valid` だけが certified であり、中間 packet は未認証」という認証水準を
材料レポート (= `verify`/`aggregate` が返す report object) に機械可読で明記し、
(2) 材料レポートに載る packet だけは未認証 snapshot 由来でないことを **1 箇所**で検査する。
中間層 (`make_packets` / `append-verdicts` / `freeze-verdicts` / `reveal-mapping` / `collect_run`)
へ再検証を足すことは scope 外 (裁定本文が「全中間層への再検証要求は取らない」と明記)。

## 確定済みユーザー裁定 (2026-08-17 /rulings 全件 第 5 回、明記 + 条件)

> 「aggregate の valid だけが certified で中間 packet は未認証」と明記する。**条件 = 材料レポートに
> 載る packet だけは未認証 snapshot 由来でないことを 1 箇所で検査する** (論文素材になるのは
> 材料レポートであるため)。全中間層への再検証要求は費用対効果が悪いので取らない。

command 引数の追加要求: 記述と実装の食い違い (謳うだけで発火しない保証) を作らない。
明記した性質が実際に成り立つことを検査する node を対で入れ、
**中間 packet を certified 扱いする変異が赤くなることを実測で示す**。実装は Codex author = D95 経由。

## 実測した現状 (brief 前の裏取り)

| アンカー | 実測した事実 |
|---|---|
| `tools/codex_reasoning_ab.py:10023-10029` | `_replay_manifest` だけが `verify_snapshot` を再走し、oracle の canonical bytes と pre/post 一致を照合する。dedup key は `oracle_path.as_posix()` (`snapshot_cache`) |
| `tools/codex_reasoning_ab.py:9899-9963` | supervisor 側 `process_started is False` の attempt は `failed_attempt` を積んで `continue` する。**この経路は snapshot 検証を一度も通らない**が `grouped` には入る |
| `tools/codex_reasoning_ab.py:10156-10160` | `final_attempts` は `grouped` の attempt 最大番号。上記の未検証 attempt も final になりうる |
| `tools/codex_reasoning_ab.py:8687-8911` | `_load_adjudication` が packet ↔ run ↔ slot を join する唯一の場所。join 条件は `mapping` の run_id 集合 == `final_attempts` の run_id 集合 (`:8788-8790`) で、**snapshot 検証の有無は join 条件に一切入っていない** |
| `tools/codex_reasoning_ab.py:9557-9580` | `_aggregate_verified` の return dict が材料レポート本体。`valid` は `not reasons` |
| `tools/codex_reasoning_ab.py:10250-10380` | `make_packets` は manifest を読んで output bytes を写すだけ。snapshot も oracle も参照しない |
| `tools/codex_reasoning_ab.py:10890-11080` | `aggregate` / `verify` の結果は stdout へ出るだけで、tool 自身は凍結 file へ書かない |

## 不変条件

1. **正しさゲートを緩めない (規律 2)。** 本 wave は `valid` の受理集合を**狭める**方向にだけ動かす。
   既存の failure_reason を消さない。
2. `make_packets` が書く `packet-state.json` / custodian mapping の **bytes は変えない**
   (`_write_frozen_json` で凍結される中間層。DW-O09/O10 の適用対象にしない)。
3. `SCHEMA_VERSION` (= 2) を勝手に上げない。上げる必要があると判断したら段 4 で裁定する。
4. 事前登録 `docs/phase3-t189-model-routing-preregistration.md` の実験プロトコル (§ 実行順序・
   判定式) を書き換えない。本 wave は report 側の認証水準の明示と検査の追加だけ。
5. 明記は**機械可読**で、かつ**恒真でない**こと。宣言 field と検査 node を対にする。

## 成果物の形

- `tools/codex_reasoning_ab.py`
  - `_aggregate_verified` の report に認証水準の宣言 field を 1 つ足す
    (certified なのは aggregate の `valid` だけ / packet・packet-state・verdict log・
    revealed mapping は未認証、という内容を機械可読に書く)。
  - `_load_adjudication` (packet↔run の唯一の join 点) に、**snapshot 検証済み run 集合**を渡し、
    材料レポートに載る packet の run が全部その集合に入ることを検査する。外れたら
    `failure_reasons` に理由を積み `valid` を false にする。**検査は 1 箇所だけ。**
- `orchestrator/tests/test_codex_reasoning_ab.py`
  - 宣言 field の内容を固定する node。
  - 宣言した性質が成り立つことを検査する node (未検証 snapshot 由来の packet で `valid` が
    false になり、理由文字列が出ること)。
  - 正例 node (完全な実験は従来どおり `valid` true、宣言 field も付く)。
- docs: decisions fragment (設計判断)、worklog fragment。insights に逐語と変異台帳。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 未検証 snapshot 由来 packet は現行コードでも到達可能である。** 根拠は上表の
  `:9899-9963` (prelaunch 失敗 attempt は snapshot 検証を通らない) と `:10156` (それが final に
  なりうる) と `:8788` (mapping は final attempt の run_id 集合と一致することしか要求しない)。
  したがって新検査は恒真ではない。**攻撃してほしい点: この経路が本当に `valid: true` へ到達
  できるのか、`experiment_complete` / `pair_invalidation` / `make_packets` の
  `final.get("output")` 要求のどれかが先に止めていないか。**
  もし先に止まっているなら、新検査は「将来 snapshot 再走が外れたら赤くなる」構造検査として
  設計し直す必要がある (その場合も変異で発火を実測する)。
- **(P2) 検査を置く 1 箇所は `_load_adjudication` である。** packet↔run の join が
  そこにしかないため。攻撃点: `_replay_manifest` 側や `_aggregate_verified` 側に置く方が
  「材料レポート側」という裁定文に忠実ではないか。
- **(P3) 宣言は report の top-level field 1 つで足りる。** 攻撃点: docs 側にも明記が要るか、
  field 名と値の形 (string か object か) が下流の消費に耐えるか。
- **(P4) `snapshot_cache` の dedup key は oracle path であり、同じ path を共有する run は
  検証済みとみなしてよい。** 攻撃点: 同一 path が別内容を指す再入経路がないか。

## 並列分割方針

軽量版ではなく段 2・3・5・6 を立てる。理由は `DW-C00` の「正しさ防壁に触る」「受理集合が変わる」の
両方に該当するため。段 3 は 2 レンズ (A = 恒真性・発火可能性への攻撃、B = 認証水準の記述と実装の
食い違いへの攻撃)。段 5 は実装子 1 本 (編集面が 2 file で分割の利が無い)。

## 成果物影響 (DW-G05)

実装しない場合、材料レポートは自分の認証水準を主張しないまま `valid: true` を出し続ける。
論文素材として引用される `valid` が「packet の由来 snapshot は未検証でもよい」受理集合を
含むことになり、report の受理集合が実際より広い。実装すると `valid` の受理集合が狭まり、
未検証 snapshot 由来 packet を含む manifest は `valid: false` になる。certified 選択の値・
proof chain の参照・凍結 bytes は変わらない。

## 受入・実測の環境

login node 既定 (`docs/pegasus-runbook.md` §7.0.0 の自動判定に従う)。受入投入は
`tools/dev_wave_wait.py acceptance` 経由。worktree =
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1263-certification-scope`、
main worktree = `/work/1/SFC/tanab/izanagi`。

## 既存被覆と純増検出力

性質「材料レポートに載る packet の由来 snapshot が検証されたか」で
`orchestrator/tests/test_codex_reasoning_ab.py` を検索した。既存の packet 系 node
(`test_make_packets_*` / `test_mapping_custodian_blocks_pre_freeze_reveal_and_packet_sha_join` /
`test_f3_1_packet_swap_restore_is_rejected` / `test_m6_verdict_packet_swap_restore_digest_layers_are_redundant`)
は packet の **bytes 同一性・盲検・freeze 順序**しか見ておらず、由来 snapshot の検証有無を見る node は
0 件。既存の snapshot 系 node は `verify_snapshot` 単体の受理集合を見ており、report の
`valid` との結線は見ていない。純増検出力 = 「report に載る packet の由来 snapshot が未検証でも
`valid` が true になる」型の欠陥の検出。
