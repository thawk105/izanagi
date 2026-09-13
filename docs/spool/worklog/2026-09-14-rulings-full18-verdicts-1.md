---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: rulings-full18-verdicts
seq: 1
title: /rulings 全件 第 18 回 — 索引 16 件を推奨どおり裁定した。相談が起草推奨を 7 件で覆し、機械抽出 38 件のうち 22 件が既裁定だった (docs のみ、branch worktree-rulings-full18-verdicts)
---

## 本文

- **窓は entry 1426〜1473。** 前回の全件走は 2026-09-10 の裁定 (D1936、全 50 項) で、
  その前が第 17 回 (entry 1407、D1872〜D1911) である。収集開始時点の main は `abbef52d5`。
- **機械抽出 38 件のうち 22 件が既裁定だった。** いずれも第 17 回の裁定 D1872〜D1911 が
  主題で覆っており、持ち越し本文が裁定後に更新されていなかった。T-ID で decisions を引くと
  38 件中 34 件が 0 件になるため、主題照合でしか出ない。恒久対応は
  {{T:ruled-items-stale-body-sweep}} として起票した。
- **稼働中の wave が既裁定を「裁定待ち」として再提起していた。** 起動検証済み凍結の関門
  (二読 fallback を現状維持にするか exact 必須へ縮めるか) は D1872 が 2026-09-09 に
  exact 必須で裁定済みだが、branch `worktree-dev-wave-t2067-efg-residual` の未 land fragment が
  2026-09-14 も裁定待ちとして書いている。**索引には載せず、該当 wave へ伝える。**
- **別系統モデル 2 本を起動した** (推奨の当否・索引漏れ、いずれも相談段・read-only)。
  **2 本とも `outcome=accepted` / `stop_reason=completed`。** 推奨の当否が wall 365 秒・
  model call 15・出力 9,672 token、索引漏れが wall 476 秒・call 23・出力 12,042 token。
  入力はほぼ cache 済み (124 万 / 281 万)。
- **相談が起草推奨を 7 件で覆した。** 4 件を既裁定として索引から外させ、6 件を新たに拾わせ、
  1 件の根拠を「不足」へ動かした。外した 4 件の内訳は、対の記録の照合の直し方
  (handoff にユーザーの委任指示が残っており返すこと自体が誤り)、事前登録の担当欄の授権
  (D1936 末尾が追加授権ではなく追記反映と決着済み)、B-10 の未了の数え方
  (D1724 が明文で内側に数えると書いており食い違いは読み違い)、変異試験の外側監視の契約
  (D1910 が実測先行と決定済みで実測は未取得) である。
- **組の同一性 (T-2485) は起草が D1841 で外していたが、相談の指摘で索引へ戻した。**
  同決定は組の中の規則と現行設定との照合要否を定めたもので、設定を変えて別の組にする経路は
  決めていない。現物で確認して戻した。
- **較正の選択規則 (項 1) だけは 2 モデルの推奨が割れた。** 起草は「下限値を動かさないので
  検査は緩まない」として規則改定を、相談は「選択器と判定器を合わせた挙動が却下から受理へ動く」
  として現状維持を推した。両論を提示してユーザーが起草推奨を採った。相談の論点は決定の
  理由欄へ残した。
- **セッション異常: 相談子の effort が既裁定に反していた。** 2026-09-10 のユーザー裁定は
  「dev-wave で起動する Codex は当面全段 `gpt-6-astra` / `medium`」だが、本回は
  `--reasoning high` で 2 本とも投入した。モデルは権威から導出されるので裁定どおり
  (受領証の requested / recorded 双方が `gpt-6-astra`) だが、effort は相談段では caller 指定であり、
  親が medium へ揃えなかった。**launcher は plan / consult の effort を検証せず、受領証にも
  effort 欄が無いので、違反は rc=0 で静かに通る。** 同日の稼働 wave も割れていた
  (1 本が high、2 本が medium)。費用側の逸脱であり結論を弱める向きではないため引き直していない。
