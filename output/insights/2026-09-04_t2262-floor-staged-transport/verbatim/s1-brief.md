# 段 1 brief — [T-2262] 床値 official の staged transport を driver 内部の production 既定へ移す

- wave: t2262-floor-staged-transport
- worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2262-floor-staged-transport
- branch: worktree-dev-wave-t2262-floor-staged-transport
- 基準 commit: c7ed565892cd4aba52d7fa47a7d1da17b117c005 (local main と同一)

## scope

床値 campaign の official 走行が起動できない状態 (D1396) を、staged FetchContent transport を
driver 内部の production 既定へ移すことで解く。本題の実装だけを行う。仮想リスク向けの gate・検査・
台帳・一般化は scope 外 (DW-G05)。official 走行そのものの実施・測定は本 wave の scope 外。

## 確定済みユーザー裁定 (D1562。覆せるのは裁定時の未見事実だけ)

- 解消案 1 を採る。payload の所在を caller の seam でなく **driver 側で導出**する。
- 18 名の不適格 seam 集合 (`REFREEZE_DISQUALIFYING_SEAM_NAMES`) と
  `_derive_refreeze_eligibility` の判定式は **literal には変えない**。
- 導出規則は**明示的に固定**し、発見 (discovery) による暗黙の入力経路を作らない。
- 却下済み: 18 名集合・判定式を変える / 既定経路 (外部取得) で投入する / 承認束縛だけ先に実装する。

## 成果物影響 (DW-G05)

放置すると床値 official は 1 回も起動できず、`eligible_for_refreeze` が真になる走行が存在しない。
v2 candidate freeze への昇格経路が閉じたままで、床値の certified 値が出ない。

## 変更面 (実アンカー、main c7ed5658 で実測)

| # | anchor | 現状 |
|---|---|---|
| A1 | `tools/pegasus/floor_campaign.sh:697-721` | `stage_floor_fetchcontent_payload` が `$SUBMISSION_DIR/masstree-payload/{masstree,mimalloc,googletest}-src` を `$TMPDIR/izanagi-floor-fetchcontent` へ `cp -a` |
| A2 | `tools/pegasus/floor_campaign.sh:1231` | `driver_argv+=(--fetchcontent-base-dir "$FETCHCONTENT_STAGING")` — この 1 行が seam を非既定にする |
| A3 | `tools/pegasus/floor_campaign.sh:1209-1211` | 既存の production env 契約は `IZANAGI_FLOOR_JOB_STAGING`(=ATTEMPT_DIR)、`IZANAGI_FLOOR_JOB_CHECKPOINT_PATH` の 2 本のみ |
| A4 | `orchestrator/campaign/s8b_floor_campaign.py:2986-3060` | `_canonical_floor_fetchcontent_base(None)` が TMPDIR 下に `mkdtemp` で**空**の base を作る (legacy) |
| A5 | 同 `:3234-3245` | `fetchcontent_base is None` → legacy 無条件 prebuild (外部取得)、非 None → staged (pin 検査 + 明示 source dir) |
| A6 | 同 `:2380-2440` | staged payload の pin 検査機構 `s8b-floor-masstree-payload/v3` は driver 内に既在 |
| A7 | 同 `:6918-6967` | seam 分類器 (18 名 closed set assert) と判定式 |
| A8 | 同 `:7039-7042`, `:8236` | official の非既定 seam 拒否、CLI `--fetchcontent-base-dir` (「pilot 専用の非 default seam」) |
| A9 | `orchestrator/campaign/s8b_floor_contract.py:42-50` | 18 名集合の literal |

導出の可否 (実測。**下の erratum で訂正済み**): `ATTEMPT_DIR="$JOB_STAGING_ROOT/$PBS_JOBID"` (sh:349) と
`SUBMISSION_DIR="$ATTEMPTS_ROOT/submissions/$IZANAGI_SUBMISSION_NONCE"` (sh:552) は互いに導出できない。

## erratum (親が段 2 投入後に自分で見つけた訂正。初稿の記述は誤り)

初稿は「既存 env 2 本から payload 所在は導けない」と書いたが、**これは誤りである。**
driver が起動される時点の環境には、`IZANAGI_FLOOR_JOB_STAGING` /
`IZANAGI_FLOOR_JOB_CHECKPOINT_PATH` 以外にも production 入力が存在する。実測は次のとおり。

| anchor | 事実 |
|---|---|
| `tools/pegasus/submit_floor.sh:621,635` | PBS へ `-v "IZANAGI_SUBMISSION_NONCE=$NONCE"` を渡す。job 環境に入る |
| `tools/pegasus/floor_campaign.sh:41-43`, `:547-549` | job 本体が `IZANAGI_SUBMISSION_NONCE` を必須とし 32 桁小文字 hex を検証する。不正なら bootstrap で停止 |
| `tools/pegasus/floor_campaign.sh:971` | driver 起動前に `IZANAGI_RESERVATION_NONCE="$IZANAGI_SUBMISSION_NONCE"` を export する |
| `orchestrator/campaign/floor_job_checkpoint.py:486` | driver が import する module が既に `IZANAGI_RESERVATION_NONCE` を読む |
| `orchestrator/campaign/certified_writer_admission.py:66` | 別 module が既に `IZANAGI_SUBMISSION_NONCE` を読む |
| `tools/pegasus/floor_campaign.sh:280-282`, `:552` | `OUTPUT_ROOT="$REPO_ROOT/output"`、`SUBMISSION_DIR="$OUTPUT_ROOT/env/pegasus/floor/attempts/submissions/$IZANAGI_SUBMISSION_NONCE"` |
| `tools/pegasus/floor_campaign.sh:716` | `FLOOR_THIRD_PARTY_PAYLOAD_ROOT="$SUBMISSION_DIR/masstree-payload"` |
| `tools/pegasus/floor_campaign.sh:46` / `orchestrator/campaign/s8b_floor_campaign.py:86-87` | job の `REPO_ROOT` は `$PBS_O_WORKDIR`、driver の `ROOT` は `__file__` 由来。production では同一 checkout |

