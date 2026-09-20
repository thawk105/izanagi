# 段 4 裁定 — [T-2609][T-2656]

入力: 段 2 plan (`codex/s2-plan.md`)、段 3 相談 A (等価性、`codex/s3-consult-A.md`) / B (fail-closed・受理集合・P2、`codex/s3-consult-B.md`)、親の追加実測
(`difftree-always-shape.txt`、`new_dir_commit_rate.py`: 直近 60 main commit の 50 % が新 directory を導入)。裁定 inbox に本 wave 関連の更新なし。

## 所見の裁定

| 所見 | 判定 | 採否・処理 |
|---|---|---|
| A-M1 (c) porcelain `git diff` → plumbing `diff-tree` で `diff.ignoreSubmodules` (UI config) の扱いが変わり gitlink merge で判定差 | real | **(c) は条件付き採用**: `git config --get diff.ignoreSubmodules` と `--get diff.relative` が rc=1 (全層で未設定) のときだけ高速経路、どちらかが設定されていれば全 merge を従来経路 (`_paths_changed_from` × 親) で取る。判定は変えない (未設定なら UI/basic config の差は name 集合に効かない — 相談 A の評価: `diff.noprefix` / `core.quotePath` (`-z`) / `diff.orderFile` (集合化) は差にならない)。gate 検査は監査 1 走に 1 回。設定を argv へ移す案 (`--ignore-submodules=`) は旧判定を変えるので不採用 |
| A-N1 (a) 親表は閉包全体、閉包外親は root と解釈せず親表全体を破棄、`--simplify-*` 等の境界を論証に明記 | real | 採用 (plan どおり閉包全体の index に対して親表を作る) |
| A-N2 (b) 全 token 検査、最終 commit の path に既知 OID / 未知 OID / 64 hex を置く fixture | real | 採用 |
| A-N3 (c) 重複除去は取得要求だけ、worker の selected 重複監査を保存、同一親の slot を統合しない | real | 採用 |
| A-N4 (d) `None` / `[]` の区別は必要、falsy 変異は契約 kill であって判定差 kill ではない | real | 採用 (変異表で区別) |
| A-N5 変異表の kill 理由: intersection→union は `--cc` が除外するので偽陽性にならない、判定差と契約差を分ける、authoritative CLI で高速経路の発火を確認してから旧取得と比較 | real | 採用 (下の事前登録に反映) |
| A-N6 brief の数値表現 (66 % は `_normal_commit_audit` 累積比、tempdir 74 秒は関数内 subprocess 外の累積差、「確実に収まる」は保証でない、3.5 % は標本値) | real | brief 末尾に段 4 訂正として追記 |
| A-N7 attributes 失効は「新 directory を持つ tracked path が index に加わる」条件、頻度は要確認 | real | 採用。親の実測: 直近 60 main first-parent commit のうち 30 (50 %) が新 directory を導入 (毎 wave の insight dir)。wave 単位ではほぼ毎回 |
| B-M1 D2148 項 8 の誤読 / land の `timeout=480` と dispatcher の queue 待ち 900 秒の構造 | real | 誤読は親の逐語切り出しミス (別 D の項 8 を切った) で修正済み。land の 480 秒と dispatch 全区間の期限の両立は **scope 外** (T-2484 = D2148 項 8 の実装 wave の範囲)。本 wave は timeout を 1 秒も変えず、構造だけ insight に記録して次の一手へ |
| B-M2 固定全史の旧版/新版比較の実行仕様 | real | 採用: 旧 checker は `b7f970dfa:tools/check_ai_provenance.py` の blob、検証用 worktree の同じ path 位置で旧/新を交互に実行、cold authoritative (公開経路は未知 `GIT_*` 変数で新 partition = cold、内部比較は `receipt_state=None`)、selected 列・重複監査回数・順序付き `HistoryAudit`・rc・stdout/stderr を比較。bounded scope の予算・ピーク行は動的診断として比較対象から除く。親が段 6 で実施 |
| B-M3 変異 matrix の nodeid・所要・5 分予算 | real | 採用: 変異は小 fixture test で kill し、全史を変異ごとに載せない。全史比較は変異とは別の 1 回。matrix は計算ノード |
| B-S1 混雑時の cold 全史は未実測、CPU 秒でなく期限内完了の予測材料が要る | real | 採用: 改善前後を同時刻帯で交互 2 ラウンド以上 (現時点の負荷)、混雑時観測は wave 中に得られたら追記。「480 秒に確実」は書かない |
| B-S2 provenance task は `env_mode="inherit"` で「clean env」は誤り、cold/warm と環境差の混同 | real | brief 訂正: 計算ノード job は PBS job 環境を継承し (allowlist 空)、login シェルの `LANG`/`GIT_EDITOR` が届かず別 partition。cold な land では dispatch に受領証の追加損失は無い |
| B-N1 見出し一致 ≠ 内容対応の証明、CR の text-mode 変換は既存挙動 | real | 採用: 実 Git の完全出力比較 fixture、両経路とも同じ text-mode decode |
| B-N2 捕捉例外は到達可能なものに限定 | real | 採用: `RuntimeError, OSError, UnicodeError` + `ValueError` (埋込み NUL) を投機取得に限り捕捉、`BaseException` は不可 |
| B-N3 (a)〜(d) 全部の必要性は未証明、wall モデル | real | 採用: 各候補を独立に有効化できる実装にし、段階測定は login 全史の改善前後比較で総量を示す (候補別の ablation は本 wave では取らない — 時間対効果) |
| B-N4 3.5 % の Wilson 95 % 区間 1.2〜9.8 %、queue は共有 | real | brief 訂正 |
| plan (e) tempdir 共有は見送り、`%(trailers)` / cwd 変更は見送り (P1) | — | 採用 (P1 維持) |

