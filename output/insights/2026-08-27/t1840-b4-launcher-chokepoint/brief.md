# 段 1 brief — [T-1840] B-4 の専用起動器と B-4 識別子を支配点にする

base main `dd66213978d3d30eed567484ec013216bff6926b` / branch `worktree-dev-wave-t1840-b4-launcher`

## 確定済みユーザー裁定

- **D1033**: B-4 実験の正式標本を機械的に分ける支配点は、**専用の起動器と B-4 識別子**として置く。
  下流で B-4 の名乗りだけを拒否する形は、名乗らない経路が残るため**不採用**。
- 実装の author は Codex (D95)。親は実装面を直接編集しない。
- 隣接裁定 D1042 (使い捨て署名 token)、D1043 (送信前の写し固定)、D1050 (受理記録の置き場所 1 本) は
  **未着地**。本 wave の scope 外だが、いずれも塞げなくなる作りにしない。

## 実測した現状 (brief 前に計測。推測ではない)

1. `create_b4_closed_critic_pair` の呼び手は、テストと同 module 内 `main()` を除いて **0 件**。
   3 driver からの呼び出しは実在しない。
2. `p3_s4_loop.run_one_iteration` (1066-1182 行) の AST 内に B-4 参照は **0 件**。
   B-4 の関門は `drive_iteration` (1423-1531) と `main` (1534-1770) にしかない。
3. `--b4-reflux-ablation` は 3 driver とも `action="store_true"` の **opt-in**。付けなければ関門は
   一切発火しない。
4. `p3_b4_closed_critic.main()` は閉じた critic を 1 往復呼んで receipt を出すだけで、campaign の
   iteration を駆動しない。実走の入口は今 3 本 (各 driver の `main`) あり、どれも支配点ではない。
5. 先例: T-1286 (certified sink の支配点) は `wal.append` を支配点にし、一回限りの receipt を
   要求させて閉じた (archive 0817-622 / 0818-660)。同じ骨格が使える。

## 純増 (この wave が新しく閉じるもの)

T-1697 の必須配線は「marker 付き走行が閉じた receipt を要求する」まで閉じた。
**純増は「B-4 識別子そのものを、専用起動器だけが鋳造できるようにする」ことである。**
marker を任意のコードが `default_cfg(b4_reflux_ablation=True)` で自作できる限り、支配点にならない。

## scope (実装する)

- (S1) 専用起動器を 1 本置く。admission record の検証 → production factory で閉じた対を鋳造 →
  driver の継続実行、までを 1 経路にする。B-4 実走の入口はこれだけにする。
- (S2) B-4 識別子を起動器だけが鋳造できるようにする。`p3_b4_closed_critic` が既に使う封印
  (`_PAIR_SEAL` 型の非公開 sentinel) の idiom を再利用する。試験用の鋳造口は
  `create_b4_closed_critic_pair_for_test` と同じく **`test-only` と明示的に分離**する。
- (S3) `run_one_iteration` を、起動器由来の承認を持たない B-4 識別子付き cfg に対して
  fail-closed にする。現在ここは B-4 を一切見ていない。
- (S4) 3 driver の `main` を、起動器由来の承認なしでは B-4 標本を作れないようにする。
- (S5) 負例検査。**支配点を通らずに実走できてしまう呼び方を、実体を名指しして赤にする。**
  最低限: `run_one_iteration` 直呼び、各 driver の `main` を `--b4-reflux-ablation` 付きで
  起動器なしに叩く、`default_cfg(b4_reflux_ablation=True)` の自作、`test-only` 鋳造口で作った
  識別子の正式標本への流用。**性質だけを述べる検査にしない** — 起動器が実際に呼ぶ相手が
  `create_b4_closed_critic_pair` と実 driver の `main` であることを名指しで固定する。
- (S6) 事前登録 §7.2 の「marker は自己申告である」の記述を、閉じた分だけ正直に更新する。

## scope 外 (実装しない)

- D1042 の使い捨て署名 token、D1043 の送信前 attest、D1050 の受理記録 path 一本化。
- proposal producer と critic 決定の因果的束縛 (事前登録 §10 の未了項)。
- 実行主体 (PATH 上の `claude`) の真正性、pair の完全性、receipt shopping。

## 不変条件 (破ったら停止)

- **marker 不在の通常走行の campaign identity を 1 bit も変えない。** 実測済みの golden は
  `p3-s4-loop-s4-autonomous-2cd75697` / `-9f43a5b8` (base)、
  `p3-s5-sort-loop-s5-sort-autonomous-081dd46f` (sort)、
  `p3-s8a-trigger-loop-s8a-trigger-autonomous-` の 8 件 (trigger)。
- 正しさゲートを緩めない (規律 2)。両アームで verifier・reject 判定・build/verify/bench の順序を
  変えない。関門の追加だけを行い、既存の受理集合を広げない。
- `projection_closure_manifest` は file bytes から live に計算され、hex の literal pin は
  repo 内に無い。新 module を閉包へ入れるかは設計判断であって既存 pin の破壊ではない。
- 凍結成果物の bytes は変えない。`.claude/agents/critic.md` は 1 byte も触らない (D904)。

## 成果物の形

新 module 1 本 + 既存 4 file (`p3_s4_loop.py` / `p3_s4_loop_sort.py` /
`p3_s4_loop_trigger_gating.py` / `p3_b4_closed_critic.py`) への関門追加 + 4 test file の負例 +
事前登録 §7.2 の更新。変異事前登録は段 4 で確定する。

## 成果物影響 (DW-G05)

実装しない場合: B-4 の正式標本を機械が区別できないままになる。marker を付けずに走らせた campaign を
報告時だけ B-4 と名乗る経路、および `run_one_iteration` 直呼びで受理記録も閉じた critic も通さずに
`evidence_class=="certified"` の標本を作る経路が残る。事前登録が発効した時点で、
**B-4 の 2 アーム比較の証拠クラスが「事前登録に束縛された標本」から「自己申告の標本」へ落ちる。**

## 親の provisional 裁定 (攻撃対象。段 3 で割ってよい)

- **(P1)** 支配点は「B-4 識別子の鋳造」に置く。下流の実行時検査ではなく、識別子を作れる場所を
  1 つに絞る。理由: D1033 が下流の名乗り拒否を明示的に却下しているため、下流側の検査だけでは
  裁定を満たさない。
- **(P2)** 封印は `p3_b4_closed_critic` の `_PAIR_SEAL` と同じ「module 非公開 sentinel を
  keyword-only 引数で要求する」形にする。同一 process からの属性書換えには耐えない
  (既に receipt の非保証 field に列挙済み) ことを、新たに保証すると書かない。
- **(P3)** 起動器は既存の `p3_b4_closed_critic.main()` を置き換えるのではなく、その上位に置く。
  `main()` は receipt 鋳造の部品として残す。
- **(P4)** 新 module を `projection_closure_manifest` の閉包へ**入れる**。起動器の bytes が
  変われば標本の projection が変わるべきであるため。ただし入れると既存 receipt の projection hash が
  変わる。段 4 で影響を測って確定する。
- **(P5)** 負例は「両層 stub で緑になる」ことを段 6 の変異 matrix で裏取りする。各負例につき
  「その検査だけを外す」変異を 1 件ずつ事前登録し、狙ったテストだけが落ちることを確認する。

## 並列分割方針

段 2 プラン 1 本 (read-only)。段 3 敵対相談 2 本 (レンズ = 迂回経路の網羅 / 既存受理集合と
golden identity の破壊)。段 5 実装子 1 本 (編集面が相互に依存するため分割しない)。
段 6 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。
