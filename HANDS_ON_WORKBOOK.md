---
title: "ForecastIQ Hands-On Workbook"
subtitle: "Build and understand the whole project yourself, one small step at a time. What we did, how we did it, and what went wrong, written for a complete beginner."
---

# Before you start

## What this workbook is

The project is already built, about 2,400 lines of code, sitting in your **DataScience_project** folder. You are **not** going to retype all of that. Professional engineers don't learn a new project that way either.

Instead you will do what an engineer does on their first week at a new job:

1. **Run** each part yourself and see what it produces.
2. **Read** the important few lines that make it work.
3. **Poke** it: change one thing and see what happens.
4. **Break** it on purpose, then fix it.
5. **Ship** it to the internet.

Every step is small and has the same layout:

| Box | What it tells you |
|---|---|
| **Goal** | what you'll understand by the end |
| **Do it** | exactly what to type or click |
| **You should see** | the real output (copied from an actual run, so you can compare) |
| **What just happened** | the explanation in plain words |
| **Problem we faced** | what went wrong for us at this step, and how it was fixed |
| **Try this** | a small experiment to make it stick |

At the end you'll have done every part of the project with your own hands, and you'll be able to explain each part from experience.

## The practice scripts

To make this easy, there is a new folder in your project called **`playground/`** with one small Python file per step. You run them with one command each. Open any of them in a text editor to see the code. Each is about 20-30 lines, with comments.

## How long it takes

About **3-4 hours** in total. Do one or two steps a day if you like. Steps 0-1 are setup, 2-10 are the data science, 11-13 the software, 14-16 deployment.

## The map

| Step | What you do | Part of the project |
|---|---|---|
| 0 | Set up your Mac | tools |
| 1 | Look around and run the tests | the whole project |
| 2 | Make the data | data |
| 3 | Check the patterns in the data | data |
| 4 | Build the clues (features) | data science |
| 5 | Make the simplest forecast and score it | models |
| 6 | Holt-Winters forecast | models |
| 7 | Machine-learning forecast | models |
| 8 | Run the full pipeline | pipeline |
| 9 | Make the ranges honest | uncertainty |
| 10 | Business analysis | BI |
| 11 | Talk to the backend directly | backend / API |
| 12 | Look inside the frontend | frontend |
| 13 | Break it on purpose | testing |
| 14 | Put it on GitHub | deployment |
| 15 | Deploy on Render | deployment |
| 16 | Change something and redeploy | deployment |


# Step 0. Set up your Mac

**Goal:** get Python and the project's libraries working, and learn the five Terminal commands you need.

## 0.1 Open Terminal

Press `Cmd + Space`, type **Terminal**, press Enter. A window with a blinking cursor opens. You type a command and press Enter; the computer answers.

The only commands you need:

| Command | Meaning |
|---|---|
| `cd folder` | "change directory": go into a folder |
| `ls` | list the files here |
| `pwd` | "print working directory": where am I? |
| `python file.py` | run a Python file |
| `Ctrl + C` | stop whatever is running |

## 0.2 Go into the project

**Do it:**

```bash
cd ~/Desktop/DataScience_project
ls
```

**You should see** names like `app.py`, `forecastiq`, `static`, `tests`, `playground`, `README.md`...

`~` means "my home folder", so `~/Desktop/DataScience_project` is the project on your Desktop.

## 0.3 Check Python

**Do it:**

```bash
python3 --version
```

**You should see** `Python 3.11` or higher (3.12, 3.13 are fine).

If it says 3.9 or 3.10, or "command not found": download Python from **python.org/downloads**, install it, then **close Terminal and open a new one**, and repeat 0.2 and 0.3.

## 0.4 Make a virtual environment and install the libraries

A **virtual environment** ("venv") is a private box of Python libraries for this one project, so it can't clash with anything else on your Mac.

**Do it:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-train.txt
```

**You should see** your Terminal line now starts with `(.venv)`, then a lot of "Downloading..." and "Successfully installed ...". It takes 1-3 minutes.

**What just happened:** `requirements-train.txt` is a shopping list of libraries (flask, pandas, numpy, scipy, scikit-learn, pytest, gunicorn). `pip` is Python's installer; it read the list and installed each item into the `.venv` box.

> **Remember:** every time you open a **new** Terminal window, run these two lines again before anything else:
>
> ```bash
> cd ~/Desktop/DataScience_project
> source .venv/bin/activate
> ```

> **Problem we faced: library versions need a new Python.**
> The project uses recent versions of pandas and numpy, which need Python 3.11 or newer. Macs often ship with 3.9. If `pip install` fails with errors about numpy or pandas, this is almost always why. Fix: install a newer Python (0.3), delete the `.venv` folder (`rm -rf .venv`), and redo 0.4.

**Optional but nice:** install **VS Code** (code.visualstudio.com), a free code editor. Open it, choose **File → Open Folder**, pick DataScience_project. You can now see and edit every file with colours, and open a Terminal inside it (**Terminal → New Terminal**).


# Step 1. Look around and run the tests

**Goal:** know where everything lives, and prove the project works on your Mac.

## 1.1 The folders

| Folder / file | What's inside, in one line |
|---|---|
| `forecastiq/` | all the data science: data, features, models, analysis, pipeline |
| `artifacts/` | 7 result files the website reads |
| `app.py` | the backend (web server) |
| `templates/`, `static/` | the frontend (web page, styles, JavaScript) |
| `tests/` | 32 automatic checks |
| `playground/` | your practice scripts for this workbook |
| `requirements.txt`, `render.yaml`, `Dockerfile`, `Procfile` | deployment files |
| `README.md`, `RESUME_NOTES.md`, `PROJECT_GUIDE.pdf` | documentation |

## 1.2 Run the tests

**Do it:**

```bash
pytest -q
```

**You should see** a row of dots, then:

```
32 passed in 10.02s
```

**What just happened:** `pytest` found every function starting with `test_` inside the `tests/` folder and ran them. Each one checks something (the data has the right size, the model beats the simple method, the website answers...). 32 green checks means your copy works exactly like ours.

> **Problem we faced:** none here, but this step is how you catch setup problems early. If you see `ModuleNotFoundError`, your venv isn't active (see the "Remember" box in Step 0).

**Try this:** run `pytest -v` (v for verbose). You'll see the name of every test. Read the names; they tell you what the project promises to do.


# Step 2. Make the data

**Goal:** create 3 years of sales data with one command and look at it.

**Do it:**

```bash
python playground/step02_data.py
```

**You should see:**

```
Rows and columns: (197280, 16)

