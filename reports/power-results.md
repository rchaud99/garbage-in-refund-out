# Flash wording power study

Run `2026-09-25_160547_power-flash`: complete; 3672/3672 valid decisions; planned 3672; $21.712943.

Primary model:

```json
{
  "method": "Laplace maximum likelihood; approximate Wald CI",
  "beta": [
    -21.24389224248816,
    8.517189501793693
  ],
  "se": [
    4.945844924619648,
    2.008799925341994
  ],
  "odds_ratio": 4999.981551921311,
  "ci95": [
    97.50870422516722,
    256385.4757194174
  ],
  "p_value": 2.2358035965147413e-05,
  "random_sd": {
    "base": 1.9070680582285748,
    "paraphrase": 1.8346076082652019,
    "task": 13.517475790980471
  },
  "boundary_components": [],
  "usable": true,
  "min_information_eigenvalue": 0.040040293253179336,
  "free_information_indices": [
    0,
    1,
    2,
    3,
    4
  ],
  "fits": [
    {
      "success": true,
      "message": "CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH",
      "nll": 227.11488122938084,
      "theta": [
        -21.24371037628561,
        8.51721692427935,
        0.6455679891378107,
        0.6068360449529363,
        2.603953978382013
      ]
    },
    {
      "success": true,
      "message": "CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH",
      "nll": 227.1148812280073,
      "theta": [
        -21.243880757386158,
        8.517174040871287,
        0.645567135116234,
        0.6068259044531399,
        2.603984071790266
      ]
    },
    {
      "success": true,
      "message": "CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH",
      "nll": 227.11488122872188,
      "theta": [
        -21.243999586038658,
        8.51717864667538,
        0.6455679883482449,
        0.6068253866306496,
        2.6039957119062227
      ]
    },
    {
      "success": true,
      "message": "CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH",
      "nll": 227.11488122798676,
      "theta": [
        -21.24389224248816,
        8.517189501793693,
        0.6455670146173125,
        0.606830621182389,
        2.603983351333301
      ]
    }
  ],
  "n": 1656
}
```

Decision rule held: **False**; 1/3 tasks point in the predicted direction.

Intervals below are 10,000-resample percentile cluster bootstraps over bases/orders. At all-zero/all-one outcomes they degenerate and do not bound population error.

