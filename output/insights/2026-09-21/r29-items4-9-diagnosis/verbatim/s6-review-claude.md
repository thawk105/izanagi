<!-- 段 6 独立 read-only レビュー。Codex 子が利用上限で出力 0 (不受理) だったため、Claude の read-only 子 (general-purpose、model=opus) が prompt-s6-review.md の依頼をそのまま実施した最終報告の逐語。harness が各行に付けた 2 字下げだけを除いた。 -->

## 所見

基準: repo 相対パスの起点は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-r29-items4-9-diagnosis/`。「README」は `output/insights/2026-09-21/r29-items4-9-diagnosis/README.md`、「fragment」は `docs/spool/worklog/2026-09-21-dev-wave-r29-items4-9-diagnosis-1.md`、「job dir」は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-r29-items4-9-diagnosis/` を指す。この点検は静的な読み取りと再計算だけで行った。書き込み・テスト・dispatch はしていない。

1. **real / must-fix — fragment の工数行は段 6 を codex 子が行ったと書いているが、実際は失敗している。**
   - 根拠: fragment:26 は「codex 子 = plan 1 + consult 1 + review (段 6) の read-only のみ (gpt-6-astra / medium)」と書く。
   - 実際の codex 段 6 は出力 0 で不受理だった。job dir の `codex/s6-review.done` = `1`、`codex/s6-review.check.log` = 「対象 … s6-review.md を開けない」。
   - 受領証 `codex/artifacts/r29-items4-9-diagnosis/r29-items4-9-diagnosis-review-3722…/receipt.json` は outcome=`not_accepted`、failure_class=`f45_missing_output`、codex_exit_code=1。
   - 同 dir の `attempt-0001.events.jsonl` 5 行目は “You’ve hit your usage limit … try again at Sep 26th, 2026 7:35 PM”。
   - 実際の段 6 は Claude の read-only 子 (本レビュー) が代行している。
   - 放置時の影響: fold 後に書き換えられない worklog に、レビュー主体と工数の誤記が残る。commit trailer とも食い違う。

2. **real / should — plan 由来の code 引用 2 件が未検証のまま断定されている。**
   - (a) README:79 の `conftest.py:1936–1948` は root に存在しない。実体は `orchestrator/tests/conftest.py:1936–1948` (`_growth_holds_opted_in` の exact token 検査) で、親の指摘どおり。
   - (b) README:71 の「計算ノード側は … `run_tests.py:2682` → `:1260` が 1 つの pytest command を実行」は経路が誤り。
     - login 側 `_dispatch_environment` (`tools/run_tests.py:1296–1299`) は task_run_id を外し、`IZANAGI_TASK_RUN_AUTO_RECORD=0` を設定する。
     - この値は tests allowlist (`tools/pegasus/dispatch_compute.py:123–126`) を通って計算ノードへ届く。
     - そのため計算ノードの runner は `run_tests.py:2689–2694` の `subprocess.call(cmd, cwd=_REPO)` を通る。`_call_and_record` (:1260) には入らない。
     - いずれも plan 原文 (`verbatim/s2-plan.md:12`) の写しである。
   - (c) (b) の帰結として、README:84 の「未見積りの費用: 計算ノード側の自動記録との二重記録の防止」の一部は既存機構が既に担っている。
     - `dispatch_compute.py:123–125` のコメント “The marker keeps a compute-side run_tests.py from creating a second generation”。
     - R2 で要るのは、要素ごとに base env を複製するときにこの marker を保つことだけである。
   - 放置時の影響: R2 の費用見積りの根拠行が誤った経路を指し、既存機構で済む項目が未見積りの費用として再提示に残る。