- **会話中に lane 名の改名が 2 度変わった。** 一度 `probe` / `counter` が採られたが、
  `probe` が下見の走りを指す語として既に定着しているため撤回し、`lens-a` / `lens-b` になった。
  決定は {{D:consult-lane-names-to-lens-ab}}、実装は {{T:consult-lane-rename}}。
- **実装面の差分は 0 である。** 変更は台帳 fragment だけで、`python3 tools/check_docs.py` は違反なし。
- 索引・起草推奨・相談の生出力は `/work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260914/`。

## 次の一手差分

### 更新

- [T-2592] **P1・裁定済み ({{D:rulings-full18-verdicts}} 項 1、2026-09-14 /rulings 全件 第 18 回) → 実装待ち**:
  レコード数の選択規則へ「品質検査の取りこぼし率下限も満たす最小の値を選ぶ」を足す。
  条件は 3 つ — workload に依存しない形で書く、走らせ直す前に登録する、今回の rr5 の却下記録は
  却下のまま残す。下限値 0.50% は動かさない。実装面なので Codex role=author と変異事前登録が要る。
  base: 23688dc63cb4eac28c0947850a65f5d39f5bc5fb7af15661aa13674643fb6f63
- [T-2515] **P1・裁定済み ({{D:rulings-full18-verdicts}} 項 1) → 実装待ち**: rr95 の accepted 較正は
  取得済み (registered/calibration-5c836a22eff9ab40.json)。rr5 は項 1 の選択規則改定が着地してから
  取得する。迂回して accepted を作らない。
  base: 5b44d70f320a2d7bc608b1584f41e3b8c943acfa95b025a4f04ee17985f69632
- [T-2594] **P2・裁定済み ({{D:rulings-full18-verdicts}} 項 2) → 追補待ち**: 保持群のラベルが
  凍結の権威と左右逆になっている件は、決定側の記述を追補で正す。凍結側は触らない。
  base: 47035925d9d0b39af1abb1fca8a9b483a3606f08948cb885e31492a9cdf8c28a
- [T-1851] **P1・裁定済み ({{D:rulings-full18-verdicts}} 項 6) → 明文化待ち**: D2 実装完了と保全 producer は
  前回のまま。持ち越していた単位分割と、誤 ordinal 束縛の訂正・sealed terminal 後の正当遷移は、
  実装を差し戻さず局所的な訂正として履歴へ明文化する形で追認する。D1660 の一般則へ広げる改訂は行わない。
  残るのは D1936 項 11 の束縛修正と C3c の実値域取得、D1909 の後続版整理。
  base: d76fc88c43199138583a09a863865a28b46800a9e802839613aa5b7bda5b4454
- [T-2590] **P2・裁定済み ({{D:rulings-full18-verdicts}} 項 5) → 実装継続**: 計測経路に残る pilot 専用の
  分岐を一式で揃える作業は AI 実装のまま進める。正式測定の認可は [T-1505] のまま据え置き、
  実装が閉じた時点で改めて諮る。本項目は認可の代替ではない。
  base: 3a553540208b2058ca959e9a2054cfa85cb35f30408f79365775b05887fb8d5d
- [T-2267] **P2・裁定済み ({{D:rulings-full18-verdicts}} 項 7、D1978 の 3 件に回答) → 据え置き**:
  (i) 対象限定の測定実行経路は今は作らず、必要になった時点で族の再設計と一緒に諮る。
  (ii) 資源 class は `unknown` を据え置く。測れた場合の扱いは測れてから決める。
  (iii) 凍結入力は既存 insight 配下へ、元 job dir と sha256 を明記して保全する。
  base: 559361cde718cb70e74ccd6a635dfa7fa68a95b0ec51d3e67c596775169f1696
- [T-2518] **P2・裁定済み ({{D:rulings-full18-verdicts}} 項 8) → 記述待ち**: 依存 prefix / FetchContent の
  供給と当該 CLI 入力をつなぐ最小の接続は新設しない。A+B+C 適用木と clean stock の supply 比較は
  測れていないものとして記述に残す。13macro witness 新設・production 配線も含めない。
  base: 297cc15c5f67f7c62d4295cc6c74fb5f183af0ed2160b453b60c5179368a40b3
