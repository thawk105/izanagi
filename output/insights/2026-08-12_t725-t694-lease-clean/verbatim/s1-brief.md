# 段 1 brief — dev-wave-t725-t694-lease-clean

対象: [T-725] (P2) + [T-694] (P3)、2026-08-12 の一括裁定 (45 件、発話「推奨通りでよろしく頼む」)。

## 裁定の前提を実測した結果 (段 4 で再裁定する新事実)

裁定された内容の実体は [T-732] / [T-740] として **2026-08-10 に裁定済み**であり、実装は
**2026-08-11 に main へ land 済み**である (`483682a6` = 待ち手内 merge + 所有実装面 overlap 判定、
`b365e477` = held-self、`6905d321` / `29bd2bfd` = runbook §7.3)。[T-725]/[T-694] は backlog に
重複して残っていた項目で、2026-08-12 の一括裁定はそれを再承認したものである。裁定を止めず、
**残差だけを実装する**。

F191 恒久対応が定める「安全配線 3 点」と `tools/dev_wave_wait.py` の逐条照合:

| 点 | 内容 | 実装状況 |
|---|---|---|
| 1 | 親が用意した message template を使う | 実装済 (`--merge-message-file` 必須、`_message_has_ai_agent` を commit 前 (`--dry-run`) と commit 後 (`git log -1 --format=%B`) の 2 回) |
| 2 | 競合・provenance preflight 非 0 なら merge 中止と lease 返却 | 実装済 (`_StageFailure` → `_cleanup_lifecycle` → `merge --abort` + `release`、`pthread_sigmask` で signal 中も保護) |
| 3a | 走行前の behind 再検査 | 実装済 (`_behind_count(..., "postcheck") != 0` で停止) |
| 3b | 走行前の `git status --porcelain` 空検査 | **未実装** |

[T-694] 側 (tools/ 正本 wrapper、`_ACCEPTED_CLAIM_STATES` の exact 一致、signal 経由の確実な
release、`_MIN_ACCEPTANCE_POLL_SECONDS = 30` の周期固定) は残差ゼロ。

## scope

- **R1**: `run_acceptance` に「受入 command 投入直前の tracked clean 検査」を 1 段追加する。
- **R2**: `docs/pegasus-runbook.md` §7.3 へ点 3b を明文化する (§7.3 の改訂は本 wave 所有と裁定に明記)。
- **scope 外** (real でも実装せず裁定パッケージへ): `--owned-path` 未指定時に overlap 判定が
  警告だけで続行する default-open、lease の fencing token 不在、holder が invocation を
  識別しない既知限界、`run_tests.py` 側への同種 gate。

## 既存被覆 (機構名でなく性質で検索した結果) と純増検出力

「受入 command が実行される瞬間に、tracked 木が HEAD と一致することを保証する検査」を探した。

- `tools/run_tests.py` `_tree_and_submodules_fingerprint`: **CAP_OOM fallback 経路でのみ**
  before/after を比較する。走行「中」の変化の検出であり、走行開始時の dirty は拒否しない。
- `tools/run_tests.py` の受入 preflight 群 (`_preflight_unstaged_deletions` / ruleops /
  submodule): 未 stage **削除**は拒否するが、変更・追加は拒否しない。
- `tools/dev_wave_land.py`: main 側の tracked/index/submodule dirty と incoming 衝突 untracked を
  拒否する。wave 側は tested_tip の SHA 一致で見るため、**走行中に存在し走行後に破棄された編集**は
  tip を動かさないので検出できない。
- `tools/dev_wave_wait.py` `_identity_preflight`: tracked clean を検査するが `claim` の**前**に 1 回だけ。

**純増検出力** = 「claim 前は clean だったが、lease 待ち (既定上限 7200 秒) と merge を挟む間に
tracked が汚れ、受入がその汚れた木で緑になり、走行後に編集が破棄されて tip が変わらないまま
land する」経路。この 1 経路は既存のどの検査にも当たらない。仮想的ではない — `CLAUDE.md`
進め方 9 が「待つ間に独立な解析・検証・合成・**文書**を進める」と親へ指示しており、
待ち窓に親が tree へ書く運用そのものが前提になっている。

## 成果物影響 (DW-G05)

実装しない場合、worklog に記録される受入結果が land される tip の木と対応しない事例が残る。
受入緑の意味が「この tip を測った」でなくなり、実際に land した木が一度も測られていない可能性を
排除できない。

## 不変条件

- 既存 rc 契約を変えない (`2` = 起動前の入力・tree identity 不正、`70` = fail-closed、
  `74` = cleanup 未確認、それ以外の非 0 = 受入 command の rc)。
- 既存 58 テストを緑のまま保つ。`--merge-message-file` / `--owned-path` / poll 30 秒下限 /
  `acquired`・`held-self` の exact 判定を緩めない。
- 恒真な検査を作らない (禁止したい形を実際に落とす負例テストを必ず添える)。
- 検査は 1 コマンド 1 値へ分解し、rc をパイプへ通さない。

## provisional 裁定 (親のものであり、段 3 の攻撃対象)

- **(P1) 実装位置 = `tools/dev_wave_wait.py` のみ。** `run_tests.py` へは入れない。F191 点 3 が
  待ち手を名指ししており、`run_tests.py` へ入れると稼働中の全 wave の受入へ即座に効く
  (blast radius が本 wave の scope を超える)。
- **(P2) 述語 = `git status --porcelain --untracked-files=no` の出力が空。** `_identity_preflight`
  の `preflight-clean` と**同一述語を 2 時点で評価する**形にする。untracked を含めると job
  artifact 由来の偽赤を招く。
- **(P3) 失敗時の lease 扱い = 既存 `_StageFailure` 経路に載せる** (ACQUIRED なら release、
  HELD_SELF なら保持)。保持案 (親が直して即再開できる) は lease leak の risk を持つため取らない。
- **(P4) 検査の位置 = `postcheck` 群の最後、`acceptance-command argv=` の出力より前。** behind>0
  経路では merge commit 直後なので構造上 clean であり、値を持つのは behind==0 経路である。

## 成果物の形

- `tools/dev_wave_wait.py` の差分 (stage 1 段追加、stage 名は `prerun-clean`)。
- `orchestrator/tests/test_dev_wave_wait.py` へテスト追加 — 通る正例 1 本 (clean なら投入される)、
  負例 (dirty なら受入 command を投入せず rc=70、lease は release される)。
- `docs/pegasus-runbook.md` §7.3 へ 1 項 (親が書く)。
- `docs/spool/` の worklog fragment (親が書く)。

## 並列分割

実装子 1 本 (コード + テストを同一所有)。docs は親。分割の余地が小さいため並列化しない。
