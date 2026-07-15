# 性能先行スクリーニング (bench-first screening) の設計 v2 (2026-07-14)

**契機:** ユーザー発案 (2026-07-14 協議)「性能で評価して価値が弱ければ正しさ検査もしない —
安い方の検査でダメとすぐ分かるならそれでよい」。WAL 実測でコスト非対称を確認済み:
**verify (legacy+S2) ≈ 120〜250 秒/variant、bench ≈ 18 秒/variant、比 ≈ 6.6〜13.7 倍**
(高競合 1M/48thread、campaign `p3-s8a-trigger-sweep-balanced-sweep-c2d838b8` の committed 8
variant をレビューが独立再計算。v1 の 140〜267 秒 / 8〜15 倍は集計起点の取り方による過大で訂正)。
verify が評価時間の 6〜7 割を占める。roadmap §2「low-fidelity proxy でスクリーニング」構想の
具体化にあたる。

**分類: 探索効率の機構設計。設計フェーズは計測ゼロ。設計 v2 は方針採用済み (2026-07-15、D58)。
当初の「実装未着手」は同日付で訂正し、監査 must-fix 対応込みで実装済み、positive control 1 点も
実走済み。初回 ablation は初回採用 campaign で行う。事前登録の凍結内容に触れない。**

**版歴: v1 (2026-07-14) → 3 レンズ敵対レビュー (§9) → v2 (must-fix 5 系統・should-fix 7 系統
全反映)。**

---

## 1. 目的と非目的

- **目的:** 偵察 sweep・8b 並走のような**点数の多い探索的計測**で、明白に劣る variant の
  verify (支配的コスト) を省き、機械時間を削減する。
- **非目的:** (i) 正しさゲートの緩和 — **採用 (COMMIT/certified) には必ず verify 全構成を通す**。
  screening は「採用しないものを早く決める」だけ。(ii) 検証相・事前登録済み手順 (S-1) への導入 —
  凍結済み手順は触らない。(iii) LLM ループの高速化 — 律速はセッション運営 (機械時間の 10〜20 倍)
  であり本機構の対象外 (worklog 07-14 (1) の診断)。

## 2. 現行構造 (pipeline.py 実コード)

`pipeline.evaluate()` (orchestrator/campaign/pipeline.py:164-451): src_token 確定 → build
(trace+perf 両ビルド) → verify (legacy → extra_correctness=S2 等を順に全部、1 つでも落ちれば
abort) → `res.certified = True` → bench (bench_lock + admission + remeasure_until_stable) →
STAGE_COMMIT (fitness_tps + verify_configs)。abort は fitness なしの terminal。COMMIT を書く
経路は evaluate() と guided.py:88 (後者は replay 専用の certified landscape 再生であり評価
ゲートの迂回ではない — live variant への再利用は常設安全規定で禁止済み)。`do_bench=False`
(配線テスト用、certified のみ commit) は既存。

**現行で厳格に成立している暗黙の不変条件 (レビューで発見):** 全 abort が STAGE_BENCH_DONE の
記録より前で return するため、**「STAGE_BENCH_DONE が存在する ⟹ その variant は certified で
COMMIT に到達する」**。screening はこの不変条件を初めて破る — 全 STAGE_BENCH_DONE 読み手の
監査が実装の gate 条件 (§3.5)。

## 3. 設計 (最小案)

### 3.1 順序の opt-in 切り替え

`evaluate()` に省略可能引数 `screening: Optional[ScreeningConfig] = None` を追加。
既定 None = 現行と完全互換 (規律 5)。`screening` 指定かつ `do_bench=False` は **ValueError で
即拒否** (fails-closed — 床判定に bench が必須のため。組合せはテスト行列に含める)。指定時のフロー:

```
src_token 確定 → build (trace+perf 両ビルド、現行のまま)
  → bench (現行の bench 段をそのまま前倒し: bench_lock + admission + remeasure)
      ├─ 測定不能/CV 不能 → 現行と同じ abort (bench-no-throughput / bench-cv-undefined)
      ├─ unstable (CV 不収束) → 棄却せず verify へ (fails-safe)
      ├─ median < baseline_tps × (1 − k·floor) → STAGE_ABORT reason="screen-slower-than-floor"
      │    (fitness を付けない。verify はスキップ。k は §3.2)
      ├─ 床際帯 (baseline×(1−k·floor) ≤ median < baseline×(1−floor)) → 棄却せず verify へ
      └─ それ以外 → verify (現行どおり legacy + extra 全部)
            ├─ 落ちる → 現行の verify-red abort (構造化 anomaly、規律 3)
            └─ 全通過 → STAGE_COMMIT (fitness = 既測の bench 値。bench 再実行なし)
```

- `ScreeningConfig = {baseline_tps: float, baseline_ref: str, baseline_measured_at: float,
  floor: float, k: float = 1.5}` — baseline_tps は同一 campaign 系列で実測済みの基準点
  (stock / ident_all 等) の median、floor は**対象別 between-run floor** (within-run CV の
  流用禁止、D19)、baseline_ref は基準点の WAL 参照 (variant_id)、baseline_measured_at は
  基準点測定時刻 (§3.2 の再アンカー判定に使う)。
- bench は screening 時も**本構成そのまま** (reps・extime・admission・remeasure 全部現行) —
  軽量ベンチ (low-fidelity) 化は将来拡張に分離 (規律 5)。COMMIT が使う fitness は screening
  段で測った値であり、「certified fitness = 本構成 bench の median」の意味は不変 (verify は
  tr.binary・bench は pf.binary の別ビルド別 run で元々独立 — 順序交換は fitness の定義を変え
  ない。レビュー裏取り済み)。順序による測定窓の微差 (verify を挟まない分の熱状態の違い) は
  初回 ablation (§6) で「同一 genome の on/off fitness が floor 内で一致」を明示確認する。

### 3.2 棄却の統計規定 (保守側 — v2 で全面改訂)

v1 の「floor を超えて劣位なら棄却」は 2 レンズが独立に must-fix: **D19 は floor〜1.5×floor
(near_floor 帯) を「単一 run で生死を確定してはいけない・cross-run 裏取り要」と規定しており、
そこを単一測定の terminal abort で不可逆棄却するのは矛盾** (P2-5「自信ある早期棄却の負債」の
再導入)。v2 の規定:

- **棄却条件は `median < baseline_tps × (1 − k·floor)`、k ≥ 1.5 (既定 1.5 = D19 near_floor
  上端)。** 床際帯 (floor〜k·floor の劣位)・床内・優位は**すべて生かして verify へ**。
- **偽棄却率は floor 較正精度だけに帰着しない** — (i) baseline 側の 1 セッション誤差、
  (ii) variant 側の between-run ドリフト (D19 実測: high-abort genome ほど大きい。unstable
  安全弁は within-run しか捕えない)、(iii) 機械の経時ドリフト、の合成。対策:
  - **high-abort クラスは screening の対象外** (bench の leading indicators で abort 率が
    基準比 2 倍超なら床判定せず verify へ — D50 の high-abort 判定不能分離と同じ閾値系)。
    k を上げる代替も可だが、既定は「対象外」(fails-safe)。
  - **baseline の再アンカー:** variant 測定と baseline 測定の時間差が閾値 (既定 30 分 —
    参照 campaign の全長 ≈36 分で系統ドリフトを跨がない粒度) を超えたら、基準点を再測して
    baseline_tps / baseline_measured_at を更新してから screening を続ける (driver の責務)。
    再測不能なら以後の screening を無効化して全点 verify へ (fails-safe)。
- **floor 未較正の動作点では screening を使わない** (ScreeningConfig を渡さない)。floor の
  出所 (対象別 between-run floor の実測 JSON) と k・baseline 再アンカー履歴を driver が
  provenance に記録する。

### 3.3 探索シグナルの隔離 (reward hack 防壁)

