# 親の provisional 見解 (段 3 の攻撃対象、2026-09-26 19:4x JST)

段 2 plan (`codex/s2-plan.md`) に対する親の暫定見解。すべて攻撃対象であり、裁定ではない。

- (Q1) plan §2 の「V28 は作れない、build・run を投入しない」に親は反対の暫定見解を持つ。依頼 (`request.md`) は V28・V29・V36 の実走を求めている。わざと壊した変異が未定義動作 (未完成 body の読み、回収済み版の参照) を持つこと自体は、計算ノード上の使い捨て test binary の問題で、規律 2 (壊し patch を baseline に混ぜない) にも規律 1 にも触れない。先例: V07 sort-nonswo は SIGSEGV を「別の層 (process の異常終了)」として記録した (`output/insights/2026-09-23/t2847-sort-nonswo/README.md`)。したがって V28 は build・実走し、crash / 停止 / verdict のどれが出ても分類規則で記録する、が親の暫定案。ただし (a) Version が free されるのか pool 再利用なのか、(b) YCSB (insert / delete を生成しない) で abort INSERT の Tuple 削除経路 (SI:579-586) に届くか、(c) R 行の cstamp が trace 出力時の再読で orphan を隠すこと、を source で確かめたい。
- (Q2) V29 は、同じ key を読んで書く取引の R 行が update で消える (SI:239-247) ので、典型的な lost update から巡回は作れず、構造的に盲点になる公算が高い (設計書 §4.5 と同じ)。K 条件 (rmw=false) では無改変 si 自体が write skew で N を出す (L0 K t4 = 巡回 2,443) ので、V29 の K t4 の N を V29 の検出と数えられない。親の暫定案: V29 の検出の主張は「同 job の V2 対照に対する巡回の増減」では立てず (性能比較でなく判定の比較だが 1 走の差は帰属できない)、発火診断 (changed・committed) と巡回の有無を並記し、K t4 は「帰属不能 (対照も N)」、W は「盲点 (R 消去で巡回が構造的に不能)」と分類する。
- (Q3) plan §3 の分類の si への写し (「盲点」を certified と呼ばない、「発火未確認の I」、V36 は「無改変 si の巡回検出 / 巡回未観測」) を親は暫定採用。
- (Q4) job は J1 = V2 + V29、J2 = V2 + V28、各 K/W × t1/t4 の 4 cell、同 job に V2 対照。計算見込みは 2 job 合計 3〜6 分、変異 matrix・焦点走・受入を足しても 2 node 時間未満。
