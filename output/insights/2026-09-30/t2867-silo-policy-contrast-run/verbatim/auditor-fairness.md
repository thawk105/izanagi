# 公平性の目視 (事前登録 §6 末尾・D2214 項 8) — auditor の報告の逐語

role `auditor` (`.claude/agents/auditor.md`、model opus・effort high) に、2026-10-01 07:0x JST、score の確定後・報告の前に依頼した。
入力は `../endpoints-v1.json` (48 系列の endpoint 本文)。親の射影の誤りとして、この file には探索時の性能値 (`search_tps`) が入っていた (本文 §6 に記録)。

---

## 公平性の目視 (事前登録 §6 末尾・D2214 項 8) の所見

この目視は正しさの判定 (reject/pass) ではありません。score・判定・系列は変えず、報告に添える所見です。監査対象は差分ではなく endpoint 本文なので、diff_digest は該当しません。

### (1) 総括
- 48 本すべてで、特定の worker を恒常的に優先したり駐車させたりする構造は見当たりませんでした。API がスレッド番号を渡さず、方策の状態は thread_local で全 worker に同じ規則が掛かるためです。
- 懸念は 2 系統あり、どちらも上限のある一時的な偏りです。
  - 連続 abort 回数に応じて待ちを伸ばし、commit で戻す方策で起きうる「勝った worker が勝ち続ける」偏り (いわゆる capture effect)。
  - lock 競合時に待ちなしで再試行を続け、実質的に backoff を切る形。
- abort 後の待ちの最大は約 64 µs で、上限 1000 µs には誰も届いていません。lock 再試行の待ちは全員 0 µs です。一方、試行回数は llm-ir-2・llm-ir-3 が骨格の 32 周回上限に張り付いています。

### (2) 懸念のある endpoint

| series | 懸念の内容 | 根拠の本文 | 重さ |
|---|---|---|---|
| llm-ir-3 (eval-6) | lock 競合への backoff が実質無効。32 回まで待ち 0 で再試行し、それでも取れず abort しても待ち 0 のまま再開する。再試行の間は write set で先に取った lock を握り続ける (骨格の lockWriteSet は prefix lock を保持したまま周回する)。キャッシュ行に近い worker が勝ちやすい。 | `bool t0 = c.attempt < 32u; ... retry` と、after_abort の `t0 = c.reason == lock_conflict; t1 = t0 ? 0u : v0; return t1;` | 中 |
| llm-ir-2 (eval-8) | lock 競合で常に retry (待ち 0)。c.attempt は 0〜31 しか来ないので、この方策は自分では一度も諦めず、骨格の 32 周回上限だけが止める。prefix lock を保持したままの周回が最長になる。abort 後は 4→6→…→28 µs と乱数なしで決まった値に伸び、commit で 0 に戻る。 | `bool t0 = c.attempt < 32u;` ・ `std::min(t3, 28u)` ・ commit の `s.f0 = 0u` | 中 |
| llm-ir-11 (eval-5) | 連続 abort ごとに待ちが 0→1→3→7→15→31→64 µs と乱数なしで伸び、commit で 0 に戻る。直前に commit した worker は次の abort で待ち 0、負け続けた worker は 64 µs 待つ。偏りは 64 µs で頭打ちで、無期限の飢餓ではない。lock 競合は待ち 0 で 16 回まで再試行 (prefix lock を保持したまま)。 | `t0 = std::min(v0, 64u)` ・ `t1 = v0 << 1u; ... + 1` ・ commit の `s.f0 = 0u` ・ `c.attempt < 16u` | 中 |
| llm-cpp-10 (eval-9) | 連続 abort が 3 回目までは待ち 0 (backoff なし)。4 回目以降は 2〜31 µs で、commit で 0 に戻るため上と同じ偏りが起きうる。lock 競合は待ち 0 で 8 回まで再試行。 | `kFreeRetries = 3u; if (state.streak <= kFreeRetries) return 0u;` ・ `kLockSpinAttempts = 8u` ・ commit の `streak = 0u` | 低〜中 |
| llm-cpp-1 / llm-cpp-6 / llm-cpp-12 | 同じ型の弱い版。いずれも乱数の揺らぎがあり、commit では半減か 0 に戻す。最大の待ちは約 24 / 30 / 23 µs。lock 競合は待ち 0 で 3 / 8 / 4 回まで再試行。llm-cpp-1 と llm-cpp-12 は最初の abort で待ち 0。 | 各 `streak` と `kLockRetryLimit` / `kLockSpinLimit` | 低 |
| llm-cpp-7 (eval-4) | 読んだ版が古いことによる abort (read_tid・node_validation など 5 種) では常に待ち 0。この 5 種に限れば backoff が切れている。lock 側は即 abort。 | `if (is_stale_version(ctx)) return 0u;` | 低 |
| llm-ir-4 / llm-ir-7 | 乱数を使わず、待ちが決まった値で伸びる (llm-ir-4 は 4→8、llm-ir-7 は最大 16 / 32 µs)。同時に衝突した worker 同士が同じ長さ待って再び衝突しうるが、どちらかを負けさせ続ける仕組みではない。 | llm-ir-4 の `std::min(t1, 8u)`、llm-ir-7 の `std::min(v0, 16u)` / `std::min(t2, 32u)` | 低 |

