## attribution

**1. 方策全体の効果 (帰属は暫定)**
- 認証済みの行は 1 本だけ。genome は `SILO_POLICY_VARIANT=1, BACK_OFF=1, NO_WAIT_LOCKING_IN_VALIDATION=1, WAL=0`。
- この行の値は throughput_tps 4,351,478、abort_rate 18.68%。同じ pair job で測った stock は fitness_tps 1,366,231、abort_rate 12.63%。
- 候補は stock の約 3.2 倍の throughput を出し、abort_rate は約 6 ポイント高い。
- 「abort を減らして速くなった」のではない。abort は増えたのに throughput が大きく上がった形である。
- commit 1 件あたりの abort は、stock 約 0.145 回に対し候補約 0.23 回。秒あたりの abort 件数は候補の方が約 5 倍多い計算になる。
- この組み合わせから立つ第一の仮説は「abort 後の待ちや施錠競合時の待ちが短いことが効いた」である。探索の相手は abort 率ではなく待機コストだった、という読み。
  - 待ちが短いと再試行が早まり、衝突が増えて abort_rate は上がる。それでも待たずに回る分、単位時間あたりの commit が増える。
  - llc_miss_rate と ipc が無いため、キャッシュや IPC 側の機序は区別できない。

**2. `policy_after_abort` (abort 後の待ち) — 帰属の主候補だが未分離**
- abort で窓を 2 倍にし (上限 64)、commit で半分にする (下限 1)。
- abort と commit の比が約 0.23:1 なので、窓は下へ流れ、多くの時間 1〜2 付近にいると推定する。
- その場合、abort 後に返す待ちはほぼ 1 単位になり、実質「ほぼ待たない」方策である。
- 待ちの単位はこの入力からは不明。

**3. `policy_on_lock_conflict` (施錠競合時の方策) — 寄与は判定不能**
- 16 回までは待ち 0 で retry し、それ以降も retry を返す。abort は一度も返さない。
- 待ちが 0/1 になるのは窓が 8 以上のときだけで、上の推定ではまれ。したがって実質「待ち 0 で回り続ける retry」である。
- genome の `NO_WAIT_LOCKING_IN_VALIDATION=1` (no-wait 政策 L = 競合で即 abort) を、この hook が T 相当 (retry) に置き換えている可能性がある。
- ただし lock hook が実際に発火した証拠は取っていない。そのため寄与の有無は言えない。
- 仮に施錠失敗による abort を減らしていても、全体の abort_rate は上がっている。abort の主因は別の経路 (例: 読み集合の版不一致) だろうと推測できるが、要因別の内訳が無いので確かめられない。

**4. フラグ軸 (BACK_OFF / no-wait / WAL)**
- digest の限界効果は各軸 1 水準しか無く、フラグを切り替えた比較が存在しない。
- この系列のデータからフラグ単位の帰属はできない。

**5. 赤 (rejection) の candidate-0001**
- 型は frame 型 (policy-grammar)、証拠は `lex.literal-suffix`。正しさ系の cycle 型・integrity 型でも liveness 型でもない。
- 字句段階で、受理されない数値リテラル接尾辞を使ったことによる拒否と読む。
- 性能数値は構造上存在せず、推定しない。
- iteration 2 は `1u` などの `u` 接尾辞と `std::min` / `std::max` を使って文法ゲートを通った。したがって少なくとも `u` 単独は受理されている。candidate-0001 がどの接尾辞を使ったかは入力に無い。

## recommend

**方向 A (第一推奨) — 待ちの寄与を切り分ける**
- 次の候補では変更を 1 か所に絞る。abort 後の待ちを常に 0 にし、窓の状態更新は残してよい。`policy_on_lock_conflict` は据え置く。
- 根拠: 上の推定では窓は低位に張り付き、待ちはほぼ 1 単位しかない。待ちそのものが効いているのか、「ほぼ 0」なら同じなのかを throughput_tps と abort_rate で分ける。
- 読み方:
  - throughput が noise floor 内で変わらず abort_rate だけ上がる → 待ちの大小は効いていない。
  - throughput が下がる → 小さなジッタ付きの待ちが衝突の同期を崩す効果を持っていた。

