# Script to find the right balance b/w loan and the investment. We'll be using following inputs:
# 1. loan_interest - interest charged by the loan.
# 2. tax_reimbursement_max_interest_limit - Govt give a tax savings on loan interest till a given amount. Assuming that tax is 30% of a person's income, govt doesn't charge tax for the money paid as loan interest till a given limit.
# 3. investment_returns - Returns if the money was invested for an investment
# 4. emi_amount - amount to be paid monthly
# 5.

from mpl_toolkits.mplot3d import Axes3D
import pyinputplus as pyip
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm

user_variables = {
  "loan_amount": 800000,
  "loan_interest_rate": 8,
  "savings_monthly": 100000,
  "investment_returns": 8,
  "investment_returns_tax_rate": 10,
  "investment_time_interval": 10,
  "initial_month": 10,
}

calendar_month_dict = {"Jan":0, "Feb":1, "Mar":2, "Apr":3, "May":4, "Jun":5,
  "Jul":6, "Aug":7, "Sep":8, "Oct":9, "Nov":10, "Dec":11}

def get_user_input():
  user_variables = {}
  user_variables["loan_amount"] = pyip.inputInt("Enter loan amount: ",
    greaterThan = 0)
  print(user_variables["loan_amount"])

  user_variables["loan_interest_rate"] = pyip.inputNum("Enter loan interest"+\
    " rate(%): ", min = 0, lessThan = 100)
  print(user_variables["loan_interest_rate"])

  user_variables["savings_monthly"] = pyip.inputInt("Monthly savings: ",
    greaterThan = 0)
  print(user_variables["savings_monthly"])

  user_variables["investment_returns"] = pyip.inputNum("Investment returns"+\
    " rate(%): ", min = 0, lessThan = 100)
  print(user_variables["investment_returns"])

  user_variables["investment_returns_tax_rate"] = pyip.inputNum("Investment"+\
    " returns tax rate after indexation adjustment(%): ", min = 0,
    lessThan = 100)
  print(user_variables["investment_returns_tax_rate"])

  user_variables["investment_time_interval"] = pyip.inputInt("Investment"+\
    " Time Interval in years: ", min = 0, lessThan = 100)
  print(user_variables["investment_time_interval"])

  initial_month = pyip.inputMenu(list(calendar_month_dict.keys()))
  user_variables["initial_month"] = calendar_month_dict[initial_month]
  print(initial_month)

  return user_variables

# Get emi_breakdown for a given month
def get_emi_breakdown(loan_balance, loan_interest_rate, emi, abs_cal_offset):

  monthly_statement = {}
  monthly_statement["loan_balance"] = loan_balance

  monthly_interest = (loan_balance * loan_interest_rate)/(100*12)
  monthly_statement["monthly_interest"] = monthly_interest
  monthly_statement["abs_cal_offset"] = abs_cal_offset

  if loan_balance + monthly_interest <= emi:
    emi_paid = loan_balance + monthly_interest
    monthly_statement["emi_paid"] = emi_paid
    monthly_statement["principal_paid"] = loan_balance
    monthly_statement["outstanding_loan"] = 0
    return monthly_statement

  emi_paid = emi
  principal_paid = emi_paid - monthly_interest
  outstanding_loan = loan_balance - principal_paid
  monthly_statement["emi_paid"] = emi_paid
  monthly_statement["principal_paid"] = principal_paid
  monthly_statement["outstanding_loan"] = outstanding_loan
  return monthly_statement

def get_investment_statement(principal, sip_amount, returns_rate):
  investment_statement = {}
  investment_statement["principal"] = principal
  returns = (principal * returns_rate)/(100 * 12)
  investment_statement["returns"] = returns
  investment_statement["sip_amount"] = sip_amount
  investment_statement["new_principal"] = principal + sip_amount + returns
  return investment_statement

# Tax rebate on home loan
def get_prev_year_tax_rebate(loan_sheet, abs_cal_offset):

  prev_year_loan_interest = 0
  for statement in reversed(loan_sheet):
    if abs_cal_offset - statement["abs_cal_offset"] > len(calendar_month_dict):
      break
    prev_year_loan_interest += statement["monthly_interest"]

  tax_rebate = (max(200000, prev_year_loan_interest)*0.3)
  return tax_rebate

