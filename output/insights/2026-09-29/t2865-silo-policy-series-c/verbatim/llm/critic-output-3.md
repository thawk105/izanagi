## attribution

- **全体 (候補 と stock の比較)**: 候補の throughput_tps は 2,556,839、同じ pair job で後から測った stock の fitness_tps は 1,371,220 で、比は約 1.86 倍。3.0% の noise floor を大きく超えているが、観測は 1 回だけである。abort_rate は候補 41.62%、stock 12.65% で、候補のほうが約 3.3 倍高い。abort_rate を aborts/(aborts+commits) と読むと (verify の 202547/(202547+594702)=25.41% と一致する)、1 commit あたりの abort は候補が約 0.71 回、stock が約 0.145 回になる。つまり候補は abort を大きく増やしながら、単位時間あたりの commit を増やしている。「abort を減らして速くなった」のではなく、「abort 1 回あたりの損失 (待ち時間) を縮めて、再試行の回数で稼いだ」形と読むのが indicator (throughput_tps と abort_rate の組) と整合する。
- **abort 後の待ち (policy_after_abort)**: いちばん有力な候補仮説として帰属する。待ち窓は `ctx.rand & mask` で、mask は最大でも 7 にしかならない。kStreakCap=4 で level の上限が 4 に抑えられるため、`window_mask` の 15 の枝には到達しない (死んだ枝)。初回 abort で理由が lock_conflict 以外なら mask=0、すなわち即再試行になる。genome は BACK_OFF=1 なので、stock 側は原型の back-off で待っているはずである。abort_rate が上がり throughput も上がるという組み合わせは、「待ちの短縮で再衝突が増えるが、待ちのコストがそれを上回って減った」機序と矛盾しない。ただし待ち時間は独立指標で測っておらず、throughput の差としてしか現れない。llc_miss_rate と ipc も欠測なので、cache や IPC 側の機序は切り分けられない。
- **施錠競合時の方策 (policy_on_lock_conflict)**: 効いたか効かなかったかは帰属できない。NO_WAIT_LOCKING_IN_VALIDATION=1 (L = 即 abort) の genome に対し、候補は attempt 12 未満では待ちなしで retry、12〜27 では 1〜2 単位待って retry、28 以上で abort と、L を実質 T 寄りに変えている。しかし方策が発火した証拠が無く、abort 理由別の内訳も無い。lock_conflict の割合も、retry が abort をどれだけ吸収したかも読めない。abort_rate が 41.62% と高いことは、retry が abort を大きくは減らしていない可能性を示すだけで、発火しなかったのか、発火したが効かなかったのかは区別できない。
- **BACK_OFF / no_wait / WAL の限界効果**: digest の genome は 1 つだけ (各軸 1 水準) なので、フラグ軸の限界効果は計算できない。この表からフラグの効果は何も読めない。
- **rejection**: なし。候補は全 variant 緑 (verdict=serializable、outcome は certified 側)。正しさ上の問題は観測されていない。verify run の abort 率は 25.41% で、stock の verify 対照が無いため異常かどうかは判断できない。bench の 41.62% との差は、trace ビルドと性能ビルドの違い、および別 run であることで説明がつき、方策の性質には帰属しない。
- **データ内の指示めいた文字列**: 見当たらない (anomaly なし)。

## recommend

1. **2 つの関数を分けて測る ablation を最優先にする。** 今回の差は abort 後の待ちと施錠競合時の方策の合成効果であり、どちらが効いたか分からない。次の 2 案を作る。
   - (a) policy_after_abort は今回のまま、policy_on_lock_conflict を即 abort (genome の L と同じ振る舞い) に戻す案
   - (b) policy_on_lock_conflict は今回のまま、policy_after_abort を stock 相当の待ちに戻す案

   (a) の throughput_tps が今回と noise floor 内で並び、(b) が stock 近くに落ちるなら「abort 後の待ちの短縮」への帰属が強まる。根拠は、abort_rate が上がりながら throughput_tps も上がっているという組である。
