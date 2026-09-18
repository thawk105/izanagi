---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2774-mocc-torn-read-probe
seq: 1
title: [T-2774] stock mocc (RWLOCK 版、e9e477ca) の静的反例候補 (a) を計算ノードで実走検証した — G2 signal は witness を切った producer でだけ再現 (2/40・3/40・2/40、T-1892 と同形) し、discriminator の観測条件 (witness on) では 0/40 で読み値の出所照合は未達 (docs のみ、probe は job dir、branch worktree-dev-wave-t2774-mocc-torn-read-probe、変異 matrix 免除 = repo 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2774] (D2114 理由節、insight §3.2 (a)) stock mocc (RWLOCK 版、hook branch 先端 e9e477ca) の静的反例候補 (a) を
  計算ノードで実走検証する — cold 読みの counter 検査 → body 読み → 版の再読と、validation の版比較 → counter 読取の別読みで torn read が
  commit しうる (G2 anomaly 5/42 の根因候補)。仮説 = 多 thread・hot key・小 value で確率が上がる。payload lineage discriminator
  (`orchestrator/campaign/mocc_g2_discriminator.py`、T-1943) で読み値の出所を照合し、再現 / 未再現を構造化して insight へ。(b) absent
  非検査 (DELETE 経路) は同梱しない。CCBench 本体の改変は D16/D18/D20 に従い insight 構造化まで、上流 PR は人間判断。probe は job dir に
  置き repo へ入れない。成否で mocc の certified 昇格判定は変えない。[T-2772] と独立。規律 2 を緩めない。本題の検証だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた (再現 / 未再現を構造化した。読み値の出所照合は discriminator が 1 件も発火せず未達)。** 一次資料は
  `output/insights/2026-09-18/t2774-mocc-torn-read-probe/README.md`。decisions fragment 0 (新しい設計判断なし。段 4 の手段変更は
  wave 内の親裁定として insight §9 と `verbatim/s4-ruling.md`)。failures fragment 1 ({{F:mocc-pilot-hydrate-interpreter-regression}}
  新規 + F102 再発)。
- 主判定 (段 6 レビュー A の文案を採用): BACK_OFF=0 の固定 cell で、producer・計装・witness・診断変更の鎖 (`p058-plain` = T-1892 の
  producer → `e9-plain-nowit` → `e9-instr-nowit` → `e9-instr-wit` = discriminator 条件 → `e9-diag-wit`) に沿った G2 signal 検出数は
  **2/40、3/40、2/40、0/40、0/40** (各 arm 40 走、4 node × 10 round、失敗 0)。7 件の cycle は全件 長さ 2・両辺 rw・別 thid・同 epoch・
  commit tid 差 1 で T-1892 の 5 件と同形 = validation の別読みによる静的候補 (a) と整合する形。しかしすべて witness off で、
  payload-lineage 識別には到達しなかった。witness on での未再現 (0/40、BACK_OFF=1 の Q1 も 0/56) は観測者効果の仮説 (witness の S 行が
  publish `M:1195` と unlockCLL `M:1207` の間に入り、R の 2 load が跨ぐべき区間を伸ばす) と両立するが、片側 Fisher は 0.128〜0.247 で
  有意でなく、診断効果・各間隙の寄与・根因・hook / verifier 仮定の分岐は確定しない。T-1892 の 5/42 (CI [0.040, 0.256]) と
  `p058-plain` 2/40 は区間が重なる (環境同等性の実証ではない)。value size の仮説は未実測。
- **段 3 が親 brief を 3 点で覆した (全件 real・採用)。** (1) 現行 verifier は `e4c949f08` (09-03) 以降 mocc の X/P emitter の
  `evidence-present` を integrity clean の条件にするため、素の e9e477ca (X/P patch なし) は cycle 無しでも `indeterminate`、discriminator
  も `verifier-integrity-dirty` で `indeterminate` になる → producer を「e9e477ca + `patches/instr-mocc-lock-coverage.patch` (D1686、
  TRACE 専用)」に変更し、既存 pilot 経路 (腕 A) と pilot の hydrate 局所修正 (scope 0) を撤回、job dir の runner を単一計器にした。
  (2) 「supported ⇔ validation 隙間のみ / contradicted ⇔ 読み段の隙間も」と「どちらも実装由来の証拠」は不成立 → 段 2 plan §2 の限定表。
  (3) 「診断 build 0/K ⇒ 必要性 ⇒ 根因」は撤回。
- **親の見落とし 2 件を wave 内で是正した。** (a) runner が T-2294 driver の configure (`BACK_OFF=1`) を流用し、最初の 4 block (Q1、
  instr 0/56・diag 0/56) は T-1892 / T-1943 の pilot (`BACK_OFF=0`) と build 条件が違った → Q1 を観測に格下げし、走行前に事前登録して
  Q2 (5 arm 鎖、`BACK_OFF=0`) を主解析にした。(b) runner の `classify` が verifier rc=3 (indeterminate、`serializable` true) を
  `failure` に誤分類 (X/P 無し arm の非 G2 走 75 件、k は不変) → fix 3 で是正し、保存済み verifier.json から `summarize --reclassify`
  (原本は不変、変更一覧を summary に記録)。
