# 段 4 裁定 — [T-740] 待ち手の正本 script

段 3 の 2 レンズ (A = 正しさ境界と受理集合、B = 実効性と consumer 到達) の全所見を
real / refuted、採用 / 不採用、scope 内 / 外に裁定する。

## 裁定表

| ID | 判定 | 採否 | 理由 |
|---|---|---|---|
| A1 (受理式の欠落) | real (部分) | 部分採用 | 下記 R1・R2 へ分解。lease dir と「直ちに投入できる状態」は不採用 |
| A2 (signal / timeout / 親死) | real | 採用 → R3・R4 | 散文でも閉じていないが、script なら安価に閉じられる |
| A3 (release 権限が wave digest だけ) | real | 不採用 (既知限界) | runbook §7.3 が「release の権限証明は wave slug の digest だけ」と明記済み。解消は `wave_land_window.py` の改変 = scope 外 |
| A4 / B6 (PID reuse・identity) | real | 採用 → R5 | `/proc` start-time 束縛は安価で、「producer の死」を実保証にする |
| A5 (pattern 面テストが恒真) | real | 採用 → R7 | 本 wave の中心的防壁が恒真化する |
| A6 (negative テストの到達証明なし) | real | 採用 → R8 | |
| A7 / B14 (変異の帰属不成立) | real | 採用 → R9 | 変異を実効 predicate へ再照準する |
| A8 (claim 出力契約の一般化) | real | 採用 (契約の限定) | rc=0 の通常結果だけ JSON と仮定する |
| A9 (registry 不要の理由が誤り) | real | 採用 (理由の訂正のみ) | 結論は不変。実装差分なし |
| A10 / B11 (poll 30〜120 vs 10) | real | 採用 → R12 (P5 撤回) | |
| B1 (lease が land 前に解放される) | real | 採用 → R1 | 現行散文との非同値 |
| B2 / B3 (consumer 未結線) | real | **不採用 (scope 外) → 裁定パッケージ** | 裁定 (a) は「runbook §7.3 から参照する」まで。command / `docs/dev-wave/**` への結線は未裁定で、L1 は [T-738] (c) が終端済み |
| B4 (任意 command / `-rf`) | real (両方) | 分割: 任意 command は不採用 (裁定へ)、`-rf` は採用 → R11 | |
| B5 (無限待機) | real | 採用 → R4 | 参照実装 (t683) も上限付き loop だった |
| B7 (死後の file 可視性) | real | 採用 → R6 | |
| B8 (誤 tree への merge / commit) | real | 採用 → R2 | script 化で新たに開く穴なので塞ぐ |
| B9 (merge message の provenance 未検査) | real | 採用 (限定) → R10 | trailer 行の実在検査まで。意味検査は `check_ai_provenance` の職掌 |
| B10 (最終再検査〜投入の残余 race) | real | 不採用 (既知限界) | runbook §7.3 に既記載。fencing token 不在は本 wave で閉じない |
| B12 (P1 の 1 ファイル) | nit | 不採用 | P1 維持。mode 別 preflight は R2 で入る |
| B13 (fake 中心のテスト) | real | 採用 → R8 の結合検査 | |
| B15 (過剰実装) | 部分 real | 部分採用 | `--pid` と rc 分類は残す。poll は R12 で 30〜120 に固定 |

## 採用した must-fix (プラン v2 への差分)

- **R1 — lease の寿命を現行散文へ揃える。** 受入 command が rc=0 で終わった場合は
  **release せず lease を保持したまま** rc=0 を返し、「lease は保持中であり land 終端で
  release すること」を stdout に 1 行出す。**それ以外の全終端 (claim 異常・Git 異常・merge 中止・
  受入赤・例外・signal・中断) では release する。** 根拠 = runbook §7.3「受入と land の
  どの終わり方でも release する」および command 段 9「受入・land の終端で必ず release」。
  受入直後に無条件 release すると、今日は存在しない「受入完了〜land の間に他 wave が
  land する窓」を新設することになる。
- **R2 — 起動 tree の identity preflight (claim より前)。** 次を順に確認し、1 つでも
  外れたら claim せず rc=2 で止める。(i) cwd が git work tree の中である。
  (ii) HEAD が detached でない。(iii) 現在の branch 名が `--wave` の値で終わる
  (runbook の「wave slug = branch 名の末尾」規約)。(iv) tracked file に未 stage / stage 済みの
  変更が無い (untracked は対象外 — job artifact や dispatch receipt を誤って弾かないため)。
