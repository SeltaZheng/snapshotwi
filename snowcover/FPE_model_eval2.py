"""
evaluating the multi-site model performance on sites outside of the training set
comparing multi-site predictions against timelapse site-specific predictions
Ting Zheng
04/15/2026
"""

import glob, os

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

dir_in = r'D:\GoogleDrive\Projects_ongoing\snapshotWI\snowcover\FPE_model'
dir_plt = r'D:\GoogleDrive\Projects_ongoing\snapshotWI\snowcover\plt\multi_sites'
df = pd.read_csv(f'{dir_in}/PROVISIONAL_FPE_model_results_user_output_2026-03-16_Snowsites.csv')
dir_pred = r'D:\GoogleDrive\Projects_ongoing\snapshotWI\snowcover\FPE_model\models\multi_sites\pred'

sites = glob.glob(f'{dir_pred}/*/')

for site in sites:
    site_name = site.split('\\')[-2]
    df_pred = pd.read_csv(f'{site}/pred.csv')
    df_comb = pd.merge(df_pred, df, on='filename', how='inner')
    if site_name == 'ADAM016':
        # # multi-sites vs. motion photo single site
        df_comb1 = df_comb[df_comb['station_name'] == 'ADAM016']
        # fig, ax = plt.subplots(figsize=(10, 6))
        # ax.scatter(df_comb1['score_x'], df_comb1['score_y'])
        # ax.set_xlabel('multi-site prediction score')
        # ax.set_ylabel('motion photo single site prediction score')
        # ax.set_title(site_name)
        # plt.tight_layout()
        # # plt.show()
        # plt.savefig(f'{dir_plt}/{site_name}_model_comp1.png')
        # plt.close()

        # temporal plot
        df_comb1['date'] = pd.to_datetime(df_comb1['timestamp_x'])
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(df_comb1['date'], df_comb1['score_x'], marker='o', color='tab:orange',
                label='multi-site prediction score')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.tick_params(axis='x', labelrotation=45)
        ax2 = ax.twinx()
        ax2.plot(df_comb1['date'], df_comb1['score_y'], marker='o', color='tab:green',
                 label='motion photo single site prediction score')
        ax2.xaxis.set_visible(False)
        # Collect all handles and labels
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        # Combine and show as a single legend
        ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
        plt.tight_layout()
        # plt.show()
        plt.savefig(f'{dir_plt}/{site_name}_temporal_plot1.png')
        plt.close()

        df_comb = df_comb[df_comb['station_name'] == 'timelapse_ADAM016']
    # plot:
    # # scatter plot comparing all vs. daily only photo:
    # fig, ax = plt.subplots(figsize=(10, 6))
    # ax.scatter(df_comb['score_x'], df_comb['score_y'])
    # ax.set_xlabel('multi-site prediction score')
    # ax.set_ylabel('daily timelapse prediction score')
    # ax.set_title(site_name)
    # plt.tight_layout()
    # # plt.show()
    # plt.savefig(f'{dir_plt}/{site_name}_model_comp.png')
    # plt.close()


    # temporal plot
    df_comb['date'] = pd.to_datetime(df_comb['timestamp_x'])
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df_comb['date'], df_comb['score_x'], marker='o', color='tab:orange', label='multi-site prediction score')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.tick_params(axis='x', labelrotation=45)
    ax2 = ax.twinx()
    ax2.plot(df_comb['date'], df_comb['score_y'], marker='o', color = 'tab:green', label='daily timelapse prediction score')
    ax2.xaxis.set_visible(False)
    # Collect all handles and labels
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    # Combine and show as a single legend
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
    plt.tight_layout()
    # plt.show()
    plt.savefig(f'{dir_plt}/{site_name}_temporal_plot.png')
    plt.close()