# 段 4 裁定 — [T-2273] 受入 shard-0 候補 (a) 前倒しの写しの効果診断

裁定時刻: 2026-09-26 20:17 JST (file mtime。段 3 相談 A の .done は 20:14:45。相談 `codex/s3-consult-{a,b}-out.md` 受領後、両方 check_codex_output rc=0、両方「修正後 GO」)。裁定 inbox: 最新 `2026-09-26-rulings-full36-verdicts.md` (19:12、wave 開始前、D2249 として台帳済み) で新着なし。local main は `265cce13c` のまま。

## 1. 所見の裁定

| ID | 裁定 | 処置 |
|---|---|---|
| A1 (P1 の原因断定) | real・採用 | pre 倍増の原因は仮説 (bytecode / rewrite cache 冷) に下げる。温めは「比較条件を実受入へ近づける試み」とし、原因の確定とは書かない |
| A2 (温めが再現しないもの) | real・採用 | 温め前後の HEAD・status 行数を記録。login collection の並行、plugin import、xdist、早期 memo は温めで再現しないと限界に明記。A の pre は有効性とは別の外挿条件 |
| B4 (温め必須化の費用) | 一部 real | 温めは job 1 の前に login で 1 回だけ (計算ノード費用 0)。計算ノード worker は bytecode を書かない (`PYTHONDONTWRITEBYTECODE=1`) ので 3 job を通じて同じ温状態。両条件に同じ |
| A3 (写しの寿命) | real・採用 | 写しは worker の共有置き場 (`_T080SharedBases.parent`) に置かず、controller 所有の別 dir `<tempfile.gettempdir()>/t2273-precopy-<identity>` に置く。identity は `test_s8b_oracle_driver.py:980–984` と同じ `sha256(json.dumps([str(ROOT), testrunuid]))`。controller が `pytest_unconfigure` で thread を join してから削除 |
| A4 (時刻記録) | real・採用 | 両条件で controller の configure_node 最初の呼出し、写しの開始・完成、早期 memo の発火と所要 (取れる範囲)、各 worker の collection 完了、最初の builder 開始を記録 |
| A5 (複製結果の同一性) | real・採用 (形を変更) | 両条件とも builder の複製呼出しの直後に `root/output` の stat digest (相対 path・size・mode・mtime_ns) と件数を採る (別 span、同じ方法)。bytes の hash は 910 MB × 8 本で W を膨らませるので採らない (copy2 は同じ source から mtime を引き継ぐので stat digest を代理とし、限界に書く)。可視集合 digest は A では実関数の戻り値、P では写し生成時の戻り値 |
| A6 (memo 超過の帰属) | real・採用 | (P2') を撤回。早期 memo 待ち超過の走は条件別件数を残して対から外す。P 固有の干渉と書くのは memo 所要・資源標本・反復で裏付けられたときだけ |
| A7 / B1 (3 対と判定語) | real・採用 | 有効 3 対は維持。基準は「診断から (a) 実装へ進むための事前基準」で、未達は「この基準では確認できない」と書く (効果ゼロと断定しない)。順序別対差を併記 (P は後走 2 回で有利側の残差がありうる) |
| A8 / B2 (発行内訳) | 両方 real。A8 を採用 | 発行 child の code を**両条件に同じ計測用 code 変換**で包む (「同じ引数の観測 wrapper」とは呼ばない)。import・loader・`sys.path`・閉包検査と stdout の document JSON は保ち、計器の出力は stderr の識別行 1 行。(b) の判断に使うのは (a) が乏しい場合だけ、効く場合は「(a) 後の次の律速」として読む。別 job を足さずに済むので費用も下がる |
| A9 / B7 (引用) | real・採用 | 実受入の pre は標本ごとに書く (前回 3 対 64.3〜65.9、T-2825 62.6〜64.4)。`_start_early_memo_job` の定義行は実測で `conftest.py:2388` (B7 の 2386 は誤り、A9 が正しい) |
| B3 (5 分判定) | real・採用 | replica の絶対値を実受入の秒数へ換算しない。5 分達成は (a) を実装したときに実受入で別判定。本 wave の結論は対差・対率・O_max の変化と「次の律速」 |
| B5 (smoke) | real・採用 | smoke は job 1 だけ、A 形と P 形の両方で 1 回ずつ |
| B6 (費用の停止点) | real・採用 | 各投入の前に「既消費の計算ノード Elapse + 残る必須 (本走・受入全走) の見積り」を更新し、合計が 7,200 秒以上になる見込みなら投入せずユーザー確認 |

## 2. plan v2 (段 5 の Codex author 1 単位)

出発点 = 第 4 回 probe `7f38ac7fd` の `tools/t2273_replica_{runner,plugin,analyze}.py`。子 worktree で書き、親が job dir `probe/` へ退避。repo には逐語 .md のみ。

- **runner:** 新 mode `ab` (`--order AP|PA`、`--smoke {none,both}`)。smoke は `-k shared_base_builds_real_builder_once_across_processes -n 2` を A 形・P 形で各 1 回。本走は既存 `replica()` と同じ argv・guard で条件 A (観測のみ) と P (env `T2273_PRECOPY=1`) を順に。staging・X は使わない (既存 mode は残してよい)。温めは runner の外 (親が login で実行)。
- **plugin (両条件共通):** 既存 span をすべて維持。追加 = 複製直後の stat digest span (`copy.digest`)、発行 child の計測用 code 変換 (phase: import 群・runtime source 検査・basis rev-parse・draft_receipt・validate_draft・finalize_receipt・git add (+extra)・git commit・verify_receipt・gate_check。壁時間と `time.process_time` と子 process の CPU)、timeline event (controller configure_node 初回、早期 memo の開始・終了が取れれば、worker collection 完了、builder 開始)。発行 child の識別は builder の child 文字列だけ (`:2527` の別 child は対象外)。
- **plugin (P のみ):** controller 側 `pytest_configure_node` 初回で非 daemon thread を起こし、実関数 `_copy_git_visible_output(ROOT, <snapshot>/output)` を 1 回。成功で `ready.json` (可視集合 digest・件数・開始/終了 epoch・CPU)、失敗で `failed.json`。`pytest_unconfigure` で join → 削除。worker の builder の複製呼出し (source_root が実 repo root のときだけ) を「ready を待つ (待ち span、上限は walltime 内で有限、超過・failed は例外で P 無効) → `shutil.copytree(<snapshot>/output, destination)` → 写しの可視集合を返す」に差し替え。fallback で直接複製しない。
- **analyzer:** job ごとの A/P 対 + 3 job の集計。事前登録の判定量と有効性を機械出力。

## 3. 事前登録 (本走を見る前に固定)

1. **有効な対:** 両走 rc 0、outcome 集合一致、builder の key ごとの `root/output` stat digest と件数が A と P で一致、P の可視集合 digest が A の builder の実関数戻り値の digest と一致、clean (前後の status 行数 0、HEAD 不変)、others 0、record-error 0、P の ready marker あり・failed なし。早期 memo 待ち超過の走は対から外し条件別件数を記録 (取り直しは費用規則の内)。
2. **判定量:** Δ_i = W_0(A) − W_0(P)、r_i = Δ_i / W_0(A)。併記: O_max・L・pre・post の対差、条件別中央値、順序別の対差、写しの開始・完成時刻と最初の builder 開始の差、builder の写し待ち、builder の構築時間 (key 別)、発行の phase 内訳。
3. **(a) へ進む基準:** 有効 3 対すべて Δ_i > 0 ∧ r_i の中央値 ≥ 10 %。満たせば「(a) の実装 wave を推奨 (実受入の隣接対で 5 分を別判定)」+ P での次の律速。満たさなければ「この基準では (a) の効果を確認できない」とし、発行の phase 内訳から (b) の対象を名指しする。
4. **5 分:** replica の絶対値から実受入の達成を言わない。P の W_0 と 300 秒の関係は参考値として書く。
5. **pre:** A の pre が 55〜80 秒の外なら外れと明記して読む (無効にしない)。

## 4. 計算量と停止点

単価 = 第 4 回 R2'' の job Elapse 1,046 秒 (smoke + 2 走 + staging)。本 wave の見積り: job 1 (smoke 2 + 2 走) ≈ 1,150 秒、job 2・3 (2 走) ≈ 1,000 秒 × 2、受入全走 ≈ 900 秒 → 計 ≈ 4,050 秒 ≈ 1.13 node 時間。各投入の前に既消費 + 残りを更新し、7,200 秒以上の見込みで止めてユーザー確認。

## 5. 変異・受入

repo の実装面差分ゼロ (probe は repo 外) なので変異 matrix は免除 (DW-S04)。受入全走は記録前に 1 回。段 6 は probe への独立レビュー 2 本 (1 本は過剰・削除レンズ)。
