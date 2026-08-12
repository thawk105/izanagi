# 既知赤 (octopus merge) の恒久修正と、既知赤で land が止まらない機構
- 目的: main 恒久赤 `[octopus-merge] d1de13ad` を履歴契約の n 親一般化で直し、既知赤で後続 wave の land が止まらないようにする
- 状態: 作業中
- 最終更新: 2026-08-13 01:55 JST
- 基準コミット: 01487bb4 (worktree clean)

## 完了した中間成果

- 赤の実体を特定・再現。`validate_condition_freeze_at(ROOT, 'HEAD')` の直呼びで
  `PreregistrationError [octopus-merge] d1de13add1bcbcfeb415cf13303848ad32dde212` を 1 秒で再現。
  フレークでなく決定的。機序 = `orchestrator/campaign/s8c_preregistration.py:1305`
  `_assert_history_transition` が親 3 つ以上を無条件拒否。
- 一次資料 2 本を回収。
  `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-known-red-octopus-merge.md` (裁定控え、(a) のみ確定)、
  `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-main-octopus-merge-blocks-all-acceptance.md`
  (Q1〜Q3 + 親推奨、Q1=(a) 一般化)。
- 見送り裁定の検索を実施 (memory `check-withdrawal-rulings-before-wave`)。
  `docs/decisions.md` D316 に「既知赤 waiver (W1 形式) の新設 — 起草まで行ったがユーザー裁定で
  取り下げた」を発見。`docs/failures.md` F101 (+ 2026-08-12 再発) が「成立済み waiver を
  引かずに停止した」手順漏れの独立 2 例。
- `DW-O09` の pin 閉包を実測 = 該当なし (brief に記載)。`DW-O08` の submodule init 済み (rc=0)。
- 段 1 brief = `/work/1/SFC/tanab/dev-wave-jobs/known-red-octopus/brief.md`
- **親の独立実測 (決定的、子より先に固定):** `d1de13ad` の 4 親と merge 本体について、
  freeze 状態を決める 3 path (`output/s8c-preregistration/condition-freeze`,
  `docs/phase3-8c-preregistration.md`,
  `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json`) の blob OID を
  `git ls-tree -r` で取ると **5 commit すべて完全一致** (`5832abef49`, `8beef5783c`, `6908cca3c7`)。
  つまりこの octopus merge は protected 集合を 1 bit も動かしていない。現行実装が拒否している
  唯一の理由は**親の個数**であり、真の不変条件違反ではない。→ A は「gate を緩める」変更ではなく
  **偽陽性の除去 (bug fix)** である。
- `octopus-merge` という reason literal に依存するテストは repo に 0 件
  (`grep -rn "octopus-merge" orchestrator/tests/ docs/` = worklog と本 handoff のみ)。
- 親の独立設計案 (A): 親状態集合に「他のすべての親状態と同値または successor」である状態が
  存在すればそれが唯一 (相互 successor は generation 狭義単調より不可能) なので、
  「存在すれば state と一致を要求、無ければ拒否」で n 親へ延長できる。n=2 の 3 分岐
  (両親同値 / 片方が successor / それ以外) はこの規則へそのまま写り、reason も
  `merge-state` / `merge-divergent-revision` を保てる。merge が世代を増やす経路は
  依然として作れない (state はどれかの親状態と一致必須)。

- 段 2 プラン完了 (02:03 JST、rc=0、22,226 bytes、`check_codex_output.py` OK)。
  成果物 = `/work/1/SFC/tanab/dev-wave-jobs/known-red-octopus/plan.md`。
  A は親の独立案と一致 (dedup + 唯一 greatest)。B は親案より強く、
  「原因 blob OID + failure literal への束縛」「checker 自身が `run_tests.py` を起動して
  親に nodeid を手入力させない」を提案。
- 段 3 敵対 2 本を 02:07 JST 投入 (lens A=sol 正しさ境界、lens B=luna 迂回機構化)。
- **親の裏取り 3 件 (プラン主張の検証):** (1) `dev_wave_wait.py acceptance` は
  `--` 以降の command を受け取り child rc で lease 保持を決める (`_parse_cli` 296-306 行) = 事実。
  (2) `check_docs.py` の `DEV_WAVE_L1_BYTES_MAX=10625` / `DEV_WAVE_L2_SECTION_BYTES_MAX=1000` = 事実。
  (3) `_is_acceptance_run` は run_tests への argv と `PYTEST_ADDOPTS` だけを見るので、
  引数なし起動を wrapper で包んでも形状判定は壊れない = 事実。