- **R3 — catch 可能な signal を release 経路へ通す。** SIGTERM / SIGHUP / SIGINT に handler を
  置いて例外へ変換し、`finally` の cleanup を通す。SIGKILL と host 停止は TTL 任せと明記する。
- **R4 — 待機に上限を置く。** `acceptance` の claim loop は `--max-wait-seconds` (既定 7200) を
  超えたら release して非 0 で返す。参照実装 (`dev-wave-t683-caller-closure/run_acceptance.sh`) も
  `seq 1 1200` の上限付き loop で rc=90 を返していた。`producer` は既定無制限とし、
  `--max-wait-seconds` を任意で受ける (段 2 の codex 子は数十分〜数時間走るため既定で切らない)。
- **R5 — producer identity を start-time で束縛する。** 初回観測時に
  `/proc/<pid>/stat` の 22 番目 field (starttime) を取り、以後の生存判定で照合する。
  値が変われば「別 process (PID 再利用)」= 元 producer は死んだ、と判定する。
  `/proc` が読めない環境では pid のみへ degrade し、その旨を stderr へ 1 行出す
  (黙って縮まらない)。
- **R6 — producer 死後の file 検査に bounded grace を入れる。** 死亡確認後、
  `.done` と成果物の両方が揃うまで 5 秒間隔で最大 30 秒だけ再確認し、それでも欠ければ rc=70。
  完成した producer を NFS の可視性遅延で失敗扱いにしない。
- **R7 — pattern 面の不存在検査を恒真にしない。** (i) producer parser の全 `option_strings` を
  収集し、**テスト側に独立に書いた literal 集合**と exact 比較する (production から import しない)。
  (ii) 利用者入力の positional action が 0 件であることを確認する。
  (iii) `--pattern X` / `--match X` / 余分な positional が公開 CLI で rc=2 になることを確認する。
- **R8 — negative テストに到達証明を入れ、default wiring を 1 本結合検査する。**
  各 negative case で `_Effects` の呼出し列を exact 比較し、対象段が 1 回走ったこと・
  後段と受入 command が 0 回・release が 1 回であることを固定する。加えて、fake を使わない
  結合検査を 1 本置く: 一時 git repo + 一時 lease dir + 無害な command で、
  実 `wave_land_window.py` との配線 (shell 不使用・cwd・capture) を確認する。
- **R9 — 変異を実効 predicate へ再照準する** (`DW-M01` の単一理由性)。詳細は下節。
- **R10 — merge message file の最小検査。** 非空であること、かつ `AI-Agent:` で始まる行を
  1 行以上含むことを、`git commit --dry-run -F` の前に確認する。満たさなければ merge せず
  (merge 進行中なら `--abort`)、release して非 0。意味の正しさは `check_ai_provenance` の職掌とし、
  ここでは重複させない。
- **R11 — §7.3 の canonical 例に余計な flag を足さない。** 受入全走は
  `python3 tools/run_tests.py` の裸形とする。**実測で確認済み**: `-rf` は
  `tools/run_tests.py:505` の `_is_acceptance_run` で `_NONSELECT_FLAGS` にも `{q,v}` 部分集合にも
  該当せず default-deny に落ちるため、acceptance 判定が False になり事前検査 (削除 gate ほか) が
  黙って無効化される。段 2 プランの例 (`-q -rf`) はこの欠陥を持っていた。
- **R12 — poll は runbook 正本の 30〜120 秒、既定 30 秒。P5 (10 秒) は撤回する。**
  根拠 = F196「待ち周期を 120 → 30 → 10 秒へ詰めても、追い越しの原因は周期ではなく
  待ち行列長なので消えない」。正しい対策は待ち手内 merge であり、プランは既にそれを持つ。

## 不採用 / 既知限界として明記するもの

- lease directory の canonical 強制 (A1): `--lease-dir` 省略時に `IZANAGI_WAVE_LEASE_DIR` を
  使うのは `wave_land_window.py` 自身の契約であり、待ち手が上乗せの gate を作ると受理集合が変わる。
- 「直ちに受入を投入できる状態」(A1): 人間の事前条件であり機械化しない。runbook に残す。
- release 権限が wave slug digest だけ (A3)、最終再検査〜投入の残余 race (B10)、
  SIGKILL / host 停止 (A2): いずれも runbook §7.3 の既知限界に既記載。本 wave で閉じない。
