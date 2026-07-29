# [T-152] write-intent shadow — 実装・実証・変異台帳 (2026-07-29)

**status: 実装完了・certified pipeline での有効化は pin bump 裁定待ち (not_integrated)**
一次資料: 本文書 + `output/env/pegasus/characterization/t152_write_intent_coverage.json` +
統合 commit afa7325 + ccbench branch izanagi-trace-t152 (c9c1a9c、ローカルのみ・push 待ち)。

## 1. 死角と設計 (要約)

W 行 emit と lock 被覆検査 (X 行) は writePhase で同じ `write_set_` を再走査する。EVOLVE 枝が
要素を落とすと W も X も出ず、verifier には「write が少ないだけの直列化可能な履歴」に見える —
**落とすほど速くなり、かつ certified になる** (worklog 2026-07-28 (27) の素材、規律 2/3 直撃)。

対策 = API 意図の信頼側 shadow (D38 lock_shadow / D42 P 行と同族の第 3 の被覆 assert):
- 記録: insert/delete_record/update の enqueue 成功直後に (storage,key,op,rcdptr) を
  thread_local shadow へ鏡映。delete_record の cancel-previous-write も鏡映
- clear: write_set_.clear() と同じ 2 点 (abort / writePhase 末尾) へ鏡映 — begin() は
  trigger-gating patch の hunk 内 + write_set_ を clear しない点で不適 (lock-step 唯一解)
- 照合: writePhase の W emit loop を shadow-consuming 化。不一致は
  `I <txid> <key_hex> <reason>` (reason = write-set-entry-without-intent /
  intent-missing-from-write-set)。X 同型 4 token・txid 相関
- verifier: parse/model/core/report の 4 層 + critic digest (機構欠落型分類) +
  pipeline correctness gate fixture。I → Integrity.write_intent_violations → clean() →
  **indeterminate** (cycle ではないので serializable の純グラフ事実は不変、D38 決定 1 と同型)

脅威モデル: 閉じるのは **EVOLVE 面からの喪失・捏造** (API 成功〜writePhase)。writePhase 骨格の
改変 (W-loop skip、照合後 drop、forced-abort 型) は DiffQuarantine + diff-of-diffs + auditor +
「hole 内の裸 izanagi_trace 呼びは TRACE=0 で compile error、directive は closed-region 拒否」の
gate 束の領分 (段 3 BG-A1/A5 の裁定)。

## 2. characterization (env=pegasus login node、correctness-only、g++-12)

`t152_write_intent_coverage.json` (all_pass=true、9 checks)。run 7 本:

| run | 構成 | 結果 |
|---|---|---|
| stock_single | YCSB 1thread rratio=0 | I=0/X=0/P=0、certified、153k txns |
| stock_abort | YCSB 2thread zipf0.9 rmw | abort 行使 + I=0、certified、158k txns |
| bomb_smoke | BOMB S1+S3 (2thread) | ops={U,I,D} (3 producer 動的被覆)、I=0、certified、1.29M txns |
| erase (pop_back) | broken patch | I=164512 全て intent-missing、X=0/P=0/cycles=0、**indeterminate** |
| forge (INSERT 捏造) | broken patch | I=149255 全て without-intent、indeterminate |
| opswap (op 改変) | broken patch | I=2 (1+1、両方向)、indeterminate |
| ptrswap (rcdptr 交換) | broken patch | I=569620 (284810+284810)、indeterminate |

characterization の核: **erase/forge/opswap/ptrswap のいずれも cycles=0 = verifier 単独なら
certify する入力で、I だけが決定的に検出** (D38 lockskip / D42 permutation と同型の operative
proof)。broken 4 run は I 以外の integrity 全 counter=0 (単一理由の機械証明、R2-1)。

観測者効果 (規律 1) の実測: TRACE=0 に izanagi_trace シンボル 0 件 (TRACE=1 は 13 件)、
同一パス A/B でシンボル集合・セクションサイズ一致。バイナリ sha は不一致 (46006 bytes =
ERR __LINE__ 即値 + build-id、段 3 BG-B2 の予言どおり) — cross-pin binary identity は元々
契約でない (campaign-id が pin で移動する content-addressed 設計)。TRACE=1 stock smoke は
68.4 万 W 行で I=0。

patch 適合: 既存 standalone 14 本 + layered topology (gating→tally→misattr) 全て c9c1a9c に
apply --check OK。

## 3. 変異台帳 (M1〜M18、事前登録 = 段 4 plan v2 + 段 6 追記 M17/M18)

**最終: 18/18 KILLED・survived 0・injection failed 0** (統合 commit afa7325 に対する本走)。
harness = codex 作 (wave 一時ツール、job tmp)、M17/M18 は親手動 (DW-O19: anchor 一意 assert →
焦点 pytest -rf → git checkout -- 復元 → HEAD 内容照合)。

