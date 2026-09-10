# [T-503] 変異復元耐久化 実装 wave — 段 4 裁定と裁定パッケージ

- `authority: none`
- `default_effect: no-state-change`

可変状態の正本ではない。可変状態は `docs/worklog.md` 末尾と現行 phase doc が正本である。
本書は 2026-08-06 の実装 wave (branch `worktree-dev-wave-t503-restore-durability`) が、
**実装差分を作らずに止めた理由**と、着手前に決めるべき択一の凍結スナップショットである。

逐語は `verbatim/` — `s1-brief.md` (親の段 1 brief)、`s2-plan.md` (段 2 プラン)、
`s3-lensA.md` / `s3-lensB.md` (段 3 敵対相談 2 レンズ)。3 子とも
`codex exec -m gpt-5.6-sol -c model_reasoning_effort=max -s read-only`、
`tools/check_codex_output.py` rc=0。

## 結論

**本 wave はコードを書かない。** ユーザー裁定 (生死確認 GO、U-1〜U-10 + §9.1 必須 6 点) を
不採用にするのではなく、**裁定時点で未見だった新事実 4 件**を添えてユーザー再裁定へ戻す。
両レンズが独立に「段 5 進行 NO-GO」を返し、親が一次資料で裏取りした。

## 裁定時点で未見だった新事実 (親が一次資料で確認)

1. **木へ実際に触る process は arm より後に生まれる。**
   `tools/mutation_harness.py:1275-1290` は target を `write_text` した**後**に
   `subprocess.Popen(..., start_new_session=True)` で runner を起動する。dispatch mode では
   その先に別 job も生まれる。したがって §4.5 が要求する quiescence 束縛を、
   arm 時点の単一 writer identity を持つ `armed` record では満たせない。
   段 2 プランの exact-key v1 schema はこの process 群を表現できない (`s3-lensB.md` 所見 5)。
2. **worktree incarnation nonce は実在しない。** 本 worktree の `.git` は
   `gitdir: .../.git/worktrees/<name>` を指すだけで、admin dir に不変の身元は無い。
   §4.3 が要求する incarnation 束縛の発行者が現時点でいない。
3. **`PBS_JOBID` は login shell では unset。** 計算ノードの job 内でのみ存在する。
   identity を必須にすると login からは arm できず、必須にしなければ束縛が空洞化する。
4. **admission / oracle の code identity は leaf-only。**
   `orchestrator/campaign/artifact_admission.py:540` は `validator_sha = _sha256_file(Path(__file__))`
   であり、判定に使う `wal.read_records_checked` の意味論を receipt が閉じていない。
   oracle の `_GENERATOR_SOURCES` (`s8b_oracle_manifest.py:44-52`) も exact 5 source の leaf hash だけである。
   **この盲点は抽出が作るものではなく既存**であり、U-4 (a) の抽出は盲点を 1 file から 2 file へ
   広げる (新しい型の穴ではない)。

## 所見の裁定

### real かつ本 wave の停止根拠

| 所見 | 裁定 |
|---|---|
| A-4 S2 の compare-then-act は lease なしで CAS にならない | real。exclusive lease は scope 外 |
| A-5 `clean` の真偽を任意 callback が自己申告できる | real。verifier の issuer が scope 外 |
| A-6 process-local poison は fsync UNKNOWN を再起動後に忘れる | real。durable pending が要る |
| A-7 clean cleanup の再試行が次 attempt の `active` を消せる | real。state-root lock が要る |
| A-9 `TrustedRoot` は canonical 性を証明しない | real。(P2) は refuted |
| B-3 S1〜S3 は本 wave の差分では成果物を変えない | real。`DW-G05` の直撃 |
| B-5 `armed.writer` 一個では runner を束縛できない | real (新事実 1) |
| B-6 typestate API は順序を callback へ逃がす | real |
| B-8 実装順は S1→S2→S3 の直列 | real。brief の並列 3 本は refuted |

`DW-G05` は「成果物影響を書けない must-fix は nit/backlog とし、段 1 で書けなければ
子を起動せずその場で 1 cycle 後へ送る」と定める。S1〜S3 のどの部分集合も、
配線しない限り certified 選択・レポート・台帳の値・受理集合・参照を変えない。
両レンズは独立に「有効な部分集合は無い」と結論した。

### real だが本 wave の停止根拠ではない (次 wave または別 task へ)