- 受入 command が本当に全走かの強制 (B4 前半): 実装しない。台帳への記録責任は親にあり、
  待ち手を記録の権威にしない。ただし実行した argv を逐語で stderr へ 1 行出す。

## ユーザー裁定へ返す (scope 外の real 所見)

- **U1 (B2 / B3) — consumer を canonical script へ機械的に結線するか。**
  本 wave が実装するのは「script の新設」と「runbook §7.3 からの参照」までで、
  `.claude/commands/dev-wave.md` の段 6 / 段 9 と `docs/dev-wave/` の `DW-C00` / `DW-O01` は
  従来どおり手書き待ち手を許したままである。**正本を作っても読まれなければ F191 / F192 / F32 は
  止まらない**というのがレンズ B の中心的主張であり、これは正しい。
  選択肢 = (a) command と `DW-O01` を canonical invocation へ結線する (L1 に触れるため
  [T-738] (c) の再訪が必要) / (b) runbook 参照だけで留め、結線は実害の再発を待つ。
  成果物影響 = (b) のままなら手書き loop が残り、無音死と誤判定の再発経路が閉じない。
- **U2 (B4 前半) — 受入 command の identity を待ち手が強制するか。**
  選択肢 = (a) `--` の argv が `tools/run_tests.py` の acceptance shape であることを検査する /
  (b) 任意 argv のまま親の記録責任に委ねる (本 wave の実装)。
  成果物影響 = (b) のままなら `-- true` でも rc=0 になり、待ち手 rc を受入完了の証拠として
  誤読する余地が残る。

## 変異事前登録 (`DW-M01` / `DW-M04` / `DW-M08`)

段 6 の fix 後 anchor で再検証してから本走する (`DW-M07`)。
各変異は「同じ入力を拒否する層が前後に無いこと」「赤理由が一つに絞れること」を
実装後に確認してから登録を確定する。

| # | 変異 | wave 前の実コードの形 | 期待 |
|---|---|---|---|
| M1 | producer の生存判定を、pid ではなく待ち手自身の argv に載る文字列の照合へ差し替える (`pgrep -f <pattern>` 相当) | `dev-wave-jobs/t139-addendum-b/wait6.sh:6` の `until ! pgrep -f "..."` と、F32 再発時の `wait.sh <done> <artifact> <pattern>` | KILLED |
| M2 | 受入投入の可否を決める predicate を `state == "acquired"` から `"acquired" in <claim stdout 全体>` へ差し替える | `dev-wave-jobs/dev-wave-t683-caller-closure/run_acceptance.sh:22` の `case "$out" in *acquired*)` | KILLED |
| M3 | 成功終端で lease を release する (R1 の反転) | — (段 2 プランの初版) | KILLED |
| M4 | `git rev-list --count HEAD..main` の再検査を削る (merge 後に確認しない) | — | KILLED |
| M5 | merge が必要なのに message file 未指定でも merge を続行する | — | KILLED |
| M6 | 失敗経路の `release` を落とす (`finally` を除去) | — | KILLED |
| M7 | producer の死亡判定後に `.done` だけを見て成果物を見ない | `wait6.sh:3-8` (`.done` 2 つだけで判定) | KILLED |
| M8 | branch identity preflight (R2 iii) を除去する | — | KILLED |

**M1 と M2 は memory `mutation-must-include-pre-wave-form` が要求する「wave 前の実コードの形」
そのものである。** 変異 spec の key は 6 つ固定 (`mutation-spec-exact-key-contract`)、
`estimated_run_seconds` は 1 run あたり (`mutation-spec-field-contract`)。

正例 (`DW-S04`「gate の禁止は署名で書き、通る正例を 1 つ添える」):

- 禁止の署名 = 「producer の生存判定に、待ち手自身の argv に由来する文字列照合を使うこと」
  および「受入投入の可否を、claim stdout 全体への部分一致で決めること」。
- 通る正例 = `producer --done-file D --artifact-file A --pid-file P` が
  `os.kill(<P の中身>, 0)` を exact PID で 1 回呼び、`acceptance` が
  `json.loads(claim stdout)["state"] == "acquired"` の exact 比較だけで投入を決めること。

## プラン v2 = 段 2 プラン + R1〜R12

段 2 プラン (`s2/s2-plan.md`) の構成・CLI 契約・状態機械・テスト計画をそのまま基礎とし、
上記 R1〜R12 を差分として適用する。プランの「実装しないもの」節は R5 (start-time 束縛) を
除いてそのまま維持する。
