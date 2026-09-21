# T-2803 着地後の実 land 連鎖における全史 provenance 監査の受領証の再利用可能性 (事後診断 + 計算ノード対照、2026-09-21)

依頼 (逐語 `verbatim/origin.md`): [T-2803] (entry 1769、D2192) が「未測定」と残した実 land の連鎖 (他 binding・partition・混雑時・計算ノード) での
全史 provenance 監査 (`tools/check_ai_provenance.py`、受領証 = D2045) の warm / cold を、T-2803 着地後に land した wave の受領証 (共有 store) と
land / 受入の log から実測し、cold の件ごとに原因を 4 種 (checker sha 変更 / `.gitattributes` / attributes 以外の binding 失効 / partition 跨ぎ) で分類し、
残る cold の主因に対する局所修正の候補 (entry 1769 §11 の 3 候補はその主因に当たる場合だけ) を効果見積り付きで裁定パッケージにする。
監査の判定・受領証 schema・D2045 / D2192 の束縛は変えない。実装 0 行 (repo 内の実装面の差分なし)。

## 1. 結論 (要約)

- 本書の「着地」は T-2803 の land (tip `65966f4d8…` を監査して ff、main の reflog で 2026-09-21 00:10:46、fold 後の main_after = `5733c0f08…`、land log の終了 00:12:00)。
  母集団 M = 受領証の mtime ≥ 00:12:00、参考 R = 2026-09-20 21:00:00 〜 00:12:00。入力は P-4 実行前の凍結目録 (08:31、501 件)。
- **M の 50 件のうち 49 件は、同じ partition に候補があり、現行 checker の関数による replay (`_receipt_prefix` と delta の raw correction 検査) が成功した。**
  残る 1 件は T-2803 入りの main を取り込む前の wave 枝で打たれた旧 checker (`7c02fb2d…`) の監査で、probe の規約で参考区分 (旧形 attributes fingerprint の候補集合変化) に分類された。
  M に依頼の 4 種の主分類に入る行は無い。これは残存受領証からの**再利用可能性の事後推定**で、当時の再利用の実績ではない (§7)。
- **凍結目録の M + R で、現行 checker (`e69764c1…`) の受領証に同 partition の祖先候補が無かったのは T-2803 自身の着地処理の 2 件**
  (受入 claim 前 23:45、`c508d1de…`、主分類 = checker sha 変更 / land 00:08、`4608b761…`、主分類 = partition 跨ぎ)。どちらも R に入る。P-4 の初回 (§6.3) は別枠。
- log 点 → 受領証 mtime の間隔 (監査単独の wall ではない) は、M の受入 claim 前 17 件で 17〜26 秒 (中央値 18)、land 7 件で 27〜96 秒 (中央値 40)。
- **計算ノード (`--force-dispatch`、2 request 直列、dispatch 受領証の hostname は両方 bnode019)**: 継承 env が `LC_CTYPE=C.UTF-8` だけの新しい partition `50fadce4…` に落ちた
  (受入・land の区画とは別)。1 回目 = 同 partition に祖先候補なし、checker 子 35.1 秒 / login 側 57.85 秒。2 回目 (同 tip) = 同 file を同 bytes で上書き、checker 子 5.2 秒 / login 側 27.31 秒。
- **裁定パッケージ第 1 案 = 局所修正を提案しない。** 観測範囲で §11 の 3 候補を支持する cold 原因は確認できなかった。区画の統一は scope 外の候補として条件付きモデルだけを示す (§8)。

## 2. 起点と段 1 の前提実測

- 起点 local main `5efd69367b641b9bfbd6fb426478f66ae5762783` (fresh worktree `dw-provenance-cold-diag`、開始 gate rc 0、login pegasus02)。
- 親が段 1 で job tmp に書いた read-only script 3 本の出力 (`verbatim/parent-prelim/`) は仮説として扱い、以下の数値には使わない。段 3 相談が 5 点の欠陥を名指しした
  (bindings 一致 + 祖先を「warm」と呼んだ、land 側の祖先候補なしの tip の取り違え、母集団を現行 checker に限った、log と受領証の突合が区間・partition で絞れず
  1 秒で拒否された land に 206 秒を結んだ、partition の用途と「dispatch 0 件」を証明なしに書いた)。確定値は Codex author の probe (§4) で再導出した。

