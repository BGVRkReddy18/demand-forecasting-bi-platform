---
title: "ForecastIQ Interview Questions & Answers"
subtitle: "Every question you are likely to be asked about the project: the idea, data, ML models, testing, business analysis, APIs, backend, frontend, database, deployment. Short, easy answers you can say out loud."
---

# How to use this

**Don't memorise the answers word for word.** Read each one, understand it, then say it in your own words. Interviewers can tell when someone is reciting.

Each answer is written to be **spoken in 20-40 seconds**. If the interviewer wants more, they'll ask a follow-up; the next questions in each section are usually those follow-ups.

**Three golden rules:**

1. **Always say the data is simulated**, before they ask. Then explain why that was useful.
2. **Know your numbers** (Section 16 has all of them on one page).
3. **When you don't know something, say so**, then say how you'd find out. "I didn't do that, but I would..." is a strong answer. Making things up is the fastest way to fail.

**Labels:** each question has a level.

- **[Easy]** almost certain to be asked
- **[Medium]** asked when they want to check you really understand
- **[Hard]** asked by senior people or data science specialists

**Sections**

| # | Topic | # | Topic |
|---|---|---|---|
| 1 | The project in general | 10 | Backend (Flask) |
| 2 | The data | 11 | Frontend |
| 3 | Features | 12 | Database |
| 4 | The ML models | 13 | Testing & CI |
| 5 | Testing the models & metrics | 14 | Deployment, Docker, Git |
| 6 | Prediction ranges (uncertainty) | 15 | Scaling, production & MLOps |
| 7 | Business analysis | 16 | Numbers cheat sheet |
| 8 | The pipeline | 17 | Behavioural & tricky questions |
| 9 | APIs | | |


# 1. The project in general

### Q1. Tell me about your project. [Easy]

"I built a demand forecasting and business intelligence platform for a retail chain: 6 stores, 30 products, 3 years of daily sales. It's simulated data, which I'll explain. It forecasts daily sales for every product in every store 28 days ahead, with a range showing how sure it is. Then it turns those forecasts into decisions: what to reorder, how prices affect sales, and which sales look suspicious. Everything is shown on a web dashboard that's deployed online. The machine-learning model cut forecast error by 34% compared with a standard benchmark."

### Q2. What problem does it solve? [Easy]

Shops lose money in two ways: **running out of stock** (lost sales, unhappy customers) and **buying too much** (money stuck in boxes, storage costs, waste). To order the right amount you need to know how much you'll sell before the next delivery arrives. That's a forecast. My project gives that forecast, says how uncertain it is, and turns it into an order recommendation.

### Q3. Who would use it? [Easy]

- **Purchasing / supply chain team:** the inventory page, what to order today.
- **Category and store managers:** the overview and forecast pages.
- **Pricing and marketing:** the price sensitivity results and what-if simulator.
- **Data science team:** the model performance page, to check the model is still accurate.

### Q4. What's the tech stack? [Easy]

Python for everything on the data side: pandas and NumPy for data, scikit-learn for the machine-learning model, SciPy for statistics. Flask for the backend API, run by gunicorn. Plain HTML, CSS and JavaScript for the frontend, with charts I drew myself in SVG. pytest for tests, GitHub Actions to run them automatically, and Render's free plan for hosting.

### Q5. What's the architecture? [Easy]

Two halves. **Offline:** a Python pipeline generates the data, trains and tests the models, runs the business analysis, and saves all results as 7 JSON files. **Online:** a small Flask server loads those files into memory and serves them through an API, and the JavaScript dashboard in the browser calls that API and draws charts. The heavy work happens before deployment, so the website is fast and fits on a free server.

### Q6. What's the most impressive part? [Medium]

Pick one you're comfortable explaining:

- The **honest evaluation**: a rolling backtest where every number comes from data the model never saw, plus a test that proves there's no data leakage.
- The **calibrated prediction ranges** using conformal prediction.
- That the **analysis is checked against ground truth**: my price-sensitivity estimates came within 0.05 of the true values.

### Q7. How long did it take? What was your role? [Easy]

Answer honestly about your own timeline and what you did. (See Q189 on using AI tools.)

### Q8. Why did you choose this project? [Easy]

"Forecasting is one of the most common real uses of data science in business: retail, e-commerce, supply chain. I wanted a project that goes beyond training a model in a notebook: proper evaluation, turning predictions into decisions, and shipping it as a working product."

### Q9. What makes this "M.Tech level" rather than a basic project? [Medium]

- Rolling-origin backtesting instead of a random train/test split.
- A leakage-safe direct multi-horizon forecasting design.
- Conformal prediction for calibrated uncertainty.
- Poisson regression with fixed effects and cluster-robust errors for price elasticity.
- A count-based anomaly detector evaluated with precision and recall.
- Holt-Winters implemented from scratch.
- Results validated against known ground truth.
- Deployed, tested and documented end to end.

### Q10. What would you do differently if you started again? [Medium]

"I'd start with a real public dataset like M5 from Walmart, alongside the simulator, so I could show results on both. And I'd split the anomaly data into a tuning period and a reporting period from the beginning."


# 2. The data

### Q11. Where did the data come from? [Easy]

"It's **simulated**. I wrote a simulator that generates 3 years of daily sales for 6 stores and 30 products, 197,280 rows. Real store-level data is private, and simulation gave me something real data can't: **ground truth**. Because I wrote the recipe, I know the true price sensitivity and where the problems are hidden, so I can check whether my analysis finds them."

### Q12. Isn't simulated data a weakness? [Medium]

"Yes and no. The weakness: it's cleaner than real data. No missing days, no products being added or removed, no returns. The strength: I can validate the analytics against known truth, which you can never do with real data. The pipeline only needs one module, `data.py`, replaced to run on real data."

### Q13. How does the simulator work? [Medium]

For every product, store and day it starts from a normal sales level and multiplies in effects: a growth trend, a weekly pattern (weekends higher), a yearly season, the price effect, a promotion boost, a Diwali build-up and dip, other festivals, a payday bump, and random noise that's "sticky" from day to day. Then it turns the expected value into a whole number of units using a **negative binomial distribution**, because real sales are counts with extra randomness.

### Q14. What's in the dataset? [Easy]

One row per product per store per day: date, store, product (SKU), category, units sold, price, list price, promotion flag, discount, unit cost, revenue, and festival information like "days to Diwali". Plus the next 28 days of planned prices and promotions, without sales.

### Q15. What's a SKU? [Easy]

Stock Keeping Unit: a code for one specific product, like `GRO-01` (Grocery product 1).

### Q16. Why include Indian festivals? [Easy]

Because they drive huge sales swings in Indian retail: Diwali sales in our data are about 70% higher in the week before. Festival dates move every year (Diwali was 20 October 2025, 8 November 2026), so a model that only learns "October is busy" would be wrong. The features include "days until Diwali" instead.

### Q17. Why is it fair to use future prices and promotions? [Medium]