| 所見 | 裁定 |
|---|---|
| A-1 / B-1 receipt の code identity closure が leaf-only | real、ただし**既存**の盲点。T-503 と独立の新規 task として起票する |
| B-2 新 file 追加は `clean_scan_digest` を変える | real、ただし file を足す全 wave に成立。主張を「歴史的 frozen bytes は不変、今後の launch lineage は変わる」へ縮める |
| A-2 WAL byte 不変が prose-only | real。抽出を行う wave の必須条件 (golden vector) として設計文書へ残す |
| A-3 facade の例外順序・materialization gate が未仕様化 | real。同上 |
| A-10 pre-arm crash の未登録 temp 残骸 | real。設計の主張を「live target に部分 bytes を作らない」へ限定する |
| A-11 / B-10 test 名・docstring が L-B UNKNOWN を超えて読まれる | real。次 wave の受入条件へ |
| B-9 metadata policy (xattr/ACL/inode flags) が未裁定・未計測 | real。下記 U-e |
| B-11 `docs/README.md` の状態が古い | real。本 wave の docs 更新で閉じる |
| B-12 durable 層を repo-wide framework へ一般化しない | real。設計文書へ限定を書く |

### 親の provisional 裁定の帰結

- **(P1) は縮小。** 「pin 不在 → proof chain 不変」の一般化は refuted。
  成立するのは「列挙した regression に対する現行挙動不変」までである。
- **(P2) は refuted。** 自由 root path も、caller が自前構築できる `TrustedRoot` も canonical にならない。
- **(P3) 成立** (何も配線しないので U-8 に抵触しない)。
- **(P4) 成立** (harness を触らないので U-10 の解除は不要だった)。

## L-B UNKNOWN の扱い (本 wave が明記する)

1. 成果物・docstring・docs は「物理ノード死 / client eviction / 電源断に耐える」と主張しない。
   設計 §10 の `[未計測]` を維持する。fsync 済み bytes の永続性は**前件**として書く。
2. 曖昧・判定不能は受理へ丸めず不受理を返す。
3. U-9 に従い [T-486] は `deferred` のまま、D130 条件 3 は closed にしない。
4. 実機 node-death 受入が無い間、活性化 gate を開けない。本 wave は何も活性化していない。
5. 次 wave の受入条件として、test 名・docstring・worklog の完了記述に
   「syscall 順序であって物理永続性ではない」「§9.1 の 1/4/5/6 未完」を exact に残す。

## ユーザーへ返す択一

| # | 軸 | 選択肢 | 親の推奨 |
|---|---|---|---|
| V-1 | T-503 の進め方 | (a) 活性化まで**どの層も配線しない**多 wave program として層を順に積む / (b) 設計 §7.1 の注記どおり「使い捨て専有 worktree 方式」を第一 slice にし、族一般化と consumer 契約そのものを回避する / (c) 履歴解決系の blocker が片付くまで T-503 全体を defer する | **(b)**。issuer 不在の 3 件 (canonical root・incarnation nonce・quiescence) は、専有・使い捨て worktree なら「捨てる」で置換でき、lease と consumer 契約も要らなくなる |
| V-2 | canonical state root と incarnation nonce の発行者 | (a) provisioner を先に作り receipt で束縛 / (b) V-1 (b) を採り root 自体を不要にする | V-1 に従属 |
| V-3 | post-arm の runner / job の束縛 | (a) journal へ runner 登録 record 型を足す / (b) 全 child を包含する exclusive lease / (c) scheduler terminal 証明だけに依存する | **(b)**。(a) は登録前の crash 窓が残る |
| V-4 | `clean` の発行権限 | (a) production verifier だけが発行できる sealed capability / (b) callback の返値を信頼する | **(a)**。(b) は段 3 が構成した「no-op restore で clean」を許す |
| V-5 | metadata の accepted set | (a) xattr/ACL/inode flags が非空・列挙不能なら arm 前に拒否 / (b) 論理 metadata だけ保存し残りは無視 | **(a)**。ただし実 target で正例が通ることを活性化前に実測する必要がある (未計測) |
| V-6 | U-4 (a) の抽出と receipt closure | (a) 抽出前に versioned transitive source closure を新設する / (b) leaf-only のまま抽出し、盲点の拡大を別 task で閉じる / (c) read 側の抽出を見送り write 側 primitive だけ共有する | **(b)**。closure の盲点は既存であり、T-503 を人質にすべきではない |

## 新規 task 候補

- **proof chain の code identity closure が leaf-only。** admission receipt の `validator.sha256` と
  oracle の `generator_versions` は、判定に使う被 import module の意味論を閉じていない。
  T-503 と独立に成立する穴であり、独立の task として起票する。
- **`_assert_clean_tracked` が ignored file を見ていない。** 設計 §10 が実測済みで、
  `*.o` / `build/` / `*.so` のようなテスト結果を左右する生成物に盲目である。
  T-503 の活性化とは独立に実装でき、成果物影響 (汚染木で得た値が台帳へ載る) を書ける。

## この wave が主張しないこと

- 段 2 プランが誤っているとは主張しない。プランは所与の scope に対して整合していた。
  止めた理由は scope の切り方であり、プランの品質ではない。
- S1〜S3 の設計が不要だとも主張しない。V-1 の答え次第で大半が再利用できる。
- 物理ノード死後の fsync 永続性については何も測っていない (L-B は UNKNOWN のまま)。