## 3. 段構成

段 1 brief (`verbatim/s1-brief.md`) → 段 3 相談 1 本 (`verbatim/s3-consult-A.md`、must-fix 9 / should 2 / nit 1) → 段 4 裁定 (`verbatim/s4-ruling.md`、全件 real・採用、login の監査 3 走を削除し
計算ノード 2 request 直列へ) → 段 5 author 4 巡 (1 巡目 probe 4 本、2 巡目 git 許可一覧の追加、3 巡目 checker 系統表の訂正、4 巡目 main の checker 履歴 probe、各巡の prompt と報告は `verbatim/prompt-author*.md` / `verbatim/s5-author*.md`)
→ 親の実走 → 段 6 review 1 本 (`verbatim/s6-review-A.md`、NO-GO、照合 81 件 / 一致 80 件) → 裁定 (`verbatim/s6-ruling.md`) → 本書の改訂 → 焦点再レビュー。
Codex は全段 gpt-6-astra / medium。段 2 は省いた。時刻は各 file の mtime と launcher の出力 (job dir) にあり、本書では結論に要るものだけを書く。

## 4. 測定の道具と本番経路

probe (Codex author 作、repo 外 job dir で親が実行、逐語は `verbatim/probe/*.txt`):

| # | probe | 何を出すか | 生出力 |
|---|---|---|---|
| P-1 | `receipt_ledger.py` | 共有 store `<common git-dir>/provenance-audit-receipts/` の全受領証の目録 (bytes・sha256・mtime・bindings 全文) と前後差分 | `measurements/p1-ledger-{before,after1,after2}.stdout.txt` (目録本体は元 bytes 込みで job dir) |
| P-2 | `receipt_reuse_replay.py` | 各受領証 B の再利用候補と replay 結果・分類 (§5) | `measurements/p2-replay.{stdout.txt,jsonl}` |
| P-3 | `audit_attempt_ledger.py` | 受入・land の attempt と受領証の突合 (§6.2) | `measurements/p3-attempts.{stdout.txt,jsonl}` |
| P-4 | `launch-force-dispatch.sh` | `/usr/bin/time -v python3 tools/check_ai_provenance.py --force-dispatch` を 1 request (env を足さない) | `measurements/force-dispatch-{1,2}.{out,err,time,meta}.txt`、dispatch 受領証 `force-dispatch-{1,2}.dispatch-receipt.json`、`force-dispatch-mtimes.txt` |
| P-5 | `main_checker_history.py` | `refs/heads/main` の reflog の各 entry の checker sha256 と遷移、指定 commit の checker の版と main 上での出現 | `measurements/main-checker-history.stdout.txt` |

P-2 のうち**現行実装そのもの**を使う部分: 選択集合 (`_commit_range(None, head=B.tip)`)、ancestry (`_build_ancestry([B.tip], authoritative=True, head=B.tip)`)、候補の並び (選択集合のうち候補 tip の祖先でない
commit 数と filename の昇順 = `_audit_history` の lookup)、`_receipt_prefix`、delta の `_batch_commit_messages` と `RAW_AI_AGENT_CORRECTION`、registry (`_known_violation_registry` と manifest digest の一致)。
**近似・非同値** (author 報告 `verbatim/s5-author-self-run-summary.md` の 7 項と段 6 所見):
(1) 当時の lookup 集合の代わりに、凍結時に残存し mtime_ns が B より小さい同 partition の受領証を候補にする (mtime は秒単位で、同じ秒の受領証は互いに候補にならない)。
(2) `_read_audit_receipt` の directory 0700 / file 0600 / 非 symlink 等の検査は再現せず、保存した元 bytes から replay する。
(3) 旧 checker の実行コードは復元せず、旧 checker の受領証も現行の関数で検証する。
(4) 同 partition に候補が無いときの他 partition の比較相手は (距離, filename, 新しい mtime, partition 名) で選んだ代表 1 件で、差分は因果の単独同定ではない。
(5) P-3 の時刻だけの land log は file mtime の日付を当て、開始が mtime より後なら前日、終了が開始より前なら翌日へ補正する (複数日に跨る log は復元不能)。
(6) P-3 の post-claim merge 後監査は、claim 前と同 partition・同区間・別 tip の受領証からの推定で、並走する他 wave の監査を含みうる。claim 前が未対応なら推定しない。
(7) P-3 の同名 `land-<n>.json` は loop の再実行で上書きされうるので、log の status を優先する。