First 5 rows (a few columns):
        date store_id  sku_id category  units  price  promo
0 2023-11-01      S01  APP-01  Apparel   29.0  760.0      0
1 2023-11-02      S01  APP-01  Apparel   23.0  760.0      0
2 2023-11-03      S01  APP-01  Apparel   56.0  608.0      1
3 2023-11-04      S01  APP-01  Apparel   74.0  608.0      1
4 2023-11-05      S01  APP-01  Apparel   70.0  608.0      1

Number of product-store series: 180
First day: 2023-11-01   Last day: 2026-10-31

Revenue by category over 3 years (in crore rupees):
Apparel            57.5
Electronics       166.9
Grocery            63.0
Home & Kitchen     74.7
Personal Care      41.7

Saved playground/one_series.csv with 1096 rows
```

**What just happened:**

- `generate()` (in `forecastiq/data.py`) is our **simulator**. It invented sales for 6 stores × 30 products × 1,096 days = 197,280 rows, in about one second.
- Look at rows 2-4: on 3 November the price drops from 760 to 608 (a 20% discount), `promo` becomes 1, and sales jump from about 25 to 56-74. The simulator built that in.
- The numbers are the same every time you run it because of a **random seed** (`SEED = 42` in `config.py`). Same seed, same "random" numbers. This makes results **reproducible**.

**How the simulator works, in one sentence:** for each product, store and day it starts from a normal sales level and multiplies in effects (trend, weekend, yearly season, price, promotion, Diwali, other festivals, payday, random noise), then rolls a weighted dice to get a whole number of units.

> **Problem we faced: we had no real data.**
> Real store sales are private, and the computer we built on had no internet to download public datasets. So we wrote this simulator. Bonus: because we wrote the recipe, we know the true answers (like "Electronics customers are exactly this sensitive to price") and can check our analysis against them later. Always say the data is simulated.

> **Problem we faced: Electronics swallowed everything.**
> The first version let Electronics cost up to ₹40,000. Electronics then made ₹423 crore while every other category made ₹40-75 crore, and every chart was just Electronics. We cut the range to ₹1,500-12,000, which gives the ₹166.9 crore you see now.

**Try this:**

1. Open `playground/one_series.csv` in **Numbers** (or Excel). It's 3 years of one product (Grocery item 1 in Bengaluru). Select the `date` and `units` columns and insert a **line chart**. You'll see weekly zig-zags and big peaks every autumn: those are Diwali.
2. Open `forecastiq/config.py` and find `CATEGORIES`. Read the Electronics line. Every number there is something the simulator uses.


# Step 3. Check the patterns in the data

**Goal:** prove the patterns we planted are really there, using pandas.

**Do it:**

```bash
python playground/step03_patterns.py
```

**You should see:**

```
Average units sold, by day of week (0 = Monday, 6 = Sunday):
0    33.7
1    33.6
2    33.7
3    34.0
4    36.1
5    41.4
6    41.5

Average units: normal days vs promotion days
0    33.9
1    50.9

Average units in the week before Diwali: 60.3
Average units on all other days:         35.7

How many days had zero sales: 2552
Hidden problem days planted by the simulator: 1373
```

**What just happened:**

The key pandas tool here is **`groupby`**: "split the table into groups, then calculate something for each group". For example:

```python
sales.groupby(sales["date"].dt.dayofweek)["units"].mean()
```

means "group the rows by day of the week, then take the average of `units` in each group". This one line is how most data analysis starts.

What the numbers tell you:

- **Weekends** (5 = Saturday, 6 = Sunday) sell about 23% more than weekdays. Friday (4) a little more too.
- **Promotion days** sell 50% more on average.
- **The week before Diwali** sells 69% more than other days.
- **1,373 days** are hidden problems (stock-outs and spikes) that the simulator planted on purpose. In Step 10 we'll see if our detector can find them.

This step is called **EDA (Exploratory Data Analysis)**: looking at the data before modelling. Always do it. If weekends weren't higher here, it would mean a bug in the simulator.

**Try this:** add this line to the end of the script and run it again. It shows average sales per category:

```python
print(sales.groupby("category")["units"].mean().round(1))
```

Grocery should sell the most units (cheap, everyday items) and Electronics the fewest.


# Step 4. Build the clues (features)

**Goal:** see the 30 clues the machine-learning model gets, and check the most important rule (no peeking at the future) with your own eyes.

**Do it:**

```bash
python playground/step04_features.py
```

**You should see:**

```
Number of features: 30
['lag_28', 'lag_35', 'lag_42', 'lag_49', 'lag_56', 'lag_364', 'roll_mean_7', 'roll_mean_28'] ...

On 2026-10-31 lag_28 = 263.0
Actual sales 28 days earlier ( 2026-10-03 ) = 263.0
Same number? True

