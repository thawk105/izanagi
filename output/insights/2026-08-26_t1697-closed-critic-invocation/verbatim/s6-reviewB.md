静的レビューのみ。pytest は実走していない。must-fix 7 件があり、現状の採用には反対する。

## 所見

### 1. [must-fix] off controller を on digest に変えても全 test が通る

- **(a) 何が壊れるか** — `reflux=(self.__binding.arm == "on")` を `reflux=True` にする 1 行変異で、off が赤詳細を受け取る。落ちる test はない。receipt は `arm="off"`、`status="success"` のまま pair 検査も通る。
- **(b) 根拠** — `orchestrator/campaign/p3_b4_closed_critic.py:601-616,647-688,833-878`。P2 は on しか起動せず、pair test は送信 digest を見ない: `orchestrator/tests/test_p3_b4_closed_critic.py:467-481,691-704`。
- **(c) 最小是正案** — pair を実際に invoke した test で、captured payload を各 admitted view から再計算した on/off digest と byte 比較し、off に fixture 固有の赤 marker がないことも固定する。
- **(d) 成果物影響** — off 汚染 block が certified 受理集合へ入り、材料レポートの arm 帰属と試行台帳の receipt 参照が偽になる。

### 2. [must-fix] test-only receipt を文字列変更だけで certified に昇格できる

- **(a) 何が壊れるか** — fake runner 由来 receipt を `replace(..., evidence_class="certified")` するだけで `assert_b4_arm_pair` が受理する。別 factory で作った on/off の混成も、共通 pair identity がないため受理可能。
- **(b) 根拠** — public dataclass と field 検査だけ: `orchestrator/campaign/p3_b4_closed_critic.py:147-183,833-871`。test 自身が昇格を実行: `orchestrator/tests/test_p3_b4_closed_critic.py:484-505,691-704`。
- **(c) 最小是正案** — pair factory に共有 `pair_id` を持たせ、pair 自身の method が自分の 2 invocation を検証する形へ閉じる。test-only からの `replace` を P4 正例に使わず、昇格を明示的な負例にする。
- **(d) 成果物影響** — fake query または別 block の receipt が certified 候補として採用され、受理集合と台帳の pair 対応が捏造可能になる。

### 3. [must-fix] certified mode でも任意 executable を trust root にできる

- **(a) 何が壊れるか** — runner は `subprocess.run` のまま、Claude 互換の偽 executable を渡せば自己生成 envelope で certified receipt を作れる。M5 は `sys.executable` を certified として作成できることを正例化している。
- **(b) 根拠** — executable は caller/CLI 入力: `orchestrator/campaign/p3_b4_closed_critic.py:764-780,881-895`。pair 検査は両 arm の path/hash が同じかしか見ない: `同:844-855`。test: `orchestrator/tests/test_p3_b4_closed_critic.py:415-426`。
- **(c) 最小是正案** — certified mode の executable path/hash を caller 外の承認済み値へ束縛する。少なくとも expected executable hash を admission 入力にし、invoke 前に exact 検査する。
- **(d) 成果物影響** — critic を一度も実行していない block が certified 選択へ入り、材料レポートと台帳が偽 executable の receipt を参照する。

### 4. [must-fix] tool-surface の 3 条件を個別に弱めても test が赤くならない

- **(a) 何が壊れるか** — permission denial、`num_turns`、server tool use を同時に壊した 1 負例しかない。いずれか 1 gate を緩めても残りが拒否するため test は通る。controller 自身は値を拒否せず bool として success receipt に載せるだけ。
- **(b) 根拠** — receipt 化のみ: `orchestrator/campaign/p3_b4_closed_critic.py:679-687`。複合負例と広い `Exception`: `orchestrator/tests/test_p3_b4_closed_critic.py:626-647,770-794`。正例の空 dict は `all()` が空母集合でも真: `同:185-200,773-775`。
- **(c) 最小是正案** — controller でも 3 条件を独立に拒否し、1 field だけを変えた負例を 3 本に分け、例外型と理由を固定する。空 `server_tool_use` の意味も明示する。
- **(d) 成果物影響** — tool 使用または複数 turn の query が success receipt を持ち、閉鎖済みとして受理集合と台帳へ入る。