checker を起動する経路と partition (partition = checker sha256 + schema + `git config --list` 全文 + 継承 `GIT_*` / `LC_*` / `LANG` の digest、D2045):

| 経路 | checker に渡る env (実装) | 観測した partition (現行 checker) |
|---|---|---|
| 受入 claim 前 / post-claim merge 後 (`tools/dev_wave_wait.py`) | 親 env から `_GIT_ENV_KEYS` (discovery 系) を除く、`_GIT_ENV_OVERRIDES` は適用しない | `c508d1de…` (継承 `GIT_EDITOR` / `LANG`、config に ~/.gitconfig 由来の lfs 4 行) |
| land (`tools/dev_wave_land.py` の `_git_env()`) | 全 `GIT_*` を除き `GIT_CONFIG_GLOBAL=/dev/null` 等と `LC_ALL=C` を上書き | `4608b761…` |
| 対話 session の直打ち | session の env のまま | session の env による (§6.1 の M の参考区分 1 件は受入と同形の継承 env の旧 checker 区画 `53e9a718…`) |
| 計算ノード dispatch (login headroom 不足 + queue 可、または `--force-dispatch`) | `dispatch_compute.py --task provenance` (env_mode=inherit = 計算ノードの job 環境) | `50fadce4…` (P-4 で実測、継承 `LC_CTYPE=C.UTF-8` のみ) |

partition の用途は、log と結べた走 (§6.2 の突合行、§6.3 の P-4) についてだけ確定している。

## 5. 分類 (P-2 の `verdict` / `cause`、実装は `verbatim/probe/receipt_reuse_replay.py.txt`)

**主分類は probe の比較規約による。比較相手 (代表候補) との差は単独原因の証明ではない。** 複合差・replay 失敗・未判定は別に数える。

| verdict | 条件 | cause (依頼の 4 種への写像) |
|---|---|---|
| 候補あり (replay 成功) | 同 partition の候補のうち bindings が B と一致するものを並び順に replay し、prefix 成功かつ delta に raw correction なし | — (再利用可能、事後推定) |
| 候補あり (replay 失敗) | 一致候補の prefix が全部失敗 / delta に raw correction | 失敗条件名 (4 種の外) |
| 候補あり (未判定) | registry loader 失敗 / registry 世代差 / delta message 読取失敗 | 未判定 |
| 候補あり (bindings 不一致) | 同 partition の候補はあるが bindings 一致が無い。最近接候補との差分で: attributes 差 → 旧形 checker なら比較区間 (候補 tip..B tip) の root `.gitattributes` 変更 commit の有無で「`.gitattributes` 変更」/「参考区分: 旧形 attributes fingerprint の候補集合変化」、新形・中間形なら「attributes 差 (原因未特定)」、系統不明なら「attributes 差 (系統不明)」; attributes 以外の項目 → 「attributes 以外の binding 失効」; 複数あれば連結 | 左の各 cause |
| 候補なし | 同 partition に祖先候補なし、他 partition に祖先候補あり: 代表候補と `environment.checker` が違えば「checker sha 変更」、同じなら「partition 跨ぎ」 | checker sha 変更 / partition 跨ぎ |
| 候補なし | どの partition にも祖先候補なし | 祖先受領証なし (初回)、partition が 64 件なら prune の可能性 |
| 未判定 | replay の入力・実行エラー | 未判定 |

checker の系統 (P-5 の出力。`d2192_lines` = D2192 の候補列挙 `diff-merges=first-parent` を含む行数): 旧形 = `5cb709cb…` (33c608726) / `7c02fb2d…` (55068f84e) / `89a60a88…` (aa81e3c64) /
`65476daf…` (62ed683ab)、中間形 = `1acbb496…` (4c532aa0b、absent を digest に含めない初版)、新形 = `2b72e1d5…` (00d781372) / `e69764c1…` (65966f4d8)。probe の定数 `CHECKER_LINEAGES` はこの 7 対応と一致する。
親は 1 巡目 prompt で T-2804 枝の 2 版 (`89a60a88…` / `65476daf…`) を新形に入れており、R の 3 件が「新形、原因未特定」に落ちていた (3 巡目で訂正)。

