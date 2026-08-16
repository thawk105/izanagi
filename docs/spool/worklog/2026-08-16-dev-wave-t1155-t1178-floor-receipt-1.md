---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1155-t1178-floor-receipt
seq: 1
title: 床値 result へ SWO PASS receipt と admission 台帳を束縛した — 敵対相談が親の実測 2 件を覆し、敵対レビュー 2 本が独立に同じ自己照合を検出 (コード + テスト、branch worktree-dev-wave-t1155-t1178-floor-receipt)
---

## 本文

[T-1155] と [T-1178] を 1 wave で実装した。sort_best cell の SWO PASS receipt を portable 形へ
射影して床値の durable record へ束縛し、`result.json` へ admission 台帳の claim identity と
run 単位の ledger digest を必須化した。設計判断は {{D:floor-receipt-binding-boundary}}、
{{D:live-admission-public-entry}}、{{D:measurement-head-non-authoritative}}。

**段 3 の敵対相談が親 brief の実測 2 件を覆した (親が独立に裏取りして受理)。**

1. 「床値の実成果物 0 件」は誤り。`dev-wave-t748-pilot-path` の証拠 bundle に pilot 実測が 2 件
   実在する (schema `s8b-floor-result/v2`、mode=pilot、sessions=120、binaries=12)。
   親は現 worktree の `output/` だけを探索していた。**結論 (v4 化で新たに壊れる実成果物は無い) は
   不変**だが、根拠は「0 件だから」ではなく「実在 2 件は現行 v3 が既に拒否する legacy だから」へ
   差し替えた。
2. 「編集面に bytes pin 無し」も誤り。`output/s8b-freeze/holdout_freeze.json` の `/generator/sha256`
   が `orchestrator/campaign/s8b_holdout_freeze.py` を pin しており、現行 bytes は**既に不一致**、
   `freeze_verification_hold` 下で保留中だった。pin 閉包の grep から `output/` を除外していた
   のが原因 (F30 の再発として記録)。hold は解除していない。

**段 6 の敵対レビュー 2 本が独立に同じ穴を検出した。** 正準 attempt ID 束縛の欠落と、
`s8b_holdout_freeze` が成果物を実測記録へ束縛していないこと。後者は [T-1155] の identity 束縛が
2 つある公開経路のうち片方で自己照合へ退化することを意味していた。

**棄却した所見 (実装せず裁定パッケージへ):**

- SWO receipt を「oracle 実行の証明」にする案 (検証時 oracle 再実行 / 署名付き追記専用 authority)。
- 台帳の削除→同一 bytes 再構成への耐性 (外部 WORM / 別権限の署名付き monotonic registry)。
- `measurement_head` の権威的な外部期待値。

いずれも凍結 pin・署名・commit 束縛・台帳の原子性強化の新設に当たり、2026-08-12 のユーザー裁定
(bytes 級 provenance 機構は既定で見送り) に直接該当する。保証範囲外であることを docstring と
commit 本文へ明記した。

**セッション異常・工数:**

- 段 5 / 段 6 の Codex 子 (実装 3 + fix 5 + spec 2 = 10 本) は**全員 pytest を実走できなかった**。
  `hooks/guard_bash.py` が pytest 直呼びを機械拒否し、正規経路の `tools/run_tests.py` は
  codex sandbox から scheduler socket へ到達できず rc=16 になる。子は迂回せず
  「実装済み・未実走」と正しく申告し、**測定は毎巡 親が引き受けた**。
- fix は 5 巡。親の実測で 192 → 8 → 2 → 4 → 0。4 巡目で入った 4 件の回帰は
  「新設 gate が既存の具体診断を先取りし構造化 cause が汎用側へ潰れた」型で、検査を弱めず
  発火順序の入替で解いた (規律 3)。
- 変異 spec の Codex author 子は 1 回目に repo 外へ書けず (sandbox が workspace 外書込を拒否)
  ファイル未作成で終わった。出力先を repo 内へ変え、親が受領後に repo 外へ退避した。
- `tools/dev_wave_wait.py producer` が producer 生存中・成果物不在のまま rc=0 で返る空振りを
  1 度実測した ({{F:dev-wave-waiter-spurious-completion}})。

## 次の一手差分