A few clues for that day:
lag_28                  263.0
roll_mean_28       199.535714
rel_price            0.704159
promo                       1
dow                         5
days_from_major            -8
```

**What just happened:**

A model can't read a calendar. We turn everything into numbers, one column per clue. These columns are called **features**. For 31 October 2026 the clues say:

| Clue | Value | In words |
|---|---|---|
| `lag_28` | 263 | sales exactly 28 days ago were 263 |
| `roll_mean_28` | 199.5 | the average over the 28 days before that was about 200 |
| `rel_price` | 0.70 | today's price is 70% of normal (a 30% discount) |
| `promo` | 1 | a promotion is running |
| `dow` | 5 | it's a Saturday |
| `days_from_major` | -8 | Diwali is in 8 days |

A human planner would guess "high sales today". The model will learn the same thing from thousands of examples.

**The 28-day rule.** We forecast 28 days ahead. On the last day of the forecast, the newest real sales we have are 28 days old. So **every sales clue is at least 28 days old**, never newer. That's why the first lag is `lag_28`, not `lag_1`. The script checks it: `lag_28` really equals the sales on 3 October. Using information you wouldn't really have yet is called **leakage**, the number-one mistake in forecasting projects.

The code is in `forecastiq/features.py`. The key line is:

```python
LAGS = (H, H + 7, H + 14, H + 21, H + 28, 364)     # H = 28, the horizon
```

> **Problem we faced: being sure there is no leakage.**
> Leakage is invisible: your test results simply look too good. We protected against it in two ways: the 28-day rule above, and an automatic test that tampers with the last 27 days of data and checks the clues don't change. In Step 13 you'll break the rule on purpose and watch the test catch it.

**Try this:** in `step04_features.py`, change `"2026-10-31"` to `"2026-10-15"` and run it again. Does `lag_28` still match the sales 28 days earlier? (It should.)


# Step 5. The simplest forecast, and how to score it

**Goal:** make a forecast with the simplest possible rule, and learn how forecasts are scored.

**Do it:**

```bash
python playground/step05_naive.py
```

**You should see:**

```
Last week of training data: [240. 140. 156. 124. 188. 121. 263.]
Forecast for first week:    [240. 140. 156. 124. 188. 121. 263.]
What really happened:       [320. 127. 114. 249. 182. 234. 188.]

MAE  (average miss in units): 83.3
WAPE (miss as % of volume):   34.5 %
```

**What just happened:**

1. We took one product's sales and **hid the last 28 days**. This hidden part is the "exam". The rest is the "training data". Never let a model see the exam answers.
2. **Seasonal naive** rule: "next week will be the same as last week". The forecast is literally last week copied 4 times. Look: the first two lines are identical.
3. We compared the forecast with what really happened, using two scores:
   - **MAE** (mean absolute error): on average we missed by 83 units a day.
   - **WAPE** (weighted absolute percentage error): total misses ÷ total sales = 34.5%. Lower is better. This is our main score.

Why bother with such a silly rule? It's the **benchmark**. Every fancy model must beat it, or it's useless. Serious forecasting projects always report one.

> **Problem we faced: which score to use.**
> The famous MAPE score divides each day's error by that day's sales. When a product sold zero, that's a division by zero, and for slow sellers the percentages explode. WAPE divides **totals** instead, so it always works and busy products count more, which matches what a business cares about.

**Try this:** in the script, change `28` to `7` in both places (`y[:-28], y[-28:]` and `seasonal_naive(..., 28)`) to forecast only one week. Is the WAPE better or worse?


# Step 6. A smarter classic: Holt-Winters

**Goal:** beat the naive rule with a classic statistical method.

**Do it:**

```bash
python playground/step06_holtwinters.py
```

**You should see:**

```
Settings it picked: alpha=0.5  beta=0.0  gamma=0.02  phi=0.9
Holt-Winters forecast, first week: [214.3 189.8 172.9 175.7 193.7 158.8 216. ]

WAPE seasonal naive: 34.5 %
WAPE Holt-Winters:   29.5 %
```

**What just happened:**

Holt-Winters keeps track of three things and updates them a little every day:

- **level:** normal daily sales right now,
- **trend:** going up or down,
- **season:** how each weekday differs from normal.

The four settings control how fast each one reacts:

| Setting | Controls | Picked here | Meaning |
|---|---|---|---|
| alpha | level | 0.5 | reacts fairly quickly to new sales |
| beta | trend | 0.0 | ignores short-term trends (good: they're mostly noise) |
| gamma | season | 0.02 | the weekly pattern is very stable |
| phi | damping | 0.9 | any trend fades out over the 28 days |

The model tried **90 combinations** of these settings and kept the one that would have predicted this product's past best. It does this separately for every product.

Result: **29.5% error vs 34.5%**. Better, because it averages out noise instead of copying one noisy week.

> **Problem we faced: the usual library wasn't available.**
> Normally you'd write `from statsmodels.tsa.holtwinters import ExponentialSmoothing`. That library wasn't installed on the computer we built on, and there was no internet to install it. So we **wrote Holt-Winters ourselves** from the textbook formulas: `class HoltWinters` in `forecastiq/models.py`, about 60 lines. It also handles all 180 products at once using NumPy arrays ("vectorised"), which is fast.
> Good interview point: "I implemented Holt-Winters from scratch."

**Try this:** open `forecastiq/models.py` and find the `_run` function inside `class HoltWinters`. Find the three update lines (`new_level = ...`, `trend = ...`, `seas[:, k] = ...`). Those three lines **are** Holt-Winters. Everything else is setup.

**Its weakness:** Holt-Winters only looks at past sales. It can't see that a promotion or Diwali is coming. The next model can.


# Step 7. The machine-learning model

**Goal:** train one gradient-boosting model for all 180 products and watch it beat both classic methods.

**Do it** (takes 20-40 seconds):

```bash
python playground/step07_boosting.py
```

**You should see:**

```
Trained and forecast 180 series in 22 seconds

