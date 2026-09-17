# 段 4 裁定 — [T-2637][T-2660] repo 外走査の並列化 (第 1 段)

作成: 2026-09-17 07:08 JST。入力 = s1-brief.md、s2-plan.md、s3-a.md (レンズ A)、s3-b.md (レンズ B)、rulings-verbatim.md。
裁定 inbox と main (abc7085ae → b4631a92e、第 20 回裁定 = **D2104 項 20** の fold のみ) を再走査し、本件に影響する更新は無い。

## 1. 所見の裁定 (real / refuted、採否、scope)

| ID | 判定 | 採否・処置 |
|---|---|---|
| A1 / B1 warm 費用の混算 (455 + 113 ≠ warm) | **real** | 採用。brief を訂正: warm 全体 **478.123 秒** = 列挙 455.376 + 残余 22.747 (parent-measurements-2)。113.5 は cold 残余。以後「570 秒」は使わない |
| A2 / B2 P1 の D958 読み替え | **real** | 採用。**D958 項 1 の受理条件は緩めない** (§3)。D2038 は「実装して実測する順序」を定めるだけで受理条件を撤回していない。上限超過なら land せず裁定パッケージへ |
| A3 brief I4「path 昇順最小でもよい」は非等価 | **real** | 採用。代表 external は**現行の first-seen 保存** (plan 決定性 (a): root 直下 → 部分木名昇順の順序付き merge、既存 group の `external`/`metadata` は保持し owners/aliases だけ union)。brief I4 を置換 |
| A4 brief I6 の例外・rc 説明が広い | **real** | 採用。OSError は現行の捕捉位置で計数、それ以外は `Future.result()` で再送出し `main` の既存捕捉 (OSError/RuntimeError/UnicodeError → rc=2) に委ねる。任意例外を RuntimeError へ包まない |
| A5 失敗数 test の具体性不足 | **real** | 採用。等価性 fixture に (i) 入れ子 root `(R, R/a)` で同一 file の alias 2 個・同一 deny dir の失敗 2 回、(ii) 同一 worker 内で `onerror` 2 回以上、(iii) root scandir が entry を返した後の失敗 (`os.scandir` の monkeypatch で再現) を入れる。新しい検査制度は作らない (既定 test の witness 追加のみ) |
| A6 M2 が等価変異になりうる | **real** | 採用。M2 は「sorted subdirectory の末尾 1 個を skip」のまま、fixture の最後の有効部分木に固有候補を置いて単一の赤理由にする |
| A7 / B4 login node 計測は runbook §7 と不整合 | **一部 refuted** | runbook §7 の「性能測定 = ベンチ・calibration・noise floor・floor/oracle 本走」は CC 計測の列挙であり、監査は掃除が login で叩く運用 tool で、D958 自身の受理値も「1 login node・1 repo・1 時点」で取られている (D958 理由 1)。**login 測定を主系列 (D958 の形)** とし、計算ノード (generic dispatch) の 1 走目を **補助系列 (cold 相当・別 node)** として old / new(16) / new(1) を各 1 走試みる。混雑で取れなければ持ち越し (T-2660 (b)) |
| A8 / B8 「単一 thread 3 走」は GNU find 1 + bfs 2 | **real (nit)** | 採用。記録の文言を訂正する。倍率 3.8〜4.4 は C 実装の探索値であり Python の受理根拠に使わない |
| A9 / B12 既定 16 の根拠 | **unknown** | 16 を試す値として採り、最適・安全の一般化は主張しない。実測で 16 が 1 より遅ければ不採用 (§4) |
| B3 prototype 先行の地点が無い | **real** | 採用。**prototype = 実装直後の production 経路 1 走** (段 5 patch 適用 → 焦点走緑 → fixture で new(16) warm-up + 1 走を old と比較)。列挙倍率 < 1.2 なら段 6 へ進まず不採用で停止 (§4)。別 script の prototype は F29 (production 経路でない模擬) の再発なので作らない |
| B5 倍率の定義 | **real** | 採用。列挙倍率 = old の「repo 外走査の列挙 elapsed」÷ new(16) の同値、全体倍率 = old の最終 `elapsed_seconds` ÷ new(16) の同値。D958 判定は new(16) の全体 `elapsed_seconds` の max |
| B6 固定 ref だけでは入力同一を保証しない | **real** | 採用。fixture repo (探索根の外、他 session が触らない) を入力にし、各走の進捗行から `commits= / finding_commits= / candidates= / candidate_oids= / external_files= / external_matches=` を写して同一性を確かめる。探索根は他 wave の job dir 生成で変わりうるので、報告行の差は新規 path の mtime で帰属し、帰属できない差は等価性未確認として止める。遅い走を外乱として捨てない |
| B7 「最大 job dir 59,723 file」は被覆表の値 | **real** | 採用。brief から削除。skew の許容は「直下 job dir 1,188 本に対し worker 16 本」の粒度だけを根拠にする |
| B9 別環境でも壊れない、は保証できない | **real** | 採用。thread 生成失敗は `RuntimeError` → rc=2 (実行不能) になりうることを記録に書く。既定 16 の安全は観測環境に限定 |
| B13 例外・SIGINT 後の待機は無上限 | **real (nit)** | 記録のみ。`with` を抜ける前に未開始 future を cancel |
| B14 import の起動費用 | **unknown (nit)** | `concurrent.futures` は module 先頭で import してよい。外側 wall と内部 elapsed を分けて記録 |
| B16 env は rescue の子 process に伝わらない | **real (nit)** | 本 wave では変更しない (T-2663 の射程)。記録に「計測用 override は直接起動にだけ効く」と書く |
| A10〜A12、B10、B11、B15、B17 | **refuted** | 修正不要 (plan が既に対処) |