## 6. 実測

### 6.1 P-2 再利用候補の replay 分類 (入力 = 凍結目録 08:31、501 件 / 19 partition、読取エラー 0)

`measurements/p2-replay.stdout.txt` の REUSE SUMMARY の逐語:

| population | verdict | cause | 件数 |
|---|---|---|---|
| M | 候補あり (replay 成功) | — | 49 |
| M | 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 1 |
| R | 候補あり (replay 成功) | — | 4 |
| R | 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 25 |
| R | 候補なし | checker sha 変更 | 6 |
| R | 候補なし | partition 跨ぎ | 2 |

- M の partition 内訳: `c508d1de…` replay 成功 38、`4608b761…` replay 成功 11、`53e9a718…` 参考区分 1。`replay` の `fail:` と「未判定」の行は stdout に無い
  (現行 manifest digest `6ad7b460d863` の値は author 2 巡目の自己実走の報告 `verbatim/s5-author-2.md` による)。
- M の参考区分 1 件 = 04:11:50、tip a6ac2c54c (T-2797 wave の段 7 記録 commit、65966f4d8 を含まない枝)、checker `7c02fb2d…`、比較相手 `53e9a718…/482f19b88dbb`。
  同 wave のその後の受入 claim 前監査 (main 取り込み後の tip e4f4c900c / 088bbdec7 / cf1c90e1f) と land (05:21、cf1c90e1f) の受領証は M の replay 成功に入る。
- R の「候補なし」8 件: checker sha 変更 6 = 4c532aa0b (21:46、`1acbb496…`)、aa81e3c64 (21:52、`89a60a88…`)、62ed683ab (22:07、`65476daf…`)、4c9c8d480 (22:12、`65476daf…`、継承 `LC_CTYPE` のみ)、
  47fbfd58c (23:03、`2b72e1d5…`)、65966f4d8 (23:45、`e69764c1…`、受入)。partition 跨ぎ 2 = 1e5fb5705 (23:27、`65476daf…`、T-2804 の land)、65966f4d8 (00:08、`e69764c1…`、T-2803 の land)。
  P-5 で main の reflog の残存 entry に一度も現れない checker の版は `1acbb496…` / `89a60a88…` / `2b72e1d5…` (残存 entry の連鎖に 09-14 以降の断絶は検出していないが、期間の内外での expire・削除を排除できないので「main が一度も指さなかった」とは断定しない)。
- R の参考区分 25 件 + M の 1 件 = 26 件は、すべて bindings 差が `attributes` の digest 差だけで、比較区間の root `.gitattributes` 変更 commit は 26 区間とも無かった (`gitattributes_commits: []`)。
  digest 差の内訳 (候補集合の変化か、errno・info / global / system attributes・working / index の差か) は復元していない。

### 6.2 P-3 監査 attempt と受領証の突合 (「log 点 → 受領証 mtime の間隔」であり監査単独の wall ではない)

突合規則: (受領証 tip = attempt の監査 HEAD) ∧ (mtime ∈ [開始 − 2 秒, 終了 + 2 秒])、全 partition から。受入の開始は `acceptance-<A>.started.txt` (直後に claim 前監査)、
land の開始は launcher の `land:` 行 (ISO) または `it=N land landing=` 行 (時刻のみ、§4 (5))。`measurements/p3-attempts.stdout.txt` の ATTEMPT SUMMARY (attempt 開始 ≥ 00:12:00) の逐語:

| stage | attempt 行 | 間隔の件数 | 最小 | 中央値 | 最大 | 未対応 |
|---|---|---|---|---|---|---|
| accept-preclaim | 17 | 17 | 17 秒 | 18 秒 | 26 秒 | 0 |
| land | 8 | 7 | 27 秒 | 40 秒 | 96 秒 | 1 |
| accept-postmerge (推定) | 21 | 21 | 38 秒 | 425 秒 | 1323 秒 | 0 |
| unsupported | 10 | 0 | — | — | — | 10 |

