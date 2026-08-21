---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: dev-wave-t189-stage2-plan-replayer
seq: 1
---

## {{D:stage2-direct-launch-recipe}}. stage2-plan-replayerのdownstream起動は`_bwrap_exec_argv`を使わず直接Popenする

**決定:** stage2-plan-replayerのdownstream (固定model/effortのauthor相当codex呼出し) 起動には
`tools/codex_reasoning_ab.py`既存の`_bwrap_exec_argv` (T-181由来のhermetic bwrap sandbox) を
使わず、`_codex_exec_argv`が構築するargvを直接`subprocess.Popen`する。ambient環境
(`os.environ`) を継承し、`HOME`だけを書込み可能な専用ディレクトリへ明示的に上書きし、
実`~/.codex/auth.json`/`config.toml`をそこへ`0600`でコピーする。T-181のhermetic
sandboxing (env clear・bwrap分離) は本機構には適用しない。

**理由:**
- 段5実装子が`_bwrap_exec_argv`経由でreal codex execを試み、実測で120秒timeout・exit -15・
  output 0 bytesを確認した (stderr: code-mode host未配置、WebSocket/HTTPS
  `Operation not permitted`)。親が`codex_worker_launch.py` (本wave内で段2/3/5と複数回
  動作実績あり) と比較し根本原因を特定: `_supervise_one`が使う`environment`辞書
  (`CODEX_HOME`/`HOME=/tmp/t181-home`/`LANG`/`PATH`/`TZ`等に限定) は、dry_run=True
  (直接Popen) でもbwrap経由でも同じ縮小dictを使う。T-1434の既存test (dry_run=True、
  292+ passed) はfake codex binaryを使っており、実codexの実ネットワーク呼出しをこの
  縮小環境で試したことは一度も無かった (実測で新規に判明した既存apparatus全体の
  未検証gap、{{F:stage2-launch-test-representativeness-gap}}参照)。
- 親が自分のBashから直接smoke testを行い、ambient env全体を継承し`HOME`だけ上書きし
  実auth/configをコピーする手順で`returncode=0`・実モデルの応答("ack") を得て実証した。
- `_bwrap_exec_argv`自体の修正 (ambient環境縮小のまま実ネットワーク到達性を確保する
  仕組みの追加) はapparatus全体に及ぶ横断的変更になり、規律5 (段階導入/盛らない) に
  反するためこのwaveでは修正しない。

**却下した選択肢:**
- `_bwrap_exec_argv`をそのまま使う — 実測でこの環境下では実ネットワーク到達不可と判明。
- `_bwrap_exec_argv`の`environment`辞書を拡張してambient変数を通す — 何のambient変数
  (env var / socket path) が必要かをこの環境で確実に特定できておらず、bwrapの
  `--clearenv`+bind-mount設計全体 (T-181のhermeticity前提) への波及も未検証。
  proven-workingな`codex_worker_launch.py`と同型の直接起動へ倒す方が安全側の最小変更。
- `tools/dev_wave_codex.py --stage author`を再利用する — modelが呼び出し側から指定不可・
  常時`gpt-5.6-luna`固定 (help実測済み) のため、model軸を実験armとして選ぶ必要がある
  stage2-plan-replayerの要件を満たさない。

**残存リスク (受容・追加修正しない):** hash検証後〜Popen前の同一UID raceは、FD経由exec等の
踏み込んだ再設計なしには理論上完全には閉じられない。本機構はローカル単一operator制御の
研究toolingであり、共有multi-tenant環境の敵対的攻撃者を脅威モデルに含まないため、次善の
staging権限強化 (0700) に留め、コード中へ残存リスクとしてコメントで明記した
(`tools/codex_reasoning_ab.py`のapparatus検証コード付近)。

## {{D:stage2-unbound-acceptance-status}}. stage2-plan-replayerはtask_acceptance_statusを常にunboundとしacceptedフィールドを出さない

**決定:** stage2-plan-replayerのcontract/receipt/CLI出力schemaは、機械的事実
(exit code・実argv・contract hash・plan hash・output byte state由来) を表す
`receipt_status: valid|invalid`と、task correctness評価を表す`task_acceptance_status`
(本waveでは常に`"unbound"`) を分離する。汎用`accepted`という名前のboolフィールドは
一切出さない。`fix_gate_eligible: false`、`routing_evidence_eligible: false`を明示
フィールドとして持たせる。

**理由:**
- 段3敵対相談の正しさレンズ・段6敵対レビューの両方が独立に「`execution-receipt`/`accepted`
  という命名は将来task correctnessの証拠と誤読される」と指摘した (段3所見、段6所見の両方が
  独立到達、根拠が強い)。具体的誤用シナリオ: exit 0かつ無関係な非空出力でも`accepted:true`
  になれば、将来のdecisions記録者やT-189 §12評価器実装者がこれをfix gateの品質証拠として
  誤用しうる。
- CLAUDE.md規律2 (正しさゲートを緩める変異を許さない) ・規律3 (正しさシグナルを
  後付けにしない) の精神に反する — genericな`accepted`を出すことは、task-specific
  oracle manifest (scope外) が実装されるまで「常に空虚な証拠」を生成し続けることになる。

**却下した選択肢:**
- `execution-receipt`/`unbound`の二択のまま`accepted`という別名で公開する — 命名だけの
  問題ではなく、フィールドの存在自体が「登録すれば証拠になる」という誤解を招く
  (段6所見: 「unbound契約の存在だけを§12 evaluatorが登録済みと数えるloophole」)。
  フィールド自体を無くし`routing_evidence_eligible: false`を明示する方が誤用耐性が高い。
