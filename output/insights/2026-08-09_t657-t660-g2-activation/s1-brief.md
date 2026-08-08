# 段 1 brief — [T-657] pegasus g2 活性化 (前提 2 件) + [T-660] head=2 検出力確認

wave: dev-wave-t657-t660-g2-activation / base: local main ee2da0bf / 2026-08-09

## scope

1. **[T-657](a) silo 歴史 evidence の historical 解決化。** committed evidence
   (`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json`, binding.calibration.
   contract_sha256 = g1) の再検証経路 (`silo_ladder_rung1.py` `verify-result`、main():4846 →
   `validate_current_bindings`:3517-3670) が検証時に `env_contract.lookup("pegasus")` (:3540)
   で current を引くのをやめ、記録済み hash の historical 解決
   (`env_contract.resolve_by_contract_sha256`、ever-active 限定) に変える。
   **producer 側 (`_binding`:4438、attest:1942、correctness:3758) と生成直後の自己検証
   (`_collect_command`:4734) は current のまま**。テストの current 依存漏れ
   (`test_silo_ladder_rung1_evidence.py:1262-1272`) も同時に閉じる。
2. **[T-657] 活性化。** `tools/issue_env_contract_activation.py --active linux-baremetal=1
   --active pegasus=2` で `00000002.json` を create-only 発行し、`env_contract.py:373-376` の
   head 定数 2 行を**同一 commit** で更新する。実 chain head=1 を pin する既存テスト
   (`test_env_contract_activation.py:343` ほか) を新 head へ追従させる。
3. **[T-657](b) floor protocol 再発行 — ユーザー手番。** `freeze-protocol` は isatty gate +
   T-080 receipt + create-only + guard_write (`output/s8b-freeze/` Write 拒否) + 初回発行
   `AI-Agent: none` の先例により、AI は実行しない。wave は活性化適用済みの本 worktree で
   ユーザーが実行する逐語手順 (旧ファイル退避 → `freeze-protocol --confirm-user-freeze` →
   user commit) を準備し、**段 5 実装後・受入前にユーザー手番で停止する**。
   再発行後に codex が `test_frozen_artifacts.py:45-46` の FROZEN_MANIFEST pin を新 sha256 へ更新。
4. **[T-660] head=2 検出力確認。** 実 chain が 2 record になった状態で
   `test_production_loader_rejects_tail_deletion_with_source_head_unchanged`
   (test_env_contract_activation.py:1477) が空 chain 拒否ではなく head 不一致で落とすことを
   確認する。match regex が「activation authority 検証失敗」と広く両者を区別しないため、
   head=2 で head (?:serial|state hash) 不一致へ絞り、DW-O19 の一時変異 (head serial 検査の
   無効化) で検出力を実測する。恒久 gate の新設はしない (既存テストの精密化)。

## 確定済みユーザー裁定

- §44 (2026-08-08): 「[T-657] = T-139 裁定後、前提 2 件 (silo 歴史解決・floor protocol
  再発行) を揃えてから活性化」。T-139 は §44/§47 で裁定済み。[T-627] (活性化前提の世代遷移
  述語) はエントリ 318 で land 済み。[T-660] は worklog 313 起票の P3 (活性化後に確認)。
- 由来: T-529 裁定パッケージ 1 (s4-adjudication.md)。実測「活性化の瞬間 committed floor
  protocol は live admission から外れる (historical 再検証は通る)」。

## 不変条件

- 「揃えてから活性化」= **land された main に floor/silo が壊れた窓を作らない**。活性化
  commit・silo 解決・floor 再発行・pin 更新は同一 wave branch で完結してから land する。
- silo の historical 化は **verifier の再検証経路のみ**。producer が記録する世代は current の
  まま (T-529 レンズ B: `validate_current_bindings` を丸ごと historical にしない)。
  s8b の先例 (current/historical resolver 対、`s8b_ratified_freeze.py:2769-2801` /
  `s8b_floor_campaign.py:308-337` / `s8b_oracle_report.py:1642`) と同型にする。
- `resolve_by_contract_sha256` は ever-active 限定のまま (正しさ防壁を緩めない)。
- 00000002.json は発行 tool の create-only 経路だけで作る (手書きしない)。head 定数と record
  は同一 commit。00000001.json の bytes は不変。
- FROZEN_MANIFEST は値の更新のみ (件数 23・key-set 不変)。floor protocol 再発行は
  `contract_sha256` (と file sha256) 以外の 17 key が不変であることを照合する。
- T126 経路は contract_sha256 非依存で影響なし (実測済み)。oracle 系は historical lane 既存。

## 成果物影響 (DW-G05)

- 実装しない場合: pegasus の current 契約が g1 較正 (753f535a) のまま T-139 本走へ進み、
  以後の certified 選択・floor/oracle/silo evidence の admission が旧較正へ束縛され続ける。
  受理集合の変化: (a) silo committed evidence の再検証が「current 一致」から「記録 hash の
  ever-active 解決」へ、(b) floor live admission の契約が g1→g2 へ、(c) 実 authority の
  末尾巻き戻しが head-pin で観測可能になる。

## 実測環境

- 受入全走・変異は Pegasus 計算ノード (`tools/run_tests.py --force-dispatch`、runbook §7.3
  lease claim/release、§7.4 変異 runner argv)。ログインノードは軽量検査のみ。

## 分割方針 (段 5)

- 実装子 A (codex): silo historical 解決 (production + test)。
- 実装子 B (codex): 活性化系テスト追従 + T-660 regex 精密化 (head=2 前提)。record 発行と
  head 定数は親が tool 実行 + codex が定数/テスト編集 (所有分離: A = silo_ladder_rung1 系、
  B = env_contract 系。交差なし)。
- ユーザー手番 (floor 再発行) は実装完了後に一括で依頼する。

## 判断が割れうる前提 (親の provisional 裁定であり攻撃対象)

- (P1) silo は s8b 同型の resolver 注入で、公開関数を current 用と historical 用に分ける
  (`verify-result` だけ historical)。新 API は追加しない。
- (P2) 活性化 record の発行は親が tool を実行する (実装面の編集ではなく保守 tool の実行)。
- (P3) ユーザー手番の placement は「段 5 実装後・受入前」。受入はユーザー手番完了後に 1 回。
  (floor 再発行前は certified_writer_fixtures 経由の admission テストが赤のため受入不能)
- (P4) [T-660] は既存テストの match 精密化 + DW-O19 一時変異の実測で閉じ、新規テスト node は
  「空 chain mask ケース」を独立に固定する場合だけ足す。
- (P5) 再発行後の floor protocol は 17 key 不変・contract_sha256 のみ g2。これを wave が照合
  してから FROZEN_MANIFEST を更新する。

## 既存被覆 (性質で検索した結果)

- 「committed evidence を記録時契約で再検証する」: s8b freeze/oracle に historical lane 既存。
  silo には無い (本 wave の純増)。
- 「実 authority の末尾巻き戻し検出」: leaf 層は合成 catalog の unit test で被覆済み
  (test_env_contract_activation.py:451)。production 層は head=1 で空 chain 拒否に mask され
  検出力未実証 (本 wave の純増 = mask 解除の実証)。