| M | 層 / 変異 | kill 証拠 |
|---|---|---|
| M1 | C++ UPDATE record 削除 | stock run I=1327863 (全 without-intent)、stock check 赤 |
| M2 | C++ INSERT record 削除 | BOMB run I=531230、同上 |
| M3 | C++ DELETE record 削除 | BOMB run I=275393、同上 |
| M4 | C++ abort clear 削除 | abort 行使 run I=19297 (stale intent、全 intent-missing) |
| M5 | C++ 残余検査 loop 削除 | erase control で I=0 化 → erase check 赤 |
| M6 | C++ 捏造 emit 削除 ((void) 置換) | forge control で I=0 化・certified 化 → forge check 赤 |
| M7 | C++ matcher op 比較削除 | opswap control で I=0 化 |
| M8 | C++ matcher rcdptr 比較恒真化 | ptrswap control で I=0 化 |
| M9 | parse I append 削除 | verifier/pipeline fixture 2 node 赤 |
| M10 | clean() から I 除外 | indeterminate fixture 赤 |
| M11 | core 集計削除 | reasons/notes fixture 赤 |
| M12 | report JSON field 削除 | JSON fixture 赤 |
| M13 | report text 欄削除 | text fixture 赤 |
| M14 | pipeline certified→serializable 誤判定 | pipeline I fixture 赤 |
| M15 | driver checks 恒真化 | synthetic 負例 赤 |
| M16 | driver CLI 例外 return 恒真化 | CLI 負例 subprocess 赤 |
| M17 | parse I の _expect 削除 (親手動) | txid 相関 fixture 赤 |
| M18 | critic I 分類削除 (親手動) | critic 分類 fixture 赤 |

**帰属 erratum (DW-M02、初回結果は消さない):** (i) M1〜M3 の初回は harness spec の期待 reason が
逆方向 (missing を要求。record 削除の正方向は without-intent) で、I が 27〜126 万件発火したのに
SURVIVED と誤分類 → spec を unexpected-positive へ修正し再走で KILLED。初回台帳 =
mutation_results.json (job tmp、集計 killed 12/survived 3/error 1)、再走 =
mutation_results_rerun.json (4/4 KILLED)。(ii) M6 初回は emit ブロック全削除が未使用変数
-Werror でビルド失敗 (ERROR) → emission のみ (void) 置換へ修正し KILLED。
検出力の帰属はいずれも「登録した検査が期待方向の赤を出す」で確定 — 誤っていたのは harness の
追加条項であり、plan v2 の事前登録期待 (どの run が赤か) は全 18 本とも初回から一致。

## 4. 残存リスク (known-limitation、D38 様式)

- (a) writePhase 骨格・trace 層自体の改変は本検査の外 (gate 束の領分、上記脅威モデル)
- (b) delete_record の cancel-previous-write 鏡映は characterization で未行使 (BOMB は同一 txn
  同一 (storage,key) の update→delete を踏まない)。M-cond は DW-M01 に従い不登録。stock の
  cancel loop には erase(itr) 後 ++itr の iterator 無効化 (vector 実装では実害未観測) が
  元から存在する — CCBench stock 挙動のため不変更 (上流判断は人間、D16/D18/D20)
- (c) thread_local shadow は 1 thread = 1 executor 前提 (D38 lock_shadow と同一の既知前提)
- (d) trace stream (ofstream) は I/O エラーに fail-open (trace.hh 全体の既存性質、C/R/W/X/P も
  同罪) — 別ロット起票
- (e) I 行の key は storage を含まない (X 同型) — 同一 key bytes が複数 storage にある場合、
  検出はするが診断が曖昧。storage 識別子の動的歯は BOMB multi-storage で将来可能
- (f) patchharness 内部の git subprocess は timeout なし (共有 infra の既存挙動、hang は
  成果物を作らないため受理集合不変 — R2-5 nit 裁定)

## 5. エージェント工数と裁定痕

codex 9 本 (プラン 1 + 敵対相談 2 + 実装 3 + fix 3) + レビュー 2 + 再レビュー 1 + harness 1
(= codex 計 13)、いずれも gpt-5.6-sol。親 = 裁定・統合・全実測。段 3 で 30 所見 (refuted 1)、
段 6 で 15 所見 (nit 降格 1) + 再レビュー R3 3 所見。全裁定は plan-v2 (job tmp、本 insight が
要約を凍結)。F43 (## 総括 + check_codex_output) は wave 途中で main に land したため後半の
codex 呼び (再レビュー・harness・fix D2) から前向き適用。