**方向 B (A の代替。一度に 1 つだけ出す) — lock hook の寄与を切り分ける**
- `policy_on_lock_conflict` を、競合したら即 abort に戻す (genome の L 政策と同じ振る舞い)。`policy_after_abort` は iteration 2 のまま据え置く。
- 根拠: lock hook の発火証拠が無いため、今の 3.2 倍に施錠 retry が寄与しているかが不明。
- 読み方:
  - abort_rate が上がり throughput が下がる → 施錠 retry が効いていた。
  - 両方とも変わらない → hook はほとんど発火していないか、効いていない。

**共通の指示**
- genome フラグは今の行 (`BACK_OFF=1, NO_WAIT_LOCKING_IN_VALIDATION=1, WAL=0`) に固定する。方策本文と同時に動かさない (交絡を避ける)。
- 数値リテラルの接尾辞は、iteration 2 で通った形 (`u`) だけを使う。hole 内の直線的なコードに収める (frame 型拒否への対処)。
- 可能なら同じ動作点で iteration 2 の方策を 1 回再測定し、between-run のばらつきを確認する。ここは呼び手 (orchestrator) の判断に委ねる。

## avoid

- **変更を同時に入れること。** 待ちの形、lock hook、genome フラグを一度に変えると、今回の差がどこから来たか帰属できなくなる。
- **検証を緩める方向。** 施錠を省く、validation を飛ばす、版の確認を弱めるなど、正しさの前提を削って待ちを減らす変異は、速くても採用対象外 (規律 2)。探索は待ち方と retry 政策の範囲に留める。
- **`u` 以外の数値リテラル接尾辞。** 例は `ull`、`UL`、`L`、浮動小数の `f`。candidate-0001 が `lex.literal-suffix` で拒否されている。どれが拒否されたかは不明なので、通った形だけを使うのが安全。
- **abort 後の待ちの上限を大きくする方向や、窓を線形に伸ばして長く待つ方向を優先すること。** 今の唯一の観測は「待ちが短いと推定される方策が stock より大幅に速い」なので、優先度は下げてよい。ただし検証済みなのはこの 1 動作点・1 候補だけで、ほかの workload や競合度には一般化しない。完全に排除するのではなく、後回しにする程度とする。
- **verify 走の abort 率 23.33% を reject の理由や異常の根拠にすること。** stock の対照が無く比を取れない。trace を有効にした build は時間の進み方が違うため、性能計測 build の 18.68% とは直接比べられない。

## uncertainty

**1 回の測定であること**
- 観測は 1 候補・1 pair job だけ。
- 3.2 倍という差は、between-run の noise floor (skew0.9 で 3.0%) を桁違いに超えている。それでも同じ方策での再測定が無く、再現性は未確認。
- 採否の正式判定は `calibrator.stability.compare` の結果に委ねる。
- stock は候補の後に測っており、測定順の影響は排除できていない。

**stock の中身が不明**
- stock の genome (BACK_OFF の値を含む) は入力に無い。
- 「stock の待ちが長いから遅い」という帰属は、stock が BACK_OFF=1 相当の待ちを持つという仮定の上に立っている。
- stock の待ちが小さい場合、差の機序は別のところにある。

**欠けている計測**
- llc_miss_rate と ipc が無い。待機コスト説とキャッシュ・IPC 説を区別できない。
- lock hook が verify 中や bench 中に発火した証拠が無い。`policy_on_lock_conflict` の寄与はゼロの可能性もある。
- abort の要因別内訳 (施錠失敗か、読み集合の版不一致か) が無い。abort_rate が上がった原因を特定できない。
- 待ちの単位 (spin 回数、clock、pause 命令など) が入力に無い。「ほぼ待たない」の実時間は不明。

**推定に頼っている点**
- 窓が低位に張り付くという読みは、平均の abort と commit の比からの推定である。スレッドごとの偏りや、競合が集中する時間帯に窓が 8 以上へ上がる頻度は観測していない。

**digest の対応づけ**
- digest の行は genome 単位で集計されている。candidate-0001 と candidate-0002 は同じ genome 文字列を持つ。
- 認証済みの行が candidate-0002 (iteration 2) の値だという対応は、candidate-0001 が拒否されているという状況からの推論であり、行の中に候補ラベルは書かれていない。

**frame 型拒否の中身**
- candidate-0001 がどの接尾辞を使ったかは不明。「`u` 以外を避ける」は安全側の推測である。

**入力の確認**
- 3 つの入力に、指示めいた文字列や振る舞いを誘導する文字列は見当たらなかった。
- rejections 節の「読み方」文は digest 自体の定型の案内であり、データとして扱った。