snaive  WAPE = 39.4 %
ets     WAPE = 32.0 %
gbm     WAPE = 26.1 %

  date  actual  snaive  ets  gbm  promo
04 Oct    44.0    32.0 35.6 41.1      0
05 Oct    22.0    14.0 25.4 29.6      0
06 Oct    34.0    31.0 30.6 31.8      0
07 Oct    61.0    32.0 26.2 41.1      1
08 Oct    71.0    31.0 29.0 41.4      1
09 Oct    57.0    22.0 28.1 41.4      1
10 Oct    78.0    66.0 39.3 57.4      1
```

(`ets` = Holt-Winters, `gbm` = gradient boosting machine.)

**What just happened:**

- We pretended "today" was 3 October 2026, trained on everything before it, and forecast 4-31 October for **all 180** product-store pairs.
- Gradient boosting wins: **26.1%** error vs 32.0% and 39.4%.
- Look at the table from 7 October: a promotion starts (`promo = 1`), real sales jump to 61-78. Seasonal naive and Holt-Winters stay around 30 because they can't see promotions. Gradient boosting jumps to 41-57 because `promo` is one of its clues. It's still too low (promotions are hard), but much closer.

**How gradient boosting works, simply:**

- A **decision tree** is a game of 20 questions: "Is the 8-week average above 50? Is it a weekend? Is there a promotion? → predict 74."
- **Boosting** builds 300 small trees in a row. Each new tree focuses on the mistakes the previous trees still make. Like students correcting each other's homework.
- **Global**: one model for all 180 series. It learns "promotions boost sales" from every product at once, which especially helps slow sellers with little data of their own.
- **Poisson loss**: a setting that tells the model it's predicting counts (0, 1, 2, ...), which can't be negative.

The code: `class GlobalGBM` in `forecastiq/models.py`, using scikit-learn's `HistGradientBoostingRegressor`. The training call is just `model.fit(X, y)`: X is the table of clues, y is actual sales.

> **Problem we faced: the "famous" ML libraries weren't available either.**
> Most tutorials use LightGBM or XGBoost. Neither was installed and we couldn't install them. scikit-learn's HistGradientBoosting is the same family of algorithm and was available. In interviews say "scikit-learn's HistGradientBoostingRegressor", never claim LightGBM.

**Try this:** in the script, change the last-but-one `"S01|APP-01"` to `"S04|ELE-01"` (an Electronics product in Mumbai) and run again. Electronics sells few units with big swings: which model does best on those 7 days?


# Step 8. Run the full pipeline

**Goal:** run the whole "kitchen" with one command: four practice exams, pick a winner, make the final forecast, do the business analysis, and save everything.

**Do it** (about 2 minutes):

```bash
python -m forecastiq.pipeline
```

**You should see** progress lines, then a leaderboard:

```
[   0.6s] data: 197,280 rows, 180 series, 2023-11-01..2026-10-31
[   1.1s] features: 30 columns
[  20.1s] fold 0: cutoff 2026-07-11  WAPE gbm=0.248 ets=0.310 snaive=0.388 ...
[  37.3s] fold 1: cutoff 2026-08-08  ...
[  56.9s] fold 2: cutoff 2026-09-05  ...
[  76.1s] fold 3: cutoff 2026-10-03  ...
[  76.7s] champion: gbm
[ 100.5s] final forecast done
[ 107.3s] analytics done; anomaly precision=0.64 recall=0.72
[ 108.5s] artifacts written to .../artifacts

Leaderboard (folds 1-3, out of sample):
   model   wape     mae    rmse  smape    bias   mase
  snaive 0.3909 16.1712 31.8845 0.4861 -0.0331 1.0752
     ets 0.3163 13.0877 25.9619 0.4012 -0.0797 0.8802
     gbm 0.2585 10.6948 21.2636 0.3247 -0.0046 0.7055