- land の突合 7 行 (wave、開始、tip、間隔): t2344-closure-stage 00:15:49 c383bac07 81 秒 / wall-decomp 02:52:01 4566c64b4 51 秒 / t2814-cleanup-command 03:16:12 8621eb641 31 秒 /
  t2810-g1-launch-validation 03:41:32 ab0374ccb 27 秒 / branch-residue-cleanup 04:29:15 98e946f9d 27 秒 / t2797-b5-contrast 05:21:30 cf1c90e1f 40 秒 / dwm08-selfrun-probe 08:22:02 98b81b5df 96 秒。
  7 件とも partition `4608b761…` で、対応する受領証は §6.1 の M の replay 成功に入る。未対応 1 = t2797 04:54:42 (rc=23 で 1 秒で拒否、監査を起動していない)。
- 受入 claim 前 17 行はすべて partition `c508d1de…` で、対応する受領証は M の replay 成功に入る。load1 (受入 gate 時点の観測) は 13 行で 1.44〜4.93、4 行は gate 行が無く欠測。
- land の間隔は lock 外の preflight・turn・lock 待ちを含む。mtime は publish の `os.replace` 前 (checker 終了前)。
- `accept-postmerge (推定)` は §4 (6) の推定で、実際の post-claim merge 後監査の件数・時間とは読まない。
- `unsupported` 10 本は、file mtime が対象期間内で開始行を解析できなかった log file である。監査 attempt 数・受領証の有無は確定していない。
- 参考 (本 wave 自身の走、凍結目録の母集団の外): 記録 commit `fdf2104c8` の直後に親が login で走らせた全史監査は rc 0 / 12,262 件 / wall 25 秒 (09:09:55〜09:10:20、`date` の実測、partition `c508d1de…`)。
  同 partition に祖先候補がある側の値で、cold の対照は無い。
- 参考 (着地の走、R): T-2803 自身の受入 claim 前 23:45:07 → 23:45:43 = 36 秒 (同 partition の祖先候補なし、load1 3.53)、land 00:07:22 → 00:08:30 = 68 秒 (同、前処理込み)。
  それぞれ 1 本で、同条件の warm 対照は無い (login の cold / warm の同条件対は未測定)。

### 6.3 P-4 計算ノード `--force-dispatch` 2 request 直列 (dispatch 先の partition と cold / warm の対照。480 秒関門は再現しない)

| 走 | request | node | rc | 監査件数 | checker 子 | login 側 wall | nqsv 作成→開始 | request.json→compute-visible.json | receipt `queue_wait_s` | 受領証 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 14603.nqsv | bnode019 | 0 | 12,261、新規違反なし | 35.14 秒 | 57.85 秒 | 9 秒 | 10 秒 | 5.23 秒 | 新 partition `50fadce4…` に tip 5efd69367 を追加 |
| 2 | 14604.nqsv | bnode019 | 0 | 12,261、新規違反なし | 5.24 秒 | 27.31 秒 | 7 秒 | 8 秒 | 5.23 秒 | 同 file を同 bytes (sha256 `97f23f77…`) で上書き |

出所: node と `queue_wait_s` = dispatch 受領証 (`force-dispatch-{1,2}.dispatch-receipt.json` の `result.hostname` (`f49_compute_marker.hostname` とも一致) / `queue_wait_s`)、checker 子 = `force-dispatch-{1,2}.err.txt` の job trace
`direct-child-wait-start` → `direct-child-wait-complete` の `time_ns` 差、login 側 wall = `force-dispatch-{1,2}.time.txt` の Elapsed、nqsv 作成→開始 = `.err.txt` の Created / Started Request Time、
request.json→compute-visible.json = `force-dispatch-mtimes.txt`、受領証 = `p1-ledger-after{1,2}.stdout.txt` の DIFF。`.meta.txt` の hostname は launcher を動かした login (`pegasus02`)。

- 1 回目の直前に同 partition の受領証は無く (P-1 基準目録)、他 partition には tip 5efd69367 の祖先の受領証がある → §5 の規約で partition 跨ぎ。2 回目は checker 子の所要が約 1/7 に下がり
  受領証が同 bytes で上書きされたことから再利用 (warm) と読む (受領証の再利用は公開出力に現れない)。