A business decides its own prices and promotions in advance, so they're known at forecast time. Future **sales** are not known, so sales-based features are only ever taken from the past.

### Q18. What is ground truth? [Easy]

The real, correct answer. With simulated data I know the true values I planted (for example, Electronics price sensitivity is exactly -2.2), so I can measure how close my estimates get.

### Q19. Did you clean the data? [Medium]

The simulated data has no errors to clean, but it does have planted anomalies: about 3 stock-outs or spikes per product-store pair, 548 events in total. I didn't remove them from training (the model has to cope with them, like in real life). I detect them separately in the anomaly module. With real data I'd add missing-date filling, duplicate checks, and correcting stock-out days.

### Q20. What did you find in exploratory analysis (EDA)? [Easy]

Weekends sell about 23% more than weekdays, promotion days about 50% more, the week before Diwali about 70% more. Grocery sells the most units, Electronics the fewest units but the most revenue. Those checks also confirmed the simulator worked as intended.

### Q21. What problem did you hit with the data? [Medium]

"In the first version Electronics prices went up to ₹40,000, and Electronics made about ₹423 crore against ₹40-75 crore for other categories, so every chart was just Electronics. I narrowed the price range to ₹1,500-12,000. I also had to adjust the simulated stock levels: the first version made 50 of 180 products 'critical', which isn't realistic."

### Q22. Why use a random seed? [Easy]

So the "random" data is identical every run. That makes results **reproducible**: anyone running the code gets the same numbers.


# 3. Features

### Q23. What features did you use? [Easy]

30 features in five groups:

- **Past sales:** sales 28, 35, 42, 49, 56 and 364 days ago.
- **Recent averages:** average over 7, 28 and 56 days, how jumpy sales are, trend, share of zero days.
- **Price and promotion:** price, price compared with normal, discount, promotion now, promotion coming next week.
- **Calendar:** day of week, day of month, month, weekend, payday.
- **Festivals:** is it a festival, days to the nearest festival, days to Diwali.
- Plus which store, product and category.

### Q24. What's a lag feature? [Easy]

A past value of the series. "Lag 28" means "sales 28 days ago".

### Q25. What's a rolling mean? [Easy]

The average over a moving window. "Rolling mean 28" on each day is the average of the 28 days before it. It smooths out daily noise.

### Q26. Why is the smallest lag 28 and not 1? [Medium]

"Because I forecast 28 days ahead. On the last forecast day, the newest real sales I'd have are 28 days old. If I used yesterday's sales as a feature, I'd be using information I won't have when making a real forecast. That's called **leakage**. So every sales-based feature is at least 28 days old."

### Q27. What is data leakage? [Easy]

Accidentally using information during training or testing that wouldn't be available when making real predictions. It makes test results look better than reality. It's the most common mistake in forecasting projects.

### Q28. How did you make sure there's no leakage? [Medium]

Three ways: all sales features are lagged at least 28 days; every evaluation step only uses earlier data; and an **automatic test** overwrites the last 27 days of sales with nonsense and checks that none of the forecast features change.

### Q29. What's the downside of the 28-day lag? [Hard]

"The model can't react to anything from the last 4 weeks. If sales suddenly jumped last week, it won't know. The benefit is one simple model for all 28 days and honest testing. A fix would be separate models for short horizons, say days 1-7, which can use more recent sales."

### Q30. What's direct vs recursive forecasting? [Hard]

**Recursive:** forecast tomorrow, then feed that forecast back in as "yesterday" to forecast the day after, and so on. Errors pile up. **Direct:** predict each future day only from real, known data. I used direct with one model for all 28 days, which works because every feature is at least 28 days old.

### Q31. Which features mattered most? [Medium]

Measured by permutation importance: the 56-day average sales by far, then which product it is, the 28-day average, price relative to normal, sales variability, day of week, store and discount. So the model works out the product's normal level first, then adjusts for price, promotions and day of week, just like a human planner would.

### Q32. What's permutation importance? [Medium]

Shuffle one feature's values randomly, which destroys its information, and measure how much worse the predictions get. Bigger damage means more important. It works with any model and is measured on test data, so it's more trustworthy than a tree model's built-in importance.

### Q33. How did you handle categorical features like store or product? [Medium]

I converted them to integer codes and told the gradient boosting model they're categorical. scikit-learn's HistGradientBoosting handles categorical features natively, so I didn't need one-hot encoding.

### Q34. How did you handle missing values? [Medium]

Early rows have no "sales 364 days ago", for example. HistGradientBoosting handles missing values natively: it learns which way to send them in each split. I also start training from day 92 so most lag features exist.


# 4. The ML models

### Q35. Which models did you use? [Easy]

Four:

1. **Seasonal naive**: the benchmark, "same as last week".
2. **Holt-Winters exponential smoothing**: a classic statistical method, which I implemented myself.
3. **Global gradient boosting**: machine learning, the winner.
4. **A weighted ensemble** of the three.

### Q36. Why use such a simple benchmark? [Easy]

Because any fancy model must beat it, or it's not worth the complexity. Seasonal naive is surprisingly hard to beat, and reporting a benchmark is standard practice in forecasting.

### Q37. Explain Holt-Winters simply. [Medium]

It tracks three things and updates them a little every day: the **level** (normal sales right now), the **trend** (going up or down) and the **season** (how much higher or lower each weekday is). Three settings, alpha, beta and gamma, control how fast each one reacts. I also used a **damped** trend, so a trend fades out instead of continuing forever.

### Q38. Why did you implement Holt-Winters yourself? [Medium]

"The statsmodels library wasn't available in my environment, so I wrote it from the formulas, about 60 lines. It's also vectorised: it updates all 180 series at once with NumPy arrays. For each series it tries 90 combinations of settings and keeps the one that fits that series' history best."

### Q39. Why model the log of sales? [Hard]

It turns multiplicative effects ("weekends ×1.2") into additive ones ("+0.18"), which Holt-Winters handles better, and converting back guarantees forecasts are never negative. I used log(1 + sales) so zero sales work.

### Q40. What's the weakness of Holt-Winters here? [Medium]

It only sees past sales. It can't see that a promotion or Diwali is coming, so it's always surprised by them. That's why its bias was -8%: it under-forecasts.

### Q41. Explain gradient boosting simply. [Easy]

A **decision tree** predicts by asking yes/no questions, like 20 questions: "Is the 8-week average above 50? Is it a weekend? Is there a promotion?" One tree is crude. **Gradient boosting** builds hundreds of small trees one after another, and each new tree focuses on the mistakes the previous trees still make. Together they're very accurate.

### Q42. Which gradient boosting library did you use? [Easy]

scikit-learn's `HistGradientBoostingRegressor`. Same family as LightGBM. (Don't claim LightGBM or XGBoost.)

### Q43. Why gradient boosting and not linear regression? [Medium]

Sales effects interact. A promotion matters more for Apparel than Grocery; weekends matter more near Diwali. Trees find these interactions automatically. Linear regression would need me to create every interaction by hand.