補足 (懸念ではなく事実の記録)
- 骨格は lock 側の応答が abort のとき wait_us を読みません。次の系列にある abort 付きの非 0 値は効かない死んだ値です。
  - evo-ir-9 の `{abort, 32u}`
  - evo-ir-3・evo-ir-10・evo-ir-11・evo-ir-12 の `{abort, c.attempt 由来}`
  - random-ir-10・random-ir-4 の `{abort, t7 / 3u}`
- 同様に、evo-ir-3・evo-ir-4・evo-ir-9・evo-ir-10 と random-ir-4・random-ir-10 の状態 field は、読んでも待ちに効かないか、書くだけの no-op です。
- lock 再試行の待ち (上限 50 µs) を 0 以外にした endpoint はありません。

### (3) arm ごとの傾向
- **random×IR:** 12 本中 10 本が共通の初期点 (静的 5 / 10 µs) のままです。残りの random-ir-4 と random-ir-10 は、実質的に定数待ち (8 / 6 µs) で lock 競合は即 abort です。全 worker に同じ規則が掛かり、偏りの懸念はありません。
- **進化×IR:** 初期点が 3 本です。他の 9 本も、abort 後は定数 5〜10 µs、lock 競合は即 abort の定数 backoff に収まっています。付随する状態や数式は効かない値ばかりです。懸念はありません。
- **LLM×C++:** 初期点が 5 本 (llm-cpp-2・3・4・8・9) です。残り 7 本はすべて「連続 abort 回数で待ちを伸ばし、commit で戻す」型に、乱数の揺らぎを付けたものです。うち 4 本は lock 競合で待ち 0 の短い再試行 (3〜8 回) を加えています。揺らぎがあるぶん、偏りは緩和されています。
- **LLM×IR:** 初期点が 7 本です。残り 5 本は同じく回数で伸ばす型ですが、どれも乱数を使いません (IR で揺らぎを書いた endpoint が無い)。再試行の回数も大きく (16 / 32 回)、骨格の 32 周回上限への張り付きもこの arm だけです。
- まとめると、機械生成の 2 arm は対称な定数 backoff から出ていません。これに対し LLM の 2 arm は状態を持つ適応型へ動き、公平性の懸念はそちらに集まっています。とくに LLM×IR は乱数なし・長い再試行という、偏りの出やすい側に寄っています。

### (4) この目視で分からないこと
- **実測の偏りは測れない:** worker ごと・キーごとの commit 数や abort 数、待ち時間の分布を見る観測点がありません (verifier・digest・auditor のどれも持たない。型15 の死角)。上の偏りが実際の走行で起きたか、どの程度かは本文からは判定できません。
- **再試行の実時間が不明:** 待ち 0 の再試行 1 周の実時間 (キャッシュ行の取り合い次第) と、その間に保持される lock 数が不明です。そのため、prefix lock の保持が他の worker の abort をどれだけ増やしたかは推定できません。
- **並び順の前提:** write set が lock 前に並べ替えられることを、デッドロックが起きない前提として置いています。この目視では骨格の並べ替え部を読み直していません。
- **乱数列の出所:** 乱数列は worker 番号で種を決めた xorshift です。worker ごとに列は違いますが、恒常的な優先を作る形ではないと判断しました。下位ビットの質の細部は検証していません。
- **勝った側の本文は未照合:** 事前登録は「各比較で勝った側の endpoint 本文」の目視も求めていますが、どの比較でどちらが勝ったかは受け取っていません。48 本全体を見たので勝者は必ず含まれていますが、勝者を特定した上での照合はしていません。
- **性能値を見てしまった:** 入力の隔離について正直に書きます。endpoints-v1.json の各要素には性能値 (search_tps) が入っていて、読み込み時に目に入りました。所見はこの値を使わず、本文の構造だけから出しています。今後この目視へ渡すときは、性能値を除いた射影にすることを勧めます。
- **受理契約の監査はしていない:** 依頼の範囲外なので、policy-C++ v1 の受理契約 (型16〜25) の全面的な再監査はしていません。目に入った範囲で、スレッド番号・fitness・マクロ・loop・再帰を参照する endpoint はありませんでした。

参照したファイル
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/endpoints-v1.json
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/docs/silo-policy-generator-contrast-preregistration.md (§2・§6)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/orchestrator/campaign/silo_function_policy_api.hh
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/patches/silo-function-policy-variant.patch (骨格の待ち上限・lock の再試行ループ)
