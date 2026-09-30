# 段 1 brief — md_22 [T-2911] read-only commit でも GC の公開を進める (2026-09-29 22:0x JST)

wave `dev-wave-ro-gc-publish` (branch `worktree-dev-wave-ro-gc-publish`)、起点 local main `8fe87f852`、worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish`、job dir `/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/`。
依頼逐語: job dir `inputs/md_22.txt`・`inputs/common.txt`。台帳 item: `docs/worklog.md` の [T-2911] (「Cicada の read-only commit は GC flag を上げない」で 1 件)。

## 研究前進 (1 行)
VHash 論文 U0 (GC 接続) の足場: md_15 が観測した「ro commit が GC flag を上げないための公開停止・公開待ち」(長い ro 1 本で 3 秒公開 0 回、S95/T95 で公開待ちの 76〜77%) を、固定 snapshot の意味を変えない安い変更で解けるかを、小モデル (安全) → Cicada inert variant (判定器) → 同時刻計測 (公開回数・境界の遅れ・生存版・throughput) で確かめる。完了 = 3 つがそろい一次資料に「(a) で解ける分 / (b) snapshot を動かさないと解けない分」を分けて書けた時点。

## 実物の読み (pin `68106660`、行番号はこの版)
- `cc/cicada/transaction.cc`: begin() 39-43 で wts を採り ThreadWtsArray へ、`rts_ = MinWts − 1` を ThreadRtsArray へ (2 手)。ro の読みは rts_ (93-97)。
  mainte() 859-893 は GCExecuteFlag が立っていれば自分の gcq を回収 (gc_versions 806: MinRts 未満の版の後ろを切る) し、timer 満了かつ flag==0 なら GCFlag[thid]=1。
  mainte は update commit (954) と abort (767) でだけ呼ばれ、ro commit (934-937) は read_set_/node_map_ を消して return する。
- `util.cc` cicadaLeaderWork 281-324: 全 thread の flag が 1 のときだけ MinWts=min ThreadWts、MinRts=min ThreadRts を公開し、全 flag を 0・GCExecuteFlag を 1。leader は worker 0 のループ先頭 (`include/ycsb.hh` 109)。
- 既知の暗黙不変条件 (md_14 の実測、記憶 model-protection-vs-implementation-invariant): 既読版を守るのは「ThreadRtsArray = tx 開始時の MinWts−1 を tx の間変えない」。

## 確定済みの裁定・事実 (覆さない)
- common.txt: 所有外は読むだけ。external/ccbench gitlink・`docs/paper-story-vhash/` を書かない。CCBench 改変は inert patch。正しさ未検証の性能値は「未検証の診断値」。2 node 時間以上は投入せず止める。性能は計器・trace なし build で同時刻対照。
- ユーザー裁定: byte 級 inert witness を必須ゲートにしない (非致命の観測として残す)。計器の有無と arm ラベルの一致は緩めない。
- Cicada variant patch は `patches/ledger.json` に登録しない (D2288 と同じ。同台帳は silo_ladder_rung1 専用 entry 1 件を契約が要求)。README だけに entry。md_22 の「ledger の entry」との食い違いとして記録。
- 実測 (本 wave、job dir `probe-stack.sh`): `instr-cicada-trace.patch` と `instr-cicada-version-lifetime.patch` (vlife) は git apply (fuzz なし) でどちらの順でも重ならない (transaction.hh:35 と transaction.cc:931 付近で衝突)。
- vlife の ro 比率 flag `izanagi_ronly_pct` は `IZANAGI_CICADA_VLIFE` の内側。長い tx の型 (`izanagi_long_kind`) は `IZANAGI_CICADA_LONGTX`。
- md_20 (最良設定の判定器通し) は並行中で main に結果なし。最良設定の正しさは本 wave では前提にしない (未検証と明記)。

## 仮裁定 (親の provisional、段 3 の攻撃対象)
- (P1) Cicada の版回収の安全は per-thread の ThreadRtsArray (tx の間不変・thread ごとに単調) が担い、GC flag は「公開の頻度・quiescence の宣言」を担う。YCSB (delete なし) では flag の立て方は版の安全に効かない。よって ro commit の終わり (read_set_/node_map_ を消した後) で mainte と同じ条件で flag を立てるのは安全。
- (P2) 小モデルの正例 (危ない版) は「flag の立て方」ではなく「下限 (slot) の扱い」で発火する見込み: (i) ro tx の途中で slot を新しい MinWts−1 へ上げる (snapshot を動かす (b) 型)、(ii) ro commit で slot を ∞ (保持しない印) にし、begin の 2 手の間に公開が入って下限が公開値より下がる。(iii) ro begin 時点で flag を立てる (参照が残るうちに立てる) は、版については安全と出る見込みで、それ自体を「flag は版を守っていない」証拠として記録する (正例に数えない)。md_22 の例示 (flag を上げる前に参照が残る・境界を下げる) との対応をこの形で書く。
- (P3) 実装: macro `IZANAGI_CICADA_RO_GCFLAG` (既定 0 で stock と同じ挙動)、1 で ro commit が read_set_/node_map_ を消した後に `mainte()` を呼ぶ (GC 実行部を含めるかは段 2 で比較、親の仮は「mainte 全体」)。flag の代行 (他 thread が立てる) は実装しない (設計メモのみ)。
- (P4) patch の重ね: variant は pin 単独・pin+trace・pin+vlife の 3 通りに厳密適用で当たる必要がある。1 file で無理なら `cicada-ro-gcflag-variant.patch` (pin / pin+trace 用) と `cicada-ro-gcflag-vlife.patch` (pin+vlife 用) に分け、同じ変更であることを test で照合する。
- (P5) 計測: 新 driver は md_15 の `vhash_cicada_vlife.py` を import で再利用 (編集しない)。md_11 最良設定 (TUNED_GENOME) を土台に、ro 指定率 {0,50,95} × 長い ro {none, wait10msR} × skew {0.9, 0} × gc {10 µs, 1 ms} × arm {stock, variant} × 3 反復を計器 build で、throughput は計器なし build (ro は YCSB の読み比率で作る) で、各 job 内で stock と variant を交互に走らせ同時刻対照にする。見積り < 1 node 時間。

## 不変条件
- 小モデルの既存場面・既存 option の結果を 1 行も変えない (新しい部分は既定 off の別 module / option)。既存テスト全緑。
- 既定 build (macro 0) の挙動は stock と同じ。正しさ: variant は trace build で判定器に掛け、巡回が出たら即失格 (規律 2)。判定の上限は indeterminate、certified と書かない。
- 性能値は計器・trace なし build だけ。計器 build の値は診断値。md_18/md_20/md_21 と同時に同じノードを使わない。
- 所有外 (vlife patch・trace patch・forwarding / interval patch・vlife driver・external/ccbench) を編集しない。

## 成果物
tools/vhash_forwarding_model/ の追加 + テスト、patches/cicada-ro-gcflag-*.patch と patches/README.md の entry、新 driver + テスト + 登録簿 (condition gate・materializer・screening 既定値・loop test 許可表・tests/README allowlist)、作図、一次資料 `output/insights/2026-09-29/vhash-readonly-gc-publish/README.md`、spool fragment (worklog: T-2911 完了/更新、decisions: 設計の選択)。

## 分割
段 5 の Codex author 2 本 (所有が交わらない): A = 小モデル (tools/vhash_forwarding_model/ と orchestrator/tests/test_vhash_forwarding_model_rogc.py)、B = patch・driver・登録簿・driver テスト・作図。計算ノード実行・受入・記録は親。
受入・実測環境: Pegasus login (静的検査・pytest)、計算ノード (build・判定器走行・計測、`docs/pegasus-runbook.md`)。