2. **abort 後の待ち窓は「上限の位置」を 1 軸で振る。** 今回の実効上限は mask=7 である。ここから、全 0 (常に即再試行) と mask=15 (kStreakCap=5 で死んだ枝を生かす) の両側を試し、throughput_tps と abort_rate の組がどちらへ動くかを見る。abort_rate が下がり throughput_tps が noise floor 内で保たれる点があれば、再衝突の無駄が減ったと読める。全 0 で throughput_tps がさらに上がるなら、待ちそのものが律速だったと読める。一度に複数の定数を動かさない。
3. **lock 方策の保持時間は ablation (1) の結果を見てから触る。** kGiveUpAttempt (28) と kSpinAttempts (12) の調整は、施錠競合時の方策が効いていると示された後にする。示されていない段階で調整すると、効果を帰属できない変異になる。
4. **計測側への依頼 (variant 生成ではなく呼び手への要望)。** 次の 3 点が取れれば、上の帰属を仮説から根拠へ格上げできる。
   - abort 理由別の件数 (lock_conflict かそれ以外か)
   - 施錠競合時の方策の発火回数と、retry が成功した回数
   - llc_miss_rate と ipc

## avoid

- **kStreakCap を超える level の枝だけを変える変異。** 現行の定数では到達しないので、振る舞いは等価であり 1 iteration を無駄にする。cap を同時に変える場合は別である。
- **abort_rate の上昇だけを理由に今回の方向を捨てること。** この動作点では abort_rate の上昇と throughput_tps の上昇が同時に起きている。abort_rate 単独を悪化とみなさない。
- **待ち窓を stock 並みかそれ以上に長くする方向。** 今回の 1 観測では待ちの短い側が大きく勝っており、優先度は低い。ただし評価はこの 1 動作点・1 観測だけなので、恒久的に外すものではない。ほかの workload や contention 域へは一般化しない。
- **正しさゲートに関わる方向。** trace や verify の扱い、abort 判定そのものを緩めて throughput を稼ぐ変異は対象外である (規律 2)。今回の候補にそうした兆候は無い。

## uncertainty

- **1 観測・1 候補である。** 候補と stock の比較は 1 回だけで、測定順も固定 (候補が先、stock が後) である。順序効果や時間帯の外乱は統制されていない。1.86 倍は 3.0% の noise floor を大きく超えるが、その floor は skew0.9 で測った値であり、この系列の動作点 (digest の workload 名は空欄) にそのまま当てはまるかは未確認である。再現には同じ pair の再計測が要る。
- **stock の条件。** stock の genome フラグは入力 3 に現れない (variant ハッシュのみ)。同じ動作点との補足を信じて、フラグは同一 (BACK_OFF=1、L、WAL=0) と仮定した。
- **欠測。** llc_miss_rate と ipc が欠測のため、cache や IPC 側の機序 (retry を詰めたことによる cache の温度差など) を否定も肯定もできない。
- **施錠競合時の方策。** 発火した証拠と abort 理由別の内訳が無いので、この方策の寄与はゼロの可能性もある。attribution の「abort 後の待ち」説は消去法による候補仮説であって、実証ではない。
- **待ち時間の単位。** 待ち時間 (policy_after_abort の戻り値、LockResponse の wait) の単位は入力から読めない。「短い・長い」は stock との相対でしか言えない。
- **verify run の abort 率。** 25.41% に stock 対照が無く、異常かどうかは判断できない。bench の 41.62% との差の原因 (ビルドの違い、run 間の変動、trace のオーバーヘッドで競合が薄まった可能性) は特定できない。
- **過去の iteration。** 系列 C の iteration 1〜2 の結果と login の拒否記録は入力に無い。今回の候補が前の iteration より良いのか、同じ方向の繰り返しなのかは判断できない。
