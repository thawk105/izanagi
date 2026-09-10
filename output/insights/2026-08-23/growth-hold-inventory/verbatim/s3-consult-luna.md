## 所見

### 1. [real] pinned fast path の成立条件と fallback が証明されていない

段 2 が示すのは、named candidate が見つかり、session identity と rollout SHA の検査を通れば早期 return することだけであり、実装上の `eligible` 条件式全体ではない。[s2-plan.md:112](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:112) [s2-plan.md:126](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:126)

確認できる条件は少なくとも以下である。

- `pinned_label` が既知の pin を指すこと
- 再帰列挙から対応する named candidate が得られること
- candidate の session identity が要求された POS identity と一致すること
- candidate bytes が POS の rollout SHA と一致すること

現 corpus では `pinned_label="POS"` が同じ path を 0.036 秒で返しているため、現在は fast path に入ったことだけは確認できる。[probes.txt:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/probes.txt:7) [probes.txt:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/probes.txt:8)

一方、段 2 自身が「valid named candidate のときだけ全 corpus scan より前に return」と書いているため、少なくとも candidate 非適格時には遅い全 corpus 経路へ沈黙して fallback する。[s2-plan.md:128](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:128) 一意な POS rollout が残っていれば、fallback 後も緑のまま遅くなりうる。identity/SHA 不一致が例外か fallback かは、射影に `tools/codex_reasoning_ab.py` 本体が無いため実 file では確定できない。

**成果物への影響:** certified 選択は「高速化済み」と確定できず、レポートの 0.036 秒と予算余白は無検知で 18〜330 秒級へ退行しうる。

### 2. [real] pinned 案は比例源を除去せず、速度退行の検査も追加しない

pinned 経路でも `rglob` による `Sdir(t)` が残ることを段 2 が明記している。[s2-plan.md:13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:13) [s2-plan.md:133](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:133) これは output artifact corpus が単調増加する D463 の比例集合に該当する。[D463.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/D463.md:3) [D463.md:6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/D463.md:6)

さらに実装案は引数追加だけで、fast path を通ったことを静的に保証する assertion、fallback 回数の検査、または予算検査を持たない。[s2-plan.md:164](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:164) 段 2 が併記する固定 `_REAL_ROLLOUT` と SHA 検証の案だけが、入力集合を固定しこの事故を構造的に除く。[s2-plan.md:133](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:133)

**成果物への影響:** pinned 案を選ぶ限り台帳上の D463 分類は「比例」のままであり、レポートに「比例源除去済み」と書けば誤記になる。

### 3. [real] replay integration の hold 継続は D451 と両立していない

段 2 は replay node の代替を「限定的」と認め、完全 replay と tamper 実行の代替ではないと明記しながら hold 継続としている。[s2-plan.md:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:34) D451 は、その防壁の既定 node がゼロになる場合は保留しないという決定である。[D451.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/D451.md:3)

「段 4 裁定付き」では既存のユーザー裁定を上書きできない。等価な動的防壁を示す、node を最適化して再導入する、またはユーザーへ新たな裁定を求める必要がある。

**成果物への影響:** 暫定の「再導入 11 / hold 5」は certified にできず、D451 をそのまま適用すれば「再導入 12 / hold 4」へ受理集合が変わる。

### 4. [refuted] fixture setup の二重計上と parametrize 数え違いはない

opt-in は 544.05 秒で、module setup 13.75 秒を含む。[durations-16-opt-in.txt:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/durations-16-opt-in.txt:8) [durations-16-opt-in.txt:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/durations-16-opt-in.txt:25) したがって `544.05 - 13.75 = 530.30` 秒、基準線との和は `665.75` 秒であり、親の約 665 秒は粗い marginal 算術として成立する。単一 pytest process の予測としては opt-in 側の session overhead まで足すため、厳密値ではない。

16 node は focus 3 items と prompt 3 itemsにより20 items、再導入11 nodeは15 itemsになるため、段 2 の数え方も正しい。[s2-plan.md:149](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:149) `<0.005s hidden` は4 nodeではなく4 duration phaseであり、選択された2 callの合計誤差は0.01秒未満である。[durations-16-opt-in.txt:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/durations-16-opt-in.txt:24)

**成果物への影響:** node/item 数や call 合計を訂正する必要はないが、665 秒を再構成後の実測値として台帳へ記録してはならない。

### 5. [real] 300秒をこの file が使い切れるという根拠がない

射影された D335、D451、D463 のいずれにも300秒上限はない。親 brief は「全走5分」とだけ述べ、それを同 file 単独の135.45秒へ直接適用している。[s1-brief.md:86](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s1-brief.md:86) [s1-brief.md:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s1-brief.md:94)

300秒が suite 全体の上限なら、この file に残り75.30秒を全額配分する計算は成立しない。他 file の走行費を先に控除する必要がある。per-file 上限なら、その権威元の参照が欠落している。

