---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-forwarding-model
seq: 1
title: [T-2877] VHash の選択的 forwarding を小さいモデルで書き、10 場面の割り込みを全探索した。v0 (出典メモ §4 の Cicada 前提を模した書き込み検査) は 3 txn で閉路反例を出し、規則 R9' を足した v1 と v1+O1 (確認済み区間で commit 時検証を省く) は固定場面の範囲で反例なし (コード + test + insight、branch worktree-dev-wave-vhash-forwarding-model)
---

## 本文

- 依頼: 並行 VHash wave の md_4 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_4.txt`、出典メモ §29 段階 2)。ユーザー就寝中のため、判断は codex の相談・レビューで決めた (マネージャーの連絡 2026-09-29 03:22)。対象 item [T-2877] は wave 開始時点の local main に無く、受入全走 2 回目の後の main 前進 merge で現れたので、完了として閉じた (記録の変更に伴い受入を取り直した)。
- 正本: `output/insights/2026-09-29/vhash-forwarding-model/README.md` (仕様、場面、63 構成の結果表、反例の最短列、規則と反例の対応表、範囲と確かめていないこと、変異検査)。設計判断は {{D:vhash-forwarding-model-spec}}。
- 素材: v0 の直前版だけの rts 検査は PENDING 版に遮られて閉路反例を出し、R9' で消える (一次資料 §7.1)。出典メモ §13.1・§13.3・§14.1・§15.2・§15.3 の各点は 1 規則だけを崩した危ない版の反例で裏付けた (同 §0・§7.3)。
- 段 3 相談 2 本 (レンズ: 正しさ境界 / 実効性・過剰): 所見はすべて real・採用。最重要は v0 の PENDING 越しの検査漏れの予想 (探索で確認) と、GC 判定の恒偽化の指摘。親の予想「最終検証があれば v0 に serializability の反例は出ない」は撤回した。
- 段 6 レビュー 2 本 + 焦点再レビュー 2 巡: 1 巡目 must-fix 1 (回収済み版への接触の検出経路の網羅)、2 巡目 must-fix なし。未修正の should-fix 1 件 (故障帰属の補助関数の偽陽性経路) は一次資料で帰属の根拠に使わない形で閉じた。
- セッション異常 (モデル自身の欠陥): v1+O1 に偽の閉路反例が出たのを、親が反例列の時刻を読んで発見した ({{F:model-checker-false-counterexample-from-duplicate-timestamps}}、一次資料 §9)。
- 段 7 の docs 事実照合レビュー 1 本: 所見 6 件中 real 5 (変異表の本数表記、S9 の witness の例外、試作への持ち込みの範囲表現、§0 の Cicada 表記、worklog の結果の重複) を修正、refuted 1 (依頼文 path は原本の path で正しい)。
- 受入全走 1 回目は赤 2 件 (いずれも本 wave に帰属: inventory test が探索の打ち切り判定の `perf_counter` を性能計測の述語と検出、新 test file に自走 harness が無い)。fix9 で直した。親の焦点走が `DW-O26` の inventory・メタテストを含めていなかった (F242 再発、一次資料 §11)。
- 親の裁定の誤り 2 件: 場面 witness に危険結果そのものを書いた (正しい版で到達しないのは当然、fix5 が停止)、述語の変更に従属する test の pin の更新許可を書き漏らした (fix6 が停止)。いずれも子は規律どおり期待を変えずに止まった。
- エージェント工数: Codex plan 1・consult 2・author 1・fix 9 巡・review 3 (段 6 の 2 本 + 段 7 の docs 1 本)・focus 2 (いずれも gpt-6-sol / medium)。子の worktree `.claude/worktrees/vhash-fwd-author` (branch vhash-fwd-author, vhash-fwd-fix1〜9)。計算ノード: 焦点走 1 本 (queue 待ち 900 秒で未実走)、変異の dispatch 本走 13 request (11 変異すべて事前登録どおり、一次資料 §8・§11)。本走は 13 request を直列に queue するので混雑時に約 1.5 時間かかった。runner 経路を含まない変異なら D842 の束ね経路 (`--task mutation`) で 1 job にできた。

## 次の一手差分

### 完了

- [T-2877] 選択的 forwarding のプロトコル (仕様 v0 / v1 と選択肢 O1) を小さいモデルで書き、reader・writer・forwarding・GC の割り込みを 10 場面の固定初期状態から全探索して、serializability (依存グラフの閉路) と GC 安全を判定した。v0 の反例から規則 R9' を足し、規則と反例の対応表を一次資料に残した (`output/insights/2026-09-29/vhash-forwarding-model/README.md`)。範囲外 (lock-free 性、弱いメモリ、途中入場、read-only 経路、不在キー等) は未主張と明記した。
  remaining: none
  base: be51a6c2d813ca8ddcb1f5d45d5eb47d83a065ac0dc21b78193f44402ac1165c

### 新規

- {{T:vhash-cicada-pending-predecessor}} **P2・新規**: Cicada の書き込み側 rts 検査が、本 wave の v0 反例 (直前版が PENDING のとき下の確定版の rts を見ない) と同じ形を持つかを、Cicada の原論文と CCBench の Cicada 実装で確かめる。持つなら、md_3 が着地させた Cicada の trace 計器 (D2279、`patches/instr-cicada-trace.patch`) と判定器で再現を試す。根拠: `output/insights/2026-09-29/vhash-forwarding-model/README.md` §7.1。