現行設計は「探索 (whiteboard / planner / critic) が見る fitness はすべて certified」を暗黙に
保証している (レビュー裏取り: digest.load_workload と replay.load_landscape は STAGE_COMMIT
で gate しており、BENCH_DONE のみの半評価点は構造的に排除される)。screening 導入後もこれを
**明文の不変条件に昇格**する:

- screen_reject された variant の **uncertified median を探索側の射影に載せない**。実装規定
  (レビュー should-fix 反映):
  - abort payload の数値は **`payload["screen"]` ネスト下**に置く (`{median_tps, cv,
    baseline_tps, baseline_ref, floor, k, margin}`)。genome 付き render 用の新 loader
    `load_screen_rejections` は**このネストを読まない** (reason コード + genome のみ抽出)。
  - 既存 `load_liveness_rejections` の `other` バケットに落とすと「infra 失敗多発」に見える
    誤分類 + genome 消失 (digest.py:268-270) — **専用 loader + 「正常棄却」カテゴリの render
    節**を digest に追加する (infra 失敗と別掲)。
  - screen-reject の payload に `verify` キーを**絶対に載せない** (load_rejections が verify-red
    と誤認しない非交差性。テストで固定)。
  - テストで「render 出力に median_tps/cv/baseline_tps が現れない」ことを**否定 assert** で固定。
- 「速いが壊れている」variant は screening を**通過**し直後の verify で落ちる = 現行と同じ
  verify-red 経路で構造化 anomaly が探索に返る。screening が落とすのは劣位方向のみなので、
  reward hack (正しさを壊して速く見せる) が screening 段で利得を得る経路は無い (レビュー
  refuted で確認)。
- COMMIT 文は verify ループ通過後にのみ存在するコード形状を維持し、**「evaluate() 内で
  screening 経路でも verify なし COMMIT が構文上存在しない」**をテストで固定する (guided.py の
  replay 専用 COMMIT は対象外と明記)。

### 3.4 規律との整合

- **規律 2 (正しさゲート):** 不変。ゲートに到達する母集団を「採用候補」に絞るだけ。
- **規律 3 (正しさシグナルの後付け禁止):** 採用候補には毎 iteration verify が走り構造化
  anomaly が返る。screen_reject 分の verify 省略は roadmap §3.2 開発相の「確率的な見逃し許容」
  の範囲内。ただし診断機会の減損は既知限界 §8。
- **規律 4:** screening の bench は現行と同一の admission・排他・remeasure 下。計測の質は
  変えない。bench_lock は現行も verify(S2) と bench が**別々の逐次セクション** (非ネスト、
  各々 admission 再チェック) であり、順序交換で構造は変わらない (レビュー裏取り)。
- **D25 (再評価冪等):** screen_reject は terminal abort (replay.py:110-112 / loop.py の
  retryable は identity-error のみ — レビュー裏取りで整合確認済み)。baseline や k を変えた
  探索は campaign を分ける。**screening 設定の campaign-id への織り込みは omit-when-None**:
  screening 有効時のみ search_config に screening キー (baseline_ref/floor/k) を追加し、
  None のときは**キー自体を出さない** (null フィールド化すると既存・歴史的 campaign の id が
  全移動して replay/report が孤立する — D19 追記の孤立問題と同型)。floor/k の float は文字列
  表現を固定 (丸め揺れで hash が割れないように)。回帰テストで「screening=None の campaign-id
  が導入前と一致」「floor/k を変えると id が変わる」の両方を固定。

### 3.5 WAL スキーマと consumer 波及 (v2 で gate 条件に昇格)