## 2. plan v2 (実装仕様、plan §2〜§7 を基本に上の採否を反映)

- 並列単位: 主 thread が `os.walk(root, topdown=True, onerror=..., followlinks=False)` の最初の iteration だけを処理し (root 直下 file の候補照合を含む)、sorted `dirnames` の各 entry を `os.path.islink` で判定して非 symlink だけを worker へ渡す。worker は同じ `os.walk` を部分木に走らせ、iteration 処理は逐次版と共有する 1 つの helper を呼ぶ。root 検査 (lstat・permission) は主 thread に残し子へ再適用しない。root の最初の iteration が `onerror` で終わったら現行どおり候補 0・failures 加算・`scan_performed=True`。
- 決定性: 結果は root 直下 → 部分木名昇順に merge し、`(OID, dev, ino)` group の `external` (path + initial_stat) と `metadata` は first-seen を保持、owners / aliases は union。`x not in list` 型の重複除去を持ち込まない。
- 計数と heartbeat: `_ProgressRateLimiter` は主 thread だけが生成・pulse。worker はローカル計数 (directories / files / failures) を持ち、lock 付き slot で累積値を公開、主 thread は待機中に合算して pulse、完了時に最終値へ置換。待機は `concurrent.futures.wait(pending, timeout=POLL_CEILING_SECONDS, return_when=FIRST_COMPLETED)` で、間隔 0 でも待ち時間を 0 にしない (F627)。`test_flat_offrepo_filename_loop_emits_heartbeat` の期待 `["repo 外走査 heartbeat directories=1 files=1"]` と monotonic 3 値は、部分木が無いとき pool を作らず主 thread の 2 pulse だけになることで維持する。
- 並列度: `OFFREPO_SCAN_WORKERS = 16` (module 定数、正整数)、env `IZANAGI_AUDIT_SCAN_WORKERS` (正整数のみ、空・非整数・0・負は `RuntimeError` → rc=2)。列挙実行時に読む。順序は (1) candidates 空なら `({}, 0, False)` で filesystem にも pool にも触れない、(2) workers 解決、(3) index、(4) root 検査・列挙。**workers=1 は pool を作らず root 全体を従来順に walk** (候補判定 helper は共有)。CLI flag は足さない。
- 例外・資源: worker の OSError は現行位置で計数、それ以外は再送出。executor は `with`、例外時は未開始 future を cancel してから再送出。
- test: `test_initial_patch_contains_no_parallel_execution` (T:1183〜1186) を**同じ位置**で `test_parallel_offrepo_scan_preserves_enumeration` に置換 (静的文字列 assert は置かない)。新設 node は plan の 10 件 + A5 の witness を既存予定 test に含める: fixture は root 直下 file、複数部分木 (workers=4 に対し 5 個以上の有効部分木)、入れ子 dir、部分木を跨ぐ hardlink、異 basename 同 inode、symlink dir (root 直下と部分木内部、先に固有候補)、symlink file、同名別 size、同名同 size 別 mode、最後の有効部分木の固有候補 (M2 用)、入れ子 root `(R, R/a)`、読めない子 dir (root 実行時 skip)。複数 thread の証拠は production worker を wrap して timeout 付き Barrier + `threading.get_ident()` 集合 ≥ 2 (executor は置換しない、wrap は保存した本物を呼ぶ)。report test は git 入力・cat-file・landed 参照を stub、列挙・実 file 比較・抑止集約は実コード、抑止あり / 未参照 copy あり / 残存 finding あり / scan failure ありの独立期待値。env を clear する autouse fixture を T:27 付近に置く。parametrize id は ASCII のみ。
- 既存 test の期待値変更は T:1183 の置換 1 件だけ。他は不変 (plan §8 の表)。
- 触らない: `_has_bounded_path_reference` / `_bounded_path_reference_matches` (T-2662)、alias 配布 (T-2664)、`tools/check_branch_rescue.py` (T-2663)、cleanup command、docs。

