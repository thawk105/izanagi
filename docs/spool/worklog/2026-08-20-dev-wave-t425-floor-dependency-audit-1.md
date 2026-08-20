---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t425-floor-dependency-audit
seq: 1
title: '[T-425] 8b H1/H2 between-run floor 実験路の依存鎖を再監査した (docsのみ、branch worktree-dev-wave-t425-floor-dependency-audit)'
---

## 本文

- command 引数の前提「[T-419] は2026-08-17付で解決済み・主要blockerは解消済み」は誤りと判明した
  — T-419には別時期・別内容の2つのサブ課題があり、2026-08-17に解決したのは「較正artifactの
  世代有効化まわりの周辺技術3件」で、U-6の依存鎖が必要とする「較正再取得」の**活性化**は
  2026-08-19 (D547) 時点でも未実施のまま。command引数はこの2つを混同していた。
- 本wave実行中 (2026-08-20) に別セッションの`/rulings`が D581 をlandした
  (branch `worktree-rulings-20260820-floor-provenance-codex-escalation`)。床値measurementを
  official mode相当の事前登録儀式なしで粗いprovenanceだけで成立させてよいという標準変更で、
  理由文が「[T-419]の生成移行chainという無関係な前提条件へ床値測定を従属させ続けていた」と
  名指しした — 本監査が特定したU-2活性化ブロッカーの一部を直接指しており、偶然の時期的一致。
  D581の当該waveは「実際の床値measurement実行は別セッション(dev-wave/next-tasks)へ委ねる」と
  ユーザーが明示しており、続waveの着手条件として扱ってよい。
- 段2 codex plan (read-only) → 段3敵対2レンズ (`--lane sol`=正確性、`--lane luna`=実効性論理) の
  順で親briefの前提P1〜P5を裏取りした。段3レンズAが「T-424/T-272はcommitゼロ」という親の
  当初理解を反証し (`950757e2`/`419d59b1`の部分実装を発見、ただし要求は未閉包)、
  U-6(iii)に「perf実体のノード個体差」という独立項目が含まれることも指摘した (親・段2plan
  ともに当初見落とし)。段3レンズBは「実装しない」という親の当初結論を「公式H1/H2実験は
  no-goだが、between_run_floor.pyのcode-only bounded preparationまで禁止する根拠にはならない」
  と補正した。
- 段2 plan投入時に `--stage consult` へ `--lane` 未指定で1回失敗した (rc=2、
  「--stage consultには--laneが必要」)。DW-C01「--laneは--stage consult専用」の読みが
  「他段では拒否される」までで止まり「consult自身には必須」を見落としていた。
  出力ファイル未生成のまま exit code だけ0を返す外側スクリプトの構造だったため、
  check_codex_output.py で必ず検証してから読む運用が有効に機能した実例。
- 詳細な逐語・file:line根拠・裁定パッケージ全文は
  `output/insights/2026-08-20_t425-dependency-reaudit/README.md` を正本とする。

## 次の一手差分

### 更新

- [T-425] **P1・裁定済み (2026-08-05 /rulings) → 実装は依存順序待ち、2026-08-20再監査で
  条件を精緻化**: 公式H1/H2実験の起票 (実行・receipt生成・受理登録) は、T-424/T-272の要求
  全体閉包またはD145決定5の明示的再訪裁定、かつrr80/rr20較正の登録 (人間lockstep) が揃うまで
  不可 — この結論自体は不変。ただし between_run_floor.py の code-only bounded preparation
  (入力検証・receipt schema・failure path・screening接続、実験起動や受理は一切しない) は
  上記blockerと独立に着手可能と判明。次wave 段1 brief の最優先確認事項は、本日land した D581
  (床値measurementのofficial mode儀式撤廃) がU-6の依存鎖 (特にU-2活性化) に及ぼす具体的な
  影響の実測。一次資料 = `output/insights/2026-08-20_t425-dependency-reaudit/README.md`。
  base: f73cad0adaa0c8e458613aaa273b5cfa38160eb5683cf788364c0c74577f812b

- [T-424] **P2・部分実装あり、要求は未閉包 (2026-08-20 再監査で判明)**: commit `950757e2` が
  `submit_certify.sh`/`certify_calibration.sh` へ `--job-script` 受理と script hash の
  pre-submit/submit receiptへの記録を実装済みだが、`job-result.json` に `job_script_sha256`
  が無く、override した script と実行結果の結び付きを最終成果物では検証できない
  (`tools/pegasus/certify_calibration.sh:752-765`)。要求 (未承認bytesの測定値を正規receiptとして
  登録しうる、を閉じる) は未達成のまま。一次資料 = 上記READMEの(b)節。
  base: 78abf6e02b80785920bf6d0dbe0cdcc548acadf575a0f31d45657b24e6f55c54