## T-2609 の裁定 (P2 の扱い)
相談 B の判定 (refuted: 「不要と確定」ではなく「証拠不足で保留」) を採る。**本 wave では CPU 時間 (負荷) を dispatch 判定に足さず、`main` の dispatch 判定・`grant_budget`・`--force-dispatch`・
`authoritative` を変えない。** 根拠: (i) login 全史 cold は空いていれば 88 秒 (CPU 368 秒) で、混雑時の現行値は未実測、(ii) dispatch は queue 待ちの尾 (最大 538 秒) と
land の 480 秒 timeout の構造 (B-M1) を抱え、基盤失敗 3/86 (Wilson 95 % 1.2〜9.8 %)、(iii) T-2656 の改善で CPU 総量が下がれば混雑時の wall も下がる見込みで、
その実測後に混雑時観測を集めて再訪する。decisions fragment に「保留 (再訪条件: 改善後の login 全史が混雑時に 480 秒を超える観測が 1 件でも出たら、負荷を入力にした
実行場所判断を別 wave で設計)」と記す。

## plan v2 (差分だけ)
- (a) 採用: `_Ancestry.parents` (閉包全体)、`_commit_paths(commit, *, parents=None)`、oracle / `--range` は従来。
- (b) 採用: `git diff-tree --stdin --root --no-renames -r --name-only -z --always`、全 token 検査、fallback は全 non-merge を従来経路。
- (c) 条件付き採用: `diff.ignoreSubmodules` / `diff.relative` 未設定 gate (監査 1 走に 1 回) を通ったときだけ親番号ごとの batch。設定あり・batch 失敗は全 merge を従来経路。
- (d) 採用: `values=None` keyword-only、`_normal_commit_audit` で 1 回だけ parse。
- (e) 見送り。dispatch 判定は不変。
- テスト: plan の計画 + A-N2/N5/B-M2/M3 の修正。旧版/新版の固定全史比較は親が段 6 で実走 (test には載せない)。
- 実装子 1 本 (所有: `tools/check_ai_provenance.py`, `orchestrator/tests/test_check_ai_provenance.py`)。

## 変異の事前登録 (DW-M01、位置は関数名。行番号は実装後に確定し単一理由性を確認する)
| # | 位置 | 変異 | 種別 | 期待 kill (test) |
|---|---|---|---|---|
| M-1 | (a) `_build_ancestry` 親 tuple 作成 | 第 1 親だけ保存 | 契約 | 親列一致 test (octopus / 2 親) が赤 |
| M-2 | (a) 親表検証 | 閉包外親を root (空 tuple) として受理 | 契約 | 親表破棄 + `%P` fallback 発火 test が赤 |
| M-3 | (b) 一括 argv | `--always` を落とす | 契約 | 空差分 fixture の見出し件数 / fallback 計数 pin が赤 |
| M-4 | (b) parser | 後半破損時に前半辞書を返す (部分結果公開) | 判定差 | 先頭の違反 commit の path を空にして後続を破損させた fixture で finding が消える |
| M-5 | (b) parser | OID 型 path を見出し候補から除外して通常 path として受理 | 契約/判定差 | hex 名 path fixture (最終 commit 位置) が赤 |
| M-6 | (c) 設定 gate | `diff.ignoreSubmodules` 設定時も高速経路を使う | 判定差 | `diff.ignoreSubmodules=all` + gitlink merge fixture で finding 差 |
| M-7 | (c) batch | 最終親 batch 失敗でも先行 batch を使う | 判定差 | 手動解消 merge fixture の finding 差 + 全親 legacy 呼出し pin |
| M-8 | (d) `_normal_commit_audit` | 別 commit の values を渡す (取り違え) | 判定差 | 混在 fixture で AI-Agent 欠落 finding が消える / 増える |
| M-9 | (d) validator | `values is None` → falsy | 契約 | 空 values の parser 回数 pin が赤 |

## 不変条件 (再掲、変更なし)
判定・findings・rc・公開出力 1 bit 不変。`authoritative` / `--force-dispatch` 不変。既知違反 56 件 (post-baseline 3) の検出は固定全史比較 (旧/新) で OID・kind・value・順序を照合。fail-open にしない。新 gate・台帳・一般化を足さない。timeout を変えない。