## 3. 受理と停止の条件 (結果を見る前に固定、規律 3)

- **等価性 (必須):** (a) 新設 test 緑 + 既存 test 期待値不変、(b) fixture repo × 実根で old / new(1) / new(16) の報告行 (進捗行・`elapsed_seconds=` 行・所要上限超過行を除く) が逐語一致、進捗行の件数 (`commits= finding_commits= candidates= candidate_oids= external_files= external_matches= suppressions= findings=`) が一致。不一致は探索根の churn に帰属できるときだけ記録して再走、帰属できなければ停止。
- **性能 (D958 項 1、緩めない):** new(16) の warm-up 1 走を捨てた独立 3 走 (max/min > 1.5 なら 3 走追加) の全体 `elapsed_seconds` の **max ≤ 300 秒** を、fixture repo (走査を強制) と現行 main の実 repo (findings 0 件、走査省略) の両方で満たすこと。fixture で超過なら land せず、実測値を添えて D958 と D2038 の関係を裁定パッケージへ返す。
- **prototype 判定 (B3):** 実装直後の fixture 1 走で列挙倍率 (old ÷ new(16)) が 1.2 未満なら「Python thread では出ない」として段 6 へ進まず不採用で停止 (既定を 1 に戻して land する案は採らない、plan §12)。
- 同時刻対照: old (変更前 commit の tool を job dir から `--repo <fixture>` で起動) と new(1) を new(16) の走の間に挿入する。順序・時刻・load・同時に走った worktree add / land / 受入を記録する。cold は主張しない。

## 4. 変異 matrix の事前登録 (DW-M01、位置は実装後に author の報告で確定、probe 走で観測 node を集めてから本走)

| ID | category | 変異 | 期待 |
|---|---|---|---|
| M0 | positive (等価対照) | `_enumerate_offrepo_candidates` の docstring を意味不変で言い換え | SURVIVED |
| M1 | negative | worker の walk failures を主 thread へ合算しない | KILLED (`test_parallel_offrepo_scan_preserves_failure_counts`) |
| M2 | negative | sorted subdirectory の末尾 1 個を worker に渡さない | KILLED (`test_parallel_offrepo_scan_preserves_enumeration`、最後の有効部分木の固有候補欠落) |
| M3 | negative | root 直下 filename の候補照合を skip | KILLED (enumeration の root 直下固有候補、+ T:1035 が落ちれば併記) |
| M4 | negative | worker walk を `followlinks=True` | KILLED (部分木内部 symlink 先の固有候補が増える) |
| M5 | negative | merge で既存 group の代表 external を後着で上書き | KILLED (`test_parallel_offrepo_scan_preserves_first_seen`、内部代表を直接検査) |
| M6 | negative | worker 例外を捕捉して空結果へ置換 | KILLED (`test_parallel_offrepo_scan_propagates_worker_exception`) |
| M7 | negative | worker から progress callback を直接呼ぶ | KILLED (`test_parallel_offrepo_scan_heartbeat_runs_on_caller`) |
| M8 | negative | `OFFREPO_SCAN_WORKERS` 16 → 0 | KILLED (`test_offrepo_scan_worker_configuration` の既定値 case) |
| M9 | negative | candidates 空の早期 return より前に executor を生成 | KILLED (`test_empty_offrepo_candidates_touch_neither_filesystem_nor_pool`) |

「`filenames` に `dirnames` を混ぜる」変異は S_ISREG で mask されるため登録しない (plan)。期待 node は probe 走の観測で確定し、完全一致だけを KILLED とする。

## 5. brief の訂正 (記録用)

- I4 → 「代表 external は現行の first-seen を保存する (順序付き merge)」。I6 → 「OSError は現行位置で計数、それ以外は再送出して main の既存捕捉に委ねる」。
- 研究前進の数値 → warm 全体 478.123 秒 (列挙 455.376 + 残余 22.747)、cold 残余 113.5 秒。「最大 job dir 59,723 file」は削除。「単一 thread 3 走」→「GNU find 1 走 + bfs 2 走」。
- P1 → 撤回 (D958 の受理条件をそのまま適用)。P5 → 補助系列 (§3)。
- 実装しない: なし (4→5 へ進む)。