### Q44. Why not deep learning, like LSTM or Transformers? [Medium]

"For tabular data with strong known drivers like price, promotions and calendar, gradient boosting is usually as accurate or better, trains in seconds, is easier to explain, and runs cheaply. Most top solutions in the M5 forecasting competition were gradient boosting. Deep learning makes more sense with much more data or many related signals."

### Q45. Why not Prophet or ARIMA? [Medium]

Prophet and ARIMA fit one model per series and handle external drivers like price less naturally. With 180 series that share patterns, one global model learns from all of them at once. Also, Prophet wasn't available in my environment. Holt-Winters already gives me a classical comparison.

### Q46. What does "global model" mean? Why one model for all series? [Medium]

One model trained on all 180 product-store series together, with store and product as features. It learns shared patterns like "promotions boost sales" from all products at once, which especially helps slow sellers that have little data of their own. And there's one model to maintain instead of 180.

### Q47. What's the Poisson loss and why use it? [Hard]

The loss is how the model measures its mistakes while learning. Sales are counts (0, 1, 2...), never negative, and products that sell more naturally vary more. The **Poisson loss** is designed for that kind of data. The default squared-error loss assumes errors are the same size everywhere.

### Q48. What hyperparameters did you use? How did you tune them? [Hard]

300 trees, learning rate 0.06, at most 48 leaves per tree, at least 40 samples per leaf, L2 regularisation 1.0. "I chose sensible values and checked them in the backtest, but I didn't run a full hyperparameter search. That's a clear next step: tune on an inner validation window with something like Optuna, so the test folds stay untouched."

### Q49. How did you prevent overfitting? [Medium]

A small learning rate, a minimum of 40 samples per leaf, L2 regularisation, a limited number of leaves, and above all honest testing on future data the model never saw. If it had been overfitting, the backtest scores would have been bad.

### Q50. What's an ensemble? [Easy]

Combining several models' predictions. Mine was a weighted average of the three models, giving more weight to whichever model was more accurate for each product in earlier tests.

### Q51. Did the ensemble win? [Medium]

"No, and that's one of the most interesting results. The ensemble had 27.8% error, gradient boosting alone 25.9%. I tried 7 variations, like stronger weighting and dropping the weakest model. The best got to 26.25%, still worse. So instead of forcing it, I set up champion/challenger selection."

### Q52. Why did the ensemble lose? [Hard]

"Ensembles help when the models are similarly good and make **different** mistakes. Here, two of the three models can't see price, promotions or festivals. Mixing them in pulls the good model's forecasts toward less informed ones."

### Q53. What is champion/challenger? [Medium]

After each test round, the model with the lowest error so far becomes the **champion** and produces the real forecast. The others stay as **challengers** and keep being measured. If a challenger becomes better, it takes over. It's a common pattern in production ML.

### Q54. How many models are trained in total? [Hard]

For each of the 4 backtest rounds and the final forecast: one gradient boosting model for the mean forecast and two for the low and high ranges, plus Holt-Winters for all 180 series. So 15 gradient boosting models and Holt-Winters fitted 5 times. The full pipeline takes about 2 minutes.

### Q55. Do you save the trained model to a file? [Medium]

"No, and I don't need to. The website only shows pre-computed forecasts, so I save the **predictions** as JSON, not the model. If the app had to forecast new inputs live, I'd save the model with joblib and load it at startup."


# 5. Testing the models & metrics

### Q56. How did you evaluate the models? [Easy]

"With a **rolling-origin backtest**. I pretended 'today' was four different past dates. Each time I trained only on data before that date and forecast the next 28 days, then compared with what really happened. The first round only calibrates; the other three give 15,120 forecasts that I score."

### Q57. Why not a normal random train/test split? [Easy]

With time series, a random split lets the model learn from Thursday to predict Wednesday. In real life you only ever have the past. The test must always be "train before a date, predict after it".

### Q58. Why four rounds instead of one? [Medium]

One test period can be lucky or unlucky (for example, it might contain Diwali). Several rounds in a row give a more reliable picture and show whether accuracy is stable over time.

### Q59. What metrics did you use? [Easy]

WAPE as the main one, plus MAE, RMSE, MASE, sMAPE and bias.

### Q60. What's WAPE? [Easy]

Weighted Absolute Percentage Error: total of all errors ÷ total actual sales. "25.9% WAPE" means the errors add up to 25.9% of the sales volume.

### Q61. Why WAPE instead of MAPE? [Medium]

MAPE divides each day's error by that day's sales. When sales are zero, you divide by zero; for slow products it explodes. WAPE divides **totals**, so it always works, and busy products count more, which matches what a business cares about.

### Q62. What's MAE and RMSE? [Easy]

**MAE:** average size of the errors, in units. **RMSE:** square the errors, average, then square root. It punishes big misses more than MAE.

### Q63. What's MASE? [Medium]

Mean Absolute Scaled Error: your error divided by the error of the naive method. Below 1 means you beat the naive method. Mine was 0.71. It's scale-free, so you can compare products of very different sizes.

### Q64. What's bias, and why does it matter? [Medium]

Whether forecasts are systematically too high (positive) or too low (negative). It matters because consistent under-forecasting means constant stock-outs. My champion's bias was -0.5%, almost none. Holt-Winters was -8%: it consistently under-forecast because it can't see promotions.

### Q65. What were the results? [Easy]

| Model | WAPE |
|---|---|
| Seasonal naive | 39.1% |
| Holt-Winters | 31.6% |
| **Gradient boosting (champion)** | **25.9%** |
| Ensemble | 27.8% |

34% less error than the benchmark, MASE 0.71, bias -0.5%.

### Q66. 25.9% error sounds high. Is that bad? [Medium]

"Not at the level of one product in one store on one day. Much of what's left is pure randomness no model can predict. When you add up, random errors cancel: the same forecasts have 11.7% error per product per day, 3.5% for the whole company per day, and 8.9% for each product-store's 4-week total, which is what purchasing actually uses."

### Q67. Does accuracy get worse further into the future? [Hard]

"Almost not: about 25.7% in week 1 and 25.9% in week 4. Normally forecasts get worse with distance. Mine don't because of the direct design: every forecast day uses the same 28-day-old information, so day 1 has no advantage over day 28."

### Q68. Which products were hardest to forecast? [Medium]

Electronics (34.5% WAPE): few units, big swings. Easiest was Grocery (23.7%): lots of units, steady.

### Q69. What's overfitting and how would you spot it? [Easy]

When a model memorises training data instead of learning general patterns. It looks great on training data and bad on new data. You spot it by comparing performance on data it never saw, which is exactly what the backtest does.

### Q70. What's the difference between validation and test data? [Medium]

Validation data is used to make choices (like which model or settings); test data is only used for the final score. In my backtest, choices for each round (champion, weights, calibration) are made only from **earlier** rounds, so each round acts as a clean test.


# 6. Prediction ranges (uncertainty)

