# [T-160] dev-wave reference の読了トリガ層化 + [T-154](1) DW-O07 削除 — 材料レポート (2026-07-28)

wave: dev-wave T-160 (全 9 段、branch `worktree-dev-wave-t088-python-gate`)。
実装 commit `a8ee4a1`。子 = codex 6 本 (プラン起草 1 + 敵対相談 2 + 敵対レビュー 2 +
焦点再レビュー 1、全て `gpt-5.6-sol` / `reasoning=max` / `read-only`)。全ハンク親作。

## 1. 実測 (すべて本 checkout = 共有ログインノード、rc のみ — F41)

- **bytes**: reference 4 冊 23,951/24,000 → **23,542/24,000** (headroom 49 → 458)。
  core.md 8,962 → **9,000/9,000 (headroom 0)** — 層定義の追加を C00 縮約で相殺。
  operations.md 6,802 → 6,355 (O07 節 -426 + 前文範囲列挙 -24)。入口 8,420 → 8,376
  (条件 07 行削除、段 5 の 2 行分割込み)。skill-self-improvement.md 5,570 → 5,997/6,000
  (headroom 3、削除 gate 追記)
- **発火実績 proxy** (worklog + archive の exact ID 言及数): O03/O04/O10/O11/O13/O14/M02 = 0、
  O16=21 / O18=25 / O19=27 / O20=27 / M01=23。ただし repo 全体では O13/O14/M02 に明示発火
  (insight・ratified memo・再照準実績)。**exact ID proxy は「タグ付け頻度」であり発火頻度ではない**
  (段 3 A-5/B と段 2 プランが独立確認) — 削除 gate の反証は意味検索とする根拠
- **検査**: check_docs rc=0 (実装後 / fix 後 / matrix 復元後)、test_check_docs 114 passed、
  受入全走 **3141 passed / 18 skipped / 0 failed rc=0 × 2 回** (実装後 22:20・fix 後 22:45)、
  check_codex_agents rc=0、check_ai_provenance 449 件違反なし

## 2. 実装 (親、docs 4 + checker + tests、コード変更は検査系のみ)

- **層定義** (DW-C00 内に固定): 層は読了トリガで決まる — L0=入口、L1=段 dispatch が無条件に
  指定する節、L2=条件成立時だけ読む節。**ファイル単位ではない**。worklog (36) の設計案
  (L1=core、L2=workers/mutation/operations の外出し) は dispatch 実態に反するため棄却
  (workers 全 H2 の 96.3%・mutation 97.1% は段 dispatch 必読、O01/O02/O03/O05/O13 は
  段 2/3 preflight 無条件、core G01-G04 は逆に意味上の条件節 — 段 3 B §6 の反例集)
- **陳腐化削除 gate** (skill-self-improvement.md routing 3): 削除を裁定パッケージへ送れるのは
  L2 のうち「発火実績なし × テスト/機械検査で義務代替済み」の両条件を満たす節のみ。
  「発火実績なし」は ID 件数でなく repo 全体 (insights・memo 含む) の意味検索で反証されない
  ことを確認。実施はユーザー裁定限定。配置は core 前文予定を変更 — 発火段 (段 8) の必読正本へ
  (core は予算超過 173B のため。R1 が候補記録 gate との混同を指摘し文言を「送れるのは」へ修正)
- **DW-O07 削除** (T-154(1) 裁定): operations.md 節 (426B)、入口の条件 07 行・段 5/6 の範囲表記
  (`O01〜O20` → `O01〜O06, O08〜O20`、段 5 は行長 140 回避で 2 行分割)、check_docs の
  `_OPERATION_NUMBERS = (*range(1, 7), *range(8, 21))` 単一契約化 (3 使用面: 必須 H2・
  `_ALL_OPERATIONS`・条件 dispatch)、test_check_docs の 20 節依存 3 ハンク
- **literal pin 新設** (`test_operation_contract_pins_exact_section_set`): 19 節の外延・
  `(path, section)` 完全一致・条件 key→節写像の operations 射影 singleton・段 5/6 の包含を
  literal で固定。checker と fixture が同一定数から導出される自己整合 (F9 型) の遮断
- **CTX ポインタ統合は撤回**: 入口冒頭 2 行の読者主体は外部 supervisor 自身、条件 21/22 の
  読者は manager — 重複でなく異なる主体への義務で「意味を変えない縮約」不成立 (段 3 A-2 real)

## 3. レビューと裁定 (段 3 = 2 レンズ、段 6 = 2 レンズ + 焦点 1 巡、全て codex read-only 静的検査)

- 段 3 A (安全義務) NO-GO: A-1 層定義誤り (real 採用 → 読了トリガ単位へ)、A-2 CTX 統合の主体
  喪失 (real 採用 → 撤回)、A-3 C00 縮約の意味喪失 (real 採用 → 「実行時契約」明文保持)、
  A-4 exact-set 独立 pin (real 採用)、A-5 O10 再裁定列挙漏れ (real 採用)、A-6 意味検索反証
  (real 採用)、A-7 受入への check_codex_agents/provenance 明記 (real 採用)
- 段 3 B (整合・実効性) NO-GO: B-1 worklog 断片は構造検査で赤 (real 採用 → 完全 entry)、
  B-2 定義位置 NameError (real 採用)、B-3 層定義の裁定改変 (real 採用 = A-1 と独立一致)、
  B-4 living index は盛らない (部分採用)、B-5 層整合の check_docs 機械化 → **設計 v2 で外延列挙を
  書かない構造にしたため drift 面が消滅、新設不要と裁定** (裁定パッケージ不送付)、B-6 段 5/6
  stale 変異 2 本 (real 採用)、B-7 正例登録 (real 採用)、B-8 段 5 focused positive control 恒久
  テスト → G05 で成果物影響を書けず nit/backlog ([T-161] 起票)