def spend_monthly_savings(loan_sheet, investment_sheet, emi, user_variables,
  calendar_offset):
  savings = user_variables["savings_monthly"]
  loan_interest = user_variables["loan_interest_rate"]
  abs_cal_offset = (user_variables['initial_month'] + calendar_offset)

  # If its month of april
  # Sum up interest for the last financial year and calculate the tax savings.
  # we'll adjust those tax savings to the principal investment.
  if abs_cal_offset % len(calendar_month_dict) == calendar_month_dict["Apr"]:
    tax_rebate = get_prev_year_tax_rebate(loan_sheet,
      abs_cal_offset)
    investment_sheet[-1]["new_principal"] += tax_rebate

  sip_amount = savings
  outstanding_loan = loan_sheet[-1]["outstanding_loan"]
  if outstanding_loan > 0:
    loan_statement = get_emi_breakdown(outstanding_loan,
      loan_interest, emi, abs_cal_offset)
    loan_sheet.append(loan_statement)
    sip_amount = savings - loan_statement["emi_paid"]

  investment_returns = user_variables["investment_returns"]
  investment_principal = investment_sheet[-1]["new_principal"]

  investment_statement = get_investment_statement(investment_principal,
    sip_amount, investment_returns)
  investment_sheet.append(investment_statement)

  return loan_sheet, investment_sheet

def get_overall_returns(loan_sheet, investment_sheet, user_variables):
  investment_tax_rate = user_variables["investment_returns_tax_rate"]

  total_outstanding_loan = loan_sheet[-1]["outstanding_loan"]

  # Returns
  total_return_before_tax = investment_sheet[-1]["new_principal"]
  total_sip_paid = 0
  for statement in investment_sheet:
    total_sip_paid += statement["sip_amount"]

  total_investment = investment_sheet[0]["principal"] + total_sip_paid

  total_profits_before_tax = total_return_before_tax - total_investment
  total_profits_after_tax = (total_profits_before_tax*(100 -
    investment_tax_rate))/100

  return total_profits_after_tax + total_investment - total_outstanding_loan

def create_financial_report(initial_investment, emi, user_variables):
  print("Creating report for Initial Investment:", initial_investment,
    "User config:", user_variables)
  time_interval = user_variables["investment_time_interval"]

  initial_loan_statement = {
    "loan_balance": initial_investment,
    "emi_paid": 0,
    "principal_paid": 0,
    "outstanding_loan": initial_investment,
    "monthly_interest": 0,
    "abs_cal_offset": user_variables["initial_month"],
  }
  loan_sheet = [initial_loan_statement]

  initial_investment_statement = {
    "principal": initial_investment,
    "returns": 0,
    "sip_amount": 0,
    "new_principal": initial_investment,
  }
  investment_sheet = [initial_investment_statement]

  for offset in range(time_interval*12):
    loan_sheet, investment_sheet = spend_monthly_savings(loan_sheet,
      investment_sheet, emi, user_variables, offset)

  return get_overall_returns(loan_sheet, investment_sheet, user_variables)


def get_sample_emi_returns(initial_investment, user_variables):
  savings = user_variables["savings_monthly"]
  loan_interest = user_variables["loan_interest_rate"]
  outstanding_loan = initial_investment

  min_emi = (outstanding_loan * loan_interest)/(100*12)
  max_emi = savings

  if min_emi >= max_emi:
    print("This is wrong config and not sustainable.",
      "Initial Investment:", initial_investment, "User config:",
      user_variables)
    return []

  for sample in range(num_samples+1):
    emi = min_emi + (sample*(max_emi-min_emi))/num_samples
    returns = create_financial_report(initial_investment, emi, user_variables)
    overall_returns_chart.append({
      "initial_investment": initial_investment,
      "EMI": emi,
      "returns": returns,
    })
  return

num_samples = 10
overall_returns_chart = []

def main():
  # user_variables = get_user_input()
  print(user_variables)

  min_investment = 0
  max_investment = user_variables["loan_amount"]


  for sample in range(num_samples+1):
    initial_investment = min_investment +\
      (sample*(max_investment - min_investment))/num_samples
    get_sample_emi_returns(initial_investment, user_variables)

  print("RETURNS CHART:", overall_returns_chart)
  # create dataframe
  df = pd.DataFrame(overall_returns_chart)
  print(df.to_string())

  fig = plt.figure(figsize=(10,8))
  ax = fig.add_subplot(111, projection='3d')

  surf = ax.plot_trisurf(df["initial_investment"], df["EMI"], df["returns"],
    cmap= cm.coolwarm, linewidth=0.2)
  ax.set_xlabel("Initial Investment")
  ax.set_ylabel("EMI")
  ax.set_zlabel("Returns")

  plt.show()

# Using the special variable 
# __name__
if __name__=="__main__":
  main()