- [T-2469] **P2・裁定済み ({{D:rulings-full18-verdicts}} 項 9) → 明記待ち**: 受入に「起点を導入した
  commit」を縛る検査を足さない。縛っていない範囲を保証の限界として明記する。
  base: 493cadd10c7b7772d16cae53fac54d310efbed55facba37054b0a9916f9d1c61
- [T-2485] **P3・裁定済み ({{D:rulings-full18-verdicts}} 項 10) → 明記待ち**: 組の同一性を policy の
  raw bytes で決めている件は閉じない。保証の限界として明記する。`--policy` は shipped 2 path に
  限られ書き換えは git diff に出る。
  base: 8e15cc2e45c693a721fea69c73d3f5d248b36f1e08dd61317ed5aa3bc8abc585
- [T-2474] **P3・裁定済み ({{D:rulings-full18-verdicts}} 項 11〜15) → 明記待ち**: 起点 schema へ
  作成時刻・実行者・実行 code 版を足さない。記録していない範囲として記述に残す。
  base: 89ac133f838a6d8881f3e8147d1c63affefa2cf8d135213b0d21c565b9b5e29f
- [T-2358] **P3・裁定済み ({{D:rulings-full18-verdicts}} 項 11〜15) → 明記待ち**: mocc trace pair の
  consumer 側へ policy 束縛の推移的証明を持たせない。job 単位までであることを明記する。
  base: 81702bc34f1be19836b538befc327fdda602f2680425f39bb3a6cf88aa1e3b77
- [T-2359] **P3・裁定済み ({{D:rulings-full18-verdicts}} 項 11〜15) → 明記待ち**: non-blocking open と
  strict JSON の読み口を他の submitter へ一般化しない。mocc trace の 3 script に閉じたままとする。
  base: 7b207617fdceacb961b6f0f003c1c284a57f9b7a782897425fd85012cddcf0d7
- [T-2376] **P3・裁定済み ({{D:rulings-full18-verdicts}} 項 11〜15) → 明記待ち**: submission / completion
  receipt へ qstat の raw stdout / stderr / rc を保存しない。producer-only invariant に留まることを
  明記する。**状態語彙の縮小は既に却下されており、保存の論点と一括しない。却下を維持する。**
  base: b0d026a2b3e5c778a6b370a2aa84def85324c8b51cf662fdcd90c8f925c51144
- [T-2476] **P3・裁定済み ({{D:rulings-full18-verdicts}} 項 11〜15) → 明記待ち**: gate report CLI へ
  評価器例外の理由を露出させない。同 CLI から読めない範囲として明記する。
  base: a497996c10642e867f83a2c6ed3d3250a4cd3aabff822dce221b673bd0c629bd

### 新規

- {{T:consult-lane-rename}} **P3・新規**: 相談段の `--lane` の値を `sol` / `luna` から
  `lens-a` / `lens-b` へ改名する。権威文書 DW-O01 の記法、`tools/dev_waves/launch_authority.py` の
  値域検査と写像、job 識別子の生成、関連テストに触れる。実装面なので Codex role=author と
  変異事前登録が要る。裁定 = {{D:consult-lane-names-to-lens-ab}}。過去の job 識別子と受領証は
  歴史的事実として書き換えない。
- {{T:ruled-items-stale-body-sweep}} **P2・新規**: 既に裁定済みなのに次の一手の本文が裁定前のまま
  残る項を一括で更新する。2026-09-14 の /rulings 第 18 回で、機械抽出 38 件のうち 22 件がこの型
  だった。決着は第 17 回の D1872〜D1911 が主題で下しているが、T-ID で decisions を引くと
  ほぼ全部すり抜けるため、毎回の収集が同じ 22 件を再提示している。対象 ID と対応する D 番号は
  同回の索引に列挙してある。