- 2 回とも同じ node。別 node に dispatch された場合に同じ partition になるか (計算ノードの job 環境が node に依らないか) は確かめていない。
- 旧 checker 期には継承 env が `LC_CTYPE=C.UTF-8` だけの partition が 3 つある (`f093170f…` 64 件 = `5cb709cb…`、`8c683754…` 11 件 = `7c02fb2d…`、`18d19753…` 1 件 = `65476daf…`)。P-4 の dispatch 先と
  継承 env の形は一致するが、計算ノードへの dispatch だったとは証明していない。凍結目録 (P-4 の前) の現行 checker の受領証に、この形のものは無い。

## 7. 限界と言わないこと

- 「replay 成功」は受領証と現在の repo・現行 checker の関数による**事後推定**であり、当時の再利用の実績ではない。並走 (lookup 後・publish 前の候補)、prune (partition あたり 64 件)、
  同 tip の上書き publish (tip ごとに 1 file、mtime だけが新しくなる)、当時の実行時失敗は事後に閉じない。§4 の近似 (1)〜(7) を含む。
- 分類は §5 の規約による。参考区分 26 件は digest 差の内訳を復元しておらず、errno 等を個別に排除していない。
- 間隔は log 点 → 受領証 mtime で、開始前の処理 (land の preflight / lock 待ち、受入の投入) を含み publish 後を含まない。login の監査単独の wall (cold / warm の同条件対) は測っていない。
- 期間は 2026-09-21 00:12〜08:31 (凍結目録) の 1 晩。load1 は受入 gate 時点の観測 (13 行、1.44〜4.93) で、全監査中の負荷ではない。
  cold 率・時間短縮率・混雑時の 480 秒保証・「他 binding の失効は起きない」は言わない。
- 現行 checker の自然な login 混雑時 (bounded local の cold、headroom 不足による dispatch の発火) は未観測。P-4 は `--force-dispatch` で admission と queue 可否の判定を迂回しており、land の外側 480 秒 deadline も
  付いていない。混雑時の login cold を推すなら「cold 実測 C 秒 × 仮定倍率 k」の感度試算であり、旧資料の「所要は実行場所で 7 倍振れる」(D1996) は仮定であって予測でも上限でもない。
- P-4 の 2 走は同じ node・同じ tip。
- 受領証が残っていない走 (publish されなかった失敗走、prune 済み) は数えていない。`unsupported` の log file 10 本の中身は数えていない。
- 母集団の限定は §1、区画統一の未検証条件は §8 に従う。

## 8. 裁定パッケージ (起票しない、採否はユーザー)

**第 1 案 (推奨): 局所修正を提案しない。** M に依頼の 4 種の主分類に入る行は無く、凍結目録の M + R で現行 checker の同 partition 祖先候補なしは T-2803 自身の着地処理 2 件だった。
§11 の 3 候補の該当性:

| 候補 | 何を減らすか | 観測との対応 | 判定 |
|---|---|---|---|
| 候補列挙の 1 走内 memo 化 (lookup と publish で 2 回 → 1 回) | cold / warm を問わない毎走の候補列挙 1 回分 ([T-2803 insight](../../2026-09-20/t2803-receipt-attributes-fingerprint/README.md) §8.3 の login 実測で `log --no-walk` 1.73〜3.48 秒 + `rev-list --merges` 0.52〜0.65 秒。本 wave では再測していない) | cold の原因ではない (cold を warm に変えない) | 主因に当たらない |
| `attr.tree` / `--attr-source` / bare / `GIT_ATTR_*` の束縛 | 束縛外の属性入力 (安全側の改善) | 新形・中間形 checker の attributes 差は凍結目録で 0 件 | 主因に当たらない |
| errno の正規化 | unreadable 候補の errno の揺れによる不要な失効 | 新形・中間形 checker の attributes 差は 0 件。旧形の 26 件は内訳未復元 (§6.1) | 観測範囲では支持なし |

