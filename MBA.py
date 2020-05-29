import os

import seaborn
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
import numpy as np
import matplotlib.pyplot as plt

from config import output_directory
from helper_scripts.Commit_date_helper import add_file_dates
from helper_scripts.components_helper import get_components
from helper_scripts.file_pair_helper import filter_duplicate_file_pairs, generate_all_pairs
from helper_scripts.smell_helper import get_class_from_package


def perform_mba():
    components = get_components()
    # group names by version
    grouped_comp = components.groupby('version')['name'].apply(list).reset_index(name='shoppingList')
    components_list = grouped_comp['shoppingList']
    # encode list of transactions to a dataframe
    te = TransactionEncoder()
    te_ary = te.fit(components_list).transform(components_list)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    # perform mba
    rules = generate_basket_rules(df)
    rules['file1'] = list(map(lambda x: next(iter(x)), rules['antecedents']))
    rules['file2'] = list(map(lambda x: next(iter(x)), rules['consequents']))
    return rules, components['name']


def generate_basket_rules(df):
    all_itemsets = apriori(df, min_support=0.0000001, use_colnames=True, max_len=2)
    all_itemsets.to_pickle(output_directory + "/mba_support_0.pkl")
    supp0 = sorted(all_itemsets['support'])
    print("----threshold results mba support----")
    print("quartile values:")
    firstquartile = np.percentile(supp0, 25)
    median = np.percentile(supp0, 50)
    thirdquartile = np.percentile(supp0, 75)
    print("90% at threshold: ", np.percentile(supp0, 90))
    print("95% at threshold: ", np.percentile(supp0, 95))
    print(firstquartile, median, thirdquartile)


    rules = association_rules(all_itemsets, metric="confidence", min_threshold=0.0)
    rules.to_pickle(output_directory + "/mba_conf_0_supp_0.pkl")
    conf_0_supp0 = sorted(rules['confidence'])
    print("----threshold results mba confidence without support threshold----")
    print("quartile values:")
    firstquartile = np.percentile(conf_0_supp0, 25)
    median = np.percentile(conf_0_supp0, 50)
    thirdquartile = np.percentile(conf_0_supp0, 75)
    print("90% at threshold: ", np.percentile(conf_0_supp0, 90))
    print("95% at threshold: ", np.percentile(conf_0_supp0, 95))
    print(firstquartile, median, thirdquartile)



    frequent_itemsets = apriori(df, min_support=0.02, use_colnames=True, max_len=2)
    frequent_itemsets.to_pickle(output_directory + "/mba_support_2.pkl")
    supp2 = sorted(frequent_itemsets['support'])

    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.0)
    rules.to_pickle(output_directory + "/mba_conf_0_supp_2.pkl")

    conf_0_supp2 = sorted(rules['confidence'])

    #TODO: extract to proper function
    #seaborn.violinplot(data=supp0)
    #plt.show()
    #seaborn.violinplot(data=conf_0_supp0)
    #plt.show()
    #seaborn.violinplot(data=supp2)
    #plt.show()
    #seaborn.violinplot(data=conf_0_supp2)
    #plt.show()

    print("----threshold results mba confidence after support threshold----")
    print("quartile values:")
    firstquartile = np.percentile(conf_0_supp2, 25)
    median = np.percentile(conf_0_supp2, 50)
    thirdquartile = np.percentile(conf_0_supp2, 75)
    print("90% at threshold: ", np.percentile(conf_0_supp2, 90))
    print("95% at threshold: ", np.percentile(conf_0_supp2, 95))
    print(firstquartile, median, thirdquartile)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.8)
    rules.to_pickle(output_directory + "/mba_conf_8.pkl")
    return rules


def generate_mba_analysis_files():
    # Create the directory
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    rules, changed_files = perform_mba()

    # 1) Build the dataframe containing the co-changes
    rules = filter_duplicate_file_pairs(rules)  # df: file1, file2
    # Add package columns
    rules['package1'] = rules["file1"].str.rsplit(".", 1).str[0]
    rules['package2'] = rules["file2"].str.rsplit(".", 1).str[0]
    rules_with_dates = add_file_dates(rules)
    # Map files to class.java
    rules_with_dates['file1'] = rules_with_dates['file1'].apply(get_class_from_package)
    rules_with_dates['file2'] = rules_with_dates['file2'].apply(get_class_from_package)

    # 2) Build the dataframe containing all changed pairs
    all_pairs = generate_all_pairs(changed_files)  # df: file1, file2
    all_pairs['package1'] = all_pairs["file1"].str.rsplit(".", 1).str[0]
    all_pairs['package2'] = all_pairs["file2"].str.rsplit(".", 1).str[0]
    # Map files to class.java
    all_pairs['file1'] = all_pairs['file1'].apply(get_class_from_package)
    all_pairs['file2'] = all_pairs['file2'].apply(get_class_from_package)

    rules_with_dates.to_csv(output_directory + "/mba.csv")
    all_pairs.to_csv(output_directory + "/file_pairs_mba.csv")


