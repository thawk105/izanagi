# 段 4 裁定 — [T-2709] (2026-09-20 07:36 JST)

入力: `s1-brief.md`、`codex/s3-consult.md` (2 レンズ、must-fix 7 / should 5 / nit 2、`check_codex_output.py` rc=0)。
裁定 inbox の再走査: `docs/handoff/` は README + 2026-08-28 の 1 件 (本 wave と無関係)、local main は `b7f970dfa` のまま (07:36 JST、`git log -1 main`)。

## 1. 所見の裁定 (real / refuted、採否、scope)

| # | 判定 | 採否 | 是正 (plan v2 へ) |
|---|---|---|---|
| A1 `.git-ref` が worktree を汚染、modules symlink は `core.worktree` を壊す | **real** | 採用 | 参照値は builder 直後に抽出し、参照 `.git` は work-root 直下 (`work/git-ref`) へ `rename` で退避。試行の再初期化は `mv .git/modules → work/modules-keep` → `rm -rf .git` → `git init` → 参照 `config` を複写 → `mv` で modules を戻す (rename、同一 FS、timed 外)。symlink は使わない。selftest で gitlink OID 一致と submodule 内変更の status 検出を正負例で確認 |
| A2 C2 の不足 blob 供給 | **real** | 採用 | source に無い OID は fixture 現物から `git hash-object -w --stdin-paths` (attributes を効かせる) で生成し **C2 の timed 区間に含める**。生成 OID ≠ 参照 OID なら失格。hash 参照は regular file のみ (gitlink・symlink を除外)、件数・bytes を記録 |
| A3 C1 に OID 選定費用が無い、pipe の wall | **real** | 採用 | C1 を「採用候補」形に改める: timed に **選定** (source の `ls-files -s -z -- orchestrator output`、`ls-tree -r -z <real_basis> -- <in_repo_sources>` の上書き、`cat-file --batch-check` の存在確認) を含める。参照 index は C1 で使わない。移送 wall は pipe 両端の外側 1 本。C2 の合計に `update-ref` を含める。python 側の準備は外側総時間との差で残す |
| A4 main 初回 ≠ cold | **real** | 採用 | 語彙は「main 初回」「反復」。事前実験の前に「初回移送」を 1 回別記録し「cold 未保証」と明記 |
| A5 「移送 + ハッシュ 1 回」は普遍的下限でない | **real** (`checkout-index -u -f` が反例) | 採用 (記述の限定) | (P1) を「複製済み worktree を変更せず空 stat の index を通常設定で検証する経路の参考費用」に限定。`checkout-index` 経路は本 wave で測らず、**裁定パッケージ候補** (移送 + checkout-index で `output/` 複製 52.9 秒そのものを置換しうる別案) として記録 |
| A6 freshen の記述・object 集合 | real | 採用 | 記述を「内容から OID を計算 → packed を freshen → 成功なら loose を省く」に改める。commit metadata (author/committer の name/email/date) を全方式で固定し、**commit OID の一致**を不変条件に加える |
| A7 事前実験は外側 wall、副次記録 | real | 採用 | 事前実験も外側 wall で比較、pack bytes・`getrusage(RUSAGE_CHILDREN)` の CPU 差分・両 rc を記録。`--window=0 --depth=0` を「再利用のみ」と説明しない |
| A8 過去値は条件付き参照値 | real | 採用 | README に限定表を載せる。9.5 秒は上限でなく整合性確認用 |
| B1 同値性の検査不足 | **real** | 採用 | 4 検査を追加 (§3) |
| B2 判定規則の語彙と最小効果量 | **real** | 採用 | §4 の事前登録を改訂 |
| B3 JSON の再計算可能性、禁止文 | real | 採用 | §5、author prompt の禁止文に採用 |
| B4 copy 後の stat 不一致 | real (scope 外) | 副次量に 1 計測を追加 + 裁定パッケージ候補 | 方式ごとに 1 回、fixture 全体を production と同じ `copytree(symlinks=True)` で複製し、複製先で production 形 status1/status2 を timed で取る (A にも C にも共通の現行費用を数値化) |
| B5 採用 wave の先取り、不採用の範囲 | real | 採用 | README の裁定パッケージ節に反映。悪化・未確定でも D2068(C) を「符号確認済み不採用」へ書き換えず「測った設定での観測」を記録 |
| B6 予算 | nit | 採用 | walltime 01:30:00、subprocess ごと timeout 1200 秒、試行ごとに JSON を書き出す (途中死でも部分結果が残る) |
| B7 selftest は時間差で assert しない | nit | 採用 | index bytes/mtime の不変・保存で判定 |

