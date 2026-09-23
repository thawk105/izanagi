# [T-2854] 残り (1) — TPC-C trace v3 の存在履歴 (設計 §3.3) を verifier に実装し、v3 を一律に認定しなかった印を撤去した。実 TPC-C trace (silo、36,156 取引) が初めて certified に届いた (2026-09-23)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
依頼は [T-2854] の残り (1)。依頼の逐語は `verbatim/request.md`。設計 `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §3.3、
前段 (単位 4) の記録 `output/insights/2026-09-22/t2854-tpcc-verifier-v3/README.md` §2・§6、裁定 D2224 項 4 (印の撤去は §3.3 を実装する単位の完了条件)。
wave branch `worktree-t2854-v3-existence`、起点 local main `cadaf3805` (開始 gate fresh rc=0、2026-09-23 08:35 JST)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-v3-existence` (起動 script・待ち手・生 log・probe と変異の script)。
全 9 段で回した (正しさ防壁の verifier の受理集合が変わるので独立の敵対検証子が必須、DW-C00)。各段の prompt と成果の全文は job dir、成果の全文は `verbatim/`。

## 0. この wave が主張すること・しないこと

- **主張する:** v3 の run について、verifier が設計 §3.3 の存在履歴を段 1 の契約 (§1) で検査し、違反があれば認定しない (indeterminate、cycle 併存なら
  従来どおり non-serializable)。違反は txid・表・key・版・種別まで構造化して返す。印 `Integrity.v3_existence_unverified` は撤去した。
  object 経路と compact 経路 (packed・tuple、workers 1/2、逐次 fallback、tuple 落ち・legacy 落ち) が同じ結果を返すことを試験で示した。
  単位 1・2 の実 TPC-C trace (silo、NewOrder 19,751・Payment 16,405) は公開 API `verify_trace_dir` で **certified** になり、同じ trace の R 行 1 本を
  違反に書き換えた写しは存在違反 1 件で indeterminate になる。v2 (YCSB) の受理・拒否・判定・出力は変えていない。
- **主張しない:** 初期ロード集合そのものの検証 (§1 の契約は silo の版付けに基づく。§4.3 の初期キー一覧は段 2 の単位 7)。段 2 (Delivery の削除・scan・
  再挿入の版順)。mocc の認定 (mocc の証拠面は単位 3・11 以後)。pipeline の allowlist・CLI・受領証 digest への配線 (単位 5)。TPC-C の run の
  commit 計数を pipeline が照合すること (単位 5)。
- **規律 2・3:** 判定できない存在は認定しない側へ倒す。version dup・genesis commit のある run は存在検査を省くが、既存の integrity で indeterminate のまま。

## 1. 段 1 の存在契約 (段 4 裁定 R1) とその根拠

**規則:** (表, key) が genesis で存在する ⇔ その object の最初の committed write (版 = commit の (epoch, tid) 辞書順) が I でない。一度も書かれない
object の genesis 読みは存在する record の読み。

段 3 の 2 レンズは一致して「これは初期集合の検証でなく推定だ」と攻撃した (`verbatim/s3-consult-A.md` A1、`verbatim/s3-consult-B.md` B2)。親は
CCBench (現 pin `e9e477ca`) の silo で次を確かめ、推定ではなく「silo の版付けに裏付けられた段 1 の契約」として採用した (`verbatim/s4-ruling.md` R1):

- 版 (1,0) を付けるのは初期ロード専用の `Tuple::init(thid, body, p)` だけ (`external/ccbench/cc/silo/include/tuple.hh:40-47`、epoch=1・tid=0)。
  実行中の insert は epoch 0・absent・lock の record を作る (`:50-54`)。実行中の commit が (1,0) 以下なら既存の genesis_commits で拒否される。
  したがって「R が (1,0) を読んだ」は「初期ロードの record を読んだ」を意味する。
- insert は key が木にあれば `WARN_ALREADY_EXISTS` で失敗する (`cc/silo/transaction.cc:74-80`)。absent な record の update は abort する (`:185-188`)。
  存在しない key の読みは read set に入らず R を出さない (相談 A2、`:230`, `:260`)。したがって「最初の committed write が I」は「その時点で木に無かった」、
  つまり初期に無かったことを意味する。
- mocc も同じ 2 点が静的に成り立つ (並走の単位 3 wave が C3 の source で確認: `cc/mocc/include/tuple.hh:74-83`、`TxExecutor::insert`)。実 trace での確認は
  §4 の mocc 行だけ。

