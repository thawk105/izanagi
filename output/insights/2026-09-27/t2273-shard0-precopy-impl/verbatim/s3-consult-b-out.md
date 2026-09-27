## 所見

- **B1 — must-fix — [s2-plan-out.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s2-plan-out.md:22)**
  正例は job を直接動かす設計で、効果の本質である「`pytest_configure_node` で起動し、collection と複製を重ねる」経路を通らない。起動を builder 開始時へ遅らせても、予定した変異では落とせない。正例一件の中で hook を通して job が直ちに起動することを確認し、起動位置を遅らせる変異を期待 node に加える。[現行 hook](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/conftest.py:2613) が確認点。

- **B2 — should — [s2-plan-out.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s2-plan-out.md:11)**
  `isinstance(config, pytest.Config)` は既存の `_early_memo_selected` にない発火条件で、模擬 hook 検査も妨げる。既存条件をそのまま共用し、既存の模擬 hook test では新 job を局所的に差し替える方が短い。実受入で発火することは B1 の検査で固定する。

- **B3 — should — [s2-plan-out.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s2-plan-out.md:3)**
  `ready.json.pending`、`ready.json`、`failed.json` の三種は過剰。worker が必要とするのは「完了したか、失敗したか」だけなので、成功・失敗を一つの結果ファイルへ atomic rename し、無ければ期限まで待つ形で足りる。thread の例外は controller job に保持する。session path の受け渡し、180 秒上限、終了時 join は維持する。

- **B4 — must-fix — [t2273lc_ab_analyze.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:19)**
  移植元の E1 は旧 test 名一件を B の追加 node と決め打ちしている。新 test 名と実際の collection 差を投入前に固定する必要がある。また、B の早期 memo 超過を旧 wave と同じ理由で自動的に infra 扱いしてはならない。今回の背景 I/O との因果を分類し、実装由来ならその赤を保存して修正後に系列を最初から測り直す。

- **B5 — should — [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s1-brief.md:23)**
  0.24 node 時間は「全走三 shard が平均 287 秒」の概算として算術上正しい。ただし単価の元になった 29 job は失敗走を含み、成功走の単価ではない。前回と同程度の取り直しまで含めると、系列だけで前回実績の **2.31 node 時間**相当になる。検査込み二時間以上の確認を要する見積りとして明示する。

## 計測の事前登録案

1. **A / B:** A は着手直前の local main、B は A に今回の実装と正例だけを加えた tip。各 SHA と clean 状態を固定し、記録 commit は測定後に作る。
2. **順序:** 実受入全走を A→B、B→A、A→B の隣接三対で逐次投入する。半走を別の対へ流用しない。
3. **門番・温め:** 前回の他 session 受入 leader ≤1、load1 ≤60 と安定確認を使う。両 tree に同じ collect-only 温めを一回ずつ行う。自分の他 job は系列中に重ねない。
4. **有効性:** 三 shard 緑、各走前後の SHA・clean 一致、条件内の collection と共通 node の shard 割付一致を確認する。A/B の collection 差は、新規正例一件だけと事前に固定する。赤は根拠を付けて infra / 実装由来に分類する。infra なら対全体を同順序で取り直し、実装由来なら系列を停止して修正後に最初から再測定する。
5. **判定量:** 各対の `Δᵢ = W₀(Aᵢ) − W₀(Bᵢ)`、`rᵢ = Δᵢ / W₀(Aᵢ)`。対差と対率の中央値を別々に報告する。land 条件は前回と同じ **三対すべて Δᵢ > 0、かつ対率中央値 ≥10%**。
6. **五分判定:** 実受入全体の待ちを問題にしているため、B の **`W_max` 三走の中央値 ≤300 秒**を別判定とする。`W₀` だけでは shard 1・2 への律速移動を見逃す。三走それぞれの超過も併記する。
7. **補助量:** 各走の `W₀・W₁・W₂・W_max`、最遅 shard、shard 0 の `O_max・L・O_max−L`、最大占有 worker の item 列を記録する。現行の実受入出力に写し待ちの直接計器はない。builder 時間や W₀ の差は待ち時間の分離可能な代理量ではないため、計器を追加せず「不明」と記す。
8. **四通りの記録:**

   | land 条件 | 五分判定 | 記録と次の扱い |
   |---|---|---|
   | 達成 | 達成 | (a) を land。実受入で両条件達成と記録 |
   | 達成 | 未達 | (a) の改善として land、五分未達と明記。次は (b) 発行 subprocess と記録して止める |
   | 未達 | 達成 | 性能改善として land しない。測定 B の五分達成は参考値として記録し、main の達成とは書かない |
   | 未達 | 未達 | land しない。五分未達、次は (b) と記録して止める |

   判定不能は四通りに押し込まず、原因と有効対数を記録する。

## 計算量見積り

前回実績は `8,333 ÷ 29 = 287.3` 秒／shard job。失敗なしの六全走は `6 × 3 × 287.3 = 5,172` 秒、**1.44 node 時間**。前回は有効三対に十走・29 job を要し、系列実績が **8,333 秒＝2.31 node 時間**だった。[前回 insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md:79)

これに焦点走の前回実績 303 秒、記録前受入一回の概算 862 秒を足すと **約2.64 node 時間**。変異・温めの job Elapse は前回資料に集計値がないため、この数字には入れていない。実績型の見積りは二時間を超える。失敗がなくても焦点走と記録前受入を含め約1.76 node 時間となり、変異分の余地は小さい。

## 削れるもの

- 変異六本のうち「thread を起こさない」と「ready marker を作らない」は、現案では同じ待ち期限超過に収束する。後者を外し、**起動を `pytest_configure_node` から builder 時へ遅らせる変異**に替える。
- `copy_function=shutil.copy` の変異は mtime 契約を守るために残す。実 repo 直読、worker ごとの実関数呼出し、全件コピーもそれぞれ別の欠陥を殺す。
- 正例は一件で足りる。ただしその一件が hook 起動、session 一回、写しからの複製を通ることが条件。symlink 状態の追加 assert は、実関数が symlink file を複製しないため省ける。
- 実受入への写し待ち計器、追加 gate、台帳は加えない。

## GO 判定

**修正後 GO** — hook 起動を正例と変異で固定し、probe の E1・赤分類・二時間超の見積りを測定前に直す。

## 総括

plan の主経路は D2253 項2に沿う。最大の穴は、正例が collection 中の起動を検査しない点。三対の land 条件は前回どおりでよく、五分は `W_max` で別判定する。前回実績を単価にした総量は、変異を除いても約2.64 node 時間。