棄却した所見: なし。

## 2. brief の訂正

- (P1) を A5 のとおり限定する。「それより下に届く経路は無い」は撤回。
- (P2) C1 = 選定 + 移送 + `add -A` + commit + status1 (採用候補形)。C2 = 移送 + 不足 blob 生成 + index-info + write-tree + commit-tree + update-ref + 明示 refresh + status1 (参照 index を無料で使う下限模型、production 設計ではない)。
- (P4) 「読取り支配」は仮説。初回は cold 未保証。
- (P5) を §4 に置換。
- 「削減上限 9.5 秒」は固定上限でなく、本 wave の A の実測で置き換える。

## 3. 不変条件 (試行の失格条件、timed 外)

各試行後: (i) tree OID = 参照 (builder の tree)、(ii) commit OID = 同方式・他方式の全試行と一致 (metadata 固定)、(iii) production 形 status1 の stdout が空、(iv) `rev-list --objects HEAD` の集合 = 参照集合 (件数でなく集合、参照 commit だけ除く)、(v) `fsck --connectivity-only` rc=0、(vi) `objects/info/alternates` 不在、(vii) 移送 pack の object が全部 blob (`verify-pack -v` の型列)、(viii) source の receipt に記録された commit (`migration_basis_commit` 等、`migration.RECEIPT_REL` の hex 値) が fixture で `missing`。
方式ごとに 1 回 (最初の成功試行の後): (ix) 独立性 — work-root 外の参照を隠した状態で fixture 全体を別 dir へ複製し、複製先で status が空・参照 blob 全件が `cat-file --batch-check` で present、(x) 変更検出 — tracked file へ 1 byte 追記 → status に ` M`、mode 変更 → status に ` M`、submodule 内の tracked file 変更 → status に submodule 行、いずれも元に戻して status が空に戻る。

## 4. 判定規則 (事前登録、結果を見て変えない)

- 主指標: base 1 回あたり `total_s` = A: add + commit + status1 / C1: 選定 + 移送 + add + commit + status1 / C2: 移送 + 不足 blob 生成 + index-info + write-tree + commit-tree + update-ref + refresh + status1。round ごとの paired 差 `d_r = C1_r − A_r` (同 round の試行、5 round)。
- **改善候補**: median(d) ≤ −1.0 秒 かつ 5 round 中 4 以上で d < 0。**悪化観測**: median(d) ≥ +1.0 秒 かつ 4 以上で d > 0。**それ以外は未確定。**
- 行動: 改善候補 → 採用再検討の裁定パッケージ (README §裁定パッケージ、採用 wave の面と変異を先取り)。悪化観測 / 未確定 → 本 wave は「現行維持」で閉じ、D2068(C) には「測った設定・集合・環境での C1 の観測」を追記する (「符号確認済み・全体不採用」とは書かない)。
- C2・(P6)・copy 後 status は主判定に使わない。失格試行は数値を採らず、失格理由と件数を報告する。5 round が揃わない (失格・timeout) ときは揃った round で同じ規則を適用し、round 数を明記する。
- 「main 初回」の C1 が同 round の A を上回るときは、その事実を裁定パッケージの再検討条件に明記する。
- per-base の差を受入 wall の改善へ読み替えない (D357/D1260 は wall の基準)。wall への写像は模型として README に別記する。

## 5. plan v2 (probe 仕様の確定版)

`codex/spec-draft.md` を次のとおり改訂して author の正本にする (改訂後の全文は `codex/spec-v2.md`)。