ensemble 0.2775 11.4825 22.9912 0.3448 -0.0361 0.7585
```

(Times will differ on your Mac. The numbers should be the same, thanks to the seed.)

**What just happened:**

In Step 7 you did one exam. The pipeline does **four**, each pretending "today" is a different date (11 Jul, 8 Aug, 5 Sep, 3 Oct). This is called a **rolling backtest**. One exam can be lucky; four in a row are convincing. The first exam is only used to warm up the calibration (Step 9); the reported scores come from the other three: 3 × 28 days × 180 products = **15,120 forecasts**.

Then it:

- **picks the champion:** the model with the lowest error on earlier exams (gradient boosting);
- trains it on all 3 years and forecasts the real future, **1-28 November 2026**;
- runs the business analysis (Step 10);
- writes **7 JSON files** into `artifacts/`. The website reads only these.

`python -m forecastiq.pipeline` means "run the `pipeline` module inside the `forecastiq` package". Open `forecastiq/pipeline.py` and find `def run():` to see every step in order.

**Reading the leaderboard:** gradient boosting has the lowest error (WAPE 0.2585 = 25.9%), 34% less than seasonal naive, and almost no **bias** (-0.5%: not systematically too high or low). **MASE** under 1 means "better than the naive method".

> **Problem we faced: the ensemble lost.**
> An **ensemble** averages several models, giving more weight to whichever was more accurate for each product. We expected it to be the best. It wasn't: 27.8% vs 25.9%.
> We tried 7 variations (stronger weighting, dropping the naive model, simple averages). The best got to 26.25%, still worse than gradient boosting alone.
> **Why:** two of the three models can't see promotions or Diwali. Mixing them in drags the good forecasts toward worse ones.
> **What we did:** instead of forcing an ensemble, the pipeline now automatically promotes whichever model is best (a **champion/challenger** setup). This is a great interview story: you tested an assumption and reported the honest result.

**Try this:** open `forecastiq/config.py`, change `HORIZON = 28` to `HORIZON = 14`, and run the pipeline again. Is the error lower when forecasting only two weeks? (We got 25.1% instead of 25.9% for gradient boosting: only a little better. With a 14-day horizon the newest sales clue is 14 days old instead of 28, which helps a bit; most of the remaining error is day-to-day randomness that no horizon fixes.) **Afterwards change it back to 28 and run the pipeline once more**, so the website and tests match again.


# Step 9. Make the ranges honest

**Goal:** understand how the project turns "we'll sell 450" into "we'll sell between 410 and 520, and that range is right 80% of the time".

**Do it:**

```bash
python playground/step09_conformal.py
```

**You should see:**

```
Before: the range 95-105 contains the real value 38 % of the time
Conformal says: widen each side by 7.5
After: the range 87.5-112.5 contains it 78 % of the time (target 80%)
```

**What just happened:**

This uses made-up numbers to show the idea clearly:

1. Real sales vary around 100. Someone gave a range of 95-105. That range is **too narrow**: it only catches the real value 38% of the time. We say its **coverage** is 38%.
2. **Conformal calibration** looks at the first 1,000 past cases and measures how far outside the range they fell. It finds the amount (7.5) that would have made 80% of them fit.
3. Applied to the **next** 1,000 cases, the widened range 87.5-112.5 catches 78%, close to the 80% target.

It's like a tailor whose shirts were always 2 cm too tight: from now on, add 2 cm.

In the real project, two extra gradient-boosting models first guess the low end (10th percentile) and high end (90th percentile), then conformal calibration fixes the width using the backtest exams.

> **Problem we faced: the ranges were overconfident.**
> The model's own ranges caught the real value only **76.9%** of the time (73.7% in our first version). After conformal calibration: **78.7%**. Still slightly under 80%, because the most recent weeks were a bit more unpredictable than the older weeks used for calibrating. Always report it honestly: "78.7% against an 80% target".

**Try this:** in the script, change `0.80` to `0.95`. How much wider does the range get to reach 95%?


# Step 10. Business analysis

**Goal:** see how forecasts become decisions: product groups, price sensitivity, anomaly detection, and an inventory plan.

**Do it** (10-30 seconds):

```bash
python playground/step10_business.py
```

**You should see:**

```
1) ABC-XYZ: how many product-store pairs in each group
xyz   X   Y   Z
abc
A    17  41  35
B    16  18  16
C    15  16   6

2) Price sensitivity: our estimate vs the truth we planted
   Apparel         estimate -1.75   truth -1.80
   Electronics     estimate -2.23   truth -2.20
   Grocery         estimate -0.82   truth -0.80
   Home & Kitchen  estimate -1.39   truth -1.40
   Personal Care   estimate -1.10   truth -1.10

3) Anomaly detector score
   precision 64%   recall 72%   (395 of 548 found)

4) One line of the inventory plan (from artifacts/inventory.json)
   on_hand         360.0
   daily_forecast  25.56
   lead_time       10
   safety_stock    46.3
   reorder_point   430.5
   days_cover      8.0
   status          Critical
   order_qty       299.0
```

**What just happened, part by part** (all the code is in `forecastiq/analytics.py`):

**1) ABC-XYZ.** Sorts products by **importance** (A = the products making the top 80% of revenue, then B, then C) and by **predictability** (X = steady, Y = medium, Z = erratic). The 35 "AZ" pairs are important **and** hard to predict: they need the most attention and safety stock.

**2) Price sensitivity (elasticity).** -2.2 for Electronics means "raise the price 1%, lose about 2.2% of sales". Grocery at -0.8 barely reacts (you need rice anyway). We estimated these with a **Poisson regression** that compares each product only with itself, at different prices, while correcting for weekends, months and festivals. Our estimates land within 0.05 of the truth we planted in Step 2. That is the payoff of simulated data: you can check your answer.

**3) Anomaly detector.** Finds days with sales the normal pattern can't explain. **Precision 64%** = when it raises an alarm, it's a real planted problem 64% of the time. **Recall 72%** = it found 395 of the 548 planted problems.

**4) Inventory plan** for Apparel product 2 in Bengaluru:

| Item | Value | Meaning |
|---|---|---|
| on hand | 360 | units on the shelf now |
| daily forecast | 25.6 | expected sales per day |
| lead time | 10 days | a new delivery takes 10 days |
| days cover | 8 | the stock lasts about 8 days |
| safety stock | 46 | cushion for forecast mistakes |
| reorder point | 431 | order when stock falls to this |
| status | **Critical** | stock (8 days) runs out before a delivery could arrive (10 days) |
| order qty | 299 | recommended order |

The safety-stock formula is `z × σ × √(lead time)`, where **σ is how wrong our forecast usually is** (measured in the backtest) and **z** comes from the service level (98% for A products).

> **Problem we faced: the first anomaly detector was bad.**
> Version one found only 44% of the planted problems, and only 21% of its alarms were real. We rebuilt it to understand that sales are counts (a product selling 2 a day can easily sell 0), to expect higher sales on promotion days, and to spot runs of zero days (stock-outs). Then we tested thresholds of 3.5, 4.0, 4.5 and 5.0 and chose 4.5: 64% precision, 72% recall.
> **Honest note:** we chose that threshold while looking at the planted truth, so these scores are a little optimistic.

> **Problem we faced: unrealistic stock levels.**
> The first simulated stock levels made 50 of 180 pairs "Critical", which no real shop would allow. We gave stores more stock (about 26 days instead of 16). Now 24 are Critical, 3 need reordering, 13 are overstocked and 140 are healthy.

**Try this:** in `forecastiq/config.py`, find `SERVICE_LEVEL = {"A": 0.98, ...}`. What do you think happens to safety stock if A becomes 0.99? (Answer: z goes from about 2.05 to about 2.33, so safety stock grows about 13%.) Don't forget to change it back.


# Step 11. Talk to the backend directly

**Goal:** start the web server on your Mac and ask it for data yourself, the same way the website does.

**Do it:**

```bash
python app.py
```

**You should see** a few lines ending with something like `Running on http://127.0.0.1:7860`. The server is now running. Leave this Terminal window open (it will look "stuck"; that's normal, it's waiting for visitors).