**成果物への影響:** レポートの「prompt に75.30秒残る」と11-node選択の予算適合は未認証となる。

### 6. [real] 同時実行により壁時計値は予算 certification に使えない

opt-in の prompt call は213.64、18.99、18.05秒である一方、外部 unpinned probe は329.754秒である。[durations-16-opt-in.txt:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/durations-16-opt-in.txt:2) [durations-16-opt-in.txt:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/durations-16-opt-in.txt:5) [probes.txt:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/probes.txt:7) 同一nodeで同時に5.13 GiB corpusを読む条件では、I/O競合と相互のpage-cache warmingを分離できない。

同様に、544.05秒のopt-in総時間、135.45秒のbaseline、0.040秒のrglob、0.036秒のpinned lookupも孤立測定ではない。[durations-default-baseline.txt:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/durations-default-baseline.txt:22) [probes.txt:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/probes.txt:1) PASS件数は有効な過去観測だが、時間値はcertification-gradeではない。

**成果物への影響:** レポートと台帳の全所要時間は「同時実行で汚染された一点観測」へ格下げし、選択後のserial単独再測定まで予算判定を空欄にする必要がある。

### 7. [refuted] 現プランでは `enforce_held_functions` の zero-hold 例外は起きない

`enforce_held_functions` は対象fileのholdがゼロなら確かに `ValueError` を投げる。[growth_test_holds.py:643](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/growth_test_holds.py:643) [growth_test_holds.py:648](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/growth_test_holds.py:648)

しかし段 2 は16件全部ではなく11件だけを外し、同fileに5件を残す。[s2-plan.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:5) 静的算出でも変更後に `test_codex_reasoning_ab.py` のholdは5件残るため、この例外は発生しない。将来5件も全解除するなら、同時に末尾のenforcement呼出しを除去または条件化する必要がある。

**成果物への影響:** 現11件案の受理集合はこの例外では壊れないため、certified選択数の修正は不要。

### 8. [real] inventory digest と contract consumer の互換性が未監査

inventory は全keyから `count` と `key_sha256` を生成する。[growth_test_holds.py:697](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/growth_test_holds.py:697) [growth_test_holds.py:703](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/growth_test_holds.py:703) 現物から静的算出すると、11件除去により次へ変わる。

- `count`: 59 → 48
- `key_sha256`: `30e646a80e6dfc7c04ec2e249462789ac7cb10f1afaa6979491a3312d5d6508c` → `9116fa7882aef824e5821f14602521e20ba75d0369723afcb4b5f56e9805a942`

段 2 は contract test と `tools/hold_inventory.py` を射影外としており、digest pin consumer の在否を確認していない。[s2-plan.md:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:68) [s2-plan.md:78](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:78) このdispatchにも当該実fileが射影されていないため、在否は判定不能である。pinが存在すれば、別waveの編集面を触らずには赤を解消できない。

**成果物への影響:** 台帳とレポートが参照するcount/digestは必ず上記へ変わり、consumer pinがあれば本waveの受理集合全体が赤になる。

### 9. [refuted] D452だけでは既存の変異事前登録は壊れない

hold解除により11 node / 15 itemsが将来の `expected_nodes` 候補へ加わるが、既存の既定走行nodeがskipへ変わるわけではない。[s2-plan.md:149](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:149) D452の適格集合が拡大するだけで、既存登録を自動的に無効化する論理はない。

ただし「既定node全体」を自動列挙してcertified選択を作るconsumerがあれば結果は変わるため、digest consumerと同様に別途監査が必要である。

**成果物への影響:** 既存変異登録の受理集合は直ちには変わらないが、新規登録候補集合は11 node / 15 items増える。

### 10. [refuted] 提案自体は稼働中waveの3 fileを編集しない

実装案の編集対象はregistryと対象testの2 fileだけであり、`conftest.py`、contract test、`tools/hold_inventory.py`、production toolを明示的に除外している。[s2-plan.md:162](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:162) [s2-plan.md:177](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s2-plan.md:177) registry内部も非空、unique rowであれば11行削除を受理する。[growth_test_holds.py:518](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/materials/growth_test_holds.py:518)

ただし所見8のdigest pinが存在した場合は、禁止fileを編集しないまま緑になるとの主張は成立しない。

**成果物への影響:** registry単体の受理集合は成立するが、contract全体の緑は未認証のままである。

## 総括

must-fixを重い順に挙げる。

1. replay integrationを非等価な静的防壁でholdしない。等価防壁、最適化後の再導入、または新しいユーザー裁定のいずれかを必須とする。
2. prompt nodeは固定 `_REAL_ROLLOUT` とSHA検証へ寄せるか、fast path成立を決定論的に検査する。現在のpinned引数追加だけでは比例性も退行事故も塞げない。
3. 300秒の適用範囲を権威元で確定し、変更後のtarget nodeと同file全走を同時負荷なしで再測定する。併せて変更後digestのconsumer pinをread-only監査する。