**残る穴 (限界、認定を止める理由にしない):** trace の行そのものの捏造・欠落 (既存の witness・framing の領分、D295 / D296 の限界と同型)。初期にある key への
不正な I で、その初期版を誰も読まないもの — 辺を 1 本も変えないので直列化可能性の判定には影響しないが、insert の意味の検証にはならない。段 2 の §4.3 で閉じる。

## 2. 実装 (commit `f7b69e3de`、fix1 `a3ef74277`)

| 面 | 内容 |
|---|---|
| dsg | v3 だけで動く存在検査 `DSG._check_existence` を 1 つ置き、object 入口 (`DSG.__init__`) と compact 入口 (`DSG.from_compact`) の両方から辺構築の後に親で 1 回呼ぶ。compact は winner 行だけを読み、表は key token から取る。辺構築・worker・parse・report.py は不変 |
| 規則 | 読み: `read-unborn-genesis` (初期不存在の key の genesis 読み)、`read-deleted-version` (op=D の版の読み)。書き: `insert-on-live`、`update-on-absent`、`delete-on-absent` (違反の後も op の事後状態へ進む)。同じ取引・同じ版に異なる op → `ambiguous-write-version` (その object の派生診断は省く)。orphan は新件数に数えない |
| model | `Integrity.existence_violations` (件数) と `existence_violation_details` (`ExistenceViolation` の列、v2 では None)。`clean()` は件数 0 を要求。印 `v3_existence_unverified` を撤去。`VerifyResult.verdict` は不変 |
| core | 印の設定と note、使わなくなった `is_v3` と `TxnV3` import を撤去。`result_to_dict_v3` は v3 のとき integrity に件数と詳細を足す。旧 `result_to_dict` (report.py) は不変で、旧 JSON では `clean` と notes にだけ現れる |
| 試験 | test_verifier.py に新規 6 本 (負例 5 種と 1 行修正の正例、正常履歴・指定版の読み・自己版、版順と表の分離、異種 op、既存 integrity との重なりと winner、出力・見本・cycle 併存)。既存の変更は裁定 R7 項 8 の限定表だけ (印の試験を改名して U 例を certified・I/D 例を新違反へ帰属、serial-tables 試験に存在件数 3 を追加) |

production は追加削除 127 行 (fix1 で +40/−23)、試験 198 行 (fix1 で +3/−3)、新規 test 関数 6 本 (段 4 の上限 300 / 450 行・10 本の内側)。

## 3. 段の経過

| 段 | 内容 | 成果 |
|---|---|---|
| 1 | brief (親)、実 trace の生死確認 (repo 外の使い捨て集計と現行 verifier) | 提案規則の違反 0 件、現行 verifier は印だけで indeterminate (11.8 秒) |
| 2 | plan (Codex read-only、5 分 41 秒) | 共通検査 + 薄い 2 adapter、見積り 545〜800 行 |
| 3 | 相談 A (正しさ境界) / B (実効性・過剰) (各約 4 分、並列) | 一致した must-fix: P1 の表現の過大 (A1 / B2)、cycle 優先順位の変更は不要 (A5 / B1)、実装後の公開 API での実測 (B3) |
| 4 | 裁定 R1〜R8、変異 M0〜M14 の事前登録 | R1 = silo の版付けに裏付けた段 1 契約、cycle 優先は不変 (D2224 を維持)、規模上限 |
| 5 | author (Codex、8 分 15 秒) | 子の自走は修正前 137 passed / 1 failed、修正後は未実走。親の単独走 solo-1 = 138 passed |
| 6 | review A (GO・所見なし) / B (GO・nit 3) → 親の同時刻対照 → fix1 (3 分 37 秒) → 焦点再レビュー (GO) | B1〜B3 closed、所要の所見は親の再測で閉じた (§5) |

## 4. 検査の結果