Now open your browser and visit these addresses one by one:

**1. The health check:** `http://localhost:7860/api/health`

```json
{"status":"ok","version":"1.0.0","generated_at":"2026-11-16 21:48 UTC"}
```

**2. The Apparel forecast:** `http://localhost:7860/api/forecast?node=category:Apparel`

You'll see a long block of text starting with:

```json
{"level":"category","key":"Apparel","label":"Apparel","hist_dates":["2026-05-03",...
```

That's **JSON**: the data format the backend sends. Chrome and Safari may show it neatly with a "pretty print" option.

**3. Something that doesn't exist:** `http://localhost:7860/api/forecast?node=nope`

```json
{"error":"Unknown node 'nope'."}
```

**4. The what-if simulator.** This one needs data sent **to** the server, so use a **second** Terminal window (`Cmd + N`) and type:

```bash
curl -X POST localhost:7860/api/scenario -H "Content-Type: application/json" -d '{"category":"Apparel","price_change":-0.1}'
```

You get back JSON with the result of a 10% Apparel price cut. Rounded:

| | Before | After |
|---|---|---|
| Units | 22,794 | 27,406 |
| Revenue (₹) | 2,45,55,666 | 2,65,72,001 |
| Gross margin (₹) | 1,15,16,647 | 1,08,94,568 |

So the price cut brings **more revenue but less profit**. That's a real business insight from one line.

**5. A bad request:**

```bash
curl -X POST localhost:7860/api/scenario -H "Content-Type: application/json" -d '{"price_change":5}'
```

```json
{"error":"price_change must be between -0.5 and 0.5."}
```

**What just happened:**

- `app.py` is a **Flask** app. Each address (like `/api/forecast`) is an **endpoint**, connected to one Python function by a line like `@app.get("/api/forecast")`.
- When the server starts, it loads the 7 JSON files from `artifacts/` into memory. Each request just looks up the answer. That's why it's instant.
- **GET** requests (visiting an address) ask for data. **POST** requests (the curl commands) send data to be processed.
- The server **checks inputs** and returns a clear error with a status code (**400** = bad input, **404** = not found) instead of crashing.

Open `app.py` and find the `forecast()` and `scenario()` functions. They're short; read them with this step in mind.

> **Problem we faced: keeping the server small.**
> The free server has only 512 MB of memory. The training code needs scikit-learn, a big library. We arranged the code so scikit-learn is only loaded when training, never by the website. The website needs only 5 libraries (listed in `requirements.txt`) and uses about 145 MB.

> **Problem we faced: the home page crashed.**
> We tested the API before writing the web page, and `/` crashed with `TemplateNotFound: index.html`. Simply the order of work, but it's why every endpoint, including the home page, now has a test.

**Stop the server** with `Ctrl + C` in its Terminal when you're done with Step 12.


# Step 12. Look inside the frontend

**Goal:** use the dashboard, then peek behind it to watch it talk to the backend.

**Do it:** with the server still running from Step 11, open **`http://localhost:7860`** in Chrome.

Click through all eight pages in the left menu. Things to try:

- **Forecast explorer:** set Level to *Category*, Selection to *Apparel*. Tick **Overlay backtest**: the orange line is what the model predicted before it saw the actual sales.
- **Inventory planning:** click a column header (e.g. *Order value*) to sort. Filter Status to *Critical*.
- **Pricing & promotions:** drag the price slider and watch the numbers change.
- **Forecast your data:** click *Try the sample series*.
- Click **Switch theme** at the bottom left for dark mode.

## 12.1 Watch the frontend talk to the backend

1. In Chrome press `Option + Cmd + I` to open **Developer Tools**.
2. Click the **Network** tab.
3. Now click *Forecast explorer* in the dashboard and change the Selection dropdown.
4. New lines appear in the Network tab, like `forecast?node=category%3AApparel`. Click one, then **Response**. It's the same JSON you saw in Step 11.

**What just happened:** the dashboard is HTML + CSS + JavaScript running **in your browser**. When you change a dropdown, JavaScript (`static/app.js`) calls `fetch("/api/forecast?node=...")`, gets the JSON back, and passes the numbers to `static/charts.js`, which draws the chart as **SVG** (shapes described in code). Frontend asks, backend answers, frontend draws. Every page works this way.

## 12.2 Change the look yourself

1. Open `static/styles.css` in VS Code (or TextEdit).
2. Find the line near the top that contains `--series-1:#2a78d6;`. That's the main blue.
3. Change it to `--series-1:#8e44ad;` (purple) and save.
4. Refresh the browser with `Cmd + Shift + R`.

