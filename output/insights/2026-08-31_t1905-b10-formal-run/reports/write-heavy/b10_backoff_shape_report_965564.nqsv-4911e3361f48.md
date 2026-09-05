# B-10 backoff shape report

- official certification: `false`
- preregistration binding: `f0f9b2a1941707b29120a93af90cec70cfeabbf2309481f29cb19e8d71924e76`
- preregistration spec SHA-256: `9c59411476018d510c8fc5d57f203920ccd3b216e6c5f341ce6b97e45041a7c2`
- analysis code: `0a07481b8d3ff180b9817500b8ef44848ebe874e` / `34072fb2a5a5aed0e19ff1e653bb31bb71c3c434f32b3055c4b0b7a9e422c4ed`
- submission request: `965564.nqsv` (`002f7eb55ff1658422cfe77b6000100dc112e14ceb0037be22b4ded54671fb5d`)
- records: `1000000` (calibration artifact)
- exposure minimum: `10000` abort/backoff calls per cell

Formal driver 経路について、登録前に性能を見ていないという限定主張だけを行う。

| workload | block | point | shape | mean us | median tps | CV | abort rate | abort count | backoff calls | calls/s | nominal total wait us | correctness certified | unstable | exposure |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| write-heavy | block-1 | none | — | — | 2422011 | 0.0322 | 0.7849 | 134719086 | 0 | 0.00 | — | yes | no | indeterminate |
| write-heavy | block-1 | adaptive | — | — | 1354088 | 0.0179 | 0.1221 | 2830938 | 2830938 | 188729.20 | — | yes | no | met |
| write-heavy | block-1 | zero-loop | constant | 0 | 2439674 | 0.0083 | 0.7818 | 130595054 | 130595054 | 8706336.93 | 0 | yes | no | met |
| write-heavy | block-1 | constant-mu2 | constant | 2 | 3454217 | 0.0074 | 0.6364 | 90469377 | 90469377 | 6031291.80 | 180938754 | yes | no | met |
| write-heavy | block-1 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 3415244 | 0.0092 | 0.6350 | 89221334 | 89221334 | 5948088.93 | 178442668 | yes | no | met |
| write-heavy | block-1 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 3923154 | 0.0056 | 0.5006 | 58974695 | 58974695 | 3931646.33 | 294873475 | yes | no | met |
| write-heavy | block-1 | constant-mu5 | constant | 5 | 3982673 | 0.0200 | 0.4990 | 58789077 | 58789077 | 3919271.80 | 293945385 | yes | no | met |
| write-heavy | block-1 | constant-mu10 | constant | 10 | 3924247 | 0.0044 | 0.3873 | 37256513 | 37256513 | 2483767.53 | 372565130 | yes | no | met |
| write-heavy | block-1 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3932174 | 0.0034 | 0.3862 | 37156234 | 37156234 | 2477082.27 | 371562340 | yes | no | met |
| write-heavy | block-1 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3505891 | 0.0068 | 0.2586 | 18271151 | 18271151 | 1218076.73 | 456778775 | yes | no | met |
| write-heavy | block-1 | constant-mu25 | constant | 25 | 3430191 | 0.0046 | 0.2631 | 18381750 | 18381750 | 1225450.00 | 459543750 | yes | no | met |
| write-heavy | block-1 | constant-mu50 | constant | 50 | 2904761 | 0.0041 | 0.1915 | 10318030 | 10318030 | 687868.67 | 515901500 | yes | no | met |
| write-heavy | block-1 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2952224 | 0.0036 | 0.1882 | 10250505 | 10250505 | 683367.00 | 512525250 | yes | no | met |
| write-heavy | block-1 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 2375988 | 0.0029 | 0.1357 | 5599704 | 5599704 | 373313.60 | 559970400 | yes | no | met |
| write-heavy | block-1 | constant-mu100 | constant | 100 | 2346648 | 0.0044 | 0.1376 | 5623103 | 5623103 | 374873.53 | 562310300 | yes | no | met |
| write-heavy | block-2 | adaptive | — | — | 1356456 | 0.0098 | 0.1247 | 2918754 | 2918754 | 194583.60 | — | yes | no | met |
| write-heavy | block-2 | zero-loop | constant | 0 | 2428482 | 0.0166 | 0.7834 | 130553071 | 130553071 | 8703538.07 | 0 | yes | no | met |
| write-heavy | block-2 | none | — | — | 2386915 | 0.0097 | 0.7906 | 135235525 | 0 | 0.00 | — | yes | no | indeterminate |
| write-heavy | block-2 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 3434411 | 0.0152 | 0.6353 | 89880322 | 89880322 | 5992021.47 | 179760644 | yes | no | met |
| write-heavy | block-2 | constant-mu2 | constant | 2 | 3375498 | 0.0144 | 0.6388 | 90148296 | 90148296 | 6009886.40 | 180296592 | yes | no | met |
| write-heavy | block-2 | constant-mu5 | constant | 5 | 3951087 | 0.0044 | 0.5000 | 59341088 | 59341088 | 3956072.53 | 296705440 | yes | no | met |
| write-heavy | block-2 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 3924361 | 0.0075 | 0.5001 | 58827499 | 58827499 | 3921833.27 | 294137495 | yes | no | met |
| write-heavy | block-2 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3950786 | 0.0038 | 0.3852 | 37084422 | 37084422 | 2472294.80 | 370844220 | yes | no | met |
| write-heavy | block-2 | constant-mu10 | constant | 10 | 3955909 | 0.0028 | 0.3849 | 37129418 | 37129418 | 2475294.53 | 371294180 | yes | no | met |
| write-heavy | block-2 | constant-mu25 | constant | 25 | 3444681 | 0.0024 | 0.2622 | 18345577 | 18345577 | 1223038.47 | 458639425 | yes | no | met |
| write-heavy | block-2 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3467458 | 0.0056 | 0.2601 | 18319305 | 18319305 | 1221287.00 | 457982625 | yes | no | met |
| write-heavy | block-2 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2948141 | 0.0043 | 0.1883 | 10246320 | 10246320 | 683088.00 | 512316000 | yes | no | met |
| write-heavy | block-2 | constant-mu50 | constant | 50 | 2916249 | 0.0031 | 0.1907 | 10302119 | 10302119 | 686807.93 | 515105950 | yes | no | met |
| write-heavy | block-2 | constant-mu100 | constant | 100 | 2353744 | 0.0019 | 0.1373 | 5620589 | 5620589 | 374705.93 | 562058900 | yes | no | met |
| write-heavy | block-2 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 2378941 | 0.0014 | 0.1356 | 5600801 | 5600801 | 373386.73 | 560080100 | yes | no | met |
| write-heavy | block-3 | zero-loop | constant | 0 | 2355992 | 0.0262 | 0.7872 | 132217987 | 132217987 | 8814532.47 | 0 | yes | no | met |
| write-heavy | block-3 | none | — | — | 2380088 | 0.0122 | 0.7896 | 133974270 | 0 | 0.00 | — | yes | no | indeterminate |
| write-heavy | block-3 | adaptive | — | — | 1375023 | 0.0119 | 0.1255 | 2967792 | 2967792 | 197852.80 | — | yes | no | met |
| write-heavy | block-3 | constant-mu2 | constant | 2 | 3373450 | 0.0078 | 0.6407 | 90258398 | 90258398 | 6017226.53 | 180516796 | yes | no | met |
| write-heavy | block-3 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 3427953 | 0.0079 | 0.6361 | 89686236 | 89686236 | 5979082.40 | 179372472 | yes | no | met |
| write-heavy | block-3 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 3918943 | 0.0099 | 0.5007 | 58883537 | 58883537 | 3925569.13 | 294417685 | yes | no | met |
| write-heavy | block-3 | constant-mu5 | constant | 5 | 3948581 | 0.0049 | 0.4999 | 59291149 | 59291149 | 3952743.27 | 296455745 | yes | no | met |
| write-heavy | block-3 | constant-mu10 | constant | 10 | 3916268 | 0.0082 | 0.3868 | 37203056 | 37203056 | 2480203.73 | 372030560 | yes | no | met |
| write-heavy | block-3 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3959094 | 0.0067 | 0.3849 | 37048838 | 37048838 | 2469922.53 | 370488380 | yes | no | met |
| write-heavy | block-3 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3484569 | 0.0040 | 0.2595 | 18303393 | 18303393 | 1220226.20 | 457584825 | yes | no | met |
| write-heavy | block-3 | constant-mu25 | constant | 25 | 3451158 | 0.0049 | 0.2619 | 18360901 | 18360901 | 1224060.07 | 459022525 | yes | no | met |
| write-heavy | block-3 | constant-mu50 | constant | 50 | 2919663 | 0.0033 | 0.1905 | 10301616 | 10301616 | 686774.40 | 515080800 | yes | no | met |
| write-heavy | block-3 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2940961 | 0.0047 | 0.1883 | 10246544 | 10246544 | 683102.93 | 512327200 | yes | no | met |
| write-heavy | block-3 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 2381736 | 0.0010 | 0.1355 | 5598223 | 5598223 | 373214.87 | 559822300 | yes | no | met |
| write-heavy | block-3 | constant-mu100 | constant | 100 | 2355560 | 0.0035 | 0.1373 | 5624052 | 5624052 | 374936.80 | 562405200 | yes | no | met |

