---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2724-freeze-v2-g1-candidate
seq: 1
title: [T-2724] freeze v2 g1 候補を official 床値 result から生成し保存 branch に置いた — producer の固定 protocol read を index authority へ直し、runbook W-3 / W-4 の stale を訂正した (コード + docs、branch land-dev-wave-t2724-freeze-v2-g1-candidate、変異 matrix = baseline PASSED・4/4 KILLED・等価 1 SURVIVED・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「完走した official 床値 result (run `20260916T111925Z-2c8cf9be`) を入力に、8b 再開 runbook W-3 の
  freeze v2 g1 候補 document を作る。producer は既に repo にあるので新設せず使い、W-3 の『producer が存在しない』と
  [T-750] carry『実装待ち』の stale を同じ commit で訂正する。読取りは [T-2386] (D2077 / D2078) に従い三軸 literal を
  repo へ複製しない。候補は一度きりの追加で書き approvals/・active/ は作らない。床が配線下限で決まった事実を明示し、
  人間承認の受領証発行まで進めるかを裁定パッケージで返す。W-4 は CLI の呼び手の有無を現物で確かめ無ければ最小の
  呼び手を足す (Codex author)」。
- 一次資料は `output/insights/2026-09-17/t2724-freeze-v2-g1-candidate/README.md`、裁定パッケージは同 `package.md`。
  設計判断は {{D:v2-candidate-producer-resolves-protocol-via-index-authority}} /
  {{D:freeze-g1-candidate-chain-isolation}} / {{D:oracle-manifest-caller-is-operator-cli}}。
- **依頼の前提を 3 つ訂正した。** (1) 候補の固定出力 path は `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`
  で、依頼文と runbook の `output/s8b-freeze/holdout_freeze.v2.g1.json` は世代文書の path (producer が拒否、hook も
  直接 Write を拒否)。(2) `--budget` は承認文書でなく budget 本体を要求する。(3) **「producer は既にあるので使う」は
  そのままでは成立しなかった** — producer は固定 `floor_protocol.json` の literal read で official result を
  `protocol_sha256 不一致` で fail-closed した (ccbench pin `d706650c…` と official 走行の版付き protocol
  `511c9538…` の差)。D589 が「3 条件が揃うまで deferred」と名指ししていた D460 型変換を Codex author で実装した。
- **段 3 の敵対相談 2 本が一致して「保存 branch への隔離は D2077 step 4 (打ち切ると決めてから restore) の決定を
  代替しない」と指摘した。** 親は依頼の候補生成指示を根拠に restore 以降を保存 branch に隔離して実施し、
  「step 4 は未裁定のまま隔離実施」と事実で記録した (「D2077 を満たした」とは書かない)。レンズ B は親 brief の
  「床 = 差の検出下限」を refute した (judge は floor を使わない、D1985 / D2024) — 撤回して記録した。
- **段 6 の実測が段 5 の実装の欠陥を 2 件出した。** 変数 `record` の影で 21 test が `AttributeError` (焦点走 1)、
  新規負例の `master_seed += 1` が str に int 加算。fix 2 巡で解消。レビュー A の指摘で campaign 側文言に依存する
  例外書換えと恒真の bytes 比較を削除した。**変異 M3 (HEAD bytes 比較の削除) は両レビューが「admission 後段が拒否する
  冗長 gate」と静的に判定したが、実測は DID NOT RAISE で producer の比較だけが止めていた** — 静的推測を実測が覆した例
  として記録する。M5 は変更外の既存検査で期待 node が無いため登録から外した。
- **実装子は 3 巡とも計算ノード dispatch を起動できず (`qstat -Q preflight rc=1`) 焦点走を実走していない。** 親が
  計算ノードで実走: 変更 test file 単独 162 passed / 2 skipped、consumer 11 file 669 passed / 2 skipped、いずれも rc=0。
- **`EnterWorktree(path)` が 2 回 timeout した** (worktree 152 本、`git worktree list` 13.7 秒 > 固定 10 秒)。
  回避として chain 木 1 本で branch を切り替え、land 用 branch `land-dev-wave-t2724-freeze-v2-g1-candidate`
  (受入の `--wave` 末尾一致のため) を X0 から切った。当初の wave 木 (`dev-wave-t2724-freeze-v2-g1-candidate`、
  X0 clean) は未使用のまま撤去する。T-2698 の木は古い tip で退避 module を持たず、main 版 module を `sys.path`
  先頭に置く runner で evacuate した。
- 候補: sha256 `7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06`、`frozen_at_head`
  `cc82edc8c9f90a9ee659c2d27f71b75b19a56490`、chain `freeze-g1-chain-t2724` = main `1042a1bc9` → P `3b0b75496`
  (producer 修正、land) → X1' `cc82edc8c` → X2 `4d8fb93b7`。producer rc=0、closure 空、`no-active`、chain 木の
  三軸走査 hit = 専用 4 path のみ、land 木 rc=0。床は両 holdout とも 0.03 × stock 中央値 (rr20 35,817.945 /
  rr80 46,065.78) で、この床値は現行 oracle の判定閾値ではない (g1 発効は driver の null 拒否を解くだけ)。
- **変異 matrix (container 木、commit P、68 node):** probe 走で観測 node を集めてから本走。baseline PASSED、
  M1 (literal read へ復帰) / M2 (記録 path を固定 path に) / M3 / M4 (result hash 比較の削除) = KILLED で期待 node
  完全一致、M0 等価 SURVIVED、rc=0。
- 全 151 worktree の走査で official namespace は T-2698 (1 run) と T-1851 (result 無し 3 run、未退避) の 2 本だけ。
  後者の退避は掃除として裁定パッケージ (e) に注記した。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 2、全段 `gpt-6-astra` / `medium`)。計算ノード job:
  焦点走 3、変異 probe 6 + 本走 6、受入は land 前に 1 回 (結果は land の受領証)。
- `check_docs.py` は記録 commit 前に rc=0。`spool_fold.py --dry-run` と受入全走は記録 commit の後に 1 回投入し、
  結果は land の受領証が持つ (本エントリ作成時点では未実施)。

## 次の一手差分

### 更新

- [T-2724] **P1・候補生成済み → 人間裁定待ち (発効は未)**: g1 候補は保存 branch `freeze-g1-chain-t2724`
  (X2 `4d8fb93b7`、sha256 `7e111406…`) にあり main には載せていない。裁定パッケージ
  `output/insights/2026-09-17/t2724-freeze-v2-g1-candidate/package.md` の (a) 打ち切り = chain の main 取り込み、
  (b) 世代導入 G → approval A → pointer X、(c) 床の採否、(d) growth hold の帰結を人間が決める。
  producer の固定 protocol read は index authority 経由に直して land 済み。
  base: d6c3568a315606c00b6d10d3adf9f2e456e1babe06fff75efab53f2e3a593ecd
- [T-750] **P2・裁定済み・実装済み → 実凍結の人間判断待ち**: producer identity・budget authority は 2026-08-11 に
  ともに (a) で裁定し、freeze v2 g1 producer と oracle manifest `build-approved` CLI は実装済み (commit 66ec0e0e6)。
  2026-09-17 に official result から g1 候補を保存 branch へ生成した ([T-2724])。残件は打ち切り・床の採用・chain の
  main 導入と承認 A → pointer X の判断、reviewed spec の承認 (P-1 の手番)。package の P-1 (pinned literal の恒久形) と
  P-3 (批准 proof chain の budget authorization field) は未解決のまま別管理。
  base: e62d5f59ef7ee5958931d3afd1d84876c09ff4f0463464935fc2a482f825ea26