**参考 (scope 外の候補): checker 起動 env の統一 (受入・land・dispatch の区画を 1 つにする)。** D2045 が明示的に採った「区画が分かれるため受入と land は受領証を共有しない」を改める
変更で、本 wave では実装しない。効果の条件付きモデル:

- 回避しうるのは、main の checker が変わった後の各区画の初回のうち、統一後に他の区画の祖先受領証と全 bindings が一致し、lookup の時点で利用可能だったものだけ。
  観測例: T-2803 着地時の land (00:08) は partition 跨ぎで、代表候補との差は config と継承 env の複合差だった (P-2)。P-4 の 1 回目も別 partition の初回だが、代表候補との全 bindings 差分は本書の保存資料では
  未確認である (P-4 の受領証は P-2 の入力である凍結目録より後)。いずれも統一後に全 bindings が一致するか・lookup の時点で利用可能だったかは未検証で、救済可能件数は確定しない。
- 救済 1 回あたりの節約 = 同条件の cold − warm の checker 単独時間。計算ノードの実測対は 35.14 − 5.24 = 29.9 秒 (P-4、同 node・同 tip)。login の同条件対は未測定。
- 頻度: 受領証の導入が main に着いた 2026-09-16 11:08:46 (reflog、checker `5cb709cb…`) から本 wave 着手までに、main の checker は 3 回変わった (P-5: 09-20 10:30:23 → `7c02fb2d…`、
  09-20 23:29:54 → `65476daf…` (T-2804 の land)、09-21 00:10:46 → `e69764c1…` (T-2803 の land))。
- 言わないこと: 「毎 land が約 30 秒短縮」「checker 変更ごとに必ず救える」「区画を統一すれば dispatch の cold が消える」。区画の差 (`GIT_EDITOR` / `LANG` / `LC_ALL` / `GIT_CONFIG_*` と
  ~/.gitconfig 由来の config 行) はそれ自体が監査の git の挙動を変えうるため D2045 が束縛している。

## 9. 事故 (自分起因) と近接失敗

- 親が段 1 で read-only 診断 script 3 本を書いて走らせてから「実行可能 script は所在不問で Codex author」の規律を思い出した (F75 型の近接、repo には入れていない)。値は仮説に格下げした。
  段 4 後の checker 系統の確認でも親が script (`verbatim/parent-prelim/checker_lineage.sh.txt`) を書いた。本書の系統表は P-5 (Codex author) の出力に置き換えた。
- author 1 巡目 prompt の git 許可一覧に `ls-files` / `ls-tree` を入れ忘れ、初回の replay が未判定で止まった (2 巡目で許可を足して再実走)。同 prompt の checker 系統表で T-2804 枝の旧形 2 版を新形に入れており、初回の分類が誤っていた (3 巡目で訂正)。
- README 初稿は main の checker 変更を「2 回」とし (正: 3 回、T-2804 の land を見落とした)、着地後の main SHA を監査 tip と取り違え、分類ラベルを原因の実証のように書いた (段 6 must-fix 9 件、§3)。
- P-4 の 1 回目の stderr の「pending orphan hold を create-only で保存しました」は、同じ stderr の次の行で削除が記録され走は rc 0 で完了した (`force-dispatch-1.err.txt` 1〜2 行目)。投入手順としての正規性は `tools/pegasus/dispatch_compute.py` の ledger 実装が正本で、本書では確かめていない。

## 10. 再現資料 (job dir、repo 外)

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-provenance-cold-diag/` — codex prompt / 出力 / launcher (`codex/`)、probe の正本 (`probe/`、Codex author 作。unit worktree の ignored 領域から退避、sha256 は
`receipt_ledger.py` 30493c84…、`audit_attempt_ledger.py` 8813195d…、`launch-force-dispatch.sh` b3a720ae…、`receipt_reuse_replay.py` 78145ba0…、`main_checker_history.py` 3ea16b5e…)、
凍結目録本体 (`measurements/p1-ledger-*.jsonl`)、P-5 の全 entry (`measurements/main-checker-history.jsonl`)。
本 insight の写し: `verbatim/` (依頼・brief・相談・裁定・prompt・子の報告・レビュー、probe と親の前提実測 script の `.txt` 逐語)、`measurements/` (生 stdout、jsonl、dispatch 受領証)。
