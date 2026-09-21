# 段 4 裁定 — 相談 A (codex/s3-consult-A.md) の所見と plan v2

裁定時刻 2026-09-21 08:1x JST。local main は 5efd69367 のまま (段 4 直前に再確認、decisions 更新なし)。

## 所見の裁定 (real / refuted、採否)

| # | 判定 | 採否 | 裁定内容 |
|---|---|---|---|
| A1 | real | 採用 | 「warm 推定」を撤回し **「再利用候補あり (事後推定)」** と呼ぶ。probe は実装と同じ候補選択 (同 partition・tip が祖先・距離昇順・filename 昇順) を再現し、A.bindings == B.bindings → `_receipt_prefix(A, B.bindings, commits(B), B.tip, ancestry(B), registry)` → delta の raw `AI-Agent-Correction` 検査 (2634〜2646 相当) まで replay する。registry は現行 loader の内容が B.bindings.registry_manifest と一致する場合だけ使い、違えば「未判定」。並走・prune・同 tip 上書き・当時の実行時失敗は閉じない → insight に「再利用可能性の事後推定であり実績ではない」と明記。wall 間隔は補助情報。 |
| A2 | real | 採用 | land partition (`4608b761…`) の候補なし初回 = **65966f4d8** (T-2803 wave の land-3.log: 2026-09-21T00:07:22 `land:` 行 → 受領証 00:08:30、間隔 68 秒、前処理込み)。c383bac07 (00:17:10) は候補あり。「land 初回 cold 81 秒」「30〜55 秒削減」は撤回。 |
| A3 | real | 採用 | 母集団 = **T-2803 着地 (65966f4d8 が local main へ land 完了、2026-09-21T00:12:00、main_after 5733c0f08) 後に publish された全受領証** (checker 旧・新を問わない) + 参考として着地の走 (T-2803 wave 自身の受入 23:45 / land 00:08) と着地前の旧 checker 期 (09-20 21:00〜、比較行と限界にだけ使う)。分類は依頼 4 種 (checker sha 変更 / `.gitattributes` 変更 / attributes 以外の binding 失効 / partition 跨ぎ) を主分類にし、**比較相手・差分全項目・複合差・判定不能を別列で残す**。「旧形 attributes fingerprint の候補集合変化 (新 directory 導入)」は 4 種の外の参考区分とし、期間中の root `.gitattributes` の変更 commit の有無 (`git log --format=%H -- .gitattributes`、最終 47a457e43 2026-08-23) で `.gitattributes` 変更と区別する。 |
| A4 | real | 採用 | 突合の鍵 = (wave, stage, 監査時 HEAD, partition, 開始〜終了区間)。計測点は launcher script を読んで確定した: **受入 = `acceptance-<A>.started.txt` (ISO) 直後に `dev_wave_wait.py acceptance` が claim 前監査 (HEAD = `acceptance-<A>.tip-before.txt`) を走らせる** (親 launcher `run-acceptance-gated.sh` 66〜100: attempt 行 → launcher 自身の pre-merge → `merged:` 行 → tip-before → started → 投入。`merged:` は監査でない)。post-claim merge 後監査は launcher が pre-merge 済みなら behind=0 で起きない。**land = 各 wave の launcher の `land:` 行 (`land-go.sh` 型、ISO) または `it=N land landing=` 行 (`run-land-loop.sh` 型、HH:MM:SS のみ → file mtime と日跨ぎ規則を明記)** → `dev_wave_land.py` 起動 → lock 外で preflight → turn → lock 待ち → locked preflight → 監査。終了 = `land rc=` 行 / `rc=N status=` 行。区間外・別 partition・上書きは「未対応」。表示は「log 点 → 対応候補の mtime 間隔」で、監査単独 wall と分ける (mtime は publish の `os.replace` 前 = checker 終了前)。 |
| A5 | real | 採用 | partition の用途は log で結べた走に限って確定する。受入 = 親 env から `_GIT_ENV_KEYS` を除去 (dev_wave_wait.py 651〜659)、land = 全 `GIT_*` 除去 + override (`LANG` / 他 `LC_*` は残る)。「計算ノード dispatch 0 件」は書かず、「現行 checker の受領証の inherited / config は login 系 2 partition の値以外に無い」とだけ書く。`LC_CTYPE=C.UTF-8` だけの partition の帰属は「不明 (推定不能)」。P4-b の走は dispatch receipt (job ID / hostname) と受領証 (inherited / config 全文) で結ぶ。 |
| A6 | should | 採用 | 限定文: 期間 (2026-09-21 00:12〜本 wave 着手 07:35)、残存件数、partition 別件数、log 対応件数、load1 は受入 gate 時点の観測。禁止文: cold 率、時間短縮率、混雑時の 480 秒保証、「他 binding 失効は起きない」。結論の形は「対象期間の残存受領証には再利用可能な祖先候補が多数ある (replay 成功 n 件 / 候補なし m 件)」。 |
| B1 | real | 採用 | P4-b の目的 = **dispatch 先の partition の実体と、その条件での cold / warm 対照**に限定。480 秒適合は評価しない。親経過時間 (`/usr/bin/time -v`)・dispatch receipt の queue 待ち・計算ノード側の checker 時間 (receipt にあれば) を分けて記録。rc=16 は dispatch 不成立として別記。 |
| B2 | real | 採用 | **(a) login 3 走は削除** (計測目的は性能測定 = 計算ノード、AGENTS.md)。login の値は既存 log の間隔で代替し、監査単独 wall は「未測定」と残す。(b) = **2 request 直列** (`python3 tools/check_ai_provenance.py --force-dispatch` × 2、前 request の終了と ledger 確定を待って次)。実行前に共有 store の受領証 bytes / mtime を凍結保存 (P-1)。1 回目の cold は事前に保証せず、実 partition を受領証から求め祖先候補の有無で判定。人工 `GIT_*` cold は作らない。ledger を手で消さない、`_JOB_SESSION_SWEEP_ENV` を流用しない、同一 worktree で HEAD / index / checker を変えない。 |
| B3 | real | 採用 | 「混雑時 = headroom_short」は撤回。書き方: 「dispatch 経路の強制実行を観測した。現行 checker の自然な login 混雑時 (bounded local の cold / dispatch 発火) は未観測」。感度試算は「現行 cold 実測 C 秒 × 仮定倍率 k」と明記し、旧資料の 7 倍は仮定であって予測・上限ではない。異なる上限値同士の比から現行値を推定しない。 |
| B4 | real | 採用 | 裁定パッケージ第 1 案 = 「観測範囲では §11 の 3 候補 (memo 化 / attr.tree / errno) を支持する cold 原因を確認できず、追加実装を提案しない」。「残る cold の主因は初回だけ」とは書かない。区画統一 (受入 / land の checker 起動 env の統一) は **裁定パッケージ候補・scope 外** (D2045 の区画分離の改訂を要する)。効果は条件付きモデルで示す: (i) checker 変更 1 回あたり、祖先・bindings・時系列が揃う場合に限り最大 1 回の初回 cold を回避、(ii) 救済 land 1 本あたり C−W 秒 (C / W は同条件の checker 単独時間 = P4-b の計算ノード cold / warm の対だけが該当。login は間隔しか無いので式のみ)。dispatch 先 cold は帰属確認できたら別項目、頻度不明のまま主因に加えない。 |
| B5 | should | 採用 | author には親 script 3 本を**参考入力 (正解扱いしない)** として渡し、相談の反例・修正点・採用範囲を明示させる。段 6 review 1 本は行単位で照合 (attempt ledger の各行と欠測、各受領証の候補・bindings 差・replay 結果、cold 候補全件の原因と複合差、時間表の n・区間・partition、裁定案の効果式・出所・限定文)。 |
| B6 | nit | 採用 | 19 partition の詳細履歴表、旧 26 件全部の原因再構築、§11 候補の個別効果実測、人工 login 混雑、全 binding 失効実験は行わない。旧期は比較行と限界に絞る。 |