3. **real / should — §2 は t2810 の held 診断 job を「集合走」に数えている。**
   - 根拠: README:54「3 (held 1 を含む)」、README:60 の仮定「held を単独走が兼ねられ」。
   - 実体は `dev-wave-t2810-g1-launch-validation/focus/run-focus-held.sh:11,15–17` で、`IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command` の下で走らせた 2 file の `-k` 選択 (8 名、`focus-held-1.log:33` = 9 passed) である。
     - 対象 2 file のうち `test_s8b_binding_driftguards.py` は t2810 の変更 test file ではない (前回 `verbatim/changed_files.txt:17`)。
     - DW-O26 の集合走ではないので、単独 1 file 走ではこの held 診断を兼ねられない。前回 README:101 (K3) も「held 診断自体はユーザー明示の要求で消さない」としている。
     - held-1 を残す側に置くと、「集合走を最低 1 本残す」前提そのものが崩れる。
   - held-1 を除くと t2810 は集合走 2・置換上限 1・残件 1〜2 になり、計は置換上限 9・残件 11〜20 になる。
   - 現行の 10 / 10〜20 は緩い上下限としては成り立つ。しかし「held 1 を含む」という書き方と仮定は、log と矛盾する。
   - 放置時の影響: 上限 10 に成立しない置換 1 本が含まれ、「集合走」の定義に DW-O26 集合ではない走が混ざる。

4. **real / should — §2 の上下限の範囲が計算ノード焦点 job だけに閉じていることが、§0・fragment に明示されていない。**
   - 根拠: README:39 は D325 の「既に回す走行」を一般形で引く。一方で job 数は計算ノード焦点 job だけで数えている (README:45)。
   - 親の login 実走・author 実走は置換元にも s にも入っていない (前回 README §5.2「login や author の実走は標本外」)。
   - 標本内にも該当例がある。`output/insights/2026-09-20/t2797-b5-contrast/README.md:90` は「親の実走 (login、各 fix 後): 変更 test file の焦点 (report 70 / driver 108 / …)」と書く。
     - report 70 と driver 108 は、単独 file 全体の件数 S04 = 70・S03 = 108 と一致する。ただし別 process の単独走だったかは未確認である。
     - 同 README:92 は「commit 5 (fix3) は親の login 実走で確認」と書く。
   - これらを既存走に含めると、上限は増え、下限 10 は下がりうる。
   - 放置時の影響: 「置換で満たせない残件は延べ 10〜20」が全経路の下限として読まれ、M3 の追加 job を過大に見積もる。

5. **real / should — 項 9 の 1 例目 (T-2737) は、既裁定 D2194 項 8 自身の根拠例である。**
   - 根拠: `docs/decisions.md:69801` (D2194 項 8 理由欄) は「entry 1695 (`test_ccbench_spawn_sites.py` の受入赤 3 件) で再発」と書く。
   - entry 1695 は T-2737 の受入赤である (`docs/archive/worklog-phase3-0920-1695.md:1,4`)。
   - README:146 と fragment:19 は「第 29 回の材料は [T-2820] を引いていなかった」とだけ書いている。索引 (`rulings-all-20260921c/final-index.md`) に T-2820・D2194・1695 の hit が 0 であることは確認した。
   - 放置時の影響: 2 例がどちらも新しい証拠に見え、既裁定の根拠例を別の択として再提示したという照合漏れの型が記録に残らない。

6. **real / should — 「88 %」の分母が本文と費用欄で食い違う。**
   - 88 % は 1,066 / 1,208 (固定費) の比である。
   - README:171「M3 の費用の 88 %」と fragment:22「費用の 88 %」では、M3 の費用欄 (README:165 = wall 1,336) が分母に読める。S07 の wall 1,081 / 1,336 は 80.9 % である。
   - README:21「固定費の 88 % (1,066 秒) は 1 本 (S07) の待ち 1,050 秒で」は、S07 の固定費 1,066 と待ち 1,050 を同一視している。待ちだけの比は 86.9 %。
   - 放置時の影響: 裁定者が wall の 88 % と読む。

