# 段 1 brief — [T-247] 予約 envelope 検査の恒真を直し宣言済みの拒否を実発火させる

## scope
1. `tools/pegasus/t126_qualification.sh:453-465` の予約 envelope 検査を実際に拒否させる。
2. `tools/pegasus/submit_t126_qualification.sh:189-232` の個別 cap を和でなく個別に凍結する。
3. D96 手続: 新しい D の記録 + 境界テストの同時更新を同じ変更単位で行う。
4. 両拒否経路を実発火させるテストを新設する。
scope 外: 他の readarray ブロックの構造改修 (単発事故 = DW-G03 により族一般化しない)、
policy 値そのものの変更、共有 `tools/pegasus/policy.json`。

## 確定済みユーザー裁定 (worklog (94) 次の一手)
択 (a) 採用。「恒真 (print が raise より前) を直し宣言済みの拒否を実発火させる。個別 cap の凍結も
和でなく個別に行う。受理集合の変更なので D96 の手続を通し、変異の事前登録で実発火を実証する」。

## 段 1 実測 (裁定前提の裏取り。script から verbatim 抽出した fragment を実行、tracked file は無改変)
- **A**: submit 側 189-232 に prologue=1500 / attestation=0 / finalize=600 (和は 29100 のまま) を与え
  **rc=0 で通過**。個別 cap が和でしか凍結されていないことを実証。
- **B**: job 側 453-468 に prologue=1500 を与えると `qualification envelope mismatch` が stderr に
  出るが **rc=0 で通過**し、`PROLOGUE_CAP_S=1500` が下流へ流れる。
- **C**: 同 job 側に walltime=1 / wmax=2 / prologue=3 を与えても **rc=0 で通過**し全値が下流へ流れる。
- 恒真の機序: `for k in keys: print(p[k])` が `raise SystemExit` より前にあり、かつ
  `readarray < <(...)` は process substitution なので子の終了状態を伝播しない。結果、後続の
  guard `[[ ${#RESERVATION_VALUES[@]} -eq 3 ]]` が常に真になる。
- 同型走査: 両 script の readarray/mapfile 9 ブロック中、print-before-raise は L453 の **1 件のみ**。

## 純増検出力 (既存被覆を先に確認した結果)
- `test_reservation_policy_and_job_headers_freeze_wmax_and_walltime` は committed policy の値を
  和 (`calculated == 29100`) でしか固定せず、1500/0/600 を緑で通す = **同じ穴を持つ**。
- `qualification envelope mismatch` / `T-126 reservation policy mismatch` を期待するテストは
  repo に **0 件**。両 script の拒否経路は現在どのテストからも実行されていない。
- 純増 = (i) job 側拒否の実発火、(ii) 個別 cap の個別凍結、(iii) 両拒否経路の実行テスト。

## 不変条件
- DW-O09 閉包: 対象 4 file (job script / submit script / collect script / 予約 policy JSON) の
  bytes を pin する committed 台帳・golden・FROZEN_MANIFEST 項目は **0 件** (各 sha256 と blob hash の
  全文検索で hit なし)。`script_identity` / `code_identity` は submission commit の git preimage から
  実行時に導出される。durable manifest の再発行は不要、DW-O10 は不発火。
- policy JSON の**値は変えない** (member 900 / gap 1800 / prologue 900 / attestation 600 /
  finalize 600 / 和 29100 / walltime 36000)。変えるのは検査側だけ。
- 既存の拒否条件を 1 つも外さない (規律 2: 正しさゲートを緩めない。純増のみ)。
- 共有 `tools/pegasus/policy.json` に触れない (他 campaign の committed evidence が bytes を pin)。

## 成果物影響 (DW-G05)
放置すると、予約 policy が drift しても job 側 guard が黙って受理し job が誤 envelope (実測 C の
wmax=2s 等) で走る → member が途中で kill され finalize reserve が消える → **attempt ledger に
試行欠落が入り**、series-result / final-receipt が「どの gate も検証していない envelope」を載せて出る。
受理集合としては、submit 側が個別 cap 任意の予約 policy を受理し続ける。

## 成果物の形
実装子 patch (script 側 + test 側)、新 D 1 本 (親)、worklog + insights 逐語 (親)。
受入は `tools/pegasus/dispatch_compute.py --task tests` で Pegasus gen_S 計算ノードの全走。

## (P) 親の provisional 裁定 — 攻撃対象
- **(P1)** job 側の修復は「print を検査の後ろへ移す」最小修正でなく、python の終了状態を明示的に
  検査する形にする (process substitution をやめる等)。行数依存の暗黙 guard は同じ事故を再発させる。
- **(P2)** job 側の個別凍結を 8 key 全部へ広げる。現状 job 側は walltime / prologue / wmax の 3 key
  しか見ていない (member_cap / round_gap / attestation / finalize が無検査)。
- **(P3)** submit 側は和の等式 `calculated == 29100` を残したまま個別 3 cap の等値を追加する
  (和は冗長に見えるが独立な検出力を持つので外さない)。
- **(P4)** D96 が要求する境界テストは
  `test_reservation_policy_and_job_headers_freeze_wmax_and_walltime` と同定し、同 test を
  個別凍結へ追随させる。

## 並列分割方針
段 2 プラン起草 1 本 → 段 3 敵対相談 2 本 (レンズ: ①受理集合と正しさ防壁、②bash 実行意味論と偽緑) →
段 5 実装子 1 本 (script と test は結合が強く、分割すると相互に壊す) → 段 6 敵対レビュー 2 本。