## Paired sign-flip permutation + Holm

- balanced / symmetric-modulo: outcome=indeterminate, pairs=0, raw_p=1, holm_p=1
- read-heavy / symmetric-modulo: outcome=indeterminate, pairs=0, raw_p=1, holm_p=1
- write-heavy / symmetric-modulo: outcome=not-detected, pairs=18, raw_p=0.025566101, holm_p=0.076698303

## Cell effects and 95% paired-block intervals

- write-heavy / constant / mu=2: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- write-heavy / constant / mu=5: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- write-heavy / constant / mu=10: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- write-heavy / constant / mu=25: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- write-heavy / constant / mu=50: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- write-heavy / constant / mu=100: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- write-heavy / symmetric-modulo / mu=2: effect=0.007442284930762007, CI=[-0.03287351722250576, 0.04775808708402978], status=estimable, equivalence=overlaps-equivalence-boundary
- write-heavy / symmetric-modulo / mu=5: effect=-0.009738229292106326, CI=[-0.020976416345050222, 0.0014999577608375714], status=estimable, equivalence=inside-equivalence-range
- write-heavy / symmetric-modulo / mu=10: effect=0.0038867971967747237, CI=[-0.011826149118458707, 0.019599743512008154], status=estimable, equivalence=inside-equivalence-range
- write-heavy / symmetric-modulo / mu=25: effect=0.012787354532664738, CI=[-0.007540514927378788, 0.03311522399270826], status=estimable, equivalence=overlaps-equivalence-boundary
- write-heavy / symmetric-modulo / mu=50: effect=0.011523456644465968, CI=[0.00021801346639591275, 0.022828899822536025], status=estimable, equivalence=inside-equivalence-range
- write-heavy / symmetric-modulo / mu=100: effect=0.011440148218973952, CI=[0.009098420777480324, 0.01378187566046758], status=estimable, equivalence=inside-equivalence-range
- balanced / constant / mu=2: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- balanced / constant / mu=5: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- balanced / constant / mu=10: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- balanced / constant / mu=25: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- balanced / constant / mu=50: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- balanced / constant / mu=100: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- balanced / symmetric-modulo / mu=2: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- balanced / symmetric-modulo / mu=5: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- balanced / symmetric-modulo / mu=10: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- balanced / symmetric-modulo / mu=25: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- balanced / symmetric-modulo / mu=50: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- balanced / symmetric-modulo / mu=100: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- read-heavy / constant / mu=2: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- read-heavy / constant / mu=5: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- read-heavy / constant / mu=10: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- read-heavy / constant / mu=25: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- read-heavy / constant / mu=50: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- read-heavy / constant / mu=100: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- read-heavy / symmetric-modulo / mu=2: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- read-heavy / symmetric-modulo / mu=5: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- read-heavy / symmetric-modulo / mu=10: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- read-heavy / symmetric-modulo / mu=25: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- read-heavy / symmetric-modulo / mu=50: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate
- read-heavy / symmetric-modulo / mu=100: effect=None, CI=[None, None], status=indeterminate, equivalence=indeterminate

## External-floor-derived reference widths

- write-heavy: reference width=1.9% (between-run CV=0.67%, source=linux-baremetal); this is not a power guarantee.
- balanced: reference width=3% (between-run CV=1.07%, source=linux-baremetal); this is not a power guarantee.
- read-heavy: reference width=0.62% (between-run CV=0.22%, source=pegasus); this is not a power guarantee.

Non-significance means only that this registered design did not detect a difference; it is not a claim of guaranteed detection power.