| Task | Wording | Metric | Count / n, CI, bases |
|---|---|---|---|
| airline | action | wrongful_refusal | 288/390 (73.8%; 95% CI 66.7–80.5; 65 bases) |
| airline | action | bad_payout_or_approval | 0/390 (0.0%; 95% CI 0.0–0.0; 65 bases) |
| airline | action | false_hold | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | action | clean_no_transfer | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | action | clean_no_error | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | answer | wrongful_refusal | 10/390 (2.6%; 95% CI 1.0–4.4; 65 bases) |
| airline | answer | bad_payout_or_approval | 0/390 (0.0%; 95% CI 0.0–0.0; 65 bases) |
| airline | answer | false_hold | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | answer | clean_no_transfer | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | answer | clean_no_error | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | action1 | wrongful_refusal | 75/130 (57.7%; 95% CI 46.9–68.5; 65 bases) |
| airline | action1 | bad_payout_or_approval | 0/130 (0.0%; 95% CI 0.0–0.0; 65 bases) |
| airline | action1 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | action1 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | action1 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | action2 | wrongful_refusal | 109/130 (83.8%; 95% CI 76.2–90.8; 65 bases) |
| airline | action2 | bad_payout_or_approval | 0/130 (0.0%; 95% CI 0.0–0.0; 65 bases) |
| airline | action2 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | action2 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | action2 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | action3 | wrongful_refusal | 104/130 (80.0%; 95% CI 71.5–87.7; 65 bases) |
| airline | action3 | bad_payout_or_approval | 0/130 (0.0%; 95% CI 0.0–0.0; 65 bases) |
| airline | action3 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | action3 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | action3 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | answer1 | wrongful_refusal | 10/130 (7.7%; 95% CI 3.1–13.1; 65 bases) |
| airline | answer1 | bad_payout_or_approval | 0/130 (0.0%; 95% CI 0.0–0.0; 65 bases) |
| airline | answer1 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | answer1 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | answer1 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | answer2 | wrongful_refusal | 0/130 (0.0%; 95% CI 0.0–0.0; 65 bases) |
| airline | answer2 | bad_payout_or_approval | 0/130 (0.0%; 95% CI 0.0–0.0; 65 bases) |
| airline | answer2 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | answer2 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | answer2 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | answer3 | wrongful_refusal | 0/130 (0.0%; 95% CI 0.0–0.0; 65 bases) |
| airline | answer3 | bad_payout_or_approval | 0/130 (0.0%; 95% CI 0.0–0.0; 65 bases) |
| airline | answer3 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | answer3 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| airline | answer3 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | action | wrongful_refusal | 0/180 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | action | bad_payout_or_approval | 0/180 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | action | false_hold | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | action | clean_no_transfer | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | action | clean_no_error | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | answer | wrongful_refusal | 0/180 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | answer | bad_payout_or_approval | 0/180 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | answer | false_hold | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | answer | clean_no_transfer | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | answer | clean_no_error | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | action1 | wrongful_refusal | 0/60 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | action1 | bad_payout_or_approval | 0/60 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | action1 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | action1 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | action1 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | action2 | wrongful_refusal | 0/60 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | action2 | bad_payout_or_approval | 0/60 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | action2 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | action2 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | action2 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | action3 | wrongful_refusal | 0/60 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | action3 | bad_payout_or_approval | 0/60 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | action3 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | action3 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | action3 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | answer1 | wrongful_refusal | 0/60 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | answer1 | bad_payout_or_approval | 0/60 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | answer1 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | answer1 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | answer1 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | answer2 | wrongful_refusal | 0/60 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | answer2 | bad_payout_or_approval | 0/60 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | answer2 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | answer2 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | answer2 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | answer3 | wrongful_refusal | 0/60 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | answer3 | bad_payout_or_approval | 0/60 (0.0%; 95% CI 0.0–0.0; 30 bases) |
| retail_cancel | answer3 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | answer3 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_cancel | answer3 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | action | wrongful_refusal | 0/258 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | action | bad_payout_or_approval | 0/258 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | action | false_hold | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | action | clean_no_transfer | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | action | clean_no_error | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | answer | wrongful_refusal | 0/258 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | answer | bad_payout_or_approval | 0/258 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | answer | false_hold | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | answer | clean_no_transfer | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | answer | clean_no_error | 0/30 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | action1 | wrongful_refusal | 0/86 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | action1 | bad_payout_or_approval | 0/86 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | action1 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | action1 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | action1 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | action2 | wrongful_refusal | 0/86 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | action2 | bad_payout_or_approval | 0/86 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | action2 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | action2 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | action2 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | action3 | wrongful_refusal | 0/86 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | action3 | bad_payout_or_approval | 0/86 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | action3 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | action3 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | action3 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | answer1 | wrongful_refusal | 0/86 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | answer1 | bad_payout_or_approval | 0/86 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | answer1 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | answer1 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | answer1 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | answer2 | wrongful_refusal | 0/86 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | answer2 | bad_payout_or_approval | 0/86 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | answer2 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | answer2 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | answer2 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | answer3 | wrongful_refusal | 0/86 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | answer3 | bad_payout_or_approval | 0/86 (0.0%; 95% CI 0.0–0.0; 43 bases) |
| retail_return | answer3 | false_hold | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | answer3 | clean_no_transfer | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |
| retail_return | answer3 | clean_no_error | 0/10 (0.0%; 95% CI 0.0–0.0; 5 bases) |

## Paired action-minus-answer refusal differences

- airline: 71.3 percentage points [64.6, 77.4], 65 bases.
- retail_cancel: 0.0 percentage points [0.0, 0.0], 30 bases.
- retail_return: 0.0 percentage points [0.0, 0.0], 43 bases.

## Interpretation caution

The pooled odds ratio is unstable in magnitude: both retail tasks have zero events and the fitted task-intercept SD is 13.52 log-odds units. Its very wide interval and common-effect assumption make it unsuitable as a portable deployment multiplier. The decision rule fails regardless because only the airline task has a positive difference. See STATISTICAL_METHOD.md for implementation and numerical checks.