All the blue forecast lines and highlights are now purple, because every colour is defined once, as a **CSS variable**, and used everywhere. **Change it back** to `#2a78d6` afterwards.

> **Problem we faced: layout bugs we only found by looking.**
> The code ran without errors, but when we took screenshots of every page (light mode, dark mode, phone size) we found: two chart labels printed on top of each other, tables cut off on the right, a tile with text so big it took three lines, a page wider than a phone screen, and code names ("gbm", "snaive") in a legend instead of readable names. All fixed after looking.
> **Lesson:** "it runs" is not "it works". Always look at your app on different screens.

> **Problem we faced: no chart library.**
> Plotly, Chart.js and similar libraries weren't available, so the line and bar charts were written by hand in `static/charts.js` (about 170 lines). Upside: the website is tiny and loads instantly.

**Try this:** make your browser window narrow (or press `Cmd + Shift + M` in Developer Tools for phone view). The menu moves to the top and panels stack. That's the "responsive" CSS at the bottom of `styles.css`.


# Step 13. Break it on purpose

**Goal:** see automatic tests protect you from a classic mistake.

Remember the 28-day rule from Step 4? Let's break it and see what happens.

**Do it:**

1. Stop the server if it's running (`Ctrl + C`).
2. Open `forecastiq/features.py`. Find this line (line 16):

   ```python
   LAGS = (H, H + 7, H + 14, H + 21, H + 28, 364)
   ```

3. Change the first `H` to `1`, so the model would use **yesterday's** sales:

   ```python
   LAGS = (1, H + 7, H + 14, H + 21, H + 28, 364)
   ```

4. Save, then run only the leakage test:

   ```bash
   pytest -q -k leak
   ```

**You should see:**

```
FAILED tests/test_pipeline_parts.py::test_features_do_not_leak_the_forecast_window
1 failed, 5 deselected in 1.57s
```

**What just happened:** the test pretends the last 27 days of sales were all 9,999 and checks whether the clues for the forecast change. With `lag_1`, the clue for forecast day 1 is "yesterday", which is inside those 27 days, so it changed. The test caught the leak instantly.

Without this test, your results would quietly look **better** than reality, and you'd only find out when the real forecasts disappointed.

5. **Now fix it.** Change `1` back to `H`, save, and run:

   ```bash
   pytest -q
   ```

**You should see** `32 passed` again.

> **Problem we faced: tests need a safe place to run automatically.**
> We set up **GitHub Actions** (in a file called `ci.yml`) to run all 32 tests every time code is uploaded to GitHub, showing a green tick or red cross. GitHub only looks for that file in a hidden folder called `.github/workflows/`, and that folder couldn't be created on your Mac when we copied the project, so `ci.yml` sits in the main folder for now. You'll put it in the right place in Step 14.

**Try this:** make a test stricter than the model can manage. Open `tests/test_api.py` and find this line in `test_champion_beats_the_naive_benchmark`:

```python
assert board[p["champion"]]["wape"] < board["snaive"]["wape"] * 0.8
```

It says "the champion's error must be under 80% of the naive method's". Change `0.8` to `0.5` (demanding half the error) and run `pytest -q -k champion`. It fails, because 25.9% is not below 19.5%. Change it back to `0.8`. This is how tests act as guard-rails: if a future change ever makes the model worse than the promise, a test goes red.


# Step 14. Put it on GitHub

**Goal:** get your code online, where recruiters can read it and Render can deploy it.

**GitHub** is a website that stores code projects ("repositories" or "repos") with their full history. It's also your public portfolio as a developer.

## 14.1 Clean up first

