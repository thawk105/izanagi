---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-22
wave: dev-wave-t2797-b5-effect-bundle
seq: 1
---

## {{D:b5-registered-launch-path}}. B-5 本走の投入経路は repo に最小実装する — driver の registered 出力、job body の受け渡し、launcher の逆順組 schedule と stage 投入、LLM 巡 tool と model 記録

**決定:** D2200 項 1 の段階認可のうち発効束の完成に要る実装として、本走を投入する経路を repo に置く。新しい gate・検査・台帳 field・report の変更は足さない。

- **driver:** `run-series` / `run-block-stock` に `--purpose {pilot,registered}` (既定 pilot)。registered は cohort `b5-registered-v1` と limits 第 2 文だけが変わり、pilot の header は不変。
  registered の探索系列に block と系列番号の拒否条件は足さない (report の既存検査と schedule の生成で足りる)。
- **job body:** `IZANAGI_S4_B5_PURPOSE` は任意 (未設定 = pilot)、pilot / registered 以外は既存の拒否、registered のときだけ driver へ `--purpose registered`。非 B-5 の既存経路と pilot の argv は不変。
- **launcher:** `registered-schedule` (純関数) と `registered` (block・stage 指定の dry-run / submit、job ごとの submit-tree、D2217 の W / W_stock を Decimal の切り上げで `elapstim_req` へ)。
  pilot 経路と walltime literal は不変。launcher 用の新しい process 起動目録 test は作らない。登録簿の launcher の説明文は今回は変えない (説明文まで完全一致で比較する hooks の golden を scope に入れないため、class は不変)。
- **schedule:** 逆順の組 A = {LRS, SRL}、B = {LSR, RSL}、C = {RLS, SLR} (L = llm、R = random、S = sweep-matched)。workload 番号 w と block b で除く組を e = (w + b − 1) mod 3 とし、
  残る 2 組 X・Y を block 内 4 系列へ X 第 1・Y 第 1・X 第 2・Y 第 2 の順に割り付ける。stage s は順序の s 番目の arm。block-stock は stage 2 (series = block)。
  各 workload で 6 順序が各 2 回、各 (block, stage) の LLM 系列はちょうど 4 本 (= D2216 の p)、各 (workload, block) で LLM と各 baseline の先後が 2 対ずつになる。
  次の stage は前 stage の全 job 終了後、次の block は前 block の全 job 終了から 1 時間以上後 (手順、runtime 検査なし)。
- **LLM 巡 tool:** `tools/b5_llm_round.py` は試走の親 glue (repo 外、sha256 8b29d95c…) の一般化で、prompt template を file 内に持つ。試走版からの変更は label・動作点・
  「同時刻対照」の訂正・欠測指標の表示 (0 や None ではなく「null (欠測)」)・path の引数化・知識射影の照合先の repo 内の写しに限る。`record-models` は会話記録の
  assistant 発話の model ID を全件集め `matches_expected` を記録する (拒否 gate ではない)。client の版は記録するだけで一致判定に入れない。

**理由:**
- 段 1 の実測で、driver は試走の cohort と purpose を header に固定し、launcher は試走 4 job の形しか受けず、prompt 生成器は試走専用の repo 外 script だった。事前登録 §12 は
  「実行 script・生成器の bytes と hash」「§10 の欠ける部品を満たす実装の所在」「全役割の prompt」を要求し、D2198 は 108 系列 launcher を見送り、D2216 が schedule・launcher を発効束の段へ送っていた。
- repo に置くのは、job dir の原本が消えた前例 (F1034) があり、本走は数日にわたり 36 本の親 session が同じ tool を使うため。§7.1 の配置性質は schedule 生成の test で確かめるのが最も安い。
- schedule を逆順組にしたのは、段 2 の案 (workload・block ごとに LLM の位置が一定) が workload 内で block と LLM の位置を完全に交絡させるため (段 3 相談)。

**却下した選択肢:**
- 実行 script を repo 外に置き hash で束縛する (B-8 の runner と同型) — 最強の形は「§12 が要るのは bytes と hash と所在だけで、test・変異・受入の対象が減る」。
  採らないのは、原本消失の前例、配置性質の test の置き場、既存 launcher の `_validate_job` が pilot 形しか受けず env 組立てを複製することになるため。
- role 定義 3 file の `model:` を完全 ID へ書き換えて model を固定する — 3 file の sha256 が role adapter・review ledger・test・図の provenance に束縛されている。
- producer 側に block と系列番号の拒否条件を足す、launcher 用に起動目録 test を新設する — 新しい検査面の追加で依頼の scope 外。

## {{D:b5-effect-bundle-draft}}. B-5 発効束の draft は D2202 と同型にし、LLM は起動構成で `claude-opus-5` に固定、不一致・A だけを消費する拒否・toolchain の扱いを事前に登録する。推奨は k = 3、総 wall 上限は試走の job Elapse 総和の 40 倍

