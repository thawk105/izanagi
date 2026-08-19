# s6_sort_sweep write-heavy 偵察実行 (command引数)
- 目的: `orchestrator/campaign/s6_sort_sweep.py` write-heavy workload の sort comparator 偵察 sweep を実行する (command 引数指示)
- 状態: 中断
- 最終更新: 2026-08-19 15:08 JST
- 基準コミット: e0a41cd16cf2df7966acfd9fa1a1db2bcfa93b8e (worktree: dev-wave-s6-sort-sweep-write-heavy-2、作業ツリー clean、計算ノード dispatch は未実行)

## 段1 brief で判明した新事実 (DW-S01 前提実測、DW-STOP 相当)

command 引数は「`--report` で provenance がまだ無いと確認した」ことを根拠に本走実行を指示しているが、
実測の結果、**この task (段6前提タスク (i)、D44) は 2026-07-10 に一度 write-heavy を含めて完走・
certified 済みであり、その後の派生決定で sort 軸自体が放棄されている**ことが判明した。

1. **`--report` の「provenance がまだ無い」は「未計測」の証拠にならない。** 自分でも実行し確認した:
   ```
   provenance がまだ無い: .../output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-e6174b76/reports/s6_sort_sweep_provenance.json (先に本走を回す)
   ```
   campaign identity `e6174b76` は現行 tree 由来。git 追跡済みの既存 provenance が 2 件ある
   (`output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-0484feef/reports/s6_sort_sweep_provenance.json` = 本走、
   `.../sweep-d4552403/...` = cross-run remeasure、いずれも commit `ffa383f4` で導入済み)。
   両方とも `"pin": "d706650"` で certified。現行 `pin.CURRENT_PIN = "511c953"`
   (`fb5e74a1`、[T-816] 手順4、2026-08-12 に前進) と一致しないため identity が変わり、
   「provenance 無し」と出る。**駆動 driver 自身 (`s6_sort_sweep.py`) も `ffa383f4` 以降
   `fb942c52`/`6bd716fe`/`9867082a` の 3 commit で改変されている**が、subject を見る限り
   certification/declared_use_class 配線等の infra 変更であり、comparator 候補列挙や測定手法の
   変更ではない (中身までは未確認、必要なら次セッションで diff 確認)。
2. **`docs/phase3.md` 391 行台 8. 節、369 行台 (i) 節は task 自体を「完了」と明記。**
   D46 (`docs/decisions.md:1574`) = 「sort 軸機械 sweep 先行実測 (段6前提 (i))」。実測記録:
   「32 本走点 + 6 再測点の全てが certified (legacy+s2、anomaly 0)。... write-heavy は sk_ad
   (storage 昇順→key降順) の stock 超えが 2 run 再現 (+3.55%/+4.12%) だが、分解すると lambda 実装差 +
   key 降順寄与の合成で各成分は floor 内、かつ floor は当該域で未較正・系列 n=2 のため断定しない」。
   結論: 「sort 軸に『順序の質』由来の floor 超地形は見当たらない — 段5 iteration2 継続の期待値は下がり、
   軸選定の見直し (段8a 前倒し) で決着済み」。
3. **後継決定 8a も完了済み、sort 軸は放棄されて trigger-gating 軸へ差し替え済み。**
   `docs/phase3.md:396-417` = 「8a 完了 2026-07-12」。sort 軸 iteration2 見送りを受けて
   axis-proposer が新設され、採用軸 `silo-backoff-trigger-gating` が段階 B〜F を完走 (floor 超地形が
   3 workload とも cross-run 再現)。かつ「**低競合動作点での性能探索はクローズし、単独の再ホストはしない**」
   (2026-07-14 裁定) とあり、8a 由来軸 (trigger-gating、sort の後継) すら単独再計測は既に禁じ手。
   現在の主経路は 8b (workload descriptor 化、進行中) と 8c (無人駆動、bounded MVP 済み) で、
   どちらも sort 軸を参照しない。
4. **2026-08-12 ユーザー裁定 (memory: `paper-claims-need-only-coarse-provenance`) が、
   まさに同じ pin bump ([T-816] 手順4) との衝突を契機に成立している。**
   「論文の主張は『どんな CC 合成システムで何が生み出せたか + おおよその時期』で足り、bytes 級の
   凍結証拠は論文に載せない」「既存の凍結チェーン検証は保留 (削除でなく skip)」「**既存機構が pin 前進を
   恒常的に赤にするなら、機構を満たしに行く前に『その束縛は主張に要るか』を先に問う。要らないなら
   束縛の側を記録基準へ緩める案を第一候補にする**」。本件はこの判断基準にほぼそのまま該当する。