### Q71. Why give a range and not just a number? [Easy]

A single number hides uncertainty. "We'll sell 450" and "we'll sell 450, give or take 200" lead to very different decisions. The range tells the business how much safety stock to hold.

### Q72. What does an "80% prediction interval" mean? [Easy]

A range that should contain the real value 80% of the time. If it does that, it's **well calibrated**.

### Q73. How did you create the ranges? [Medium]

Two extra gradient boosting models trained with **quantile (pinball) loss**: one predicts the 10th percentile, one the 90th. Between them is a raw 80% range. Then I calibrated it with conformal prediction.

### Q74. What's quantile or pinball loss? [Hard]

A loss that trains a model to predict a percentile instead of the average. For the 90th percentile it punishes under-predictions 9 times more than over-predictions, so the model learns a value that's exceeded only 10% of the time.

### Q75. What is conformal prediction? [Medium]

"A way to make ranges honest using past mistakes. Look at the backtest: measure how far outside the ranges the real values fell. Find the amount you'd have needed to widen them so 80% fit. Widen all future ranges by that amount. Like a tailor whose shirts were always 2 cm too tight: from now on, add 2 cm. The version I used is called Conformalised Quantile Regression, CQR."

### Q76. What was the coverage? [Easy]

Raw ranges: 76.9%. After conformal calibration: **78.7%**, against an 80% target. Consistent across categories (77.8%-79.6%).

### Q77. Why isn't it exactly 80%? [Hard]

"Conformal prediction assumes the future looks like the calibration period. The most recent weeks were a bit more volatile than the earlier ones, so coverage is slightly under. It's close, and I report it honestly as 78.7%."

### Q78. Why scale the widening by product size? [Hard]

A product selling 1,000 a day needs a wider range than one selling 5. I divide the errors by the square root of the forecast before calibrating, which matches how count data naturally varies.


# 7. Business analysis

### Q79. How do forecasts become business decisions? [Easy]

Four ways: an **inventory plan** (what to reorder, how much), **ABC-XYZ grouping** (which products need most attention), **price sensitivity** with a what-if simulator, and **anomaly detection**.

### Q80. What's safety stock? [Easy]

Extra stock kept as a cushion in case sales are higher than forecast before the next delivery arrives.

### Q81. How did you calculate it? [Medium]

Safety stock = z × σ × √(lead time).

- **σ** is how wrong my forecast typically is per day, measured in the backtest.
- **lead time** is how many days a delivery takes.
- **z** comes from the service level: 98% for the most important products gives z ≈ 2.05.

### Q82. Why use forecast error and not demand variability for σ? [Hard]

"The forecast already expects the weekend rush, promotions and Diwali. The cushion only needs to cover what the forecast gets **wrong**. Using total demand variability would mean holding stock for swings the forecast already predicts. It's the more modern approach."

### Q83. Why the square root of lead time? [Hard]

Daily errors partly cancel out: a good day and a bad day balance. If errors are independent, the uncertainty over L days grows with √L, not L. Over 4 days it's twice one day's uncertainty, not four times.

### Q84. What's the reorder point? [Easy]

The stock level at which you place a new order: expected sales during the lead time + safety stock.

### Q85. What's EOQ? [Medium]

Economic Order Quantity: the order size that balances two costs. Ordering often costs more in order fees; ordering rarely means big piles of stock that cost money to hold. I assumed ₹500 per order and 20% of the item cost per year for holding.

### Q86. Give an example from your output. [Medium]

"Apparel product 2 in Bengaluru: 360 units on hand, selling about 26 a day, so about 8 days of stock. But deliveries take 10 days. So it's **Critical**: it will run out before a new order can arrive. The system recommends ordering 299 units, about ₹2.7 lakh."

### Q87. What's ABC-XYZ analysis? [Medium]

Two ways of grouping products. **ABC** by importance: A = the products making the top 80% of revenue, B = next 15%, C = last 5%. **XYZ** by predictability: X = steady, Y = medium, Z = erratic, measured by the coefficient of variation of weekly sales. AZ products are important and hard to predict, so they get the most attention and the highest service level.

### Q88. What's price elasticity? [Easy]

The % change in sales when price changes by 1%. Electronics at -2.2: a 1% price rise loses about 2.2% of sales. Grocery at -0.8 barely reacts. Below -1 is "elastic": cutting price raises revenue.

### Q89. How did you estimate elasticity? [Hard]

"A **Poisson regression** of units sold on log price and a promotion flag, with **fixed effects** for every product-store, plus day-of-week, month and festival controls. Fixed effects mean each product is only compared with itself at different prices. I solved it with IRLS (iteratively reweighted least squares) and used **cluster-robust standard errors**, clustered by series, for the 95% intervals."

### Q90. Why not just compare high-price days with low-price days? [Medium]

**Confounding.** Low prices happen during promotions, and promotions happen before Diwali, when sales are high anyway. A simple comparison would credit the price for what Diwali did. The regression controls for those other effects at the same time.

### Q91. Why Poisson regression and not ordinary regression on log sales? [Hard]

Log of zero doesn't exist, so log-regression has to drop or fudge zero-sales days, which biases the result. Poisson regression handles zeros naturally and stays consistent even when the variance doesn't match a Poisson exactly. Economists call this PPML.

### Q92. What are fixed effects? [Hard]

A separate baseline for each group, here each product-store pair. They absorb everything constant about that product in that store, so the price effect is estimated only from changes within the same product.

### Q93. What are cluster-robust standard errors? [Hard]

Sales on consecutive days of the same product are related, not independent. Normal standard errors assume independence and would be too small, making me overconfident. Clustering by series corrects that.

### Q94. How accurate were the elasticity estimates? [Easy]

Within 0.05 of the true values for all five categories, and every true value was inside its 95% interval. For example, Electronics: estimated -2.23, true -2.20.

### Q95. What's the what-if simulator? [Easy]

You pick a category, store, a price change (-30% to +30%) and whether it's a promotion. It applies the elasticity to the forecast and shows the new units, revenue and margin, plus a curve across all price changes. For example, cutting Apparel prices 10% raises revenue but lowers profit.

### Q96. What are the simulator's limits? [Medium]

It assumes constant elasticity at any price, and ignores competitors reacting and customers switching between products. "In fact the curve said margin is highest at +30%, the edge of the range. I changed the page to say that's a direction, not a target."

### Q97. How does anomaly detection work? [Medium]

For each day, expected sales = the median of the same weekday over the previous 8 weeks (non-promotion days), raised on promotion days. Then a z-score: how far actual sales are from expected, compared with normal variation for count data. Flag if beyond 4.5. Runs of zero-sales days are flagged if their combined probability is that unlikely, which catches stock-outs on slow sellers. Festival windows are skipped.

### Q98. Why the median and not the average? [Easy]

The median ignores occasional extreme values, so one past spike doesn't distort what's "normal".

### Q99. What are precision and recall? [Easy]

