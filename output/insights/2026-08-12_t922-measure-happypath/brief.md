# 段 1 brief — [T-922] 測定装置の production 正例経路

base main `6331284e` / 2026-08-12 21:18 JST。

## 確定済みユーザー裁定

- 第 5 束: T-923 は「T-922 後に再提示・deny 維持」。**T-922 の実施は裁定と整合。**
  admission policy の `status: unratified` は本 wave では解消しない (T-923 の scope)。
- 起動条件 (ユーザー指定): 稼働 wave との編集面重複を実測 → **重複なし**、実装へ進む
  (handoff「起動条件の実測」節)。
- (P1) D328 判定: (2) は**保留対象外**。付帯不変条件 = 新規の凍結 pin 台帳・`FROZEN_MANIFEST`
  entry・署名連鎖を新設しない。effect 直前に実 bytes を読んで hash するだけに留める。
  **親の provisional 裁定であり攻撃対象。**

## 段 1 実測 — 焦点レビューは古い。現行 main で測り直した

焦点再レビュー (`verbatim/s6-focus.md`) は `dev-wave-t810-harness` worktree に対するもので、
その後 5 commit (`5326536a`〜`80d6e9f4`) が入っている。**must-fix 7 件のうち 2 件は既に閉じている。**

| 焦点 # | T-922 項 | 現行 main の実測 | 判定 |
|---|---|---|---|
| 1 | (1) | `t810_coordinator.py:678` が `wrapper_argv == ["python3.10", wrapper_path, "--request", request_path]` を要求、`:716` が `publish_wrapper_request` を production で呼ぶ。`_request_from_json` (`t810_pbs_wrapper.py:1104-1124`) は静的 request を読み `PBS_JOBID` / `uname` / `sched_getaffinity` から runtime identity を補う | **実質閉** — 未検証 (下記 #7 が唯一の検証手段) |
| 2 | (台帳から脱落) | barrier (`t810_coordinator.py:1008-1012`) は `False/False/True/False` を要求、wrapper (`t810_pbs_wrapper.py:404-408`) はその形を返す | **閉** |
| 3 | (2) | `wrapper_sha256` は schema の宣言 field のみ (`t810_harness_schema.py:289,345`)。**実 bytes と照合する行が production に 0 行**。fixture も `wrapper_sha256: H` の定数 (`test_t810_coordinator.py:139`) | **開** |
| 4 | (3) | `t810_guard.py` / `t810_budget.py` の**非 test caller = 0**。coordinator は receipt の JSON 形式のみ検査し (`:357`, `:388`)、`ledger_sha256_after` を `ledger_path` の実 bytes と照合しない | **開** |
| 5 | (4) | `coordinate()` は roots を `document["validator_kwargs"]["approved_git_identity"]` = caller config から導出 (`:1622-1624`)。live 導出 `resolve_git_identity()` は `t810_validator.py:365` に実在するが effect 前に呼ばれない | **開** |
| 6 | (5) | executable identity は slot の caller 値。(2) と同一機構で閉じる見込み | **開** |
| 7 | (6) | coordinator artifact から実 wrapper CLI を起動する test は**存在しない** (`main([` の hit は coordinator の異常系 1 件のみ) | **開** |

DW-O09 pin 閉包: `tools/pegasus/t810_*.py` は `FROZEN_MANIFEST` に hit 0 → 凍結 bytes は動かない。DW-O10 不適用。
DW-O13 gate 入力の実在: `wrapper_sha256` / `ledger_path` / `ledger_sha256_after` /
`validator_kwargs.approved_git_identity` はいずれも実 artifact の field として実在。同名二義化なし。

## scope

**S-A (2)(5):** wrapper path/hash と executable path/hash を effect 直前の実 bytes へ束縛し、
caller 申告値を権威から降格させる (一致しなければ拒否)。
**S-B (4):** roots を effect 前に live git common-dir から導出し、caller の approved identity は
一致検査の対象に降格。
**S-C (3):** guard/budget producer を coordinator へ結線し、`ledger_sha256_after` を
`ledger_path` の実 bytes と照合。
**S-D (1)(6):** coordinator artifact から実 wrapper CLI (`--request`) を通す正例統合テスト。
S-D が (1) の唯一の検証手段であり、**本 wave の headline**。

## 不変条件

- 規律 1: 追加する検査は正しさ検証用であって、性能計測 build の実行経路に分岐を足さない。
- 規律 2: 受理を広げる方向の変更を一切しない。**すべて拒否側の純増**であり、
  既存の期待値を緩めない。正例テストの追加は「今まで通らなかった正しい経路を通す」であって
  「今まで拒否していた入力を受理する」ではない — 敵対レビュー 2 本でこれを検査させる。
- (P1) の付帯: 凍結 pin 台帳・署名連鎖を新設しない。
- admission policy の ratify 状態は触らない (T-923)。

## 純増検出力 (性質で検索した既存被覆)

- 「宣言 hash と実ファイル hash の照合」= production に 0 行 (上表 #3)。純増。
- 「live git から repo 境界を導出して effect を弾く」= `assert_repository_external` は
  与えられた roots に対してのみ働く。roots 自体の素性検査は 0 行。純増。
- 「receipt の宣言値と台帳実 bytes の照合」= budget は 0 行。純増。
- 「coordinator → 実 CLI の正例」= 0 件。純増。

## 成果物影響 (DW-G05)

- S-D 未実施: T-810 の測定が 1 件も実行できず §9.1 item 1 が未充足のまま
  → 材料レポートに T-810 由来の測定値が 1 件も載らない。
- S-A 未実施: 任意 binary/wrapper の測定値が正規 receipt を持って台帳へ入りうる
  → 受理集合が「申告どおりの実装で測った」保証を失う。
- S-C 未実施: 形式だけ整えた偽 budget receipt が通り、node 秒台帳が実消費と乖離
  → 予算超過が検出されない。
- S-B 未実施: 偽 identity で repo 内書込みが external 判定を通過
  → 測定成果物が repo を汚染し provenance が壊れる。

## 分割方針 (provisional)

- (P2) author-1 = `t810_harness_schema.py` + `t810_coordinator.py` + `t810_pbs_wrapper.py` + 各 test
  (S-A / S-B / S-D)、author-2 = `t810_guard.py` + `t810_budget.py` + 各 test (S-C の producer 側)。
  S-C の coordinator 側照合は author-1 が持つ。**所有 file は排他。**
- (P3) S-D の統合テストは `subprocess` で実 CLI を起動するか、`pbs_wrapper.main([...])` を
  同 process で呼ぶかを段 2 で決める。PBS 環境変数は test で注入する (規律 1 に触れない)。
- (P4) 本 wave では計算ノードへの実投入 (qsub) を行わない。正例経路の**成立**までが scope。

## 受入・実測環境

Pegasus login (親)。焦点走・受入全走は `tools/run_tests.py` の dispatch recipe を使う。
受入全走は背景投入・lease 取得後。計算ノードでの CC 計測は行わない。
