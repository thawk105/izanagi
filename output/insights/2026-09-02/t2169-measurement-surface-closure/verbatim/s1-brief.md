# 段 1 brief — [T-2169] 正しさ検証を経ない測定面の repo 全体の閉包確認

## scope

repo 全体で「正しさ検証 (verifier) を通さずに性能数値を作れる経路」を実測で数え上げ、一覧にする。
各経路について、その数値が official report / selector / 順位 / headline へ到達しうるかと、
到達を実際に止めている機構 (または止めていないこと) を file:line で名指す。

**本 wave の成果物は閉包の一覧と評価まで。** 新しい gate・検査・台帳・一般化は作らない。
実在する正しさ欠陥が見つかった場合だけ、その修正を同じ変更単位に含める。見つからなければ
実装差分 0 で返す。

## 確定済みユーザー裁定 (本 wave 内で覆さない)

- 閉包の実測と一覧化までとする。新しい防壁は作らない。
- 実在する正しさ欠陥が見つかった場合だけ修正を同じ単位に含める。無ければ実装差分 0。
- 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- 実装面は Codex `role=author` が書く (D95)。親は実装面を直接編集しない。
- 規律 2 を緩めない。anomaly を検出した variant の即 reject は不変。

## 起票元の逐語 (docs/archive/worklog-phase3-0902-1170.md:424-430)

段 6 の 2 レンズが独立に挙げた 3 点:

1. `measure_point_floor()` の直接呼出しは admission を通らない
2. floor CLI は admission 通過後 `trace=False` build を測るだけで verifier を実行しない
3. screening は verifier より先に bench を実行できる

同 stub は「本 wave が作った欠陥ではなく既存の状態」「official commit writer は certified 判定後に
閉じている」とも書いている。

## 既存被覆 (純増の確認)

- **D1360**: stock 専用計測経路は certified な cross-protocol 比較を成立させない。得られるのは
  正しさ未検証の性能観測であり、公式 report・selector・比較表・順位・headline のいずれにも入れない。
- **D1373**: between-run floor の生成を許す protocol は、CCBench source の trace hook 証拠へ束縛する。
  「この判定が証明しないこと」に「verifier が通ること」を逐語で含む。
- **D58**: bench-first screening v2。bench を verify より先行させることは**既裁定の設計**であり、
  適用先は事前登録外の偵察 sweep と 8b campaign の opt-in に限定、不変条件は
  「certified / COMMIT へ到達する候補は従来どおり全 verify 構成を通す」
  「screen-reject の未認証性能値を探索射影や正式結果へ混入させない」。
- 純増部分: **上記 3 決定はいずれも個別の経路を裁定しているが、repo 全体で何本あるかの
  数え上げは存在しない。** 「正しさ検証を経ない測定面」「未検証性能観測」の語で docs 全体を
  検索して該当するのは起票元 stub と D1360 の 2 箇所だけで、閉包一覧の先行成果物はない。

## 不変条件

- 規律 1: 正しさ検証は trace-enabled build、性能計測は trace-disabled build。別ビルド・別 run。
  この分離自体は正しく、「floor CLI が `trace=False` build を測る」ことは規律 1 の要求であって
  それ単独では欠陥ではない。
- 規律 2: verifier が anomaly を検出した variant は即 reject。
- 規律 3: verifier は pass/fail でなく構造化した理由を返す。
- 規律 7: 現行コードとの差だけを理由に、記録された測定を無効にしない。
- 本 wave は測定を 1 件も行わない。build も benchmark も走らせない。read-only の静的閉包確認。
- 既存の凍結成果物、campaign WAL、`output/` 配下の bytes を変更しない。

## 閉包の定義 (P1 — 親の provisional 裁定・攻撃対象)

「正しさ検証を経ない測定面」= 次を両方満たす経路とする。

- (a) CCBench binary を実行し、throughput / latency / perf counter などの性能数値を導出する。
- (b) その数値を導出する前に、同じ genome + source について verifier の certified verdict を
  要求しない。

閉包は 2 層で数える。

- **層 A (producer)**: 上記 (a)(b) を満たす経路。CLI `__main__` からの経路と、module 外から
  import して直接呼べる公開関数の両方を数える。
- **層 B (consumer 境界)**: 各 producer の出力が official report / selector / 順位 / headline へ
  到達しうるか。到達を止めている機構を file:line で名指す。止めていないなら「止めていない」と書く。

この定義自体が攻撃対象である。狭すぎて実在経路を落とす / 広すぎて calibration や sanity check まで
「欠陥」に数える、のどちらも成果物を壊す。

## 実アンカー表 (変更面ではなく調査面)