**Precision:** when the alarm rings, how often is it a real problem? **Recall:** of all real problems, how many did the alarm catch? Mine: 64% precision, 72% recall (395 of 548 planted events).

### Q100. How did you choose the threshold? [Hard]

"I tried 3.5, 4, 4.5 and 5 and picked 4.5 as a balance. Honestly, I chose it while looking at the planted truth, so the scores are slightly optimistic. Properly, I'd tune on one period and report on another."

### Q101. What problem did you hit with anomaly detection? [Medium]

"My first version used a simple robust z-score and got 21% precision and 44% recall. I rebuilt it with a count-aware noise model, promotion adjustment and a zero-run check, which got it to 64% and 72%."


# 8. The pipeline

### Q102. What is a pipeline? [Easy]

A fixed sequence of steps where each step's output feeds the next, so the whole process can be re-run with one command. Mine is `python -m forecastiq.pipeline`.

### Q103. What are the steps? [Easy]

Generate data → build features → 4 backtest rounds → pick the champion → calibrate the ranges → final forecast → business analysis → save 7 JSON files.

### Q104. How long does it take? [Easy]

About 110 seconds on a laptop. Most of it is training gradient boosting.

### Q105. What are artifacts? [Easy]

The files a training run produces. Mine are 7 JSON files (1.9 MB) with forecasts, model scores, inventory plan, pricing results and anomalies. The website reads only these.

### Q106. Why separate training from serving? [Medium]

Training is slow and needs more memory and libraries; serving needs to be fast and cheap. Running training offline means the website starts in about 1 second, uses about 145 MB, and doesn't even need scikit-learn installed. This pattern is called **batch scoring** or offline inference.

### Q107. How would you refresh forecasts with new data? [Medium]

Re-run the pipeline and commit the new artifacts; Render redeploys automatically. In production I'd schedule it, for example a weekly GitHub Action or a cron job, and add checks before publishing.

### Q108. Where are the settings stored? [Easy]

All in one file, `config.py`: horizon, number of folds, coverage target, stores, categories, festival dates, costs, service levels and the random seed.


# 9. APIs

### Q109. What is an API? [Easy]

Application Programming Interface: a set of addresses (URLs) a server offers, so other programs can ask it for data or ask it to do something. My frontend gets all its data from my backend's API.

### Q110. What endpoints does your API have? [Easy]

| Method | Endpoint | Returns |
|---|---|---|
| GET | `/api/health` | "status ok", for health checks |
| GET | `/api/meta` | basic info and dropdown options |
| GET | `/api/overview` | KPIs and summary tables |
| GET | `/api/forecast?node=...` | forecast for one level (total, region, category, store or product) |
| GET | `/api/performance` | model scores |
| GET | `/api/inventory` | replenishment plan |
| GET | `/api/pricing` | elasticities |
| GET | `/api/anomalies` | anomaly report |
| POST | `/api/scenario` | runs the what-if simulator |
| POST | `/api/forecast-upload` | forecasts an uploaded CSV |
| GET | `/api/sample.csv` | a sample file to try |

### Q111. What's REST? Is your API RESTful? [Medium]

REST is a common style for web APIs: resources at clear URLs, standard HTTP methods (GET to read, POST to create or process), and stateless requests. Mine follows it in spirit: GET for reading results, POST for the two endpoints that calculate something, and no server-side sessions.

### Q112. What's the difference between GET and POST? [Easy]

**GET** asks for something and sends no body (like reading a page). **POST** sends data in the request body for the server to process (like submitting a form). The scenario and upload endpoints use POST because they send inputs.

### Q113. What's JSON? Why use it? [Easy]

JavaScript Object Notation: a simple text format for data, like `{"label": "Apparel", "forecast": [812, 790]}`. Both Python and JavaScript read it natively, so it's the standard for web APIs.

### Q114. What's a query parameter? [Easy]

Extra information in the URL after `?`. In `/api/forecast?node=category:Apparel`, `node` is the parameter and `category:Apparel` its value.

### Q115. What HTTP status codes does your API return? [Easy]

**200** OK, **400** bad input (for example, a price change of 500%), **404** not found (unknown forecast node), **413** file too large (over 2 MB). **500** would mean a server bug.

### Q116. How do you validate input? [Medium]

The scenario endpoint checks the price change is a number between -50% and +50%, and that the category/store exists. The upload endpoint checks file size (2 MB), row count (5,000), that it's a readable CSV with a date and a number column, no negative values, and enough history. Each problem returns a clear error message, not a crash.

### Q117. What happens step by step when the frontend calls the API? [Medium]

1. JavaScript calls `fetch("/api/forecast?node=category:Apparel")`.
2. The request goes over HTTP(S) to the server.
3. gunicorn receives it and passes it to Flask.
4. Flask matches the URL to the `forecast()` function.
5. The function looks up the data in memory and returns JSON with status 200.
6. JavaScript receives the JSON and draws the chart.

### Q118. How fast is the API? [Medium]

About 0.4 milliseconds per forecast request on my machine, because it's a lookup in memory. On the free server the network adds more, but it's still fast.

### Q119. Is the API secure? [Medium]

"It's read-only and public, with no personal data and no secrets, so the risk is low. It validates all input, limits upload size, doesn't store uploads, and the Docker container runs as a non-admin user. For a real company I'd add authentication, rate limiting, HTTPS-only headers and logging." (Render provides HTTPS automatically.)

### Q120. Did you need CORS? [Hard]

No. CORS matters when a web page calls an API on a **different** domain. My frontend and API are served from the same server and domain, so the browser allows it by default.

### Q121. Did you version your API? [Medium]

"No. With one frontend that ships together with the API, it wasn't needed. If other apps depended on it, I'd add a version prefix like `/api/v1/` so I could change it without breaking them."

### Q122. Did you document the API? [Medium]

In the README, with a table of endpoints. With FastAPI I'd get automatic interactive docs (Swagger/OpenAPI). That's an improvement I'd consider.


# 10. Backend (Flask)

### Q123. What is the backend? [Easy]

The part that runs on the server: receives requests, finds or calculates the answer, sends it back. Mine is `app.py`, a Flask application.

### Q124. What is Flask? [Easy]

A small Python library for building web servers. You write normal functions and attach each to a URL with a decorator, like `@app.get("/api/forecast")`.

### Q125. Why Flask and not Django or FastAPI? [Medium]

"Django is a big framework with a database, admin panel and user accounts, which I don't need. FastAPI would be a good choice too, with automatic docs and type validation, but it wasn't available in my environment and Flask was. For a small read-mostly API, Flask is simple and enough."

### Q126. What's a decorator? [Medium]

A line starting with `@` above a function that wraps it with extra behaviour. `@app.get("/api/health")` registers the function as the handler for that URL.

### Q127. What happens when the server starts? [Medium]

It reads the 7 JSON artifact files into a Python dictionary in memory (about 1 second). If any file is missing, it stops with a clear message telling you to run the pipeline.

### Q128. What is gunicorn? Why not just `python app.py`? [Medium]

