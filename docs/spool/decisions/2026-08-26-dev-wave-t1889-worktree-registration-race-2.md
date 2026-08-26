---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1889-worktree-registration-race
seq: 2
---

## {{D:worktree-registration-race-is-fixed-in-tests-not-production}}. 生きた worktree 登録の競合は、テスト側を hermetic にして閉じ、production の受理集合は変えない

**決定:** 共有 repository の生きた worktree 登録を読むために並行 session の撤去と競合して落ちる
テストは、**テスト側で必要な状態を自分で作る形へ直す**。production の登録 scan は変更しない。
churn 中に完全な 1 枚が読めなければ従来どおり fail-closed で拒否する。

主題が live authority に結び付く node だけを逐語 allowlist に残し、それ以外は `tmp_path` の中に
自分で作った登録骨格へ寄せる。骨格は実際の登録を持ち、導出関数を実物として通す。
allowlist の node には登録 churn の失敗本文だけを狭く捕捉する有界 (3 回・sleep なし) の再試行を
テスト内に置く。**production 側には再試行を置かない。**

新しい node が再び live registry を読む形は、AST で class 内も含めて全 test 関数を列挙し、
hermetic fixture か逐語 allowlist のどちらかであることを要求する gate が塞ぐ。
allowlist は `frozenset` literal とし、実使用からの自動生成を literal 形の検査が拒否する。

**理由:**
- **有界な取り直しを production へ入れると、実行の流れ全体では受理集合が広がる。** 現行は churn を
  見た時点で拒否する。取り直し版は「後から取った、より小さい roots」を成功として返すため、
  撤去された worktree の中の work_root / output_root が repository-external として受理されうる。
  1 枚の scan の内部は不変でも、trace 全体では不変でない。churn を起こせる立場の者は
  最初の観測を意図的に失敗させ、後続だけ自分の登録を外す形で timing を合わせられる。
- **`missing_ok` 相当と走行開始時 snapshot は、いずれも roots を減らす方向である。** roots が
  小さくなると repository-external gate は緩む。絶対規律 2 が禁じる向きと同型である。
- **観測される害はテストの代表性の問題に留まる。** 実測された損害は受入全走が非帰属に赤くなる
  ことだけで、certified 選択・レポート・台帳の値は変わらない。production の fail-closed は
  measurement launch の挙動としては正しい。
- **同主題のユーザー裁定 (D1045) が択一の順序を与えている。** 「検査が要求する状態を自分で作る」を
  採り、「判定器の基準を変える」と「前提未充足なら明示的に飛ばす」を却下している。
  同一の事故ではないので拘束力ある裁定としては扱わないが、向きは一致する。
- **上限 3 回という値を凍結する根拠が無い。** 親の実測では、連続 churn 下で 3 回でも 1.5% 残り、
  48 worker 相当の regime は測れていない。D1017 が同じ理由で回数の引き上げを退けている。
  production へ入れるなら回数の根拠が要る。

**却下した選択肢:**
- **production へ有界な取り直しを入れる** — 上記のとおり trace の受理集合を広げる。
  実装案自体は成立するが、受理集合を変える判断なので裁定が要る。
- **既知の非帰属赤として hold registry へ登録する** — susceptible な基底 node は 26 件で、
  実測できた赤は 5 件しかない。registry は node ごとの実測赤と canonical failures の逐語一致を
  要求するので正直に登録できない。26 node を hold すると repo-external gate の実 repo 結合が
  丸ごと消える。D1017 が同型の案を同じ理由で退けている。
- **production に identity 注入 seam を新設する** — D349 が authority を設置場所から導くと定め、
  caller は roots を増やせるが減らせないとしている。注入 seam は caller が減らせる形になる。
- **land 側の同型経路も同じ wave で直す** — F633 は land 側の独立再発を証明していない。
  確認できる例は coordinator の 1 例だけで、独立 2 例を要求する族一般化の条件を満たさない。
- **全 node を hermetic にする** — live authority が実 repository 内の work_root を拒否することを
  検査する node は、hermetic にすると検査の意味が消える。

## {{D:test-authority-partition-needs-an-anti-drift-gate}}. テストの authority 分割は、逐語 allowlist と AST gate の対で固定する

**決定:** 「どのテストが実環境の authority を読むか」を分割したら、その分割を機械で固定する。
分割は逐語の allowlist と、全 test 関数を AST で列挙して allowlist 外の node が authority へ
到達していないことを要求する gate の対で表現する。allowlist は immutable な literal とし、
実使用から自動生成してはならない。

**理由:**
- **分割は「今ある node」を直すだけでは保たれない。** 後から足される node が同じ穴を開ける。
  実際に本 wave の初版 gate は top-level 関数だけを見ており、class 内の test は無検査で
  live scan を追加できた。
- **述語が自分の候補集合から生成されると恒真になる。** allowlist を実使用から導けば、
  どんな逸脱も allowlist ごと動いて常に一致する。literal と実行時値の一致検査は、
  allowlist が独立した台帳であるときだけ意味を持つ。`frozenset` にすると
  `clear()` / `update()` による後追い改変も構造的に塞がる。
- **恒真でないことは変異でしか示せない。** 本 wave は allowlist から 1 件外す変異、
  未固定 node を足す変異、allowlist を計算式へ置き換える変異の 3 つで gate が赤くなることと、
  正当な追加では緑のままであることを実測した。

**却下した選択肢:**
- **命名規約だけで分割する** — 規約違反を機械が検出しない。
- **allowlist を実使用から生成する** — 恒真になる。
- **gate を他 file へも広げる** — file open 数と総 bytes に比例して所要が伸び、
  共有 filesystem の遅延まで取り込む。分割が必要になった file で個別に足す。
