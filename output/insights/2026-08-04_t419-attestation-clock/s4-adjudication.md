# 段 4 裁定 — [T-419] 実行時 attestation の effective_clock

親が段 2 プランと段 3 敵対 2 レンズを real / refuted で裁定し、plan v2 と変異事前登録を確定する。
一次資料: `brief.md` (段 1)、`s2-plan.md`、`s3-lensA.md`、`s3-lensB.md`
(後者 3 つは repo 外 `/work/1/SFC/tanab/dev-wave-jobs/t419-attestation-clock/`、逐語は本 dir へ凍結)。

## 1. 親自身の主張に対する裁定 (レンズ A)

| # | 親の主張 | 裁定 | 根拠 |
|---|---|---|---|
| A1 | 帯外要素を持つ Pegasus 観測は 16 件 | **real だが件数は過少** | レンズ A が独立観測を **23 件以上**、最大 3096.51、追加 index 25/27/47 を実測。親の glob が `calibration/**` に閉じていた |
| A2 | 帯外の正体は観測者自身のコアの turbo | **refuted (因果としては未立証)** | ログインノード 6/6 は強い状況証拠だが、**計算ノードの成果物は probe の走行 CPU を記録していない**ため対応が取れない。「最有力仮説」へ格下げする |
| A3 | 取り直しても取得時受入検査はほぼ確実に落ちる | **real (現行 sanctioned probe/config に限定)** | 同一 probe・同一 config の計算ノード観測 23/23 が帯外 |
| A4 | どんな較正を登録しても実行時述語は通らない | **refuted (普遍命題として)** | 述語自体は全要素帯内の観測を通す。正しい言明は「**現行 probe/config では観測側が構造的に帯外要素を出すため、現行構成の Pegasus campaign は塞がれたまま**」 |
| A5 | E2E fixture のクランプが F97 の型を隠す | **real** | `test_s8b_floor_campaign.py:3457-3473`。原因は `tolerance_pct=100` ではなく samples のクランプ |

**帰結。** ユーザー裁定の前提「較正を取り直せば campaign が開く」は、**現行 probe/config では成立しない**
(A3 real)。ただし親が brief に書いた「原理的に不可能」は言い過ぎであった (A4 refuted)。
再裁定へ返す範囲は、レンズ A の指摘どおり**「全 48 要素を保つ probe 補正を既存裁定の範囲と見るか」だけ**へ狭める。

## 2. 設計に対する裁定 (レンズ B)