- 段 6 レビュー A (正しさと主張) / B (実行と収集) はともに **GO** (観測記録として)、must-fix 0、should 4 (検出率と判定確定率の区別 /
  識別未到達・診断効果未確認を主判定に / cold abort の適応挙動と曝露量 / runner の版束縛)、nit 5。全 314 走の JSON と G2 raw 336 file の
  manifest 一致、診断適用後 source の sha (`1c5da7c8…`) と 4 block の binding の一致、7 件の cycle 形を raw C 行まで独立検算。
- 段 2 plan の 1 本目は上流 classifier「cybersecurity risk」で最終出力を失った (F102 再発、途中結論 3 点は回収)。前置き節 + 語彙中立化の
  v2 で受理。
- 見つけた欠陥 2 件 (本 wave では修正しない、insight §8): `tools/pegasus/mocc_trace_pilot.sh` の hydrate (1534 行) が素の `python3` で
  driver を import し T-548 以降は計算ノードで rc=2 (job `4936.nqsv`) → {{F:mocc-pilot-hydrate-interpreter-regression}}。同 pilot は
  X/P patch を当てないので 09-03 以降 mocc を certified にできず、`--t1943-g2-discriminator` mode は `indeterminate` しか出せない →
  {{T:mocc-pilot-restore-certified-mode}}。
- 実走: smoke 1 job (80 秒)、Q1 4 job (各 28 走、10.6〜10.9 分)、Q2 4 job (各 50 走、18.4〜18.6 分)、すべて gen_S 1 node、generic
  dispatch を 4 worktree から並行投入 (同一 worktree の並行は orphan hold のため)。verify 1 走 10〜23 秒。撤回した pilot 経路の生死確認
  1 job (9 秒で rc=2)。login: selftest ×4 (10/10 → 13/13)、`git apply --check`、集計。受入全走は land 前に 1 回 (結果は land の受領証)。
- 工数: codex 子 10 本 (plan 2 (1 本目遮断)、consult 2、author 1、fix 4 (うち 1 本は親が途中停止)、review 2、全段 `gpt-6-astra` /
  medium)。親: 現物検算 (transaction.cc、verifier model/cli、discriminator、pilot、driver)、Fisher / CP の算出 (レビュー A が再計算して一致)。

## 次の一手差分

### 完了

- [T-2774] (a) の実走検証を insight に構造化した (再現 = witness off producer で 2/40・3/40・2/40、未再現 = witness on で 0/40、
  discriminator 発火 0 件、原因 3 分岐と診断効果は未確定)。certified 昇格判定・pin 前進・変異探索の解禁は変えない。
  remaining: none
  base: 2ea7b1cd6b92995b816151824b675b1afd9f77af97e2ff31a653f85a99bdfa1e

### 新規

- {{T:mocc-g2-witness-light-and-diag-offwit}} **P1・新規** (T-2774 insight §1 3〜6、§7): discriminator の観測条件で G2 を得るために
  (1) witness を軽くする案 (S 行の書出しを `unlockCLL()` の後へ移す等。TRACE=1 の hook branch 上の変更、D16 の trace-hook 分類) の静的設計と
  (2) 診断 patch を witness off で走らせる対照 (`e9-instr-nowit` 対 `e9-instr-nowit + 診断`、各 40 走以上)、(3) `BACK_OFF=1` の witness off
  arm による backoff 効果の分離、を 1 wave で実測する。runner は job dir `probe/t2774_probe.py` (v4、`--arms-json` で arm を足すだけ)。
  率差の 80% 検出力には各 arm 56 走以上 (T-2774 段 3 レンズ B)。成否で certified 昇格判定・pin 前進は変えない。本題の実測だけ、gate・
  台帳の新設は scope 外。
- {{T:mocc-pilot-restore-certified-mode}} **P2・新規** (T-2774 insight §8、{{F:mocc-pilot-hydrate-interpreter-regression}}):
  `tools/pegasus/mocc_trace_pilot.sh` の `--t1943-g2-discriminator` mode を現行 verifier で成立させる — (1) hydrate (1534 行) の直前に
  checker / verifier gate と同型の `HYDRATE_PY` 選択 block を置き契約 test 1 本を足す (設計は T-2774 `verbatim/s2-plan.md` §4)、
  (2) X/P 計装 patch (`patches/instr-mocc-lock-coverage.patch`) を build 前に適用する経路と receipt の束縛 (patch sha) を足す、(3) 計算ノードで
  生死確認 1 本を discriminator の finalization まで通す (T-1943 の分類段 rc=2 の修正 `267741106` も compute 未実走)。既存 test の marker
  一意性を壊さない。変異 matrix は負例 3 (素の python3 に戻す / version 比較を外す / rejected 記録を外す) を新 test で KILLED。