- 段 6 R1 (docs 意味保存) NO-GO: R1-1 must-fix = 実行時契約 + 層定義が無見出し前文へ脱落
  (節単位読了の到達保証欠落) → C00 節内へ移動で closed。R1-2 = routing 文言 + 反証目的語 →
  修正で closed。R1-3 nit = operations 前文の外延列挙除去 → **理由付き不採用** (prose 列挙は
  節増減で虚偽化する F1 型転写元、外延は checker + literal pin の機械保証が優る。焦点再レビューが
  不採用理由を妥当と判定)
- 段 6 R2 (checker/テスト) NO-GO: R2-1 must-fix = 変異 3/4 の対向 mask 誤り (`_ALL_OPERATIONS`
  は段 5/6 共有で他段が赤になる) → 段別契約への個別追加に訂正し closed。R2-2 = 加算型誤配線
  (条件 08 に O09 併記) が `in` 検査を通る → operations 射影の singleton 完全一致へ修正、
  親が in-memory 検証で closed (加算型は検出・条件 15 の複合 union は誤検出なし)。R2-3 =
  docstring の「唯一の独立 oracle」過大 → fixture literal range との役割分担へ修正し closed
- 焦点再レビュー: must-fix 全 closed、fix 起因の回帰・新規所見なし。R2-2/R2-3 partial は
  上記の親 fix + 検証で閉じた (O16 の 3 巡上限内 1 巡)

## 4. 変異台帳 (matrix、統合 commit a8ee4a1 後に O19 規律で実施、復元は全て commit 内容と一致)

| # | 変異 (単一 diff --stat 確認済み) | 結果 | 赤 finding (1 件のみ) | 対向 mask → check_docs 緑 |
|---|---|---|---|---|
| 1 | 入口の条件 07 行のみ復元 | KILLED rc=1 | 条件 dispatch '07' 不一致 extra=[DW-O07] | CONDITION_DISPATCH_CONTRACT["07"] 再追加 rc=0 |
| 2 | operations.md の O07 節のみ復元 | KILLED rc=1 | 孤児 H2 ['DW-O07'] | 必須節集合へ O07 追加 rc=0 |
| 3 | 入口の段 5 行のみ旧 `O01〜O20` へ | KILLED rc=1 | 段 dispatch '段 5' 不一致 extra=[DW-O07] | 「段 5」契約のみ O07 追加 rc=0 |
| 4 | 入口の段 6 行のみ旧 `O01〜O20` へ | KILLED rc=1 | 段 dispatch '段 6' 不一致 extra=[DW-O07] | 「段 6」契約のみ O07 追加 rc=0 |
| 正 | 編集後の実 repo そのまま | 緑 | check_docs rc=0 + pytest `-k real_repo` 1 passed | — (過剰拒否なしの正例) |

「緑」= check_docs finding の消失 (R2-1 の定義)。pytest 全体では literal pin が変異 1/2 を
独立検出する (mask 失敗ではなく検出力の証拠)。前段検査の素通りは R2 検算 (条件 07 復元
8,473/9,500、O07 節復元 23,989/24,000、段 5/6 旧行 130/64 chars) と実測 rc で一致。

## 5. 陳腐化削除候補の裁定パッケージ (ユーザーへ — 本 wave では削除ゼロ)

exact ID proxy ゼロの 7 節を新 gate (両条件 + 意味検索反証) で判定した結果、**全て維持**:

1. **O03** (266B): guard_bash は防護パス×不透明構文の同居を拒否するが、`printf > prompt` 等の
   透明経路・script 経由・Codex 面 (hooks 未配線) を閉じない — Write 義務は代替されず維持
2. **O04** (200B): hook/テストは防護パス入り単一行 `-m` を正例として許可しており、
   Write + `-F` 義務の代替ではない — 維持
3. **O10** (261B): freeze テストは既知 23 成果物の bytes 検査のみで producer の全 write-path
   棚卸しを要求しない — 維持
4. **O11** (201B): 削除検出テストはあるが受入前 `git add -A` の時系列義務を強制しない — 維持
5. **O13** (177B): 発火実績あり (T-088 設計で不存在 field を検出し停止) — 候補から除外
6. **O14** (200B): 発火実績あり (ratified memo で正規 seam の非等価確認) — 候補から除外
7. **M02** (294B): 複数回発火 (T-088 floor-wrapper・T-119 の mask 再照準)。S06-A/M07 は
   等価変異疑い・両層再照準・erratum 義務の部分集合しか持たず重複でない — 候補から除外

O03/O04/O10/O11 は**先に完全機械化できた場合だけ再裁定** (O10 含む — 段 3 A-5)。

## 6. 素材

- 段 2 プラン・段 3 攻撃 (A/B)・段 6 レビュー (R1/R2)・焦点再レビューの逐語:
  job tmp `t160-wave/` (plan-out / attack-a-out / attack-b-out / review-1-out / review-2-out /
  refocus-out)。wave 終了時に handoff とともに消えるため、本レポートが凍結正本
- 統合 patch snapshot: t160-integrated.patch (fix 前) / t160-integrated-v2.patch (fix 後)
- 層定義の反例集 (dispatch 実態): 段 3 B §6 — workers/mutation の段 dispatch 被覆率、
  operations の preflight 無条件節、core G01-G04 の意味上条件性