| 検査 | 対象 commit | 結果 |
|---|---|---|
| 単独走 solo-1 / solo-2 (test_verifier.py の自走 harness、login) | `f7b69e3de` / `a3ef74277` | 138 passed / 138 passed |
| 焦点走 focus-1 (test_verifier.py + verifier を参照する consumer 26 本 + inventory 4 群、test_campaign.py の重複を除き計 30 file、計算ノード request 19130.nqsv、Elapse 349 秒) | `a3ef74277` | 3,837 passed / 9 skipped / 0 failed |
| 実 trace (silo B0、`verify_trace_dir`、protocol=silo、ccbench_root = worktree の submodule (pin e9e477ca)、expected_commits=36,156) | `f7b69e3de` / `a3ef74277` | workers 1 / 2 とも **certified**、存在違反 0、orphan 0、辺 268,209、commit 計数一致 (`measurements/real-trace-probe-{1,2}.json`) |
| 同じ trace の写しで R 行 1 本を「insert された OrderLine の key の genesis 読み」へ書き換え | 同上 | workers 1 / 2 とも indeterminate、存在違反 1 件 (read-unborn-genesis)、orphan 0 (`measurements/real-trace-probe-inj{1,2}.json`) |
| mocc の実 trace (単位 3 wave の B0、35,572 取引、外部データとして読むだけ) | `a3ef74277` | 存在違反 0・orphan 0・cycle 無し。indeterminate の理由は現 pin の mocc に X/P 証拠面が無いこと (proof gate 不成立) だけ (`measurements/mocc-trace-probe.txt`) |
| AI provenance 全史監査 (各 commit 後) | 各 commit | 新規違反なし (12,613 件 → 12,614 件) |

実 trace の probe は repo 外で、repo 内の正例・負例と変異の代わりにはしない (相談 B3)。この trace には insert 対象表の読みも D も無いので、実 trace の certified
だけでは検査の検出力を示せない。検出力は注入版・試験・変異 (§6) で示した。焦点走は受入形でない走行で、受入全走の代わりにはしない。

## 5. 所要 (同時刻の対照)

段 6 レビュー B が「所要 +52%」と指摘したが、比較条件 (変更前は workers 1/2 の合計、変更後は各回) が揃っていなかった。親が同じ trace・同じ引数・別 process で、
変更前 (main checkout `cadaf3805`) と変更後を交互に 3 回ずつ測った (login、`measurements/paired-timing-{1,2}.log`)。

| 版 | workers=1 (3 回) | workers=2 (3 回) |
|---|---|---|
| 変更前 (印だけ) | 7.27 / 7.28 / 6.94 秒 | 4.53 / 4.67 / 4.65 秒 |
| `f7b69e3de` | 9.98 / 9.99 / 9.84 秒 | 7.44 / 7.58 / 7.47 秒 |
| 変更前 (2 回目の対照) | 6.86 / 6.79 / 6.55 秒 | 4.05 / 4.37 / 4.48 秒 |
| `a3ef74277` (fix1) | 8.42 / 8.61 / 8.46 秒 | 6.06 / 6.08 / 6.10 秒 |

存在検査は親で逐次に走るので workers によらず一定の追加になる。追加は fix1 前 約 2.7〜2.9 秒、fix1 後 約 1.8 秒 (この trace、R 約 50 万・W 約 54 万行)。
fix1 は key / op token の復号の memo、版ごとの set 生成の廃止、読みの照合集合の事前構築 (判定・出力は不変、焦点再レビューが等価性を静的に確認、試験と変異で裏取り)。
login の値で、計算ノードの値ではない。

## 6. 変異 matrix

段 4 で M0〜M14 を事前登録し (`verbatim/s4-ruling.md`)、fix1 の最終 commit `a3ef74277` の行へ anchor を付け直した (DW-M07、全 anchor が累積適用で各 1 回)。
期待 node は独立 clone (main = `a3ef74277`) の login 自走 probe で集めた (`mutation/probe-1-results.json`、baseline 緑 10.4 秒)。

**本走** (spec `mutation-spec-final.json` sha256 `0897d034…3022193f`、`tools/mutation_harness.py` を `tools/mutation_worktree.py` の独立 clone で dispatch、
2026-09-23 09:47〜10:02 JST): baseline PASSED、**19 / 19 が事前登録どおり** (赤 node の集合が probe の期待と完全一致、`mutation/mutation-final-results.json`)。