### 5. [must-fix] snapshot・digest・argv・receipt chain の hash 検査が自己整合または長さだけ

- **(a) 何が壊れるか** — WAL hash を loop-state bytes の hash に替える、digest/start hash を固定 64 桁にする等の 1 行変異が生存する。P4 の「両 arm で異なる」も誤った別 bytes なら通る。
- **(b) 根拠** —生成箇所: `orchestrator/campaign/p3_b4_closed_critic.py:663-689`。test は snapshot/hash の長さのみ、argv も長さのみ、start hash は再計算なし: `orchestrator/tests/test_p3_b4_closed_critic.py:467-479,604-623,672-688`。
- **(c) 最小是正案** — fixture の WAL、loop-state、captured argv、送信 digest、start receipt bytes から各期待 hash を独立再計算し、receipt と exact 比較する。
- **(d) 成果物影響** —別 snapshot・別 digest が同じ block に束縛され、材料レポートの precursor 対応と台帳の artifact 参照が壊れる。

### 6. [must-fix] 「state/proposal へ fold しない」assert は恒真に近い

- **(a) 何が壊れるか** — test 内で作った `LoopState` は controller/parser へ渡されないため、不変 assert は常に通る。禁止名 3 個を使わず checkpoint や proposal を書く 1 行変異も検出しない。
- **(b) 根拠** —無関係な local state: `orchestrator/tests/test_p3_b4_closed_critic.py:467-472,734-743`。裁定の義務: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1697-closed-critic/s4/adjudication.md:105-111`。
- **(c) 最小是正案** — invoke 前後の実 loop-state bytes を比較し、artifact/campaign root に proposal が新設されないことを確認する。`co_names` blacklist は補助に降格する。
- **(d) 成果物影響** — `prior_critic_reverse` や停止理由、次 synthesis 数が変わり、試行台帳の標本数と結果列が変化する。

### 7. [must-fix] CLI test は main の本体を空にしても通る

- **(a) 何が壊れるか** — `main()` 冒頭を `return 0` にする変異で A10 は通る。sanctioned route の pair 生成、2 arm invoke、receipt 出力、pair 検査の到達性を固定していない。
- **(b) 根拠** — test は callable、文字列 `def main(`、禁止名 2 個だけを見る: `orchestrator/tests/test_p3_b4_closed_critic.py:797-802`。実経路: `orchestrator/campaign/p3_b4_closed_critic.py:881-905`。
- **(c) 最小是正案** — factory を制御可能な seam で差し替えて `main()` を呼び、2 invoke、pair 検査、terminal receipt path を含む stdout、失敗時 rc=1 を検査する。
- **(d) 成果物影響** —閉じた route が到達不能でも材料レポートが利用可能と扱い、旧 critic 経路の block を誤受理し得る。

### 8. [medium] 「real admitted fixture」の admission は実 API だが、証拠材料と layout は合成

- **(a) 何が壊れるか** — digest は本当に `make_critic_digest` を通るが、source/diff/input hash は合成文字列由来、controller layout は mock、role 応答も fake runner である。P1 の `# rejections` は赤が空でも renderer が常に出す見出しなので、fixture の赤到達を証明しない。
- **(b) 根拠** —合成 evidence: `orchestrator/tests/test_p3_b4_closed_critic.py:74-125`、mock layout/runner: `同:171-210,213-274`、実 digest 経路: `同:158-168`、見出しは無条件: `orchestrator/critic/digest.py:1303-1307`。
- **(c) 最小是正案** —表現を「policy-admitted synthetic WAL fixture」へ縮小し、少なくとも `b4-fixture-reject` の on 出現/off 不出現を固定する。実 source evidence を使う end-to-end 正例を 1 本追加する。
- **(d) 成果物影響** —実 campaign だけが過剰拒否される場合を見逃し、certified 受理集合が空または偏ったまま材料レポートへ反映される。

### 9. [must-fix] M15 は provider 以外の closure entry の内容を固定しない

- **(a) 何が壊れるか** — digest entry を role file bytes の hash に差し替える等の変異が通る。末尾の「変更した dict の hash が違う」は production を通らない数学的恒真検査。
- **(b) 根拠** — manifest: `orchestrator/campaign/p3_b4_closed_critic.py:424-447`。test が bytes を再計算するのは provider だけ: `orchestrator/tests/test_p3_b4_closed_critic.py:650-669`。
- **(c) 最小是正案** — expected key から実 path/contract bytes への対応表を test 側に独立定義し、全 6 entry を再計算して exact 比較する。
- **(d) 成果物影響** —意味の異なる projection が同じ群へ併合され、certified 選択の比較群と材料レポートの projection 参照が壊れる。

### 10. [medium] exact schema の型・値 gate に負例がない

- **(a) 何が壊れるか** — response の bool 型検査や文字列型検査、payload の result 列挙を削る変異が生存する。M10/M9 は key 集合しか攻撃していない。
- **(b) 根拠** — production gate: `orchestrator/campaign/p3_b4_closed_critic.py:255-301`。test: `orchestrator/tests/test_p3_b4_closed_critic.py:525-551`。
- **(c) 最小是正案** — `reverse_recommended=1`、各文字列 field の非 str、空 digest、未知 result を 1 field ずつ変えた負例として追加し、例外メッセージも固定する。
- **(d) 成果物影響** — malformed decision/outcome が成功 receipt に束縛され、後続 consumer の受理集合または停止・方向列を変える。

## 追加確認

- P1〜P3 は名目上実装済み。P4 も呼ばれるが、test-only receipt の手動昇格なので正例として不適格。
- 直接登録された M1〜M12、M14、M15 の provider-entry 削除、A3、A4、A7、A9 は対応変異を概ね kill する。検出力ゼロ相当なのは、P2/A8 の未接続 state assert、A10 の CLI 本体、M15 末尾の local hash assert、長さだけの hash assert。
- 負例だけの test は見当たらない。一方、実効的に正例だけなのは A8、A10、hash chain の一部。A13 は正負を持つが複合負例なので各 gate の対にはなっていない。
- working-tree hash、時刻、tmp path、現行 SHA の固定期待値は見当たらない。`L.PIN` と closure hash は実行時導出であり、揮発値の焼き込みではない。
- D824 決定 2 の docstring 義務は後退していない。両 docstring は「critic role 自体の能力遮断」と「専用 controller の実効 lowering」の双方を証明しないと明記している: `orchestrator/tests/test_p3_s4_loop.py:1833-1839,1948-1952`。事前登録側の限定も残る: `docs/phase3-b4-reflux-ablation-preregistration.md:214-248`。
- 事前登録が認める既知の生存変異も残る。`build_digest()` 側から赤を緑 digest に混入すれば、off receipt は閉鎖を主張しないまま成功できる: `docs/phase3-b4-reflux-ablation-preregistration.md:250-256`。所見 1 はそれより狭い controller 1 行変異さえ未検出である。

## 総括

must-fix は所見 1、2、3、4、5、6、7、9。特に、off を `reflux=True` にする 1 行変異が全 test をすり抜けることと、test-only receipt の certified 昇格を test 自身が正例化していることは、報酬ハック面の直接的な blocker である。

したがって、この実装と test の組合せは現状では採用不可。production の主要経路は裁定に沿っているが、test が off 閉鎖・certified provenance・receipt 束縛を固定できていない。