Flask's built-in server is for development only. **gunicorn** is a production server: more robust, handles several requests at once, restarts crashed workers. I run 1 worker with 4 threads to save memory on the small free server.

### Q129. What's the difference between a worker and a thread? [Hard]

A **worker** is a separate copy of the app (a process) with its own memory; each would load the data again. A **thread** runs inside one worker and shares its memory. With read-only data in memory, 1 worker with 4 threads handles concurrent requests while using memory once.

### Q130. How much memory does it use? [Easy]

About 145 MB, well inside the free plan's 512 MB.

### Q131. Why doesn't the website need scikit-learn? [Medium]

"I import scikit-learn only inside the training class. The website never trains, so it only needs 5 libraries: flask, gunicorn, numpy, pandas and scipy. That makes the server smaller and faster to deploy. I tested the website with scikit-learn blocked."

### Q132. Which endpoints compute something live? [Medium]

Two: the **what-if simulator** applies the elasticity formula to the forecast, and the **CSV upload** fits Holt-Winters on the user's data. Everything else is a lookup.

### Q133. Why does the upload use Holt-Winters and not gradient boosting? [Medium]

Training gradient boosting on every request would be too slow on a tiny free server, and an uploaded file has no price or promotion columns anyway, which is where gradient boosting's advantage comes from. Holt-Winters fits in well under a second.

### Q134. How does the upload decide daily, weekly or monthly? [Hard]

It looks at the typical gap between dates: about 1 day means daily, about 7 weekly, otherwise monthly. Then it regularises the dates, fills small gaps, checks there's enough history for the seasonal period, and tests Holt-Winters against seasonal naive on held-back data before forecasting.

### Q135. What happens if something crashes? [Medium]

Input problems return clear 400/404/413 errors. Render's health check calls `/api/health`; if the app stops responding, Render restarts it. In production I'd add error logging and alerts.


# 11. Frontend

### Q136. What is the frontend? [Easy]

What runs in the visitor's browser: **HTML** for structure, **CSS** for appearance, **JavaScript** for behaviour and charts.

### Q137. What does the dashboard have? [Easy]

Eight pages: Overview, Forecast explorer, Model performance, Inventory planning, Pricing & promotions, Anomaly monitor, Forecast your data (CSV upload), and Methodology.

### Q138. Did you use React or another framework? [Medium]

"No, plain JavaScript. For a dashboard this size, a framework adds build tools and complexity without much benefit. Plain JavaScript loads instantly and has nothing to install or build, which also makes deployment simpler. For a larger app with many developers, I'd use React."

### Q139. Why not Streamlit or Dash? [Medium]

Streamlit is great for quick demos, but it controls the layout and runs everything server-side, and it wasn't available in my environment anyway. Building the frontend myself gave full control of the design and shows I understand how frontends and APIs connect.

### Q140. What's a single-page application? [Medium]

A website that loads once and then swaps content with JavaScript, without reloading the page. My menu changes the part of the URL after `#` (like `#inventory`), and JavaScript shows the right page. Bookmarks and the Back button still work.

### Q141. How does the frontend get data? [Easy]

With JavaScript's `fetch()` function, calling my API and receiving JSON. It keeps a small in-memory cache, so asking for the same data twice doesn't call the server again.

### Q142. How did you make the charts? [Medium]

"By hand, in SVG. SVG describes pictures as shapes, like 'a line from here to here'. My `charts.js` (about 170 lines) draws line charts with shaded ranges and hover tooltips, and bar charts. No chart library was available, and this keeps the site tiny."

### Q143. What's SVG? [Easy]

Scalable Vector Graphics: pictures described as shapes in code. They stay sharp at any zoom and can be created with JavaScript.

### Q144. How does dark mode work? [Medium]

Every colour is a **CSS variable** defined in one place. Dark mode swaps the variable values. It follows the computer's setting automatically (`prefers-color-scheme`), and the "Switch theme" button overrides it.

### Q145. Does it work on mobile? [Easy]

Yes. Below 980 pixels wide, CSS media queries move the menu to the top and stack the panels in one column. Charts redraw to fit their width when the window resizes.

### Q146. What did you do for accessibility? [Medium]

Status colours always come with a text label (never colour alone); the colour palette was checked for colour-blind readers; charts have labels and a hover tooltip with exact numbers; buttons and inputs are keyboard-focusable with visible focus outlines. A full accessibility audit would be a next step.

### Q147. What frontend problems did you hit? [Medium]

"I took screenshots of every page in light mode, dark mode and phone size, and found layout bugs the code didn't report: overlapping chart labels, tables cut off, a page wider than a phone screen, oversized text in a tile, and internal code names in a legend. All fixed. Lesson: 'it runs' isn't the same as 'it works'."

### Q148. How do numbers appear in the Indian format? [Easy]

JavaScript's `toLocaleString("en-IN")` gives 2,32,832, and I format money as ₹13.87 Cr or ₹66.9 L.


# 12. Database

### Q149. What database did you use? [Easy]

"None, on purpose. The website only reads results and the data changes only when the pipeline runs. So I store results as JSON files and load them into memory. That's faster than a database query, simpler, free, and nothing extra to secure."

### Q150. Isn't a project without a database incomplete? [Medium]

"A database is a tool for data that changes often or is written by many users: orders, accounts, transactions. My app is read-only, so a database would add cost and complexity without benefit. Choosing not to use one when it isn't needed is a design decision."

### Q151. When would you add a database? [Medium]

If real sales data arrived daily, if users logged in, or if users could save their own scenarios. Then I'd store sales and forecasts in **PostgreSQL**, have the pipeline read from and write to it, and have the API query it.

### Q152. Which database would you choose, and why? [Medium]

PostgreSQL: reliable, free, excellent for structured tables like sales, and widely used. For very large analytics, a warehouse like BigQuery or Snowflake. A NoSQL store like MongoDB doesn't suit this data, which is naturally a table.

### Q153. How would you design the tables? [Hard]

- `stores` (store_id, city, region)
- `products` (sku_id, category, base price, lead time)
- `sales` (date, store_id, sku_id, units, price, promo), with the primary key (date, store_id, sku_id)
- `forecasts` (run_id, date, store_id, sku_id, forecast, low, high, model)
- `model_runs` (run_id, created_at, champion, wape, coverage)

Indexes on (store_id, sku_id, date) for fast lookups of one series.

### Q154. What's SQL vs NoSQL? [Easy]

**SQL** databases (PostgreSQL, MySQL) store data in tables with fixed columns and relationships, queried with SQL. **NoSQL** databases (MongoDB, Redis, etc.) store documents, key-value pairs or graphs with flexible structure. Sales data is naturally tabular, so SQL fits.

### Q155. What's an index? [Medium]

A sorted lookup structure that makes searches fast, like a book's index. Without it the database scans every row. The trade-off: writes are slightly slower and it uses extra space.

### Q156. What's a primary key and foreign key? [Easy]