| # | 所見 | 裁定 | 措置 |
|---|---|---|---|
| B1 | S1 は `registered/` への全経路を守らない (git 直接追加・旧 worktree・attempt copy・外部持込・pin 更新) | **real / must-fix** | S1 の主張を **CLI publish 限定**へ明記して縮め、**registry 全走査の不変条件テスト**を置く (下記 S2') |
| B2 | `tolerance_pct` は操作者手入力で権威束縛がなく、100 を渡せば S1 も実行時述語も恒真化する | **real / scope 外・裁定へ返す** | 権威の出所 (policy 値か smoke 分布か) を決めるのは設計択一。**U-3 として返し、再登録前の blocker と明記**する。本 wave は S1 を「恒真化されうる gate」と正直に書く |
| B3 | P4 (publisher と consumer で述語を共有しない) は誤り | **real / P4 を撤回** | issuer (`env_attestation._recorded_verdict`) が別実装のまま残るので独立性は保たれる。**publisher は consumer の canonical 述語を共有**し、drift を構造的に不能にする。正本は consumer 側 |
| B4 | 等価性 golden vector が mean drift を検出しない | **real / must-fix** | 中央値対称でない・奇数長・平均が動くと落ちる vector を含める |
| B5 | 単純な fact pin は将来の反転を強制しない (新しい self-fail entry にも緑) | **real / must-fix** | B1 の registry 全走査へ統合。**既知例外 = 現 path/SHA を exactly 1 件**とし、それ以外の entry は自己整合を必須とする補集合検査にする |
| B6 | `silo_ladder_rung1.py:1962` に median-to-median の別 consumer が残る | **real / scope 外** | 別 attestation 受理集合であり本 wave の変更面でない。**U-4 として返す** |
| B7 | S1 は恒真または常に false | **refuted** | 合成正例 (`[2400,2410,2390]`/5%) は通る。実 Pegasus で常に落ちるのは probe 側の性質であって gate の論理的性質ではない |
| B8 | 推奨位置で `rejection.json` や staging の形が壊れる | **refuted** | 既存 quality rejection と同形 |
| B9 | `calibration.md` に reasons を出す、reason 綴り、pre/post bench の資源効率 | **nit** | reason 綴りは `effective-clock-self-comparison-failed` を採用。他は採らない |

## 3. plan v2 (実装するもの)

- **S1 (CLI publish gate)。** `orchestrator/calibrator/cli.py::_certify_main` の品質理由算出
  (`certification_quality_reasons` 呼び出し直後、status 決定前) に、候補 artifact の
  `attestation_profile.effective_clock` を**自分自身の観測値として consumer 述語にかける**検査を足し、
  落ちたら reason `effective-clock-self-comparison-failed` を積んで rejected にする。
  publish (registered/ への rename) より前で必ず発火する。
  - **述語の所有 (B3):** consumer 側 (`execution_guard`) が使う純関数を canonical として切り出し、
    publisher はそれを**共有**する。issuer (`env_attestation`) は従来どおり独立実装のまま触らない。
- **S2' (registry 全走査の不変条件、B1+B5 統合)。** `env_contract.REGISTRY` が参照する
  全 calibration を走査し、
  (i) 自己整合を満たさない entry は**既知例外の集合と厳密に一致**すること、
  (ii) 既知例外は現 Pegasus の path + sha256 のちょうど 1 件であること、
  (iii) それ以外の全 entry は自己整合を満たすこと、を検査する。
  新たな自己不整合 entry が増えれば赤、既知例外が直れば赤 (反転を強制)。
- **S3 (golden vector、B4)。** consumer 述語の表駆動テストに、
  中央値不変・平均可動の vector、奇数/偶数長、境界 (帯の端ちょうど)、
  型不正・空列・tolerance 極値を含める。
- **S4 (記録)。** 新事実と件数訂正、裁定の台帳化、裁定パッケージ U-1〜U-4。

## 4. 実装しないもの (裁定へ返す)

- **U-1: probe の観測者効果補正 (α/β/γ)。** レンズ A・B とも「証拠不足のまま採るな」で一致。
  **先に計算ノードで、probe の走行 CPU・cpufreq driver・boost 設定・同居プロセスを束縛した
  probe 実験**を行い、A2 の因果を立証してから方式を選ぶ。α (K 回読んで論理 CPU ごとに最小) は
  受理集合を緩めない利点があるが、「本当に忙しいコア」を見逃す構成の検討が未了である。
- **U-2: 較正の再取得と pin 更新。** U-1 の後。`method` 文字列が変わるため凍結 bytes と
  `env_contract.py:186-192` の pin 更新が同時に要る。
- **U-3: `tolerance_pct` の権威束縛 (B2)。** 再登録前の blocker。
- **U-4: `silo_ladder_rung1` の別 attestation 受理集合 (B6)。**

**本 wave の性格を明記する。** これは**封じ込め (containment) wave** であり、
**Pegasus campaign は開かない。** 開けるのは U-1 → U-2 の順に裁定と実験が済んだ後である。

## 5. 変異事前登録 (DW-M01 / B-057)

本 wave は rejection gate を新設するため B-057 の述語 `validator_or_rejection_gate_changed` が成立する。
実装前に次を登録する。各変異は「手前に同じ入力を拒否する検査がないこと」「無効化時の赤理由が一つ」を
実装後にコードで確認し、確認できなければ登録を実効 gate へ再照準する。

| # | 変異 | 期待赤 (単一理由) |
|---|---|---|
| M1 | S1 の reason 追加を消す (gate を無効化) | 帯外 profile の certify が rejected でなく accepted になり、publish される |
| M2 | S1 の述語呼び出しを「中央値同士の比較」へ差し替える | 帯外要素 1 個を見逃し、同じ certify テストが緑になる |
| M3 | S2' の既知例外集合を「全 entry を例外扱い」へ緩める | 新規 self-fail entry を検出できず invariant が緑になる |
| M4 | canonical 述語の tolerance を無視して常に true を返す | golden vector の負例が緑になる |
| M5 | golden vector から mean-drift ケースを外す (`DW-M08` の新旧両走で扱う) | 新テストが drift を検出しなくなる |
| P (正例) | 帯内の合成 artifact (`[2400,2410,2390]`/5%) | S1 を通り accepted のまま publish される (過剰拒否しない) |

## 6. 段 5 への指示

- 実装単位は 1 つ (編集面が `orchestrator/calibrator/cli.py`、`orchestrator/campaign/execution_guard.py`、
  `orchestrator/tests/` に閉じ、相互依存があるため分割しない)。
- 既存テストの期待値を変更しない。受理集合を指示外に広げない。
- probe、`env_attestation.py`、`env_contract.py` の pin、registered artifact の bytes は触らない。