| 対象 | path | 現時点で親が確認した事実 |
|---|---|---|
| floor の測定関数 | `orchestrator/campaign/between_run_floor.py:202` `measure_point_floor` | module-level 公開関数。admission 呼出しを内部に持たない |
| floor の admission | 同 `:111` `_protocol_source_has_trace_hook_evidence_only` / `:351` `main` | admission は `main()` 内にだけある (`:361`)。関数直接呼出しは通らない |
| floor CLI の build | 同 `:384` `buildcache.build(..., trace=False, ...)` | admission 通過後、verifier を呼ばずに測って `_write_out` する |
| floor の出力先 | 同 `:255` `_write_out` → `env_scope_dir(env_tag)/calibration/between_run_noise*.json` | 出力は calibration 系 artifact |
| もう 1 本の同名関数 | `orchestrator/campaign/pegasus_floor_scoping.py:135` `measure_point_floor` | 別実装。`:221` で `trace=False` build。admission の有無は未確認 |
| screening | `orchestrator/campaign/pipeline.py:952-957, 1005-1010, 1532-1553` | D58 の bench-first。`ident.verify_screening_preimage` と baseline 鮮度で制御 |
| certified writer 境界 | `orchestrator/campaign/execution_guard.py` `require_certified_writer_authorization` (`pipeline.py:1030`) / `certified_writer_admission.py` | stub が「certified 判定後に閉じている」と述べる箇所。実測で確認する |
| trace-disabled build の全出現 | `rg -n "trace=False"` が `orchestrator/` で 18 hit (test 除く) | うち campaign module は `backoff_profile.py:857`, `s8b_oracle_n_pilot.py:951`, `pipeline.py:1263`, `between_run_floor.py:384`, `s8b_floor_campaign.py:4342,4431`, `s2_verify_calibration.py:354`, `backoff_requested_us.py:1116`, `backoff_overthrottle.py:438`, `pegasus_floor_scoping.py:221`, `b10_backoff_shape_sweep.py:2538,2896` |
| bench 実行の中核 | `orchestrator/calibrator/runner.py:1057` `measure_point` / `:803` `capture_measure_point` | caller は `s8b_floor_campaign.py:7684,7690`, `calibrator/sweep.py:236,244`, `pipeline.py:739,747,2027`, `pegasus_floor_scoping.py:137,144`, `between_run_floor.py:213,220`, `s8b_floor_attempt_launcher.py:435` |
| CLI 入口の母集合 | `orchestrator/campaign/` の `__main__` を持つ module (40+ 件) | 全件を層 A の候補として走査する |

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 上記「閉包の定義」。
- **(P2)** 主張 3 (screening が verify より先に bench を実行できる) は**欠陥ではない**。D58 の
  既裁定であり、不変条件も明記されている。閉包一覧には「既裁定の sanctioned 経路」として載せるが、
  欠陥として数えない。ただし D58 の不変条件が現行コードで実際に守られているかは検査対象。
- **(P3)** 主張 1 (`measure_point_floor()` 直接呼出しが admission を通らない) は**構造的事実だが、
  それ単独では正しさ欠陥ではない**。python module の公開関数は import すれば呼べるのが常であり、
  「呼べる」ことと「その値が official 成果物へ入る」ことは別。欠陥かどうかは層 B で決まる。
- **(P4)** 主張 2 (floor CLI が verifier を実行しない) は**規律 1 の要求どおり**であり欠陥ではない。
  floor は noise floor 較正であって variant の性能主張ではない。欠陥になるのは、その値が
  certified な性能比較の権威として使われる場合に限る。
- **(P5)** repo 内に、層 A に属し層 B で止まっていない経路は**存在しない可能性が高い**。
  D1360 / D58 / certified writer admission の 3 層で塞がれているという読み。これは楽観であり、
  最も強く攻撃されるべき裁定である。

## 成果物の形

- 層 A の全経路一覧 (path:line、入口の種類、admission の有無、verifier 要求の有無)。
- 各経路の層 B 評価 (到達可能な consumer、止めている機構の file:line、止めていない場合その旨)。
- 実在する正しさ欠陥があればその名指しと修正 (Codex author 1 単位)。無ければ実装差分 0。
- `output/insights/` への実施記録、worklog fragment、必要なら decisions fragment。

## 成果物影響 (DW-G05)

放置した場合: tictoc / cicada を floor / campaign consumer へ接続する時点で、どの admission が
D1360 を強制するかが未確定のまま実装が進む。閉包が不明なら「塞がっている」という主張が
コードの事実に束縛されず、恒真な保証になる。本 wave の一覧は、その接続作業の前提を実測へ束縛する。

**scope 外の real 所見は実装せず裁定パッケージへ返す** — 特に「どの admission で D1360 を強制するか」の
確定は設計択一であり、本 wave は候補と根拠を返すだけにする。

## 分割方針

- 段 2: codex read-only plan 1 本。file:line 粒度で層 A の走査手順と層 B の判定手順を起草させる。
- 段 3: codex read-only 敵対相談 2 本。レンズ A = 閉包の定義と走査範囲の穴 (落とした入口・
  落とした呼出し形態)。レンズ B = 層 B 判定の恒真性 (「止まっている」の主張がコードの事実へ
  束縛されているか) と親の (P2)〜(P5) への攻撃。
- 段 4: 親が裁定。実装面が必要なら段 5 に Codex author 1 単位。不要なら 4→7→8→9。
- 実測環境: Pegasus login node 上の read-only 静的検査だけ。build・benchmark・dispatch は行わない。

## 受入

`python3 tools/run_tests.py` の全走 (`tools/dev_wave_wait.py acceptance --lease-optional` 経由)。
実装面 0 なら変異 matrix は免除、受入全走は免除しない。