**Primary key:** a column (or columns) that uniquely identifies each row, like `sku_id` in products. **Foreign key:** a column pointing to another table's primary key, like `sku_id` in sales pointing to products.

### Q157. Write a SQL query for total revenue by category last month. [Medium]

```sql
SELECT p.category, SUM(s.units * s.price) AS revenue
FROM sales s
JOIN products p ON p.sku_id = s.sku_id
WHERE s.date >= '2026-10-01' AND s.date < '2026-11-01'
GROUP BY p.category
ORDER BY revenue DESC;
```

### Q158. Is JSON-in-memory a problem if data grows? [Hard]

Yes, eventually. My forecast file is 1.7 MB for 180 series. At tens of thousands of series it would be too big to load into memory per server, so I'd move it to a database and fetch only what each request needs, possibly with a cache like Redis.


# 13. Testing & CI

### Q159. How did you test the code? [Easy]

"32 automatic tests with pytest. They check the models, the data, the features, the analysis and the API, and run in about 10 seconds. GitHub Actions runs them automatically on every change."

### Q160. Give examples of your tests. [Medium]

- **No leakage:** tamper with recent sales and check forecast features don't change.
- **The champion beats the benchmark** by at least 20%, with MASE under 1 and coverage between 70% and 90%.
- **Forecasts add up:** category forecasts sum to the total.
- **Elasticity is recovered** within 0.15 of the truth.
- **The API rejects bad input** with 400/404 errors.
- **CSV upload works** for daily, weekly and monthly files, and rejects bad files.

### Q161. What's the difference between unit tests and integration tests? [Medium]

**Unit tests** check one small piece alone, like "seasonal naive repeats the last week". **Integration tests** check pieces working together, like "the API returns a forecast whose categories add up to the total". I have both.

### Q162. What's CI? [Easy]

Continuous Integration: tests run automatically on a remote computer every time code is pushed. GitHub shows a green tick or red cross next to each change, so problems are caught before they reach users.

### Q163. What's CI/CD? [Medium]

CI = automatic testing on every change. CD = Continuous Deployment, automatic release on every change. I have both: GitHub Actions runs the tests, and Render redeploys automatically when GitHub changes.

### Q164. How do you test an ML model, when its output isn't exact? [Hard]

You test **properties** instead of exact values: the forecast is never negative, ranges contain the forecast, totals add up, the model beats a benchmark by a margin, accuracy stays within a range, and known effects are recovered within a tolerance. These act as guard-rails: if a change makes the model worse than promised, a test fails.


# 14. Deployment, Docker, Git

### Q165. Where is it deployed? [Easy]

On Render's free plan. Code lives on GitHub; Render builds and runs it and gives a public HTTPS link.

### Q166. Walk me through how deployment works. [Medium]

I push code to GitHub. Render, connected to the repository, reads `render.yaml`: it runs `pip install -r requirements.txt`, then starts the app with gunicorn, and checks `/api/health`. When it responds, the site is live. Every later push to GitHub triggers a new deploy automatically.

### Q167. What's in `render.yaml`? [Medium]

The service type (web), plan (free), build command, start command, health-check path, auto-deploy on, and the Python version (3.13.5). It's "infrastructure as code": the deployment is described in a file, not set up by hand.

### Q168. Why Render? [Medium]

It runs any Python web app, connects to GitHub, gives HTTPS, and has a free plan. I compared alternatives: Hugging Face Spaces now reportedly requires paid plans for Docker apps, Streamlit Cloud only runs Streamlit apps, and static hosts like GitHub Pages can't run a Python server.

### Q169. What are the free plan's limits? [Easy]

512 MB memory, 0.1 CPU, and the app **sleeps after 15 minutes** without visitors; the next visit takes about a minute to wake it. That's why I open the link a few minutes before a demo.

### Q170. What is Docker? Did you use it? [Medium]

Docker packages an app with everything it needs (operating-system parts, Python version, libraries) into a **container** that runs the same everywhere. I wrote a `Dockerfile` so the app can run on any container host. Render doesn't need it because it builds Python apps directly.

### Q171. What's in your Dockerfile? [Hard]

Start from the official Python 3.13 slim image, install the 5 web libraries, copy the app code and artifacts, create and switch to a non-admin user for security, expose port 7860, and start gunicorn. A `.dockerignore` keeps tests and docs out to keep the image small.

### Q172. Why are there two requirements files? [Medium]

`requirements.txt` has only what the **website** needs (5 packages) so deployment is small and fast. `requirements-train.txt` adds scikit-learn and pytest for training and testing.

### Q173. What is Git? What is GitHub? [Easy]

**Git** is a version control tool: it records every change to your code so you can see history and undo mistakes. **GitHub** is a website that hosts Git repositories online, for backup, sharing and collaboration.

### Q174. What's a commit, a push and a branch? [Easy]

**Commit:** a saved snapshot of changes with a message. **Push:** upload your commits to GitHub. **Branch:** a separate line of work, so you can try changes without affecting the main version.

### Q175. What's in `.gitignore`? [Easy]

Files that should never be uploaded: Python cache files, my local virtual environment (`.venv`), Mac `.DS_Store` files, and secret `.env` files.

### Q176. What problems did you face in deployment? [Medium]

- The free tier sleeps, so I documented opening the link early.
- The `.github/workflows` folder couldn't be created locally, so the CI file had to be added on GitHub directly.
- The package versions need Python 3.11+, which older Macs don't have.
- gunicorn couldn't be tested in my build environment, so I tested with Flask's server and an automated browser instead.

(Adjust this to what actually happened when you deployed.)


# 15. Scaling, production & MLOps

### Q177. How would this work for 10,000 products and 500 stores? [Hard]

Training: the global model scales well, but I'd move from pandas to something like Polars or Spark for data prep, and train on a bigger machine or a scheduled cloud job. Storage: move forecasts to a database and fetch per request instead of loading everything into memory. Serving: the API is stateless, so I can run more copies behind a load balancer.

### Q178. What does "stateless" mean, and why does it matter? [Hard]

The server doesn't remember anything between requests; every request has all it needs. So any copy of the server can answer any request, which makes it easy to run more copies when traffic grows.

### Q179. How would you know if the model gets worse over time? [Medium]

Monitoring: every week, compare last week's forecasts with actual sales and track WAPE, bias and interval coverage over time. Alert if they cross a threshold. Also watch for **data drift**: inputs like prices or sales levels moving outside what the model was trained on. I didn't build this, but it's the next step for production.

### Q180. What's data drift vs concept drift? [Hard]

**Data drift:** the inputs change (new price ranges, new stores). **Concept drift:** the relationship changes (customers become more price-sensitive). Both make a model less accurate over time; retraining and monitoring handle them.

### Q181. How often would you retrain? [Medium]

Weekly is typical for retail daily forecasts, plus immediately after big changes like a new store or a pricing strategy change. It would be automated with a scheduled job and checks that the new model beats the old one before publishing (champion/challenger again).