Running the scripts created some throwaway folders called `__pycache__` (Python's speed-up files). They're harmless but messy. In Terminal:

```bash
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
```

## 14.2 Create the repository

1. Go to **github.com**, sign up or log in.
2. Click **+** (top right) → **New repository**.
3. Name: `demand-forecasting-bi-platform`. Choose **Public**. Leave everything else unticked.
4. Click **Create repository**.

## 14.3 Upload the files (no Terminal needed)

1. On the new repository page, click **"uploading an existing file"**.
2. In Finder, open **Desktop → DataScience_project**, press `Cmd + A` to select everything, and drag it into the GitHub page. Use **Chrome**.
3. Wait until all files are listed, then click **Commit changes**.

Hidden files and folders (names starting with a dot, like `.venv` and `.gitignore`) aren't selected by Finder, which is what we want for `.venv`. If GitHub complains about too many files at once, upload in two batches (for example, the folders first, then the loose files).

**You should see** your folders and files on GitHub, with the README and its screenshots displayed below them.

## 14.4 Put the test file in the right place

1. On your repository page, click **Add file → Create new file**.
2. In the name box type exactly: `.github/workflows/ci.yml` (typing the `/` creates the folders).
3. On your Mac, open `ci.yml` from the project folder in TextEdit, copy everything, and paste it into the big box on GitHub.
4. Click **Commit changes**.
5. Click the **Actions** tab. Within a few minutes you'll see a run with a **green tick** ✓: GitHub installed Python and ran your 32 tests on its own computer.

> **Problem we faced:** the `.github` folder couldn't be created on your Mac, which is exactly why `ci.yml` needs this manual step. Creating it directly on GitHub sidesteps the problem.

**Try this:** click on `forecastiq/models.py` on GitHub. This is how a recruiter will read your code. Then click **README.md** and check that the screenshots show.


# Step 15. Deploy on Render

**Goal:** get a public link to your dashboard.

**Render** is a hosting company. It copies your code from GitHub onto one of its servers, installs the libraries, starts the app, and gives you an address. The free plan is enough.

**Do it:**

1. Go to **render.com** → **Get Started** → **Sign in with GitHub**.
2. Click **New +** → **Blueprint**.
3. Allow Render to see your GitHub repositories, then choose `demand-forecasting-bi-platform`.
4. Render finds `render.yaml` and shows a service called **forecastiq** on the **Free** plan. Click **Apply** (or **Deploy Blueprint**).
5. Click the service to watch the **logs** scroll. You'll see lines like:

   ```
   ==> Running build command 'pip install -r requirements.txt'...
   Successfully installed flask ... gunicorn ... numpy ... pandas ... scipy ...
   ==> Running 'gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 60 app:app'
   ==> Your service is live
   ```

6. After 3-6 minutes the status says **Live**. Click the link at the top: `https://forecastiq-xxxx.onrender.com`.
7. Check it the same way as Step 11: add `/api/health` to the end of the link.

**What just happened:** `render.yaml` is a short instruction sheet. Open it in your folder and you'll recognise everything:

```yaml
buildCommand: pip install -r requirements.txt      # like Step 0.4
startCommand: gunicorn ... app:app                  # like Step 11, but production-grade
healthCheckPath: /api/health                        # Render checks this, like you did
plan: free
autoDeploy: true                                    # redeploy whenever GitHub changes
```

**gunicorn** is the "proper" server for the internet. `python app.py` (Step 11) is only for testing on your own computer.

**If Blueprint asks for a card or fails:** choose **New + → Web Service** instead, pick the repository, and fill in:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 60 app:app`
- Instance type: **Free**

> **Problem we faced: we couldn't do this step for you.**
> Deployment needs **your** accounts and passwords. Everything was prepared so that this step is only clicks.

> **Problem we faced: gunicorn wasn't tested beforehand.**
> It wasn't installed on the computer we built on, so the app was tested with Flask's own server instead. If the first deploy fails, the error will be in the last lines of the log. Copy them and ask for help.

> **Problem you will notice: the app sleeps.**
> On the free plan, after **15 minutes** with no visitors, Render pauses the app. The next visitor waits **about a minute**. Not a bug, just the free plan. **Always open your link a couple of minutes before an interview or demo.**

**Common problems:**

| You see | Why | Fix |
|---|---|---|
| Build fails at `pip install` | Python version or a typo | `render.yaml` should say Python 3.13.5; read the log |
| "Missing artifacts" in the log | the `artifacts/` folder didn't upload | upload it on GitHub (Step 14.3) |
| "Service Unavailable" | the app is waking up | wait 60 seconds, refresh |
| Page says "Could not load this page" | an API call failed | check `/api/health` and the logs |


# Step 16. Change something and redeploy

**Goal:** see the full loop: change code → GitHub → Render updates the live site automatically.

**Do it:**

1. On GitHub, open `README.md` and click the **pencil** icon (Edit).
2. Find `_add your URL here after deploying_` and replace it with your Render link.
3. Click **Commit changes**.
4. Go to Render. Within a minute a new deploy starts by itself (because of `autoDeploy: true`). Watch it go **Live**.
5. On GitHub, open the **Actions** tab: the tests ran again too, and you should see a green tick.

**What just happened:** this loop (change → test automatically → deploy automatically) is called **CI/CD**: Continuous Integration (tests on every change) and Continuous Deployment (deploy on every change). Real companies work exactly like this, just at a bigger scale.

**Try this:** on GitHub, edit `static/styles.css` and change `--series-1` to purple like in Step 12. Commit. Wait for Render to redeploy and open your live site (`Cmd + Shift + R`). Your change is now on the internet. Change it back the same way.


# You did it

## Checklist

Tick these off:

- [ ] Python and the libraries work on my Mac, and `pytest` says 32 passed
- [ ] I made the data and charted one product in Numbers
- [ ] I found the weekend, promotion and Diwali patterns with `groupby`
- [ ] I checked the 28-day rule by hand
- [ ] I scored seasonal naive, Holt-Winters and gradient boosting myself
- [ ] I ran the full pipeline and read the leaderboard
- [ ] I saw conformal calibration fix a too-narrow range
- [ ] I ran the business analysis and read an inventory line
- [ ] I called the API from the browser and with curl
- [ ] I watched the frontend's requests in Developer Tools and changed a colour
- [ ] I broke the leakage rule, saw the test fail, and fixed it
- [ ] My code is on GitHub with a green tick in Actions
- [ ] My dashboard is live on Render, and the link is in my README

## What you can now say from experience

> "I built an end-to-end demand forecasting platform. I simulated three years of retail sales with known ground truth, engineered leakage-safe features, and compared a seasonal-naive benchmark, a Holt-Winters model I implemented myself, and a global gradient-boosting model in a rolling backtest. Gradient boosting cut error by 34%. I calibrated its prediction intervals with conformal prediction, and turned the forecasts into an inventory plan, price-elasticity estimates and anomaly alerts. It's served by a Flask API to a JavaScript dashboard, tested with 32 automated tests in CI, and deployed on Render."

Every sentence there is something you've now **done**, not just read.

## Where to go next

When you're comfortable, try one of these on your own:

1. **Use real data.** Download the M5 or Favorita dataset from Kaggle and rewrite `forecastiq/data.py` to load it into the same columns.
2. **Add a feature.** Add `lag_21` or a "days until next promotion" clue in `features.py`, rerun the pipeline, and see if the error drops.
3. **Add a page.** Add a ninth dashboard page that shows the ABC-XYZ list as a table.
4. **Schedule retraining.** Make a GitHub Action that runs the pipeline every week.

For the deeper "why" behind any step, open **PROJECT_GUIDE.pdf** in your folder. It explains every concept in more detail, and has a glossary at the end.