- STAGE_BENCH_DONE: 現行スキーマ + `"screening": true`。
- STAGE_ABORT: 新 reason `"screen-slower-than-floor"`、数値は `payload["screen"]` ネスト (3.3)。
- STAGE_COMMIT: 現行スキーマ + `"screened": true`。
- キー追加自体は後方互換 (読み手は全て .get() アクセス — レビュー裏取り)。
- **gate 条件: 「STAGE_BENCH_DONE ⟹ certified」不変条件の崩壊 (§2) に対する全読み手の監査。**
  レビューが特定した具体的な取り残し (F2/D25 型):
  - `s8a_trigger_sweep.py` の `_load_rows` (:377,:386) は BENCH_DONE を無条件に読み、report
    (:444-457) が **screen-reject の uncertified median を certified 点と同一テーブルに印字
    してしまう** (D48 firewall「診断数値を insight に入れない」への違反経路。E 段起草への
    記憶汚染面)。同型が `s6_sort_sweep.py` (:331-345)。
  - **修正: _load_rows は commit が在る row のみ median/cv/leading_indicators を格納。report
    テーブルは certified 行のみ数値を描画し、screen-reject は「reason のみ・数値なし」の別節。
    sweep の集計 (レンジ・min・best vs 基準) が生存点限定になる事実を出力に明記。**
  - テスト: screen-reject 行の median が report 出力に現れないことを否定 assert で固定。

## 4. 適用範囲 (opt-in の宛先)

| 用途 | screening | 根拠 |
|---|---|---|
| 偵察 sweep (s8a_trigger_sweep 型、事前登録外) | **使う** | 点数が多く効果が出る。ただし偵察の目的が「floor 超地形の有無 (生死二値)」に限られ下端の magnitude を要さない場合に限定 (レンジ集計は生存点限定になるため) |
| 8b 並走 campaign (将来) | 使う | 3 workload × grid で点数最多 |
| 基準点再計測・floor 再実測 | **使わない** | 基準点は全点フル評価が必要 (screening の前提を作る側) |
| S-1 検証相 (事前登録済み) | **使わない** | 凍結手順に触れない |
| LLM ループ (F 段型) | 当面使わない | 律速がセッション運営 + 挙動変更リスク |

## 5. 実装計画 (方針採用済み・当初未着手)

**2026-07-15 状態訂正:** 以下 1〜6 は実装・consumer 監査・監査 must-fix 対応・positive control
まで完了。7 の ablation は初回採用 campaign で実施予定。

1. bench 段 (~80 行、pipeline.py:363-441) を `_run_bench()` ヘルパに切り出し (挙動不変の
   refactor)。注意 2 点 (レビュー): (a) ycsb_tuple_num ガード (:366-370) の移設を含める、
   (b) bench 段は res.certified を読まないので前倒しで挙動不変 — これを既存テスト + 回帰で固定
2. `ScreeningConfig` + evaluate() の順序分岐 + do_bench=False 併用の ValueError + WAL スキーマ
3. digest: `load_screen_rejections` (genome + reason のみ、screen ネスト非読取) + 正常棄却
   カテゴリの render 節
4. **consumer 監査 (gate 条件、§3.5):** s8a_trigger_sweep / s6_sort_sweep の _load_rows +
   report 修正。他の STAGE_BENCH_DONE 読み手を grep で全数列挙して波及確認
5. テスト: (i) evaluate() 内で verify なし COMMIT が構文上不可能なこと、(ii) 閾値境界
   (k·floor 超劣位=棄却 / 床際帯=通過 / 床内=通過 / unstable=通過 / high-abort=通過)、
   (iii) 既定 (screening=None) の完全回帰 + campaign-id 不変、(iv) floor/k 変更で campaign-id
   が変わる、(v) screening×do_bench=False の ValueError、(vi) render 出力に uncertified 数値が
   現れない否定 assert、(vii) screen-reject payload の verify キー非交差。
   **実出力サンプルをテスト母集団に含める (F15 教訓)** — 初回実走 1 点の WAL からの回帰を追加
   - **2026-07-15 完了:** campaign `backoff-sweep-silo-read-heavy-sweep-6f169f90` の実 WAL
     (baseline の build_start〜COMMIT と対照の build_start〜ABORT) を fixture に固定し、critic、
     sweep report gate、replay、P2-2 report、backoff consumer の回帰へ通した。