7. **real / should — 長い待ちの帯の定義が混ざり、R2 を見送る根拠の強さが読み取れない。**
   - (a) README:171「その帯の頻度 (本試行 2 / 10 本、前回 12 / 27 本が 300 秒以上)」は、17 分半の帯と ≥ 300 秒の件数を同列に置いている。
     - 前回の 17 分前後は 3 / 27 (1,007 / 1,020 / 1,020 秒)。
     - 前回の ≥ 300 秒は 12 / 27 (337〜1,020 秒、平均 632 秒、前回 README:41)。
   - (b) M3 費用欄 (README:165) の「長い待ちの帯は 1 本 1,050〜1,064 秒」について:
     - 1,064 は S01 (集合 job) の待ちで、M3 の単独 job ではない。
     - 並記の「18〜26 秒」は固定費なのに、この 1,050〜1,064 は待ちだけで、量が揃っていない。S07 の固定費は 1,066 秒。
   - (c) README:173 と fragment:22 の「17 分半前後待つ」について、前回の長い待ちは 337〜1,020 秒に散っている。
   - (d) README:130 と fragment:23 の「前回診断の長待ち 3 本」について、前回の長待ちは 12 本あり、3 本はそのうち 17 分前後のものである。
   - (e) README:174 の再提示の目安「長い帯に入る例が複数 wave で出たとき」は、帯の閾値も「複数」の数も未定義である。
     - 前回 12/27・本試行 2/10 の頻度なら、数 wave で発火する見込みが高い。
     - 「今は実装しない」の理由は「節約を示せていない」だが、逆向き (見送りの費用が小さいこと) も示せていない。現状は見積りの無い判断であることを明記すべきである。
   - 放置時の影響: M3 の長い待ちの費用と頻度が 1 試行の 1/7 を基準に過小に読まれる。R2 の再提示の条件が判定できない。

8. **real / nit — README:148「同じ集合のノード間の差 (27 秒)」は帰属のしすぎである。**
   - S01 は bnode024 で chain の 1 本目 (14:53 開始)、S10 は bnode020 で最後 (15:21 開始) である。
   - node・時刻・順序が交絡しており、README 自身が引く D289 決定 (2) の論理そのものに当たる。
   - 放置時の影響: ノード差を測ったと読まれる。

9. **real / nit — `verbatim/contract/` の 7 file の正規化が記録されていない。**
   - 7 file とも job dir の原本 (`verbatim/contract/`) と 1 byte ずつ違い、末尾の空行が削られている (`\n\n` → `\n`。例: D325.md は 2183 → 2182 bytes)。
   - `verbatim/NORMALIZATION.md` にも README:8 にも記載が無い。内容は不変。
   - 放置時の影響: byte 一致と誤認される。

10. **real / nit — `/tmp/.git` の現存に根拠の記録が無い (README:18、:97)。**
    - 「15:2x JST 時点でも残り」「ls -ld で確認」の出力が verbatim に無く、既知型 F457 (`docs/failures.md` の F457 節、2026-09-08 の再発で makiart・2026-09-07) も引いていない。
    - 本レビューで 15:42:07 JST に再観測した: `drwxr-xr-x 2 makiart KASYS … 2026-09-07 18:07:20 /tmp/.git`。事実は正しい。
    - 放置時の影響: 根拠を辿れない。

11. **real / nit — README:143 の D2194 項 8 の「」引用が逐語ではない。**
    - 実文 (`docs/decisions.md` 項 8 決定) は「DW-O26 の『production file を変えた wave は inventory test 4 群を参照関係に依らず焦点走に含める』の集合に … を足す (4 群 → 6 群)」である。
    - 発火条件と対象 2 file の意味は一致している。

12. **real / nit — README:126「どの手段でも残る分 = RUN 128 秒」は言い過ぎである。**
    - RUN と pytest の差 7.6 秒には、job 単位の起動・probe import・結果の fsync が含まれ、束ねればその一部は消える。
    - 残る分は 120.42〜128 秒と書くべきである。README:20 の「消すのはこの固定費」も上限として書くべきである。