### Q182. What's MLOps? [Medium]

Practices for running ML in production reliably: versioning data and models, automated training pipelines, testing, deployment, monitoring and retraining. My project has some of it (pipeline, tests, CI, auto-deploy, champion/challenger) but not monitoring or scheduled retraining.

### Q183. How would you handle stock-outs in training data? [Hard]

On a stock-out day, recorded sales are zero but real demand wasn't. That's **censored demand**. I'd detect those days (my anomaly module already does) and either exclude them from training or replace them with an estimate of true demand, so the model doesn't learn to under-forecast.

### Q184. What's hierarchical forecasting and reconciliation? [Hard]

Forecasts exist at many levels (product, store, category, total) and should add up. I used **bottom-up**: forecast the lowest level and sum. **Reconciliation** methods like MinT combine forecasts from all levels to get coherent and often more accurate results. That's a possible improvement.

### Q185. How would you explain one specific forecast to a manager? [Hard]

Show the feature contributions for that forecast: "normal level for this product is 40, +8 because it's Saturday, +12 for the promotion, +15 for Diwali". Tools like SHAP give this per prediction. My project shows global feature importance, not per-forecast explanations; SHAP would be the next step.


# 16. Numbers cheat sheet

Know these. Everything on your resume should be on this page.

| What | Number |
|---|---|
| Stores / products / categories | 6 / 30 / 5 |
| Product-store series | 180 |
| History | 1 Nov 2023 - 31 Oct 2026 (3 years) |
| Rows | 197,280 |
| Forecast horizon | 28 days (1-28 Nov 2026) |
| Features | 30 |
| Backtest | 4 rounds, 3 reported, 15,120 forecasts |
| Champion | Gradient boosting (scikit-learn HistGradientBoosting) |
| WAPE: naive / Holt-Winters / champion / ensemble | 39.1% / 31.6% / 25.9% / 27.8% |
| Error reduction vs naive | 34% |
| Champion MASE / bias | 0.71 / -0.5% |
| WAPE at company-day level | 3.5% |
| WAPE for product-store 4-week totals | 8.9% |
| 80% interval coverage | 76.9% raw → 78.7% calibrated |
| Elasticity: estimate vs truth | within 0.05 for all 5 categories |
| Anomalies | 548 planted, 395 found: recall 72%, precision 64% |
| Inventory | 24 Critical, 3 Reorder, 13 Overstock, 140 Healthy |
| Pipeline run time | about 110 seconds |
| Artifacts | 7 JSON files, 1.9 MB |
| Web app | about 145 MB memory, about 1 s startup |
| Tests | 32 |
| Code | about 2,400 lines |


# 17. Behavioural & tricky questions

### Q186. What was the hardest part? [Easy]

Pick one true story and tell it as **problem → what I tried → result → lesson**:

- "The ensemble I expected to win lost. I tried 7 variations, none beat the single model, so I changed the design to champion/challenger. Lesson: test assumptions, don't follow rules of thumb blindly."
- "My first anomaly detector had 21% precision. I rebuilt it with a model that understands count data, and got to 64% precision and 72% recall."

### Q187. What did you learn? [Easy]

"That evaluation matters more than the model: a fancy model with leaky testing is worse than a simple one tested honestly. That a model is only useful once it drives a decision, like a reorder. And how all the parts of a product connect: data, model, API, frontend and deployment."

### Q188. What are the project's limitations? [Medium]

Say these before they find them:

- Simulated data, cleaner than real data.
- Stock-out days aren't corrected in training.
- Diwali effects learned from only 3 years.
- The what-if simulator is simple (constant elasticity).
- Coverage 78.7%, slightly under the 80% target.
- The anomaly threshold was tuned on the same data it's scored on.
- No hyperparameter search, no monitoring, no scheduled retraining.
- Free hosting sleeps after 15 minutes.

### Q189. Did you use AI tools like ChatGPT or Claude? [Medium]

**Be honest.** Interviewers increasingly expect it, and lying is easy to catch with follow-up questions. A good answer:

"Yes, I used an AI assistant to help build parts of it, the same way engineers use them at work now. What I focused on was understanding every part: I ran each component myself, broke things on purpose to see what the tests catch, deployed it, and I can explain every design choice and its trade-offs. Ask me about any part."

Then make sure that's true: work through the hands-on workbook.

### Q190. Can you walk me through the code? [Medium]

Know where things are:

| Topic | File → function |
|---|---|
| Data simulator | `data.py` → `generate()` |
| Features | `features.py` → `build_features()` |
| Holt-Winters | `models.py` → `class HoltWinters` |
| Gradient boosting | `models.py` → `class GlobalGBM` |
| Backtest | `pipeline.py` → `backtest()` |
| Champion choice | `pipeline.py` → `pick_champion()` |
| Conformal calibration | `models.py` → `conformal_quantile()` |
| Inventory | `analytics.py` → `inventory_policy()` |
| Elasticity | `analytics.py` → `price_response()` |
| Anomalies | `analytics.py` → `detect_anomalies()` |
| API | `app.py` |
| Charts | `static/charts.js` |

### Q191. If you had two more weeks, what would you add? [Easy]

"Run it on the real M5 dataset from Walmart, add hyperparameter tuning, a weekly scheduled retraining job with accuracy monitoring, and correct stock-out days in the training data."

### Q192. Your model is wrong for a product and the manager is angry. What do you do? [Medium]

"First check the data for that product: a stock-out, a price error, or a new promotion the model didn't know about. Look at the backtest error for that product to see if it's always hard. Explain the range, not just the number: if the actual was inside the 80% range, the forecast did its job. Then fix the cause: correct the data, add a missing feature, or give that product more safety stock."

### Q193. Why should we trust your 34% number? [Hard]

"It's measured on 15,120 forecasts the model never saw, across three separate 28-day periods, with every decision for each period made only from earlier data. There's an automatic test against leakage. And it's measured against a standard benchmark, not a weak straw man."

### Q194. Isn't checking against your own simulator circular? [Hard]

"Partly, and that's a fair point. The simulator uses the same kind of multiplicative formula my elasticity regression assumes, which makes recovery easier than with real data. So the ground-truth checks prove the code is **correct**, not that it would be equally accurate on messy real data. That's exactly why running it on a real dataset is my top next step."

### Q195. What would break first in production? [Hard]

"Probably the data: missing days, new products with no history, or a store closing. The model has no special handling for new products (the cold-start problem). I'd add a fallback, like using the category average for new products until they have enough history."

### Q196. Explain this project to a 10-year-old. [Easy]

"A shop needs to know how many toys to buy, so it doesn't run out or have too many. I made a computer program that looks at what the shop sold in the past, notices patterns like 'more toys sell on weekends and at Diwali', and guesses how many it will sell next month. Then it tells the shop how many to order. And it shows all of this on a website."

---

**Last tip:** before any interview, open your live link a few minutes early so it's awake, re-read Section 16, and have the GitHub repository open in a tab. Good luck!