6. **positive control (F9 教訓):** 基準点より k·floor を明確に超えて遅い既知 variant で
   screen_reject の発火を実走 1 点で確認 (計測窓を使う)
   - **2026-07-15 実走完了:** ccbench pin `d706650`、read-heavy (skew 0.9 / rr95 / rmw 0) の
     campaign `backoff-sweep-silo-read-heavy-sweep-6f169f90`。baseline `84319b1127a6`
     (BACKOFF_FIXED=-1, BACK_OFF=0) は median 8,470,959 tps、CV 0.28%、legacy verify は
     serializable (534,083 commits / 222,242 aborts / anomaly 0) で COMMIT。対照 `610e879931c4`
     (BACKOFF_FIXED=100, BACK_OFF=1) は median 1,912,074 tps、CV 0.93%、abort_rate 0.0457 で、
     rr95 の between-run 実較正値 `floor=0.0010979692594382789` と `k=1.5` に対し margin −77.4%。
     `screen-slower-than-floor` が発火し、verify 未実行の uncertified reject となった。
7. **ablation (初回採用 campaign で 1 回):** 基準は v1 の「生き残り集合の一致」から置換
   (screening の目的が集合縮小である以上、集合等値は自己矛盾 — レビュー指摘):
   (i) **誤棄却ゼロ** = screening 却下集合 ⊆ off 側で確認された明白劣位 (baseline×(1−k·floor)
   未満) 集合、(ii) **結論不変** = floor 超地形の有無の判定が on/off で一致、(iii) 総機械時間の
   削減率実測、(iv) 同一 genome の on/off fitness が floor 内で一致 (§3.1 の測定窓微差の確認)

## 6. 却下した代替案

- **(i) 正しさ検査を先に軽量化する (verify 側の圧縮):** S2 verify の規模は D36 gate 3 点の
  実測で確定済み — 縮めると赤検出力の根拠が崩れる。
- **(ii) trace ビルドの遅延 (screening 通過後にビルド):** 見送り。理由の訂正 (レビュー):
  sweep は別 genome 続きで cache miss が常態 (参照 campaign で 10 件中 9 件 fresh) のため
  「buildcache が効くから利得薄」は誤り — 正しくは**絶対額が小さい** (棄却 variant あたり
  ~20 秒 ≪ verify 120〜250 秒) ため優先しない。点数が桁で増えたら再考。
- **(iii) 軽量ベンチ (reps 減・extime 短縮) での screening:** 床判定の統計的根拠 (between-run
  floor は本構成で較正) が使えなくなる。規律 5 で分離。
- **(iv) screen_reject を非 terminal にする:** 冪等性 (D13/D25) と衝突。campaign 分離で解決。

## 7. 効果の見積もり (v2 で棄却率仮定を撤回)

- v1 の「棄却率 50%」は未導出だった (レビュー指摘: D50 実 sweep では勝ち点は通過・退化点は
  high-abort で bench-abort 系 = screen-slower とは別経路・床内は通過 — clean な screen-reject
  は少数の可能性)。**棄却率 p は baseline×(1−k·floor) と実 fitness 分布に依存し事前に確定
  できない**。帯で提示: verify ≈120〜250 秒/点として、10 点 sweep で p=0.1 → 2〜4 分、
  p=0.3 → 6〜13 分、p=0.5 → 10〜21 分の節約。8b (3 workload × 10 点) はその 3 倍。
- 損益分岐 (verify-red 率): f = V/(V+B) = 87〜93% (V の実測レンジ対応)。適用先の機械列挙
  sweep は D50 実績 anomaly 0 なので実害なし。
- 初回 ablation (§5-7) で実測の削減率を記録し、この見積もりを実データで置換する。

## 8. 既知限界 (主張時に限定表現)

- screen_reject された variant の「遅さの原因が正しさ違反」という診断機会は失われる (規律 3 の
  探索フィードバックの部分的減少)。発火条件: screen_reject 率が異常に高い campaign。対策:
  driver が screen_reject 率を digest に出し、閾値超で「screening を切って 1 点 verify する」
  提案を人間に出す (機械化はしない、規律 5)。