### 完了

- [T-1155] 床値 durable record へ SWO PASS receipt を束縛した。identity 5 項目
  (`cell_id` / `holdout_id` / `configuration_id` / `entry_sha256` / `binary_sha256`) で receipt 移植を
  拒否し、ホスト絶対パスは載せず `compiler_version` は sha256 のみ載せる。
  remaining: none
  base: b70748a2eaaf842b190a74ad53eda47e5b5860ba218f681457fefe466005be0b

- [T-1178] 台帳の無い floor result を下流が拒否する形へ倒した。`result.json` へ
  `holdout_admission` 節を必須化し、公開 consumer は expected を caller から受け取らない入口だけを
  使う。台帳へ到達できない場合も内容不一致と別 reason で必ず拒否する。
  remaining: none
  base: 56708afae9740868330dfef6d9bf4197335e5822c34704f34b4ba93d468857c1

### 新規

- {{T:oracle-execution-proof}} **P2・新規 (本 wave の保証範囲外)**: SWO receipt を
  「oracle が実際に走った」証明にする手段を審査する。現状の receipt は全 field が公開かつ決定的で、
  oracle を実行せずに合成できる。検証時の oracle 再実行か、artifact author と分離された
  署名付き追記専用 oracle authority が要る。**署名機構の新設は既定で見送りの裁定に該当する**ため、
  実装可否はユーザー裁定を要する。
- {{T:admission-ledger-reconstruction-resistance}} **P2・新規 (本 wave の保証範囲外)**:
  admission 台帳を削除して同一 bytes で再構成する攻撃への耐性を審査する。claim digest も
  ledger digest も公開・決定的な値だけから作られ、`O_EXCL` は file が存在する間しか効かない。
  repo 所有者が消せない外部履歴 (WORM / 別権限の署名付き monotonic registry) が要る。
  **台帳の原子性強化は既定で見送りの裁定に該当する**ため、実装可否はユーザー裁定を要する。
- {{T:measurement-head-authority}} **P3・新規**: `measurement_head` を権威的に束縛するか、
  非権威 field のまま据えるかを決める。現状は台帳と claim を**同期して**書き換えれば
  portable receipt も受理集合も変わらない (片側だけの変更は拒否される)。
  権威化には測定 commit の外部期待値が要り、commit 束縛機構の新設に当たる。
- {{T:dev-wave-doc-budget-blocks-measured-corrections}} **P2・新規 (ユーザー裁定待ち)**:
  本 wave の実測に裏付けられた dev-wave 手順の是正 3 件が、**予算超過で 1 行も入らなかった**。
  (a) `DW-O09` の pin 閉包へ「検索から成果物側 (`output/`) を除外しない。generator source hash pin は
  成果物 JSON の中に source path と sha256 を持つ」— L2 単節予算 1000 bytes に対し 1223 bytes。
  (b) `DW-S01` へ「不在を主張する実測は探索範囲を brief に書く」— L1 予算 10,625 bytes に対し 10,737 bytes。
  (c) `DW-S05-C` へ「実走経路が子の環境で構造的に塞がっているなら試行させず親が測ると prompt に書く」—
  L1.5 予算 9,566 bytes に対し 9,668 bytes。
  3 件とも本 wave で実害が出ている ((a) は F30 再発、(b) は段 3 が親の実測を覆した、
  (c) は Codex 子が 3 回 rc=16 を踏んで 20 分を失った)。
  既裁定どおり予算引き上げは提案せず、削除可能な陳腐化節も過去 2 wave が「ゼロ件」を実証済みのため、
  **DW-S08 の「予算に収まらなければ変更を止めてユーザー裁定へ返す」に従って差し戻した**。
  予算の作り方 (層別上限の見直し / 別 reference への分割 / 機械検査への移送) をユーザー裁定で決める。
- {{T:holdout-freeze-generator-pin-transition}} **P3・新規**:
  `orchestrator/campaign/s8b_holdout_freeze.py` の generator source pin と
  `freeze_verification_hold` の世代移行を設計する。凍結文書が記録する sha256 と現行 bytes は
  既に不一致で、hold により保留中である。hold 解除はユーザー明示命令に限る既裁定のため、
  本 wave では触っていない。