**決定:** 事前登録 §12 の全項目を `output/insights/2026-09-22/t2797-effect-bundle/bundle/b5-effective-bundle.draft.json` (status draft) と同 README の表に固定する。
発効 commit は構成値を変えず status と effective 節 (承認情報) だけを足す。自己 hash は書かない。

1. **承認対象:** 本 wave の land commit と、承認に基づく発効 commit。校正 job と本走は発効 commit の固定 checkout で走らせる。列挙した hash が一致しても他の commit は承認の対象外。
   束は実装・検査器・環境契約など 31 file の sha256 と、束の data file 12 本の sha256 を持つ。
2. **LLM:** 親 session (1 系列 1 本、D2216) を `claude --model claude-opus-5 --settings <束の b5-parent-settings.json>` で起動する。settings は alias `opus` を `claude-opus-5` に対応づける
   `ANTHROPIC_DEFAULT_OPUS_MODEL` (API キーでも課金経路の切替でもない) と親の effort だけを持つ。role 定義は `model: opus` / `effort: high` のまま、Agent 起動時に model 引数を渡さず、
   `CLAUDE_CODE_SUBAGENT_MODEL`・`CLAUDE_CODE_EFFORT_LEVEL` が未設定であることを起動手順で確かめる。生成 parameter は client が指定口を持たず観測もできない (client 既定) と明記する。
3. **不一致時の処置:** role の記録のどれかで `matches_expected` が false なら、その原提案では proposal も reject も公開せず親 session を閉じる。系列は通常 handshake の期限切れ、
   walltime が先に不足すれば allocation-exhausted で終わり、どちらでも score は欠測。救済・再抽選しない。
4. **critic の実行条件:** 次の原提案の request が公開され、その評価番号が増えたときに、還流する直前の評価の critic だけを走らせる。最後の評価の後は走らせない
   (driver は最後の評価の後に handshake を待たず score へ進むので、そこでの不一致は欠測にできない)。
5. **A だけを消費する拒否:** planner / coder の出力が空・不正・検査落ちなら、親は候補を直さず role を呼び直さず reject する。子側の前処理拒否・Tier0 不通過では評価が出ず、同じ評価番号の次の request が来る。
6. **toolchain:** 本走の要求値 = 試走の計算ノードの観測値 (gcc / g++ 11.4.0-1ubuntu1~22.04.3、cmake 3.22.1、python3.10 sha256 d6bca2b8…)。compiler・cmake は prebuild receipt、python は同じ job の
   `compute-result.json` から照合し、異なる job はその系列 (または block-stock) を集計時に欠測扱いにする (手順であって機械 gate ではない)。
7. **rep 1 (D2200 項 1 (2) 2):** 試走 53 session で rep 1 を除いた 4 rep の中央値との差は最大 0.6960%、1% 以上 0 件、CV 5% 判定の変化 0 件なので、5 rep 構成を維持する
   (write-heavy 試走の範囲の感度分析で、warm-up 不要の一般証明ではない。D28 とは別の操作)。
8. **N1 (投入済み duplicate-skip の B 計上):** コードは変えない。fresh layout と 1 呼出し 1 genome の下では到達せず、到達しても report の invalid では検出されずに系列は score 欠測になる
   (初回 attempt なら B が 1 少なく記録、retry なら保持)。
9. **推奨値 (ユーザー裁定):** k = 3 (W = 63,777 s、W_stock = 16,341 s)、総 wall 上限 = 試走の job Elapse 総和 61,261 s の 40 倍 (2,450,440 s)。

**理由:**
- 事前登録 §4.1 は「可変 alias や既定モデルのまま発効させない」と定め、Claude Code の公式 docs は alias の解決先が時間とともに更新されると書く。起動構成で対応を固定し、巡ごとの記録で実際の ID を確かめる。
- 不一致・critic・A だけの拒否の扱いは、段 6 のレビュー 2 本と焦点再レビューが driver の実挙動との食い違いを指摘した点を、driver に待機や gate を足さずに手順で閉じたもの。
- k = 3 は換算の中心 (read-heavy の LLM 系列 ≈ 24,500 s) では余るが、旧単価のストレス例と A = 30 の使い切りを重ねた試算 (63,312 s、各機会 780 s の仮定) まで覆う。
  総 wall の分母は事前登録 §11 の「試走の実測所要への倍率」に最も忠実な raw の job Elapse 総和とし、session 比例の外挿値とは混ぜない。

**却下した選択肢:**
- alias 起動のまま観測 ID を事後に記録するだけ — §4.1 を満たさない (段 3 相談 2 本)。
- 最後の critic を待つ driver の待機、model 記録を読む report、台帳の不一致 field — critic の実行条件を手順で限れば不要で、新しい gate・台帳の追加になる。
- session 定義を warm-up rep 付きに変える — 登録した感度基準を満たさない。
- k = 2 — 換算の中心では足りるが、ストレス例と A = 30 の使い切りで不足しうる。walltime の不足は n や正しさ条件を下げる理由にしない (§11)。