- 床判定は点比較 (median vs baseline median) であり分布比較 (§3.6(4)) の簡約。偽棄却率は
  floor 較正精度・baseline 1 セッション誤差・variant 側 between-run ドリフト・経時ドリフトの
  **合成** (v1 の「floor 較正精度だけ」は誤り — レビュー must-fix)。k·floor 化 + high-abort
  対象外 + baseline 再アンカーで保守側に倒すが、偽棄却ゼロの保証はない (だから初回 ablation で
  誤棄却ゼロを実測確認する)。
- 順序変更は「壊れた variant の bench に計測窓を ~18 秒使う」ことを意味する (現行は verify が
  先に落とすため 0 秒)。verify-red 率が高い局面 (f > 87〜93%) では逆に高くつく — 適用先を
  機械列挙 sweep に限定する根拠。
- sweep の記述統計 (レンジ・min) は生存点限定になる — 偵察の結論を「floor 超地形の有無」に
  限る運用 (§4) とセットでのみ健全。

## 9. レビュー (3 レンズ敵対レビュー、2026-07-14)

独立コンテキスト read-only (Explore 型)、実コード・WAL 裏取り必須で実施 (workflow
`wf_754084df-1cf`、22.0 万 subagent トークン)。**3 レンズとも adopt-with-conditions**:

- **正しさゲート・規律整合レンズ:** must 1 / should 3 / nit 2 / refuted 5。must = near_floor
  帯の不可逆棄却 (D19 矛盾)。refuted に「verify なし COMMIT の抜け道」「reward hack 利得経路」
  「探索射影への漏洩 (critic 経路)」「新規の信頼境界侵犯」— 設計の核は実コード裏取りで生存。
- **統計・測定整合レンズ:** must 3 / should 4 / nit 3 / refuted 3。must = near_floor (独立
  収束) / 偽棄却率の合成要因無視 / baseline 経時ドリフトの系統的偽棄却。実測数値の訂正
  (120〜250 秒 / 6.6〜13.7 倍)。refuted に「screening 済み campaign の headline 混入」(勝ち側は
  screening を通過するため生死シグナル保存)。
- **実効性・実装整合レンズ:** must 1 / should 4 / nit 3 / refuted 5。must = bench_done ⟹
  certified 不変条件の崩壊で s8a/s6 report が uncertified median を印字 (consumer 取り残し
  F2/D25 型)。refuted に「bench_lock 逐次性の崩壊」「WAL スキーマ後方互換の破壊」「replay での
  再評価」— いずれも実コードで反証。

**must-fix 5 系統・should-fix 7 系統は v2 に全反映** (§3.1 fails-closed 組合せ、§3.2 全面改訂、
§3.3 ネスト隔離 + 専用 loader、§3.4 omit-when-None、§3.5 consumer gate 条件、§5 テスト拡充 +
ablation 基準置換、§6 却下理由訂正、§7 見積もり撤回、§8 限界の訂正)。nits も §2 (guided.py の
訂正)・§5-1 (切り出し注意) 等に反映。

## 裁定欄 (ユーザー)

- **設計 v2 の採用:** 採用 (2026-07-15、D58)。偵察 sweep / 8b の opt-in に限定して将来実装する。
- **実装状態:** 未着手。本裁定は実装方針を決めたもので、このセッションの実装・計測着手を指示しない。
  D58 の範囲内で着手するときの再承認は不要だが、適用先拡大・棄却規則変更・correctness gate 変更は
  別裁定を要する。
- **実装状態の 2026-07-15 訂正:** 上記は裁定時点の履歴。監査 must-fix 対応込みで実装し、positive
  control と実 WAL fixture 回帰まで完了。ablation は初回採用 campaign で §5-7 に従って実施する。
- **逐次停止:** 本裁定の対象外。Best-of-∞ 型の計測反復 / verify seed 数の逐次停止は別設計・別裁定とする。