13. **real / nit — 取りこぼし。**
    - fragment:7 の title に [T-2843] が無い。
    - [T-2832] の状態文「([T-2842] の計測後)」が更新されない。計測は済んだので、「[T-2842] 再提示の裁定待ち」が現況である。

14. **refuted — [T-2843] の `完了` (remaining: none) は依頼の完了条件を満たす。**
    - 依頼は `docs/worklog.md` の [T-2843] 本文で、「既存の探索で拾える局所策とその追加実行時間だけを測る。無条件の集合拡張・DW-O26 の改訂はしない」。
    - 局所策の有無: module 名探索は hit 0 で再現した。追加で、変更関数の symbol 探索も hit 0 だった (`build_target` / `prepare_masstree_fetchcontent` @`134ea235c^`、`default_runner` @`517fd5451^`)。
    - 既裁定との関係: [T-2820] は条件付き拡張で、本 wave による新たな DW-O26 改訂ではない。
    - 追加時間: 限定付きで実測している。
    - 補足: 「DW-O26 の改訂はしない」と既裁定 [T-2820] の関係を 1 文で書くと誤読を防げる。

15. **refuted — §4 の表・派生値、§3/§5 の他の引用、正規化 (S*.log 10 本と s3-consult.md) は一次資料と一致する** (下表)。

16. **refuted — 過剰は無い。**
    - gate・台帳・一般化の提案は無い (README:174 は「新しい台帳は作らない」)。
    - 130 file の探索は、局所策にならない理由として置かれているだけである。

## 派生値の検算表

