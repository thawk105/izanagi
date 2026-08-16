# 段 1 brief — [T-650] 受入 lease の解放を親の規律から機械へ移す

wave slug `t650-lease-release` / branch `worktree-dev-wave-t650-lease-release` /
基準 main `0c689a96c91ad2ab2a71b7e948658e741f5281eb` / 2026-08-16 22:10 JST

## scope

受入 lease の**解放**を、親 (LLM セッション) の手作業から `tools/dev_wave_land.py` の機械的な
終端処理へ移す。あわせて land が自分の終端性 (同じ tip を叩き直して直るか) を結果 JSON で宣言し、
呼び手が rc を自前分類しなくてよいようにする。**land の受理条件・監査・ff-only の権威は 1 bit も
変えない。** lease TTL 2400 秒・待ち札 FIFO・通知の advisory 性 (D239 / D253) も変えない。

## 確定済みユーザー裁定 (2026-08-16)

1. 受入全走のボトルネックを根治する。**リワードハック禁止** — 検査を弱めて速くする方向は不可。
2. 「終わった dev-wave が lease を解放していないケースがあるだろう」「タイムアウト頼みで他に
   めっちゃ迷惑かけてるやついる気がする」→ 両方とも実測で確認済み (下記 F1 / F2)。
3. t1142 セッション経由で伝達された裁定: 「二度とそんな無駄を繰り返すな、**全セッションに対して
   許さない**」(決定的な赤の再試行ループについて)。
4. 並行セッションと通信してよい。

## 実測した事実 (一次資料は handoff.md、すべて 2026-08-16)

- **F1**: `perf-optional` が 21:01 に land 成功、**release せず**、lease は mtime 21:00 + TTL 2400 秒の
  満了 (21:41) まで残存。その間 6 wave が 11〜50 分待ち。holder digest は `sha256("perf-optional")[:12]`
  で一致確認。
- **F2**: `t1142-oracle-n-pilot` が land rc=29 を 45 秒ごとに再試行し lease を占有。当該セッション
  申告で**計 42 回 (前回 31 + 今回 11)**。真因は決定的 (wave tip の merge 2 本が provenance 新規違反)
  で、`land2.log` 最終行に理由本文があった。親が独立に再現し rc=1 を確認、main 単独は rc=0。
- **F3**: lease 内実作業は中央値 **308 秒** (26 対、`受入 lease 内` merge → 直後の fold)。TTL は 2400 秒。
  max は 4827 秒で、TTL を超えて生存する holder も実在しうる (= 生きた holder から奪う側の危険も同居)。
- **F4**: 機構上、解放を保証する機械は 1 か所も無い。`dev_wave_land.py` は receipt の `lease_holder` を
  **照合するが release しない**。`dev_wave_wait.py` には `release` 動詞が無く、先に claim 済みの wave は
  `HELD_SELF` で「no release authority」と明記して保持したまま返る。runbook §7.3 は
  「成功時は release しない。land の終端で親が release すること」と親の手作業を正本にしている。
- **F5**: D253 の「受容した限界 (iv)」が「release 忘れが連鎖すれば lease TTL 2400 秒に比例する」と
  **明文で予見**していた。今日それが発火した。**承認済み裁定の前提を覆す新事実ではなく、
  受容していた限界にユーザーが実害を認めて根治を指示した**という位置づけである。

## 不変条件 (破ったら停止)

- I1. 受入の受理条件・監査 (DW-O25 の全史 provenance、ff-only、fold、lock) を緩めない。
  release は land が**成功または終端的に失敗した後**にのみ起こり、判定より前には起こらない。
- I2. release は holder 照合が成立するときだけ行う。他 wave の lease に触れない。
- I3. release の失敗は land の成否を書き換えない (main は既に進んでいる)。結果 JSON に記録する。
- I4. 既存の明示 release 経路 (`wave_land_window.py release`) は残し、二重 release は冪等。
- I5. lease TTL・待ち札・通知の意味論を変えない。

## (P1)〜(P4) — 親の provisional 裁定であり段 3 の攻撃対象

- **(P1)** 「terminal」の既定は**手放す側**に倒す。retryable と明示分類した rc (制御面 churn / lock-busy)
  だけ保持を継続し、それ以外 (`landed` / `already-landed` / rc=10 stale-main / rc=29 provenance /
  rc=26 fold / postcondition 失敗 / 未知の rc) は terminal として release する。
  根拠: 未知を保持側に倒すと F1/F2 が再発する。手放して困るのは自 wave の待ち時間だけで、
  正しさゲートには触れない。