- 段 3 完了 (02:16/02:19 JST、両 rc=0、11,274 / 12,579 bytes、受理検査 OK)。
  レンズ A = blocker 1 (A-06) + must-fix 2 (A-02, A-05)、レンズ B = blocker 6。
- **段 4 裁定確定 = `/work/1/SFC/tanab/dev-wave-jobs/known-red-octopus/ruling.md`。**
  決め手は `docs/failures.md` **F266 の恒久対応**が複数 branch land に
  `git merge --no-ff --no-commit <b1> <b2> <b3>` (親 = main + 3 = 4 つ) を**明示的に命じている**こと。
  → A-05 (all-equal 限定) と A-06 (3 親以上を land で禁止) を **refuted**。(P3) 維持。
  → B は registry 形式を破棄し、**非帰属を再実行で実測する checker** へ設計変更 (B-02 が決定的)。
  → B-04 (land が受入結果を検証しない)、B-05 (login 経路で preflight 未到達)、
     A-02 (state 同値でも tree 相違、n=2 でも同じ) は **scope 外 → 裁定パッケージ**。
- local main を 02:30 JST に取り込み (18 commit、merge `61a5aa72`、submodule 同期 rc=0)。
  取り込み後も赤は同一で再現。
- 段 5 実装子 2 本を 02:41 JST 投入。専用 worktree は
  `.claude/worktrees/known-red-octopus-a` / `-b` (両方 `git worktree lock` 済み)。
  **wave 終了時に必ず撤去 + `git worktree prune` すること** (残骸は全 wave の land を止める)。

- 段 5 完了 (02:45 JST、両 rc=0、受理検査 OK)。**両子とも codex sandbox で dispatch できず
  (`qstat -Q preflight rc=1` → rc=16) テストを 1 件も実走していない。** 実走は親が担う。
- 親が成果物を監査のうえ回収 (isolated session なので `git -C` 不可、
  `/home/SFC/tanab/.claude/jobs/52c8f815/tmp/collect.py` で blob 比較 → 上書き)。
- **02:52 JST: 既知赤の消滅を実測。** `validate_condition_freeze_at(ROOT, 'HEAD')` が
  `GREEN generation=1` を返す (修正前は `RED [octopus-merge] d1de13ad`)。
- 焦点走 02:54 JST **353 passed / rc=0** (request 908578.nqsv)。
  対象 = `test_s8c_preregistration_core.py` + `test_check_acceptance_reds.py`。
- 段 6 敵対レビュー 2 本を 02:56 JST 投入。

- 段 6 レビュー完了 (02:55 / 03:05 JST、両 rc=0、受理検査 OK)。
  レンズ A = blocker 0 / must-fix 0 / nit 6。レンズ B = **blocker 6 + must-fix 2**。
  B の核 = B6-B-02 (summary block 外の赤を無視して緑)、B6-B-04 (probe worktree 使い回し +
  ignored 汚染 + submodule 未初期化で attributable を non-attributable にできる)。
- 統合 snapshot 退避 = `snapshot-s5/` (4 ファイル)。
- 段 6 fix 2 本を 03:12 JST 投入 (fix-a = テスト追加のみ・production 不可、fix-b = blocker 6 件)。
- **B6-B-01 の残余 (任意の過去 log を渡せる) は本 wave で塞ぎ切らない。** 裁定パッケージへ返す。

## 未完の作業と次の一手

- 段 2 codex plan (read-only, reasoning=max) を投入 → 段 3 敵対 2 本 → 段 4 裁定。
- 本 wave は軽量版に**しない**。正しさ防壁に触り受理集合が変わるため (`DW-C00`)。

## 落とし穴・気づき

- **B (既知赤 registry) は迂回機構へ堕しやすい。** D316 の却下理由と衝突しない論拠は
  「A で実際に直す + B は成立済み裁定の取りこぼし (F101 独立 2 例) の機械化」。段 3 の主攻撃面。
- 受入 lease は 3〜4 wave が争う。稼働 worktree 14 本。投入直前に main を再確認する。
- docs 予算に余裕が無い。registry は `docs/` へ置かない。

## dev-wave 改善候補

- (未記入)
