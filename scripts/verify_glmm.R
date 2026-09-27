# Optional independent implementation check. Requires R and lme4; not run on this Mac.
library(lme4)
d <- read.csv('reports/power-decisions.csv')
d <- subset(d, cell == 'corrupt_no' & error == '' & unreadable == '')
d$base <- interaction(d$task, d$base_id, drop=TRUE)
d$action_tied <- as.integer(d$wording_type == 'action')
d$refusal <- as.integer(d$action == 'refuse')
fit <- glmer(refusal ~ action_tied + (1 | base) + (1 | wording) + (1 | task),
             data=d, family=binomial, nAGQ=1,
             control=glmerControl(optimizer='bobyqa', optCtrl=list(maxfun=200000)))
print(summary(fit))
print(exp(cbind(OR=fixef(fit), confint(fit, parm='beta_', method='Wald'))))