- **(P2)** stale-main (rc=10) は terminal に分類する。同じ tested_main では二度と通らず、
  再 merge と受入再走が要るため。
- **(P3)** 終端性は land 結果 JSON の**新 field**として出す (既存 field の意味を変えない)。
  `wave_land_window.py message` の `_load_land_result` は未知 field を受理するので破壊しない (実測済み)。
- **(P4)** TTL 短縮・heartbeat・fencing token は本 wave では扱わない。[T-1172] が未裁定で衝突し、
  [T-649] は見送りで終端済み。terminal-release だけで F1/F2 の両方が消える。

## 変更面 (実アンカー)

| file | anchor | 変更の性質 |
|---|---|---|
| `tools/dev_wave_land.py` | `LandResult` (129 行付近) | 終端性 field を足す |
| `tools/dev_wave_land.py` | `main()` の結果出力 (3098 行 `print(json.dumps(...))`) | 終端なら release を挟む |
| `tools/dev_wave_land.py` | `_acceptance_receipt_is_valid` 系 (563-568 行) | `lease_holder` の再利用 |
| `tools/wave_land_window.py` | `release()` (784 行) | 呼び出しのみ。挙動は変えない想定 |
| `orchestrator/tests/test_dev_wave_land.py` | 新規 | 下記の純増検出力 |

`tools/dev_wave_wait.py` は現時点で**触らない**方針 (t1142 wave と調整済み。触ると決めたら先方へ一報)。
`tools/check_acceptance_reds.py` は触らない (t1142 が同 file を改修中)。

## 既存被覆 (性質で検索した結果) と純増検出力

性質「land の終了後に lease directory の状態がどうなるか」を `orchestrator/tests/test_dev_wave_land.py`
(5829 行) 全体で検索したところ、`lease` の出現は land lock / provenance lock / 受入 receipt の
`lease_holder` 検証だけで、**acceptance lease の在否を land 前後で比較する検査は 0 件**である。
純増検出力は次の 3 つ:

1. land 成功後に lease が残っていたら赤 (F1 の型)。
2. 終端的な赤の後に lease が残っていたら赤 (F2 の型)。
3. holder が自分でない lease を land が消したら赤 (I2 の型)。

**変異は wave 前の実コードの形を必ず含める** — 現行 land は release を一切行わないので、
「release 呼び出しを丸ごと削る」変異は wave 前の実コードそのものであり、必ず事前登録に入れる。

## 成果物の形

コード + テスト + 記録 fragment。`docs/dev-wave/**` は 3 層とも予算満杯のため**編集しない**
(DW-S08 に従い、契約文の是正が必要と判明したらユーザー裁定へ返す)。runbook §7.3 の
「成功時は release しない」記述は実装が変われば事実と食い違うので、段 4 で扱いを裁定する。

## 成果物影響 (DW-G05)

直さない場合、certified 選択・レポート・台帳の**値は変わらない**。変わるのは受入直列窓の実効利用率で、
今日 1 日で F1 = 39 分 × 6 wave、F2 = 42 回の空転が発生した。campaign 反復速度と wave 完了率が落ち、
受入待ちのあいだ計算ノードが空く (F2 の間 qstat は空だった)。

## 受入・実測環境

Pegasus。受入全走は `python3 tools/run_tests.py` を相対・素の名前ちょうどで、
`tools/dev_wave_wait.py acceptance` 経由・背景投入。焦点走は `orchestrator/tests/test_dev_wave_land.py`
と `orchestrator/tests/test_dev_wave_wait.py`。lease dir は
`/work/1/SFC/tanab/dev-wave-jobs/land-lease/`。

## 並列分割方針

軽量版ではなく段 2・3 を回す。理由: 正しさ防壁 (land の終端判定) に触り、受理集合ではないが
**main を進める経路の制御流**を変えるため、DW-C00 の「設計択一が割れる・正しさ防壁に触る」に該当する。
段 3 は 2 レンズ — (a) release が判定より前に起きうる経路・他 wave の lease を消しうる経路の探索、
(b) 終端分類の誤り (retryable を terminal と誤る / その逆) が招く新しい停止・二重走行の探索。

## scope 外 (報告のみ、別 wave)

- **F57 フレーク**の fixture harden ([T-190]/[T-553])。20 件超の再発、恒久対応未実施。
- **ff-only 連鎖やり直し** (`_main_is_allowed`)。緩めるとゲートを弱めるので、健全な軽減は
  merge train / batch land であり別規模。