## 親の暫定評価 (P1、ユーザー裁定/敵対検討の攻撃対象)

- command 引数の根拠 (「段6本走前の準備」「coder 到達点の空間内位置を記述」) は、上記により
  2026-07-10 (D46) 時点で一度実施・decision 化・2026-07-12 (8a) で軸放棄まで完了した内容の
  再演に見える。「段6本走」という前提自体、sort 軸を対象にする限り現在の主経路 (8b/8c) から外れている。
- pin drift は実在するが、2026-08-12 裁定に照らすと「pin-current backfill のために 16 点を
  計算ノードで再計測する」動機は弱い。研究上の問い (sort 軸に floor 超地形があるか) は既に
  「無い」で決着しており、再計測しても軸放棄の結論を覆す見込みは薄い (write-heavy の sk_ad も
  「floor 未較正・n=2 につき断定しない」と規定済みで、pin を跨いでも同じ限定が付く)。
- 一方 command 引数は D44/docstring/`--list`/`--report` の実測を踏まえた起票に見えるため、
  「pin を跨いだ裏取りをあえて求めている」可能性を完全には排除できない。断定はしない。

## 未完の作業と次の一手

1. ユーザーへ本発見を提示し、次のいずれかの裁定を仰ぐ (提示済み、返答待ち):
   (a) それでも計算ノードで write-heavy 16 点 sweep を pin=511c953 で実行する (backfill の目的を
       明確化した上で)
   (b) stale premise として本 wave を docs のみの carry closure で終える ([T-1408]/[T-699] と同型)
   (c) balanced 側 (sibling 並行 wave) も含め、8a/8b/8c の現状棚卸しを先にまとめてから再検討する
2. balanced workload を並行担当している sibling session (`s6_sort_sweep provenance check`,
   `uds:/run/user/31609/cc-socks/2426768.sock`) へ本発見を共有する (未送信、次のアクションで送る)。
   sibling は compute dispatch 手順を質問してきたが、本発見が先に解決すべき前提問題である旨を伝える。
3. 裁定が出たら:
   - (a) 選択時: 実装ではなく計測 dispatch のみなので codex plan 起草 (段2) は不要。Pegasus
     runbook に従い単独性確認 → 計算ノードへ本走 dispatch (段5 相当) → 結果を
     `docs/spool/worklog/` へ fragment 記録 (段7) → local main 取込 (段9)。
   - (b) 選択時: 本 handoff の発見内容をそのまま fragment 化し (`docs/spool/README.md` 形式)、
     [T-1408]/[T-699] と同じ体裁で「carry を stale として完了で閉じる」worklog entry を書く
     → 段9 で local main 取込。
   - (c) 選択時: 本 wave は継続保留のまま、別途棚卸し wave を起こす。

## 落とし穴・気づき

- `python3 -m orchestrator.campaign.s6_sort_sweep write-heavy --report` は毎回現行 tree 内容
  依存の campaign identity を再計算するため、駆動 driver への無関係な infra commit だけでも
  「provenance 無し」と出る。**「provenance 無し」は「一度も計測していない」の証拠にならない** —
  決定的判定には `git log -- <driver>` + `docs/decisions.md` + `docs/phase3.md` の完了マークを
  必ず突合する。
- D-番号を引用した command 引数でも、その D 自身のタスク台帳側の「完了」マークまでは検証されて
  いないことがある。DW-S01 の前提実測は「引用された decision の結論」だけでなく「その後の派生決定
  (本件では 8a) が premise を上書きしていないか」まで辿る必要がある。
- 本件は 2026-08-12 の「粗い provenance で足りる」裁定 (`paper-claims-need-only-coarse-provenance`
  memory) が具体的にどう適用されるかの一次実例になる。同種の「pin 前進で既存 provenance が赤に
  見える」ケースに今後も再利用できる判断基準として価値がある。

## dev-wave 改善候補 (段8 裁定待ち、暫定記録)

- `DW-S01` の前提実測は「決定の結論」までしか明示的に要求していないが、本件のように
  「決定が指す task 自身が別の完了マーク・派生決定で上書きされていないか」の追跡が必要になる
  ケースが実在した。`DW-S01` (または `DW-G02`/`DW-STOP`) へ「decision 引用時は当該 decision が
  属するタスク台帳の完了マークと、その後の派生決定を辿る」旨を明文化する候補。段8 (本 wave が
  完走した場合) で正式裁定する。