したがって payload 所在は、**既存の production env 契約 1 本と固定の path 式だけ**で導ける:
`ROOT / "output/env/pegasus/floor/attempts/submissions" / <nonce> / "masstree-payload"`。
新しい env 変数の新設は必要条件ではない。

## 不変条件

1. A9 の 18 名集合の literal と A7 の判定式の literal は変えない (D1562)。
2. official・fresh・非既定 seam ゼロだけを適格にする**意味**も緩めない (規律 2)。
   pilot は mode 条件で不適格のまま (D811 と整合) — 実測で確認する。
3. staged payload の pin 検査 (A6) を production 既定経路でも必ず通す。検査失敗を legacy/外部取得へ
   フォールバックさせない (A5 のコメントが既に禁じている)。
4. 導出規則は明示・固定。directory 走査や候補探索で payload を「見つける」経路を作らない。
5. 凍結 bytes pin は不在 (DW-O09 閉包: `admission_registry.json` は dispatch 分類のみ、
   `test_official_perf_closure.py` は perf 呼出し述語のみ)。DW-O10 は非発火。
6. 計算ノードは直結 network を持たない。外部取得へ落ちる既定を production に残さない。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- (P1-a) payload 所在の導出規則は、**既存の submission nonce の env 契約と固定 path 式**から driver 側で
  導く (erratum の式)。新しい env 変数は作らない。**検査点: これは 18 名 seam の言い換えによる gate 迂回ではないか。**
  env 契約と caller seam の境界を、判定式の意味 (誰が何を注入できるか) で言えるか。
  nonce は 32 桁 hex に制約されるので path 注入面は seam より狭い、と親は見ているが、
  これはコードで確かめること。
- (P1-b) staging の `cp -a` 自体も driver 側へ移す。**攻撃点:** sh 側に残して base だけ driver が導出する案と
  比べ、どちらが「caller の seam でない」を満たすか。sh に残すと A2 の argv は消せても base path の合意が
  暗黙になる。
- (P1-c) `--fetchcontent-base-dir` CLI は pilot 専用 seam として残す。**攻撃点:** 残すと official でも
  渡せてしまう経路が残るのではないか (A8 の拒否で閉じるか)。

## 分割方針

- 段 2: read-only codex 1 本 (plan, file:line 粒度)。
- 段 3: 敵対 2 本 (sol / luna)。レンズ A = 規律 2 (gate 迂回・受理集合の拡大)、
  レンズ B = 機構の実在 (計算ノードの offline 条件・pin 検査の到達性・pilot/official の分岐)。
- 段 5: Codex `role=author` 1 本 (D95)。編集面が 2 file 系で producer/consumer 契約が跨るため分割しない。
- 段 6: 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。
- 軽量版は採らない。正しさ防壁 (official 拒否 gate) に触り受理集合が変わるため (DW-C00)。

## erratum 2 — official の起動を止める関門は 2 つある (親が段 2 投入後に実測)

D1396 が列挙した機構は staged transport の seam だけだが、**official にはもう 1 本、独立した
無条件拒否がある。**

| anchor | 事実 |
|---|---|
| `orchestrator/campaign/s8b_floor_campaign.py:8434-8440` | CLI `main` が `args.mode == "official"` を無条件で `status=refused` / rc=2 にする。理由は「承認束縛方式が §8 未裁定」 |
| 同 `:462-471` | `_assert_official_permitted` が core でも official を無条件 raise。docstring が「production flag・環境変数・引数での bypass を作らない」「テストは局所的な monkeypatch だけで dormant な official 結線を検証し、production の拒否意味論を変えない」と明記 |
| `run_campaign` `:7045` | official のとき `_assert_official_permitted(mode)` を呼ぶ |

帰結:

- 本 wave が seam を解いても、official は CLI からは依然起動できない。**本 wave が外すのは
  2 本のうち 1 本だけである。** 残る 1 本は §8 の承認束縛方式の裁定待ちであり、D1396 は
  その実装を明示的に見送っている。この点は段 4 で裁定し、最終報告に明記する。
- official 側の挙動変化は dormant 結線であり、既存の慣行どおり
  `_assert_official_permitted` の局所 monkeypatch でだけ検証できる (DW-O14 の正規 seam)。
- 一方 **pilot の観測可能な出力は変わる。** 現行 pilot は `--fetchcontent-base-dir` を受け取るので
  結果の `nondefault_seams` (`:7718`) に `fetchcontent_base_dir` が載る。既定化後は載らなくなる。
  pilot の `eligible_for_refreeze` は mode 条件で False のまま変わらない。