1. 土台: builder 1 回 (`issue_receipt=False`)。直後に参照値を抽出 (tree、commit、`ls-files -s -z`、`rev-list --objects HEAD` 集合、`count-objects -v`、`config` の複写元)。`.git` を `work/git-ref` へ rename。以後 fixture root 直下には `.git` 以外の隠し dir を置かない。
2. 再初期化 (timed 外): `.git/modules` を `work/modules-keep` へ rename → `rm -rf .git` → `git init -q` → `work/git-ref/config` を `.git/config` へ複写 → `work/modules-keep` を `.git/modules` へ rename。
3. commit metadata の固定: 全方式の commit で `GIT_AUTHOR_NAME/EMAIL/DATE`、`GIT_COMMITTER_NAME/EMAIL/DATE` を env で固定 (builder と同じ name/email、date は固定文字列)。
4. A / C1 / C2 の timed 区間は §4 のとおり。C1 の選定は source から (参照 index を使わない)。in_repo_sources と real_basis は builder と同じ導出 (known_axes JSON と receipt JSON、timed 外)。
5. 移送: `git -C <source> pack-objects --stdout <args> < oid-list` | `git index-pack --stdin -v` (cwd=root)。外側 wall + 両 rc/stderr + pack bytes + `RUSAGE_CHILDREN` 差分。
6. 事前実験: 「初回移送」(既定設定、1 回、cold 未保証) → {既定, `--window=0 --depth=0`} 交互 × 3 → 外側 wall 中央値が小さい設定を main に採用 (同点は既定)。
7. 順序: round 1..5 で A/C1/C2 を巡回、round 先頭で hash 参照 (regular file のみ)。
8. 副次量: 各試行で `.git` copytree の wall と `du -s .git/objects`、`count-objects -v`。方式ごと 1 回、fixture 全体を copytree (symlinks=True) → 複製先で status1/status2 (timed) → 削除。
9. 検査: §3。失格は `failed` と理由を試行 record に残す。
10. 出力 JSON: B3 の項目全部。試行ごとに `--out` を上書き保存 (途中死でも残す)。subprocess timeout 1200 秒。
11. selftest (login): 合成 repo で (a) 3 方式の tree/commit 一致、(b) index-info 直後の index が空 stat (`ls-files --debug`)、production 形 status 2 回で index bytes が不変、明示 refresh 後に stat が埋まる、(c) pack 既在の add で loose が増えない (pack 無しの対照で増える)、(d) 失格判定の負例 (alternates を置く / tree を変える / 余分な commit を移送する)、(e) submodule 復元の gitlink 一致と submodule 内変更の検出。
12. 禁止事項 (author prompt へ逐語): 「選定・移送・不足 object の生成・index の検証と保存に必要な処理を timed 外へ移して、自己完結経路の総費用と記述してはならない。production の status 引数・環境・変更検出を弱めてはならない。失格・timeout・欠測を黙って除外または再試行し、成功分だけで事前登録判定を満たしたと報告してはならない。main 初回を cold と断定し、per-base の差を受入 wall の改善へ読み替えてはならない。」

## 6. 変異事前登録

実装面の差分ゼロ (probe は repo に残さない) → DW-S04 により変異 matrix は免除。受入全走は免除しない。probe の fail-closed 挙動は `--selftest` の正負例で親が login で実走する。

## 7. 裁定パッケージ候補 (scope 外の real 所見、README に記録し起票はしない)

1. 移送 + `checkout-index -u -f` で `output/` 複製 (D2086 §2-1 で 52.9 秒 = 45%) そのものを置換する経路 (A5)。未測定。
2. base→test の `copytree` 後に index stat が一致せず、`GIT_OPTIONAL_LOCKS=0` の status が test copy ごとに全件再ハッシュしている可能性 (B4)。本 wave で方式ごと 1 回だけ数値を取る。
3. 採用 wave の面・変異 (B5)。

## 7b. 段 5 後の追記 (07:57 JST、本走投入前に確定)

- 親レビュー: probe (`0e675923…`、959 行) の timed 区間・再初期化・production 形 status・検査 (i)〜(x) は §5 の仕様どおり。fix は投げない。
- 判定規則の縮退: 成功 round 数 n が 3 未満なら probe の `verdict` にかかわらず README では「未確定」とする (n=1 で閾値 0 になり 1 round で決まるのを避ける)。結果を見る前に確定。
- JSON の大きさ: 各 git record が stdout 全文を hex で持つため本走 JSON は 100 MB 級になる見込み。insight には先例 (T-2708 `run2-result.projected.json`) と同じく、大きい hex field を落とした射影 JSON と、原本の sha256・bytes を置く。原本は job dir に保全。
- selftest (login、pegasus02、Lustre) rc=0 で 20 項目緑、hold-session-only rc=0 (内部 pytest rc=5、module は W から load)。

## 8. 工程

段 5: author 1 本 (unit worktree `t2709-unit-probe`、所有 `tools/t2709_blob_transfer_probe.py`)。親: selftest / hold-session-only を login で実走 → probe を job dir へ退避 → generic dispatch (walltime 01:30:00、queue-wait 7200、grace 5400) → 結果 JSON を読む → 段 6 review 1 本 (probe + JSON + README 草稿) → 段 7。