## plan v2 — Codex author に書かせる probe (repo 外 job dir `probe/` で実行、repo へ入れない)

| # | file | 役割 | 入力 | 出力 (job dir `measurements/`) |
|---|---|---|---|---|
| P-1 | `receipt_ledger.py` | 共有 store の全受領証を read-only で凍結目録化 (partition dir 名 / file / mtime_ns / size / sha256 / tip / bindings 全文 / selection / candidate_count / records の件数) | store path | `receipt-ledger-<stamp>.jsonl` (追加走の前後で 2 回取り、差分 = 追加走の副作用) |
| P-2 | `receipt_reuse_replay.py` | A1 / A3 の replay 分類。対象 = 母集団 (着地後 publish) + 参考 (着地の走・着地前旧期)。各 B について実装と同じ候補選択順で A を並べ、bindings 一致 → `_receipt_prefix` → raw correction を replay。主分類 4 種 + 参考区分 + 比較相手 / 差分全項目 / 複合差 / 判定不能 | P-1 の ledger、worktree (git、`tools/check_ai_provenance.py` を import) | `reuse-replay.jsonl` + 集計 stdout (tee 逐語) |
| P-3 | `audit_attempt_ledger.py` | A4 の attempt 突合。dev-wave-jobs の各 wave の受入 (`acceptance-*.started.txt` / `.finished.txt` / `.tip-before.txt` / chain.log の gate load1) と land (`land-*.log` の `land:` 型 / `it=N land landing=` 型、`land-*.json`) を列挙し、(wave, stage, HEAD, partition, 区間) で受領証と突合。未対応は理由付きで残す | dev-wave-jobs、P-1 ledger | `audit-attempts.jsonl` + 表 stdout (tee 逐語) |
| P-4 | `launch-force-dispatch.sh` | P4-b の launcher: `/usr/bin/time -v python3 tools/check_ai_provenance.py --force-dispatch` を 1 request。stdout / stderr / time を逐語保存。2 回目は親が 1 回目の終了 (`.done`) と dispatch receipt の確定を確認してから起動 | worktree | `force-dispatch-<n>.{out,err,time}` |

- 実装面 (repo 内) 差分ゼロ → 変異 matrix は免除 (DW-S04)。受入全走は免除しない。
- author は workspace-write で worktree 内 `probe/` (untracked) に書き、親が実行前に job dir `probe/` へ退避して worktree を clean に戻す (DW-C01)。
- 段 6 review 1 本 (read-only) は insight README を P-2 / P-3 の生 stdout と行単位で照合。

## 条件表 (段 4 時点)
O08 / O09 / O10 / O13 非成立 (変更なし)。O11 非成立。O01 / O02 / O05 は各子の直前に再読。O06 非該当 (submodule 系 test なし)。