| 変異 | 内容 | 結果 | 赤の試験数 |
|---|---|---|---:|
| M0 | 等価変異 (版の並べ替えに同じ順の key を指定、harness の正例) | SURVIVED (期待どおり) | 0 |
| M1 | 初期存在を常に真 (最初の I を見ない) | KILLED | 6 |
| M2 | D 版の読みの検査を外す | KILLED | 5 |
| M3a / M3b / M3c | insert-on-live / update-on-absent / delete-on-absent を個別に外す | KILLED ×3 | 1 / 1 / 1 |
| M4 | D の後も存在のまま (D 版の記録は残す) | KILLED | 3 |
| M5 | clean() が存在違反を見ない | KILLED | 7 |
| M6 / M7 | object 入口 / compact 入口だけ検査を呼ばない | KILLED / KILLED | 17 / 18 |
| M8 | v2 にも検査を掛ける | KILLED (v2 の既存試験 2 本を含む) | 3 |
| M9 / M10 | 版順を (tid, epoch) / txid 順にする | KILLED / KILLED | 1 / 1 |
| M11 | 読みの判定を指定版でなくその key の最新の op で行う | KILLED | 1 |
| M12a / M12b | 異種 op の版を I / D に潰す | KILLED / KILLED | 1 / 1 |
| M13 | result_to_dict_v3 が詳細を出さない | KILLED | 1 |
| M14 | 存在検査の identity から表を落とす | KILLED | 7 |

単一理由の確認 (DW-M01): 各負例は cycle 無し・orphan 0・framing 0・X/P gate 充足・witness 一致で、件数を 0 に差し替えると clean になることを試験自身が確かめる。
M6 / M7 の赤が多いのは、既存の v3 試験が object 経路と compact 経路の integrity の一致を比べていて、入口を外すと詳細が None と [] で食い違うため (原因は入口の除去だけ)。
M8 は v2 の既存試験 (`test_capacity_last_wins_drops_old_writer_edges_and_orphans_reads`、`test_v3_output_validation_and_v2_projection`) でも赤になり、v2 に検査を掛けない不変条件が既存試験で守られる。
kill の内訳: 事前登録の非等価 17 変異すべて KILLED、等価 1 は SURVIVED。

## 7. 計算量

D2219 項 1 (1 タスクの job 合計が 2 node 時間以上なら事前確認) の線で数える。

| 項目 | 値 | 出所 |
|---|---|---|
| 焦点走 focus-1 (計算ノード 1 台、19130.nqsv) | Elapse 349 秒 | 実測 (job の Resources Information) |
| 変異本走 19 走 (計算ノード、1 走 1 台) | 各走の所要の合計 539.9 秒 (最大 32.9 秒、queue 待ちを含む上限) | 実測 (台帳の `duration_s`) |
| 単独走 2 回・変異 probe 1 回・実 trace probe・同時刻対照・mocc trace | login のローカル実行 (計算ノード 0) | 実測 |
| 受入全走 1 回 | 約 0.25 node 時間 | 換算 (直近の受入の job Elapse の実測単価)。本 README の commit 後、同じ tip で land 直前に行う (本 README の時点では未実施) |
| **合計** | **約 0.5 node 時間** (349 s + 540 s ≈ 0.25 h に受入 0.25 h を足した上限側の見込み) | 2 node 時間の線の内側 |

LLM の直列時間 (Codex 子 9 本) は node 時間と別。

## 8. 後続への引継ぎ

- **単位 5 (pipeline の allowlist・witness 試験・§6.1 の正例負例):** 本 wave で前提 (D2224 項 4 の印の撤去) が満たされた。§6.1 の「genesis の誤用 → indeterminate」は
  存在検査の `read-unborn-genesis` に帰属する。v3 の構造化出力 (`result_to_dict_v3` の存在詳細) を CLI・pipeline へ出すのは単位 5。
- **mocc (単位 3 の後):** §1 の 2 点 (初期ロードの版 (1,0)、insert の存在検査) は mocc でも静的に成り立つ (単位 3 wave の確認)。mocc の実 trace でも存在違反 0。
  mocc の認定は X/P 証拠面が pin に入った後 (単位 11)。
- **段 2 (単位 6〜9):** Delivery の DELETE と再 INSERT で版順が存在の遷移と逆になりうる (相談 A4、静的な推論、TPC-C が削除済みの NewOrder key を再利用するかは未確認)。
  範囲読みで見えなかった初期 key は R/W だけでは列挙できない (§4.3 の初期キー一覧)。段 1 の契約を段 2 へそのまま広げない。

## 9. 限界

- 合成 fixture・静的レビュー・silo と mocc の実 trace 各 1 本による確認。実 CC の異常 schedule で違反を起こした例は無い (違反は写しへの注入だけ)。
- §1 の契約は silo (と静的には mocc) の版付けに依存する。別の CC や版付けの変更では根拠を確かめ直す必要がある。
- v2 の不変は既存試験 (JSON bytes・witness 順・全 fixture 結果 hash を含む) と段 6 レビューの静的追跡による。全入力の不変を証明したものではない。