| 値 | README の値 | 再計算値 | 一致 |
|---|---|---|---|
| S01 投入前/待ち/RUN/collection/wall | 2/1,064/151/14/1,231 | 2/1064/151/14/1231 (start 14:35:24, C 14:35:26, S 14:53:10, E 14:55:41, end 14:55:55) | 一致 |
| S02 | 1/11/6/14/32 | 1/11/6/14/32 | 一致 |
| S03 | 1/9/6/11/27 | 1/9/6/11/27 | 一致 |
| S04 | 2/11/6/13/32 | 2/11/6/13/32 | 一致 |
| S05 | 2/8/80/15/105 | 2/8/80/15/105 | 一致 |
| S06 | 1/7/9/10/27 | 1/7/9/10/27 | 一致 |
| S07 | 1/1,050/15/15/1,081 | 1/1050/15/15/1081 (C 14:59:39, S 15:17:09) | 一致 |
| S08 | 1/11/6/14/32 | 1/11/6/14/32 | 一致 |
| S09 | 1/8/137/14/160 | 1/8/137/14/160 | 一致 |
| S10 | 1/20/124/15/160 | 1/20/124/15/160 | 一致 |
| request → node (10 本) | 15194 bnode024 … 15314 bnode020 | compute-visible/*.json と dispatch 原本 10 本が一致 | 一致 |
| pytest 集計 (10 本) | 表の値 | 各 log の集計行と一致 | 一致 |
| rc | 10 本すべて 0 | end rc=0 ×10、*.done = 0、child rc=0 | 一致 |
| 単独 7 本の wall | 1,336 | 1,336 | 一致 |
| 単独 7 本の RUN / 固定費 | 128 / 1,208 | 128 / 1,208 | 一致 |
| 投入前 / 待ち / collection | 9 / 1,107 / 92 | 9 / 1,107 / 92 | 一致 |
| S07 の固定費と比 | 1,066 = 88 % | 1,066 / 1,208 = 88.2 % (wall 比 1,081 / 1,336 = 80.9 %、待ち比 1,050 / 1,208 = 86.9 %) | 一致 (「費用の 88 %」は分母不一致、所見 6) |
| 他 6 本の固定費 | 142、1 本 18〜26 | 26+21+26+25+18+26 = 142 | 一致 |
| pytest 秒の合計 | 120.42 | 120.42 | 一致 |
| RUN − pytest | 7.6 | 7.58 | 一致 |
| chain | 2,887 = 10 本の wall の和 | 14:35:24→15:23:31 = 2,887、wall の和 2,887、各 start = 直前 end | 一致 |
| 待ち 7〜20 秒 | 10 本中 8 本 | 11/9/11/8/7/11/8/20 の 8 本 | 一致 |
| 長待ちの時刻 | S01 14:35:26→14:53:10、S07 14:59:39→15:17:09 | 同じ | 一致 |
| S09 − S10 | RUN +13 / pytest +11.58 / +78 passed / +2 skipped | 137−124 / 135.09−123.51 / 2660−2582 / 12−10 (Elapse でも 141−128 = 13) | 一致 |
| S01 − S10 の RUN | 27 | 151 − 124 = 27 (Elapse 155 − 128) | 一致 (帰属は所見 8) |
| k / s の計 | 22 / 2 | changed_files.txt 3+1+6+1+2+2+7 = 22、s = t2803 1 + t2344 1 | 一致 |
| 集合走 job 数 | t2804 2・t2803 4・t2344 3・t2814 2・t2810 3・residue 4・t2797 3 | focus_runs_table.md から、単独 job (t2803 focus-2/7/8、t2344 f4) を除いて同値 | 一致 (t2810 は held-1 を含む、所見 3) |
| 置換上限 計 | 10 | 1+0+2+1+2+2+2 = 10 (held-1 を除けば 9) | 一致 (条件付き) |
| 残件 下限〜上限 | 10〜20 | Σmax(0,·) = 2+0+3+0+0+0+5 = 10、Σ(k−s) = 20 (held-1 を除けば 11〜20) | 一致 (条件付き) |
| rg の追随候補 | 36 file | rg / grep とも 36、優先 8 file は全部含まれる | 一致 |
| 列挙型探索 | 369 中 130 | 369 中 130、台帳に無いもの 12 | 一致 |
| 列挙型の直列合計 | 13,519 秒 = 74.8 % | 13,519.1 / 18,067.7 = 74.82 % | 一致 |
| 台帳の同 file | 47 entry / 224.5 秒 | 47 / 224.535 (整数値 5: 100/43/41/13/8) | 一致 |
| 丸め処理 | `update_acceptance_duration_ledger.py:124–143` | `_quantize_seconds` (有効数字 2 桁、ROUND_HALF_UP) | 一致 |
| 現行の同 file | 74 node | S05 = 72 passed + 2 skipped | 一致 |
| bytecode guard の test 数 | 6 | `def test_` 6、台帳 6 entry、80 − 74 = 6 | 一致 |
| git grep ×2 | hit 0 | ともに rc=1。`134ea235c^` = 4c9d9ecc2、`517fd5451^` = e4f4c900c で、各 acceptance-final-1 の tip-before と一致 | 一致 |
| 受入赤 | T-2737 3 failed / 25276 passed / 69 skipped、T-2797 2 / 26725 / 69、5 node すべて spawn_sites | 両 log の 3–6 行 / 3–5 行 | 一致 |
| T-2737 の production 変更 | `0bd0895da` = run_ss2pl_lock_study.py + patch | git show で同じ、受入 tip の祖先 | 一致 |
| K3 の固定費 | 735 | 6 + 715 + 14 | 一致 |
| 前回の長待ち | 1,007 / 1,020 / 1,020、12 / 27 が ≥ 300 秒 | 前回 README:41 と同値 | 一致 (呼び方は所見 7) |
| D130 | 0.15 % | 988.2 対 989.7 (contract/D130-D131.md:12) | 一致 |
| 相談の内訳 | 20 = must-fix 7 / should 5 / refuted 7 / 判定不能 1 | s3-consult の所見 1〜20 を数えて同値 | 一致 |
| login_headroom の上下限 | 4 GiB / 1 GiB | `login_headroom.py:31–32` | 一致 |
| check_docs の pin | `check_docs.py:618–628`、`test_check_docs.py:178`、`:9534`、`:9549` | 同じ行 (9534 / 9549 は test の docstring 行)、`run_tests` と `force-dispatch` の literal は 0 | 一致 |
| `conftest.py:1936–1948` | root の conftest.py | root に無い。実体は `orchestrator/tests/conftest.py` | 不一致 (所見 2a) |
| `run_tests.py:2682 → :1260` | 計算ノード側の pytest 実行 | 実経路は `:2689–2694` | 不一致 (所見 2b) |
| 正規化 (S01〜S10.log、s3-consult.md) | sha256 と bytes | 原本 11 本の sha256・bytes が一致。記載の空白を戻すと原本 bytes に一致 | 一致 |
| 正規化 (contract/ 7 file) | 記載なし (無変更と読める) | 各 1 byte 短い (末尾の空行を削除) | 不一致 (所見 9) |
| scripts.sha256 | 4 本 | 4 本とも一致 | 一致 |
| chain.log、table.md、その他の verbatim | 写し | chain.log と table.md は sha 一致。brief、parent-notes、s4-ruling、s2-plan、prompt ×2、origin-rulings、consult-a-out は cmp 一致 | 一致 |
| ff 先 `bea98c67d` との submodule 差 | 0 | `git diff --raw d99c556df bea98c67d` の 160000 行は 0 | 一致 |

## 訂正案

- **fragment:26 (must-fix)** →「工数: codex 子 = plan 1 + consult 1 (read-only、gpt-6-astra / medium)。段 6 review の codex 子は利用上限で出力 0 (不受理、解除表示 2026-09-26 19:35、再試行せず)。段 6 は Claude の read-only 子 1 本が代行。親の計算ノード job 10 本 (chain 2,887 秒)。」README §9 も同じ内容にする。
- **README:79** → 「`orchestrator/tests/conftest.py:1936–1948` の token 検査」。
- **README:71** → 「計算ノード側は `dispatch_compute.py:1880` で runner を 1 回起動する。runner は login 側が付けた `IZANAGI_TASK_RUN_AUTO_RECORD=0` (`run_tests.py:1299`、tests allowlist `dispatch_compute.py:123–126`) を受け、`run_tests.py:2682` で組んだ 1 つの pytest command を `:2691–2694` の `subprocess.call` で実行する。」
- **README:84** → 「計算ノード側の自動記録との二重記録は既存の marker (`AUTO_RECORD=0` の転送) で防がれている。要素ごとの env 複製でこれを保つことだけが要る。」
- **README:54・:60 (t2810)** → 表の注に「t2810 の focus-held-1 は held opt-in の `-k` 診断 (2 file、うち driftguards は変更 test ではない) で DW-O26 集合ではない。単独 1 file 走では兼ねられない。除くと t2810 は置換上限 1・残件 1〜2、計は置換上限 9・残件 11〜20」を足す。§0:13 と fragment の「最大 10」「10〜20」には「held 診断の置換を認める場合」と添えるか、9 / 11〜20 に改める。
- **README:12–13・§2 冒頭・fragment:42** →「上下限は計算ノード焦点 job を既存走とした値。親の login 実走・author 実走は標本外 (例: t2797 は各 fix 後に login で変更 test file を実走、同 wave README:90・:92)。これを含めると上限は増え、下限は下がりうる。」
- **README:146・fragment:19** → 追加する文: 「項 9 の 1 例目 (T-2737) は、D2194 項 8 の理由欄が挙げる entry 1695 (受入赤 3 件) そのもので、既裁定の根拠例だった。」
- **README:21** →「固定費の 88 % (1,066 秒、うち待ち 1,050 秒) は 1 本 (S07)」。**README:171・fragment:22** の「(M3 の) 費用の 88 %」は「固定費の 88 % (wall では 81 %)」に改める。
- **README:165 (M3 費用欄)** →「短い待ちなら 1 本の固定費 18〜26 秒、長い待ちに当たった 1 本 (S07) は固定費 1,066 秒 (待ち 1,050)。前回標本の ≥ 300 秒の待ちは 337〜1,020 秒」。
- **README:171–174 と fragment:22–23・:47** について:
  - 「その帯の頻度 (本試行 2 / 10 本。前回は 17 分前後が 3 / 27 本、≥ 300 秒が 12 / 27 本)」とする。
  - 蹴った帰結は「単独 job が長い待ちに当たるたびに、その分 (前回 337〜1,020 秒、本試行 1,050 秒) が wave に足される」とする。
  - README:130・fragment:23 は「前回診断の 17 分前後の待ち 3 本」とする。
  - 再提示の目安は「単独 job の待ち ≥ 300 秒 (または ≥ 1,000 秒) が 2 wave 以上で出たとき」のように閾値を明記する。
  - 見送り理由には「節約・費用のどちらも見積もっていない状態での判断」と添える。
- **README:148** →「別ノード・別時刻 (chain の先頭と末尾) の同一集合の差 (27 秒)」。
- **NORMALIZATION.md** に節を足す: 「contract/ の 7 file は末尾の空行 1 行 (1 byte) を削った。原本は job dir の verbatim/contract/」。
- **README:18・:97** に根拠を足す: `ls -ld /tmp/.git` の出力 (owner makiart、2026-09-07 18:07:20) と既知型 F457。
- **README:143** → 「」を外して要約にするか、決定文を逐語で引く。
- **README:126** →「どの手段でも残る分 = 単独 process の起動・collection・test (pytest 合計 120.42 秒〜RUN 128 秒)」。README:20 は「消せるのは最大この固定費」とする。
- **fragment:7** → title に [T-2843] を足す (任意)。**[T-2832]** の状態文の更新は任意。

## 判定

**NO-GO** (must-fix 1 件: fragment の工数行)。

must-fix は 1 行の書き換えで閉じる。§4 の実測値・派生値・node・正規化 (S*.log) はすべて原データと一致し、結論の骨格 (置換の上下限、固定費の分解、[T-2820] で項 9 を覆えること、R2 の見送り推奨) は維持できる。上の should 6 件 (所見 2〜7) は、再提示の数字の読まれ方を変えるので同時に直すことを勧める。

## 総括

- 必読資料はすべて読めた。
- 計測 log 10 本から 4 区間・wall・pytest・rc・node を再計算し、README §4 の表と派生値 (1,336 = 128 + 1,208、9 / 1,107 / 92、88 %、142 秒、120.42 秒、7.6 秒、2,887 秒、8 / 10、S09 − S10、S01 − S10) はすべて一致した。
- 正規化は S*.log 10 本と s3-consult.md が可逆で原本と一致した。contract/ 7 file だけは、末尾の空行削除が記録されていない。
- §2 の上下限は算術としては正しい。ただし次の 2 点が明示されていない。
  - t2810 の held 診断 job を置換可能な「集合走」に数えている (除くと 9 / 11〜20)。
  - 既存走を計算ノード job に限っている。
- §3 の引用は、plan 由来の 2 件が誤りである (`conftest.py` のパス、計算ノード側の `:1260`)。その帰結として、二重記録の防止を未見積りの費用に数えている点も過大である。その他の file:line・36 / 8 / 130 file・13,519 秒・74.8 %・47 entry・224.5 秒・74 node・git grep hit 0・受入赤 5 node は一致した。
- 項 9 の「既裁定 [T-2820] で覆える」は D2194 項 8 の発火条件・対象 2 file と一致する。加えて、T-2737 は D2194 項 8 自身の根拠例 (entry 1695) であり、これを README に書くべきである。
- 推奨の書き方には次の言い過ぎ・分母の混同がある。
  - 「費用の 88 %」
  - 長い待ちの帯の定義 (17 分半と ≥ 300 秒)
  - 「前回の長待ち 3 本」
  - 未定義な再提示の目安
- [T-2843] の完了は依頼条件を満たす。
- fragment の工数行は段 6 を codex が担ったと書いているが、codex 子は利用上限で失敗しており、これが唯一の must-fix である。
